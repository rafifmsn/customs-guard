"""CustomsGuard Ingestion JSON Validator Component for Langflow.

Provides a robust tool for the Ingestion Agent to validate JSON syntax,
extract the outermost JSON object if conversational text surrounds it,
and verify completeness against the CustomsGuard ingestion schema.
"""

import json
import re
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool, tool
from langflow.custom import Component
from langflow.io import Output


def extract_outermost_json(raw_text: str) -> Optional[str]:
    """Finds and extracts the outermost balanced JSON object {...} from raw text.

    Handles leading and trailing conversational text, markdown fences,
    or accidental commentary produced by the LLM.
    """
    if not raw_text:
        return None

    cleaned = str(raw_text).strip()

    # Strip markdown code blocks if wrapped (e.g. ```json ... ```)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    start_idx = cleaned.find("{")
    if start_idx == -1:
        return None

    # Track nested brace depth to locate the matching outermost closing brace
    depth = 0
    in_string = False
    escape = False

    for i in range(start_idx, len(cleaned)):
        char = cleaned[i]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return cleaned[start_idx : i + 1]

    # Fallback if unclosed string or trailing text
    last_idx = cleaned.rfind("}")
    if last_idx > start_idx:
        return cleaned[start_idx : last_idx + 1]

    return None


def parse_and_validate_ingestion_json(raw_payload: str) -> Dict[str, Any]:
    """Parses raw text into JSON, extracts the outermost object, and verifies completeness."""
    json_candidate = extract_outermost_json(raw_payload)
    if not json_candidate:
        return {
            "valid_json": False,
            "status": "error",
            "message": "No JSON object structure {...} found in the provided text.",
            "extracted_data": None,
        }

    try:
        parsed = json.loads(json_candidate)
    except Exception as exc:
        return {
            "valid_json": False,
            "status": "error",
            "message": f"Invalid JSON syntax: {str(exc)}",
            "extracted_data": None,
        }

    if not isinstance(parsed, dict):
        return {
            "valid_json": False,
            "status": "error",
            "message": "Extracted JSON is not a key-value dictionary object.",
            "extracted_data": None,
        }

    # Verify status flag if present
    status_val = parsed.get("status")
    if status_val == "rejected":
        return {
            "valid_json": True,
            "status": "rejected",
            "message": "Document flagged as rejected.",
            "missing_fields": parsed.get("missing_fields", []),
            "error_message": parsed.get("error_message", "Document rejected."),
            "extracted_data": parsed,
        }

    invoice_data = parsed.get("invoice_data")
    if not isinstance(invoice_data, dict):
        invoice_data = parsed  # In case the agent output the invoice payload directly

    items = invoice_data.get("items")
    if not items or not isinstance(items, list):
        return {
            "valid_json": True,
            "status": "incomplete",
            "message": "JSON syntax is valid, but the 'items' list is missing or empty.",
            "missing_fields": ["items"],
            "extracted_data": parsed,
        }

    missing_in_items = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            missing_in_items.append(f"item_{idx}_is_not_an_object")
            continue
        if not item.get("declared_description"):
            missing_in_items.append(f"item_{idx}_declared_description")
        if not item.get("declared_hs_code"):
            missing_in_items.append(f"item_{idx}_declared_hs_code")
        if "total_value" not in item and ("quantity" not in item or "unit_price" not in item):
            missing_in_items.append(f"item_{idx}_total_value")

    if missing_in_items:
        return {
            "valid_json": True,
            "status": "incomplete",
            "message": f"JSON syntax is valid, but required line item fields are missing: {', '.join(missing_in_items)}",
            "missing_fields": missing_in_items,
            "extracted_data": parsed,
        }

    return {
        "valid_json": True,
        "status": "complete",
        "message": "Valid and complete ingestion JSON successfully verified.",
        "missing_fields": [],
        "extracted_data": parsed,
    }


class IngestionValidatorToolkitComponent(Component):
    display_name = "Ingestion Validator Tools"
    description = "Custom tool for validating JSON syntax, outermost bracket extraction, and line-item completeness."
    icon = "CheckCircle"
    name = "IngestionValidatorToolkit"

    inputs = []
    outputs = [
        Output(
            name="tools",
            display_name="Tools",
            method="build_tools",
            types=["Tool"],
        ),
    ]

    def build_tools(self) -> List[BaseTool]:

        @tool
        def validate_invoice_json(json_text: str) -> str:
            """Validates raw text from an extraction attempt.

            Extracts the outermost {...} JSON block, tests if it parses cleanly,
            and checks whether required customs line item fields are present.
            Pass the raw JSON string or conversational response to verify it.
            """
            result = parse_and_validate_ingestion_json(json_text)
            return json.dumps(result, indent=2)

        return [validate_invoice_json]

