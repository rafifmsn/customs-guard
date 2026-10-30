"""Regression test suite executing canonical prompts against reference dossiers in scenarios/expected-outputs/."""

import json
import os
import re
import pytest
from unittest.mock import patch, MagicMock
from scripts.customs_components import CustomsGuardToolkitComponent


@pytest.fixture
def audit_tools():
    component = CustomsGuardToolkitComponent()
    tools = component.build_tools()
    return {t.name: t for t in tools}


def _extract_json_from_prompt(prompt_path: str) -> dict:
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"(\{[\s\S]*?\})\s*```", content)
    if not match:
        raise ValueError(f"Could not extract JSON from {prompt_path}")
    return json.loads(match.group(1))


def test_scenario_01_high_risk_discrepancy(audit_tools):
    """Scenario 01: High risk classification evasion, SDPPI requirement, detention risk."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_file = os.path.join(base_dir, "scenarios", "prompts", "01_high_risk_discrepancy_prompt.md")
    expected_file = os.path.join(base_dir, "scenarios", "expected-outputs", "01_high_risk_dossier.md")

    invoice = _extract_json_from_prompt(prompt_file)

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8517.11",
                        "duty_rate": 0.0,
                        "restricted": True,
                        "required_permits": ["Telecommunication Type Approval / SDPPI Certification (Kemkominfo)"]
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res_raw = audit_tools["audit_shipment_compliance"].invoke({"invoice_json": json.dumps(invoice)})
        audit_res = json.loads(res_raw)

    assert audit_res["shipment_id"] == "SHP-2026-0042"
    assert audit_res["overall_status"] == "NON_COMPLIANT_HIGH_RISK"
    assert audit_res["container_detention_risk"] is True
    assert audit_res["container_count"] == 4
    # 4 containers * $101/day (Slab 1, 40ft Dry Standard) = $404/day
    assert audit_res["estimated_demurrage_per_day_usd"] == 404.0
    assert audit_res["findings"][0]["restricted"] is True
    assert any("SDPPI" in p for p in audit_res["findings"][0]["required_permits"])

    with open(expected_file, "r", encoding="utf-8") as f:
        expected_md = f.read()
    assert "NON_COMPLIANT_HIGH_RISK" in expected_md
    assert "$404.00 USD / day" in expected_md


def test_scenario_02_demurrage_detention(audit_tools):
    """Scenario 02: Multi-container scaled demurrage calculation."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_file = os.path.join(base_dir, "scenarios", "prompts", "02_demurrage_detention_prompt.md")
    expected_file = os.path.join(base_dir, "scenarios", "expected-outputs", "02_demurrage_detention_dossier.md")

    invoice = _extract_json_from_prompt(prompt_file)

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "9018.12",
                        "duty_rate": 0.0,
                        "restricted": True,
                        "required_permits": ["Medical Device Distribution License / Izin Edar (Kemenkes)"]
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res_raw = audit_tools["audit_shipment_compliance"].invoke({"invoice_json": json.dumps(invoice)})
        audit_res = json.loads(res_raw)

    assert audit_res["shipment_id"] == "SHP-2026-0089"
    assert audit_res["overall_status"] == "NON_COMPLIANT_HIGH_RISK"
    assert audit_res["container_count"] == 3
    # 3 containers * $66.00/day (20ft Dry, Slab 1) = $198.00/day
    assert audit_res["estimated_demurrage_per_day_usd"] == 198.0
    assert audit_res["total_duty_shortfall_usd"] == 0.0

    with open(expected_file, "r", encoding="utf-8") as f:
        expected_md = f.read()
    assert "$198.00 USD / day" in expected_md


def test_scenario_03_duty_restitution(audit_tools):
    """Scenario 03: Duty overpayment restitution recovery."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_file = os.path.join(base_dir, "scenarios", "prompts", "03_duty_restitution_prompt.md")
    expected_file = os.path.join(base_dir, "scenarios", "expected-outputs", "03_restitution_dossier.md")

    invoice = _extract_json_from_prompt(prompt_file)

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8471.50",
                        "duty_rate": 0.0,
                        "restricted": False,
                        "required_permits": []
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res_raw = audit_tools["audit_shipment_compliance"].invoke({"invoice_json": json.dumps(invoice)})
        audit_res = json.loads(res_raw)

    assert audit_res["shipment_id"] == "SHP-2026-0099"
    assert audit_res["total_duty_shortfall_usd"] == 0.0
    # 15% declared vs 0% official on $100,000 = $15,000 restitution
    assert audit_res["total_restitution_usd"] == 15000.0
    assert audit_res["container_detention_risk"] is False

    with open(expected_file, "r", encoding="utf-8") as f:
        expected_md = f.read()
    assert "$15,000.00 USD" in expected_md


def test_scenario_04_compliant_audit(audit_tools):
    """Scenario 04: Fully compliant shipment with zero risk."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_file = os.path.join(base_dir, "scenarios", "prompts", "04_compliant_audit_prompt.md")
    expected_file = os.path.join(base_dir, "scenarios", "expected-outputs", "04_compliant_dossier.md")

    invoice = _extract_json_from_prompt(prompt_file)

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8471.50",
                        "duty_rate": 0.0,
                        "restricted": False,
                        "required_permits": []
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res_raw = audit_tools["audit_shipment_compliance"].invoke({"invoice_json": json.dumps(invoice)})
        audit_res = json.loads(res_raw)

    assert audit_res["shipment_id"] == "SHP-2026-0105"
    assert audit_res["overall_status"] == "COMPLIANT"
    assert audit_res["total_duty_shortfall_usd"] == 0.0
    assert audit_res["total_restitution_usd"] == 0.0
    assert audit_res["container_detention_risk"] is False

    with open(expected_file, "r", encoding="utf-8") as f:
        expected_md = f.read()
    assert "COMPLIANT" in expected_md
    assert "$0.00 USD" in expected_md
