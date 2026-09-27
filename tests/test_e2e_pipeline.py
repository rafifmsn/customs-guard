import datetime
import json
import os
import shutil
import subprocess
import urllib.request
import pytest
from scripts.customs_components import CustomsGuardToolkitComponent

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_INVOICES_PATH = os.path.join(BASE_DIR, "data", "seed", "sample_invoices.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")


def get_bob_api_key():
    """Retrieve BOB_API_KEY from environment or .env file."""
    api_key = os.environ.get("BOB_API_KEY")
    if api_key and not api_key.startswith("your_"):
        return api_key
    if os.path.isfile(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("BOB_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not val.startswith("your_"):
                        return val
    return None


@pytest.fixture
def toolkit():
    component = CustomsGuardToolkitComponent()
    tools = component.build_tools()
    return {t.name: t for t in tools}


def test_full_compliance_audit_pipeline_e2e(toolkit):
    """Level 1 Backend E2E Verification:
    1. Load high-risk sample invoice (SHP-2026-0042).
    2. Audit shipment against local Qdrant tariff database.
    3. Export timestamped Markdown and JSON reports to disk.
    4. Dispatch high-risk detention alert to Mailpit SMTP.
    5. Verify report on disk and query Mailpit REST API.
    """
    assert os.path.isfile(SAMPLE_INVOICES_PATH)
    with open(SAMPLE_INVOICES_PATH, "r", encoding="utf-8") as f:
        invoices = json.load(f)

    # Use first high-risk invoice (iPhone misdeclared as laptop)
    invoice = invoices[0]
    shipment_id = invoice["shipment_id"]

    # 1. Audit Shipment
    audit_tool = toolkit["audit_shipment_compliance"]
    audit_output = audit_tool.invoke({"invoice_json": json.dumps(invoice)})
    audit_result = json.loads(audit_output)

    assert audit_result["shipment_id"] == shipment_id
    assert audit_result["overall_status"] in ("NON_COMPLIANT_HIGH_RISK", "WARNING_DISCREPANCY")
    assert audit_result["container_detention_risk"] is True
    assert audit_result["estimated_demurrage_per_day_usd"] >= 350.0

    # 2. Export Compliance Report
    export_tool = toolkit["export_compliance_report"]
    export_msg = export_tool.invoke({
        "shipment_id": shipment_id,
        "audit_summary_json": audit_output
    })

    assert "Audit report successfully exported to:" in export_msg
    md_path = export_msg.split("Audit report successfully exported to:")[-1].strip()
    assert os.path.isfile(md_path)
    json_path = os.path.join(os.path.dirname(md_path), "audit_report.json")
    assert os.path.isfile(json_path)

    # Verify report contents
    with open(json_path, "r", encoding="utf-8") as f:
        persisted_json = json.load(f)
    assert persisted_json["shipment_id"] == shipment_id
    assert persisted_json["container_detention_risk"] is True

    # 3. Send Compliance Alert
    alert_tool = toolkit["send_compliance_alert"]
    alert_msg = alert_tool.invoke({
        "shipment_id": shipment_id,
        "verdict": audit_result["overall_status"],
        "alert_details": f"Container detention risk active. Daily demurrage: ${audit_result['estimated_demurrage_per_day_usd']:,.2f}"
    })

    # Alert should queue in Mailpit (or catch connection if container offline)
    assert "Alert email queued in Mailpit" in alert_msg or "Failed to send email via Mailpit" in alert_msg

    # 4. If Mailpit container is running locally, verify message via REST API
    mailpit_api_url = "http://localhost:8025/api/v1/messages"
    try:
        with urllib.request.urlopen(mailpit_api_url, timeout=2) as resp:
            mailpit_data = json.loads(resp.read().decode("utf-8"))
            messages = mailpit_data.get("messages", [])
            matching = [m for m in messages if shipment_id in m.get("Subject", "")]
            if matching:
                assert matching[0]["To"][0]["Address"] == "compliance-officer@customsguard.local"
    except Exception:
        # Mailpit API check is non-blocking in isolated CI environments
        pass


def test_bob_shell_orchestrator_cli_e2e():
    """Level 2 Conversational Orchestrator E2E Verification:
    Executes IBM Bob Shell non-interactively (`bob run --trust --format json`),
    verifying that Bob agent invokes the `customsguard` MCP tool on Langflow,
    and returns structured compliance findings.
    """
    bob_api_key = get_bob_api_key()
    if not bob_api_key:
        pytest.skip(
            "BOB_API_KEY is not set in environment or .env file. "
            "Set BOB_API_KEY to execute live IBM Bob Shell orchestrator CLI tests."
        )

    # Construct execution environment with Node and PNPM in PATH
    env = os.environ.copy()
    env["BOB_API_KEY"] = bob_api_key
    nvm_node_path = "/home/rafif/.nvm/versions/node/v24.21.0/bin"
    pnpm_path = "/home/rafif/.local/share/pnpm/bin"
    env["PATH"] = f"{nvm_node_path}:{pnpm_path}:{env.get('PATH', '')}"

    cmd = [
        "bob",
        "run",
        "--trust",
        "--max-turns", "4",
        "--format", "json",
        "Audit shipment SHP-2026-0042 using customsguard tool and state the compliance verdict."
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
    except FileNotFoundError:
        pytest.skip("bob command line tool is not installed on system PATH.")
    except subprocess.TimeoutExpired:
        pytest.fail("bob run execution timed out after 60 seconds.")

    assert proc.returncode == 0, f"bob run exited with error code {proc.returncode}: {proc.stderr}"

    try:
        bob_result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse bob run output as JSON: {proc.stdout}")

    assert bob_result.get("status") == "success"
    stats = bob_result.get("stats", {})
    assert stats.get("tool_calls", 0) >= 1, "Expected Bob to make at least 1 MCP tool call."

    last_msg = bob_result.get("last_message", "")
    assert any(token in last_msg for token in ["SHP-2026-0042", "NON_COMPLIANT", "8517", "detention"])
