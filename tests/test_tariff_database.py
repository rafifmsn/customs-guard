import json
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARIFF_DB_PATH = os.path.join(BASE_DIR, "data", "seed", "tariff_database.json")
SAMPLE_INVOICES_PATH = os.path.join(BASE_DIR, "data", "seed", "sample_invoices.json")


def test_tariff_database_file_exists():
    """Verify tariff_database.json exists on disk."""
    assert os.path.isfile(TARIFF_DB_PATH), f"Tariff database missing at: {TARIFF_DB_PATH}"


def test_tariff_database_volume_and_schema():
    """Verify tariff_database.json contains full Indonesian HS schedule and valid fields."""
    with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 5600, f"Expected at least 5,600 HS codes, got {len(data)}"

    required_keys = {"hs_code", "description", "duty_rate", "search_text", "restricted", "required_permits"}
    sample_entry = data[0]
    assert required_keys.issubset(sample_entry.keys()), f"Missing keys in sample entry: {sample_entry.keys()}"


def test_known_commodity_classifications():
    """Verify specific high-risk and restricted trade items have correct regulatory tags."""
    with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    tariffs_by_code = {item["hs_code"]: item for item in data}

    # Verify smartphone classification (8517.11)
    assert "8517.11" in tariffs_by_code
    smartphone = tariffs_by_code["8517.11"]
    assert smartphone["restricted"] is True
    assert any("SDPPI" in permit for permit in smartphone["required_permits"])

    # Verify laptop classification (8471.30)
    assert "8471.30" in tariffs_by_code
    laptop = tariffs_by_code["8471.30"]
    assert laptop["duty_rate"] == 0.0

    # Verify medical ultrasound classification (9018.12)
    assert "9018.12" in tariffs_by_code
    ultrasound = tariffs_by_code["9018.12"]
    assert ultrasound["restricted"] is True
    assert any("Kemenkes" in permit for permit in ultrasound["required_permits"])


def test_sample_invoices_exist_and_valid():
    """Verify test scenarios exist and have valid structure."""
    assert os.path.isfile(SAMPLE_INVOICES_PATH)
    with open(SAMPLE_INVOICES_PATH, "r", encoding="utf-8") as f:
        invoices = json.load(f)

    assert isinstance(invoices, list)
    assert len(invoices) >= 3

    for inv in invoices:
        assert "shipment_id" in inv
        assert "importer_name" in inv
        assert "items" in inv
        assert len(inv["items"]) > 0
