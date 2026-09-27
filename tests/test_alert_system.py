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
