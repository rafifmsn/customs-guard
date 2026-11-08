import pytest
from unittest.mock import patch, MagicMock
from scripts.customs_components import CustomsGuardToolkitComponent


@pytest.fixture
def alert_tool():
    component = CustomsGuardToolkitComponent()
    tools = component.build_tools()
    return {t.name: t for t in tools}["send_compliance_alert"]


def test_send_compliance_alert_success(alert_tool):
    """Verify send_compliance_alert formats email and dispatches to SMTP."""
    shipment_id = "SHP-TEST-ALERT"
    verdict = "NON_COMPLIANT_HIGH_RISK"
    details = "Duty shortfall $11,500. Container detention risk active."

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    with patch("smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_class:
        result = alert_tool.invoke({
            "shipment_id": shipment_id,
            "verdict": verdict,
            "alert_details": details
        })

        # Verify SMTP server initialization
        mock_smtp_class.assert_called_once_with("mailpit", 1025, timeout=5)

        # Verify sendmail was called with proper sender, recipient, and message
        assert mock_smtp_instance.sendmail.called
        args, _ = mock_smtp_instance.sendmail.call_args
        sender, recipients, msg_string = args
        assert sender == "alerts@customsguard.local"
        assert recipients == ["compliance-officer@customsguard.local"]
        assert f"Subject: [CustomsGuard Alert] {verdict}: Shipment {shipment_id}" in msg_string
        assert "CUSTOMSGUARD AUTONOMOUS COMPLIANCE & DETENTION ALERT" in msg_string
        assert "FINANCIAL & DEMURRAGE EXPOSURE" in msg_string
        assert "http://localhost:8025" in msg_string

    assert "Alert email queued in Mailpit" in result


def test_send_compliance_alert_smtp_failure_handling(alert_tool):
    """Verify that SMTP communication errors are caught gracefully."""
    with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("Connection refused")):
        result = alert_tool.invoke({
            "shipment_id": "SHP-TEST-FAIL",
            "verdict": "NON_COMPLIANT_HIGH_RISK",
            "alert_details": "Test failure."
        })

    assert "Failed to send email via Mailpit" in result


def test_send_compliance_alert_plain_text_enriches_from_disk(alert_tool, tmp_path):
    """Verify that when an LLM passes a plain text summary, the alert is enriched with cached dossier numbers."""
    from scripts.customs_components import format_compliance_alert_body
    import json
    import os

    shipment_id = "SHP-DISK-ENRICH-001"
    report_dir = os.path.join("data", "reports", "2026-10-22", shipment_id)
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, "audit_report.json")

    mock_audit = {
        "shipment_id": shipment_id,
        "importer": "Enriched Importer PT",
        "container_count": 3,
        "total_duty_shortfall_usd": 7500.0,
        "estimated_demurrage_per_day_usd": 303.0,
        "demurrage_assessment": {
            "container_size": "40ft",
            "container_type": "Standard Dry",
            "applicable_slab": "Days 6 to 10 ($101.00/day)",
            "projected_cumulative_liability_usd": 1515.0,
        },
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(mock_audit, f)

    try:
        body = format_compliance_alert_body(
            shipment_id=shipment_id,
            verdict="NON_COMPLIANT_HIGH_RISK",
            alert_details="Critical discrepancies identified by Bob LLM.",
        )
        assert "Importer                : Enriched Importer PT" in body
        assert "3x 40ft Standard Dry" in body
        assert "$7,500.00 USD" in body
        assert "$303.00 USD / day" in body
        assert "$1,515.00 USD" in body
        assert "Critical discrepancies identified by Bob LLM." in body
    finally:
        import shutil
        shutil.rmtree(report_dir, ignore_errors=True)

