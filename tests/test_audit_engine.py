import json
import pytest
from unittest.mock import patch, MagicMock
from scripts.customs_components import CustomsGuardToolkitComponent


@pytest.fixture
def audit_tool():
    component = CustomsGuardToolkitComponent()
    tools = component.build_tools()
    return {t.name: t for t in tools}["audit_shipment_compliance"]


def test_audit_tool_handles_invalid_json(audit_tool):
    """Ensure audit tool safely catches and returns malformed JSON inputs."""
    res = audit_tool.invoke({"invoice_json": "invalid-json-string"})
    assert "Error parsing invoice JSON" in res


def test_audit_discrepancy_and_penalties(audit_tool):
    """Test discrepancy detection, duty shortfall calculation, and container detention risk."""
    sample_invoice = {
        "shipment_id": "TEST-SHP-001",
        "importer_name": "Test Importer Ltd",
        "items": [
            {
                "item_id": 1,
                "declared_description": "Apple iPhone 15 Pro Max Smartphone",
                "declared_hs_code": "8471.30",
                "declared_duty_rate": 0.0,
                "quantity": 100,
                "unit_price": 1000.0,
                "total_value": 100000.0
            }
        ]
    }

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8517.11",
                        "duty_rate": 5.0,
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
        output = audit_tool.invoke({"invoice_json": json.dumps(sample_invoice)})
        result = json.loads(output)

    assert result["shipment_id"] == "TEST-SHP-001"
    assert result["overall_status"] == "NON_COMPLIANT_HIGH_RISK"
    assert result["container_detention_risk"] is True
    # CMA CGM Indonesia 40ft Dry Standard Slab 1 (Days 6-10) = $101/day
    assert result["estimated_demurrage_per_day_usd"] == 101.0
    assert result["demurrage_assessment"]["daily_rate_per_container_usd"] == 101.0
    assert result["demurrage_assessment"]["projected_cumulative_liability_usd"] == 505.0

    # 5.0% official duty vs 0.0% declared on $100,000 = $5,000 shortfall
    assert result["total_duty_shortfall_usd"] == 5000.0

    finding = result["findings"][0]
    assert finding["declared_hs"] == "8471.30"
    assert finding["matched_hs"] == "8517.11"
    assert finding["restricted"] is True
    assert any("SDPPI" in p for p in finding["required_permits"])


def test_audit_compliant_shipment(audit_tool):
    """Test that compliant shipments with matching HS codes yield zero shortfall and zero detention risk."""
    sample_invoice = {
        "shipment_id": "TEST-SHP-CLEAN",
        "importer_name": "Compliant Importer Ltd",
        "items": [
            {
                "item_id": 1,
                "declared_description": "Standard Server Rack System",
                "declared_hs_code": "8471.50",
                "declared_duty_rate": 0.0,
                "quantity": 10,
                "unit_price": 5000.0,
                "total_value": 50000.0
            }
        ]
    }

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
        output = audit_tool.invoke({"invoice_json": json.dumps(sample_invoice)})
        result = json.loads(output)

    assert result["overall_status"] == "COMPLIANT"
    assert result["container_detention_risk"] is False
    assert result["total_duty_shortfall_usd"] == 0.0
    assert result["estimated_demurrage_per_day_usd"] == 0.0
    assert len(result["critical_notes"]) == 0


def test_audit_multi_container_scaled_demurrage(audit_tool):
    """Verify that multi-container shipments scale daily demurrage liability by container count."""
    sample_invoice = {
        "shipment_id": "TEST-SHP-MULTI-CONTAINER",
        "importer_name": "Logistics Multi Corp",
        "container_count": 4,
        "items": [
            {
                "item_id": 1,
                "declared_description": "Smartphones Cellular Units",
                "declared_hs_code": "8471.30",
                "declared_duty_rate": 0.0,
                "total_value": 200000.0
            }
        ]
    }

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8517.11",
                        "duty_rate": 0.0,
                        "restricted": True,
                        "required_permits": ["SDPPI Certificate"]
                    }
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        output = audit_tool.invoke({"invoice_json": json.dumps(sample_invoice)})
        result = json.loads(output)

    assert result["container_count"] == 4
    assert result["container_detention_risk"] is True
    # 4 containers * $101/day = $404/day on CMA CGM Slab 1
    assert result["estimated_demurrage_per_day_usd"] == 404.0
    assert result["demurrage_assessment"]["daily_burn_rate_total_usd"] == 404.0
    assert result["demurrage_assessment"]["projected_cumulative_liability_usd"] == 2020.0


def test_audit_cma_cgm_progressive_matrix(audit_tool):
    """Verify CMA CGM progressive day-slabs across container sizes and types."""
    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8517.11",
                        "duty_rate": 0.0,
                        "restricted": True,
                        "required_permits": ["SDPPI Certificate"]
                    }
                }
            ]
        }
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_qdrant_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        # 1. 2x 20ft Dry containers held for 12 days (Slab 2: $86/day)
        inv_20ft = {
            "shipment_id": "TEST-20FT",
            "container_count": 2,
            "container_size": "20",
            "container_type": "DRY",
            "days_held_projected": 12,
            "items": [{"declared_description": "Smartphones", "declared_hs_code": "8471.30", "total_value": 50000.0}]
        }
        res_20ft = json.loads(audit_tool.invoke({"invoice_json": json.dumps(inv_20ft)}))
        assert res_20ft["demurrage_assessment"]["daily_rate_per_container_usd"] == 86.0
        assert res_20ft["estimated_demurrage_per_day_usd"] == 172.0
        # Days 1-5 free (0), Days 6-10 (5*66=330), Days 11-12 (2*86=172) -> 502 * 2 = 1004
        assert res_20ft["demurrage_assessment"]["projected_cumulative_liability_usd"] == 1004.0

        # 2. 1x 40ft Reefer container held for 6 days (3 free days, Slab 2: $176/day)
        inv_reefer = {
            "shipment_id": "TEST-REEFER",
            "container_count": 1,
            "container_size": "40",
            "container_type": "REEFER",
            "days_held_projected": 6,
            "items": [{"declared_description": "Smartphones", "declared_hs_code": "8471.30", "total_value": 50000.0}]
        }
        res_reefer = json.loads(audit_tool.invoke({"invoice_json": json.dumps(inv_reefer)}))
        assert res_reefer["demurrage_assessment"]["daily_rate_per_container_usd"] == 176.0
        assert res_reefer["estimated_demurrage_per_day_usd"] == 176.0
        # Days 1-3 free (0), Days 4-5 (2*141=282), Day 6 (1*176=176) -> 458
        assert res_reefer["demurrage_assessment"]["projected_cumulative_liability_usd"] == 458.0


def test_audit_duty_overpayment_restitution(audit_tool):
    """Verify that when an importer over-declares duty, zero shortfall is charged and restitution is advised."""
    sample_invoice = {
        "shipment_id": "TEST-SHP-OVERPAID",
        "importer_name": "Conservative Importer Ltd",
        "items": [
            {
                "item_id": 1,
                "declared_description": "Standard Server Unit",
                "declared_hs_code": "8471.50",
                "declared_duty_rate": 15.0,
                "total_value": 100000.0
            }
        ]
    }

    mock_qdrant_response = {
        "result": {
            "points": [
                {
                    "payload": {
                        "hs_code": "8471.50",
                        "duty_rate": 5.0,
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
        output = audit_tool.invoke({"invoice_json": json.dumps(sample_invoice)})
        result = json.loads(output)

    # Importer overpaid (15% declared vs 5% official), so shortfall must be 0.0
    assert result["total_duty_shortfall_usd"] == 0.0
    # Overpayment is (10% / 100) * 100,000 = $10,000.00
    assert any("Potential duty overpayment" in note for note in result["critical_notes"])
    assert any("$10,000.00" in note for note in result["critical_notes"])
