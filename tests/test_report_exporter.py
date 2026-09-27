import json
import os
import shutil
import pytest
from scripts.customs_components import CustomsGuardToolkitComponent


@pytest.fixture
def export_tool():
    component = CustomsGuardToolkitComponent()
    tools = component.build_tools()
    return {t.name: t for t in tools}["export_compliance_report"]


def test_export_compliance_report(export_tool, tmp_path):
    """Verify that export_compliance_report creates markdown and json reports."""
    shipment_id = "TEST-REPORT-001"
    audit_data = {
        "shipment_id": shipment_id,
        "importer": "Global Tech Corp",
        "overall_status": "NON_COMPLIANT_HIGH_RISK",
        "container_detention_risk": True,
        "total_duty_shortfall_usd": 12000.0,
        "estimated_demurrage_per_day_usd": 350.0
    }
    audit_json = json.dumps(audit_data, indent=2)

    # Invoke tool
    result_msg = export_tool.invoke({
        "shipment_id": shipment_id,
        "audit_summary_json": audit_json
    })

    assert "Audit report successfully exported to:" in result_msg

    # Extract target report path
    exported_path = result_msg.split("Audit report successfully exported to:")[-1].strip()
    assert os.path.isfile(exported_path), f"Report file not found: {exported_path}"

    with open(exported_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    assert "# CustomsGuard Compliance Audit Report" in md_content
    assert shipment_id in md_content
    assert "NON_COMPLIANT_HIGH_RISK" in md_content

    # Also verify companion JSON report exists
    json_path = os.path.join(os.path.dirname(exported_path), "audit_report.json")
    assert os.path.isfile(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        loaded_json = json.load(f)

    assert loaded_json["shipment_id"] == shipment_id
    assert loaded_json["total_duty_shortfall_usd"] == 12000.0

    # Cleanup test output directory
    shutil.rmtree(os.path.dirname(exported_path), ignore_errors=True)
