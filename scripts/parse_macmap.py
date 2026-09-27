#!/usr/bin/env python3
"""
CustomsGuard Tariff Database Parser
Extracts all 5,613 Indonesian HS-6 codes, MFN tariff rates, and product descriptions
from docs/macmap.xlsx and enriches them with trade restriction metadata.
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


def clean_description(text: str) -> str:
    """Clean extra spaces and non-breaking spaces from text."""
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def determine_restrictions(raw_code: str, chapter: str, description: str):
    """
    Determine trade restrictions, required permits, and risk categories
    based on Indonesian customs regulations (Lartas / Non-Tariff Measures).
    """
    desc_lower = description.lower()
    permits = []
    restricted = False
    risk_level = "LOW"

    # Chapter 85: Telecommunications, Smartphones, Radios
    if chapter == "85" and any(
        kw in desc_lower
        for kw in [
            "cellular",
            "smartphone",
            "telephone",
            "radio",
            "transmitter",
            "transceiver",
            "wireless",
            "radar",
        ]
    ):
        restricted = True
        permits.append("Telecommunication Type Approval / SDPPI Certification (Kemkominfo)")
        risk_level = "HIGH"

    # Chapter 90: Medical, Surgical, and Diagnostic Equipment
    elif chapter == "90" and any(
        kw in desc_lower
        for kw in [
            "medical",
            "surgical",
            "dental",
            "veterinary",
            "ultrasonic",
            "scintigraphic",
            "diagnostic",
            "prosthetic",
            "orthopaedic",
        ]
    ):
        restricted = True
        permits.append("Medical Device Import & Distribution License / Izin Edar (Kemenkes)")
        risk_level = "HIGH"

    # Chapter 30: Pharmaceuticals & Medicaments
    elif chapter == "30":
        restricted = True
        permits.append("Food & Drug Import Certificate / SKI BPOM (Badan POM)")
        risk_level = "HIGH"

    # Chapters 61 & 62: Apparel & Garments (Textile Quota & Verification)
    elif chapter in ["61", "62"]:
        restricted = True
        permits.append("Textile Import Verification & Surveyor Report / Laporan Surveyor (Kemendag)")
        risk_level = "MEDIUM"

    # Chapter 84: Heavy Machinery, Compressors, Refrigeration
    elif chapter == "84" and any(
        kw in desc_lower
        for kw in [
            "refrigerat",
            "compressor",
            "air conditioning",
            "boiler",
            "engine",
            "crane",
            "bulldozer",
        ]
    ):
        restricted = True
        permits.append("Surveyor Technical Inspection / Laporan Surveyor (Sucofindo / Kemenperin)")
        risk_level = "MEDIUM"

    # Chemical & Hazardous Substances (Chapters 28, 29, 38)
    elif chapter in ["28", "29", "38"] and any(
        kw in desc_lower
        for kw in ["toxic", "explosive", "precursor", "acid", "radioactive", "pesticide"]
    ):
        restricted = True
        permits.append("Hazardous & Toxic Substance Permit / Rekomendasi B3 (KLHK)")
        risk_level = "HIGH"

    return restricted, permits, risk_level


def parse_macmap(xlsx_path: str, output_json_path: str):
    """Parse macmap.xlsx and generate structured JSON database."""
    print(f"Reading {xlsx_path}...")
    if not os.path.exists(xlsx_path):
        print(f"Error: {xlsx_path} not found.")
        sys.exit(1)

    with zipfile.ZipFile(xlsx_path, "r") as z:
        # Load shared strings
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for elem in tree.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
                shared_strings.append(elem.text or "")

        # Read sheet2 (Data sheet)
        tree = ET.fromstring(z.read("xl/worksheets/sheet2.xml"))
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

        records = []
        for i, row_elem in enumerate(tree.iter(f"{ns}row")):
            if i == 0:
                continue  # Skip header

            row_vals = []
            for c in row_elem.findall(f"{ns}c"):
                t = c.get("t")
                v = c.find(f"{ns}v")
                val = v.text if v is not None else ""
                if t == "s" and val.isdigit():
                    val = shared_strings[int(val)]
                row_vals.append(val)

            # Columns: ReportingCountry, Year, Revision, ProductCode, ProductDescription, NoOfTariffLines, AVE
            if len(row_vals) >= 7:
                raw_code = str(row_vals[3]).strip().zfill(6)
                description = clean_description(row_vals[4])

                try:
                    ave_val = float(row_vals[6])
                    duty_rate = round(ave_val * 100, 2)  # Convert 0.05 to 5.0%
                except (ValueError, TypeError):
                    duty_rate = 0.0

                chapter = raw_code[:2]
                heading = raw_code[:4]
                subheading = raw_code[4:]
                formatted_code = f"{heading}.{subheading}"

                restricted, permits, risk_level = determine_restrictions(
                    raw_code, chapter, description
                )

                record = {
                    "hs_code": formatted_code,
                    "raw_code": raw_code,
                    "chapter": chapter,
                    "heading": heading,
                    "subheading": subheading,
                    "description": description,
                    "duty_rate": duty_rate,
                    "vat_rate": 11.0,
                    "restricted": restricted,
                    "required_permits": permits,
                    "risk_level": risk_level,
                    "search_text": f"HS {formatted_code} (Chapter {chapter}): {description}",
                }
                records.append(record)

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {output_json_path}")
    print(f"Total HS-6 records processed: {len(records)}")
    restricted_count = sum(1 for r in records if r["restricted"])
    print(f"Total restricted / Lartas records identified: {restricted_count}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    xlsx_file = os.path.join(base_dir, "docs", "macmap.xlsx")
    json_file = os.path.join(base_dir, "data", "seed", "tariff_database.json")
    parse_macmap(xlsx_file, json_file)
