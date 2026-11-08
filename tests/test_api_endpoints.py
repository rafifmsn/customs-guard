"""Automated endpoint tests for the CustomsGuard FastAPI backend."""

import asyncio
import json
import os
import shutil
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import BOB_SEMAPHORE, app

client = TestClient(app)


def test_openapi_schema_generated():
    """Verify programmatic OpenAPI and Swagger schema generation."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "CustomsGuard Autonomous Trade Compliance API"
    paths = schema["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/audit" in paths
    assert "/api/v1/reports" in paths
    assert "/api/v1/assistant" in paths


def test_health_endpoint():
    """Verify /api/v1/health returns structured service checks."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "qdrant" in data
    assert "langflow" in data
    assert "mailpit" in data


def test_audit_endpoint_and_reports_archive():
    """Verify /api/v1/audit executes deterministic audit, exports dossier, and lists in /api/v1/reports."""
    payload = {
        "shipment_id": "TEST-API-SHP-001",
        "importer_name": "PT API Verification Indo",
        "carrier": "CMA CGM",
        "destination_port": "Tanjung Priok, Jakarta (IDTPP)",
        "container_count": 2,
        "container_size": "40",
        "container_type": "DRY",
        "days_held_projected": 10,
        "items": [
            {
                "item_id": 1,
                "declared_description": "Apple iPhone 15 Pro Max Smartphone",
                "declared_hs_code": "8471.30",
                "quantity": 50,
                "unit_price": 1000.0,
                "total_value": 50000.0,
                "declared_duty_rate": 0.0,
            }
        ],
    }

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8517.11",
                        "duty_rate": 5.0,
                        "restricted": True,
                        "required_permits": [
                            "Telecommunication Type Approval / SDPPI Certification (Kemkominfo)"
                        ],
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    mock_smtp = MagicMock()
    mock_smtp.__enter__.return_value = mock_smtp

    with patch("urllib.request.urlopen", return_value=mock_resp), patch(
        "smtplib.SMTP", return_value=mock_smtp
    ):
        resp = client.post("/api/v1/audit", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    audit = body["audit"]
    assert audit["shipment_id"] == "TEST-API-SHP-001"
    assert audit["overall_status"] == "NON_COMPLIANT_HIGH_RISK"
    assert audit["container_detention_risk"] is True
    assert audit["total_duty_shortfall_usd"] == 2500.0
    assert audit["estimated_demurrage_per_day_usd"] == 202.0
    assert "### Executive Summary" in body["markdown_dossier"]
    assert "Alert email queued in Mailpit" in body["alert_status"]

    report_path = body["report_path"]
    assert os.path.isfile(report_path)

    # Verify /api/v1/reports includes the newly archived report
    reports_resp = client.get("/api/v1/reports")
    assert reports_resp.status_code == 200
    reports = reports_resp.json()
    matching = [r for r in reports if r["shipment_id"] == "TEST-API-SHP-001"]
    assert len(matching) >= 1
    assert "### Itemized Audit Findings" in matching[0]["markdown_content"]

    shutil.rmtree(os.path.dirname(report_path), ignore_errors=True)


def test_assistant_endpoint_bob_cli_success():
    """Verify /api/v1/assistant spawns bob CLI in isolated session and parses NDJSON."""
    fake_proc = MagicMock()
    fake_proc.pid = 99991
    fake_proc.returncode = 0
    ndjson_line = json.dumps(
        {
            "type": "result",
            "status": "success",
            "last_message": "HS 8517.11 requires mandatory SDPPI Type Approval certification.",
        }
    )
    fake_proc.communicate = AsyncMock(return_value=(ndjson_line.encode("utf-8"), b""))

    with patch(
        "asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)
    ) as mock_exec:
        resp = client.post(
            "/api/v1/assistant",
            json={"prompt": "What permits are needed for HS 8517.11?", "timeout_seconds": 30},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["engine"] == "ibm-bob-cli"
    assert "SDPPI" in data["answer"]
    _, kwargs = mock_exec.call_args
    assert kwargs.get("start_new_session") is True


def test_assistant_endpoint_timeout_kills_process_group():
    """Verify /api/v1/assistant enforces timeout and kills process group via os.killpg."""
    fake_proc = MagicMock()
    fake_proc.pid = 88882

    async def slow_communicate():
        await asyncio.sleep(10)
        return (b"", b"")

    fake_proc.communicate = slow_communicate
    fake_proc.wait = AsyncMock(return_value=0)

    with patch(
        "asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)
    ), patch("os.killpg") as mock_killpg:
        resp = client.post(
            "/api/v1/assistant",
            json={"prompt": "Simulate hung CLI query", "timeout_seconds": 5},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "timeout"
    assert "exceeded hard timeout" in data["answer"]
    assert mock_killpg.called
    called_pids = [call.args[0] for call in mock_killpg.call_args_list]
    assert 88882 in called_pids


def test_assistant_endpoint_langflow_agent_online():
    """Verify /api/v1/assistant routes to Langflow regulatory agent when online."""
    with patch(
        "asyncio.create_subprocess_exec",
        new=AsyncMock(side_effect=FileNotFoundError("bob not found")),
    ), patch(
        "api.main._try_langflow_assistant",
        return_value="HS 8517.11 requires SDPPI Type Approval certification.",
    ):
        resp = client.post(
            "/api/v1/assistant",
            json={"prompt": "What permits are needed for HS 8517.11?"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["engine"] == "langflow-regulatory-agent"
    assert "SDPPI" in data["answer"]


def test_assistant_endpoint_local_rag_fallback():
    """Verify /api/v1/assistant falls back to local tariff RAG & CMA CGM engine if bob CLI is absent and Langflow is unreachable."""
    with patch(
        "asyncio.create_subprocess_exec",
        new=AsyncMock(side_effect=FileNotFoundError("bob not found")),
    ), patch("api.main._try_langflow_assistant", return_value=None):
        resp = client.post(
            "/api/v1/assistant",
            json={"prompt": "Explain CMA CGM demurrage slabs and HS 8517.11 permits"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "fallback"
    assert data["engine"] == "local-tariff-rag-fallback"
    assert "CMA CGM Indonesia" in data["answer"]
    assert "8517.11" in data["answer"]


def test_streamlit_zero_css_bloat_and_declarative_theme():
    """Verify ui/app.py preserves declarative theming via .streamlit/config.toml with zero layout bloat."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ui_path = os.path.join(base_dir, "ui", "app.py")
    config_path = os.path.join(base_dir, ".streamlit", "config.toml")
    compose_path = os.path.join(base_dir, "docker-compose.yml")

    assert os.path.isfile(ui_path)
    assert os.path.isfile(config_path)
    assert os.path.isfile(compose_path)

    with open(ui_path, "r", encoding="utf-8") as f:
        ui_code = f.read()
    # Verify zero layout CSS hacks; only typography/font protection is declared
    assert ui_code.count("<style>") <= 1
    assert "Material Symbols Rounded" in ui_code
    assert ".stButton" not in ui_code
    assert ".stMetric" not in ui_code

    with open(config_path, "r", encoding="utf-8") as f:
        toml_text = f.read()
    assert "[theme]" in toml_text
    assert "primaryColor" in toml_text
    assert "[theme.sidebar]" in toml_text

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_text = f.read()
    assert "customsguard-api:" in compose_text
    assert "customsguard-ui:" in compose_text

