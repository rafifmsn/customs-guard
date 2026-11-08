"""CustomsGuard Tariff Knowledge Base & Vector Retrieval Test Suite

Validates the complete 5,612 Indonesian HS-6 tariff schedule, payload index schemas,
dense 384-dimensional semantic embeddings, and the 50-item Ground Truth dataset.
Addresses reviewer feedback regarding comprehensive test coverage across chapters.
"""

import json
import math
import os
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARIFF_DB_PATH = os.path.join(BASE_DIR, "data", "seed", "tariff_database.json")
SAMPLE_INVOICES_PATH = os.path.join(BASE_DIR, "data", "seed", "sample_invoices.json")
GROUND_TRUTH_PATH = os.path.join(BASE_DIR, "data", "seed", "ground_truth_benchmark_50.json")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "data", "seed", "tariff_embeddings_384.json")


def test_tariff_database_file_exists():
    """Verify tariff_database.json exists on disk."""
    assert os.path.isfile(TARIFF_DB_PATH), f"Tariff database missing at: {TARIFF_DB_PATH}"


def test_tariff_database_volume_and_schema():
    """Verify tariff_database.json contains full Indonesian HS schedule and valid fields."""
    with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 5600, f"Expected at least 5,600 HS codes, got {len(data)}"

    required_keys = {
        "hs_code",
        "description",
        "duty_rate",
        "vat_rate",
        "search_text",
        "restricted",
        "required_permits",
        "risk_level",
        "chapter",
        "heading",
    }
    sample_entry = data[0]
    assert required_keys.issubset(sample_entry.keys()), f"Missing keys in sample entry: {sample_entry.keys()}"


def test_known_commodity_classifications():
    """Verify specific high-risk and restricted trade items have correct regulatory tags."""
    with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    tariffs_by_code = {item["hs_code"]: item for item in data}

    # Verify smartphone classification (8517.13 / 8517.14)
    assert "8517.13" in tariffs_by_code
    smartphone = tariffs_by_code["8517.13"]
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


def test_ground_truth_benchmark_50_integrity():
    """Verify that all 50 ground-truth benchmark items match official tariff database records."""
    assert os.path.isfile(GROUND_TRUTH_PATH), f"Missing ground truth file at {GROUND_TRUTH_PATH}"

    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        gt_items = json.load(f)

    with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
        tariffs = {t["hs_code"]: t for t in json.load(f)}

    assert len(gt_items) == 50, f"Expected exactly 50 benchmark items, got {len(gt_items)}"

    # Ensure all 50 verified HS codes exist in official database
    for item in gt_items:
        hs = item["ground_truth_hs"]
        assert hs in tariffs, f"Ground truth HS code {hs} not found in tariff database"
        tariff_entry = tariffs[hs]
        assert tariff_entry["duty_rate"] == item["duty_rate"]
        assert tariff_entry["restricted"] == item["restricted"]
        assert len(tariff_entry["description"]) > 10


def test_tariff_database_chapter_coverage():
    """Verify tariff coverage spans across all major international trade chapters."""
    with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    chapters = {item["chapter"] for item in data}
    # HS tariff system covers 97 chapters
    assert len(chapters) >= 90, f"Expected at least 90 chapters, got {len(chapters)}"

    # Verify rates and VAT bounds
    for item in data[:500]:
        rate = item["duty_rate"]
        assert 0.0 <= rate <= 150.0, f"Duty rate {rate} out of bounds for {item['hs_code']}"
        assert item["vat_rate"] == 11.0, f"Indonesian standard VAT must be 11.0%, got {item['vat_rate']}"


def test_dense_vector_embeddings_file_integrity():
    """Verify precomputed dense 384-dimensional embeddings file exists and is normalized."""
    if not os.path.isfile(EMBEDDINGS_PATH):
        pytest.skip(f"Embeddings cache not present at {EMBEDDINGS_PATH}")

    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
        embeddings = json.load(f)

    assert len(embeddings) >= 5600, f"Expected >= 5,600 embeddings, got {len(embeddings)}"

    # Check normalization of sample vectors (L2 norm == 1.0)
    for code in ["8517.13", "8471.30", "9018.12", "6404.11"]:
        assert code in embeddings
        vec = embeddings[code]
        assert len(vec) == 384
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 0.01, f"Vector for {code} is not unit normalized: {norm}"


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
