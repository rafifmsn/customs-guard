"""CustomsGuard Centralized FastAPI Controller."""

import asyncio
import datetime
import json
import os
import signal
import socket
import time
import urllib.request
from typing import Any, Dict, List, Optional

import io
from fastapi import FastAPI, File, HTTPException, UploadFile

from api.schemas import (
    AssistantQuery,
    AssistantResponse,
    AuditResponse,
    AuditResult,
    HealthStatus,
    IngestionResponse,
    InvoiceItem,
    InvoicePayload,
    ReportItem,
    ServiceCheck,
)
from scripts.ingestion_validator import (
    extract_outermost_json,
    parse_and_validate_ingestion_json,
)
from scripts.customs_components import (
    CMA_CGM_TARIFFS,
    CustomsGuardToolkitComponent,
    calculate_cma_cgm_demurrage,
    format_markdown_dossier,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARIFF_DB_PATH = os.path.join(BASE_DIR, "data", "seed", "tariff_database.json")

MAX_CONCURRENT_BOB_WORKERS = 2
BOB_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_BOB_WORKERS)

app = FastAPI(
    title="CustomsGuard Autonomous Trade Compliance API",
    description=(
        "Centralized REST controller for Indonesian HS-6 tariff discrepancy auditing, "
        "Lartas regulatory permit verification, CMA CGM Indonesia progressive demurrage modeling, "
        "evidentiary dossier archiving, Mailpit alerting, and bounded IBM Bob CLI orchestration."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


def _get_toolkit_map() -> Dict[str, Any]:
    component = CustomsGuardToolkitComponent()
    tools = component.build_tools()
    return {t.name: t for t in tools}


def _check_http_service(urls: List[str], timeout: float = 2.0) -> ServiceCheck:
    last_err = "Unreachable"
    for url in urls:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if 200 <= resp.status < 500:
                    return ServiceCheck(
                        reachable=True,
                        endpoint=url,
                        detail=f"HTTP {resp.status}",
                    )
        except Exception as exc:
            last_err = str(exc)
    return ServiceCheck(reachable=False, endpoint=urls[-1], detail=last_err)


def _check_tcp_service(hosts: List[str], port: int, timeout: float = 2.0) -> ServiceCheck:
    last_err = "Unreachable"
    for host in hosts:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return ServiceCheck(
                    reachable=True,
                    endpoint=f"{host}:{port}",
                    detail="TCP connected",
                )
        except Exception as exc:
            last_err = str(exc)
    return ServiceCheck(
        reachable=False,
        endpoint=f"{hosts[-1]}:{port}",
        detail=last_err,
    )


def _build_executive_narrative(audit: AuditResult) -> str:
    """Generates a deterministic executive compliance narrative from the structured audit result."""
    dem = audit.demurrage_assessment
    status_line = (
        f"Shipment `{audit.shipment_id}` for importer **{audit.importer}** "
        f"({audit.container_count}x {dem.container_size} {dem.container_type} via {audit.carrier} "
        f"into {audit.destination_port}) received official compliance verdict **{audit.overall_status}**."
    )
    if audit.overall_status == "NON_COMPLIANT_HIGH_RISK":
        risk_line = (
            f"Red-Lane customs hold and container detention risk is **ACTIVE**. "
            f"Total duty shortfall is **${audit.total_duty_shortfall_usd:,.2f} USD**, with an active "
            f"CMA CGM daily burn rate of **${audit.estimated_demurrage_per_day_usd:,.2f} USD/day** "
            f"({dem.applicable_slab}) and a projected {dem.detention_days}-day detention liability of "
            f"**${dem.projected_cumulative_liability_usd:,.2f} USD**."
        )
    elif audit.overall_status == "WARNING_DISCREPANCY":
        risk_line = (
            f"Tariff classification discrepancy detected without Lartas restriction. "
            f"Assessed duty shortfall is **${audit.total_duty_shortfall_usd:,.2f} USD**."
        )
    elif audit.total_restitution_usd > 0:
        risk_line = (
            f"Declaration is compliant with zero detention risk, but an import duty overpayment was identified. "
            f"The importer qualifies for **${audit.total_restitution_usd:,.2f} USD** in customs duty restitution recovery."
        )
    else:
        risk_line = (
            "All declared HS-6 classifications, MFN tariff rates, and ministry import requirements match "
            "the official Indonesian schedule with zero duty shortfall and zero detention exposure."
        )
    return f"{status_line}\n\n{risk_line}"


def _get_langflow_api_key() -> Optional[str]:
    """Resolves Langflow API key from LANGFLOW_BOT_API_KEY, LANGFLOW_API_KEY, .env, or .bob/mcp.json."""
    for env_var in ["LANGFLOW_BOT_API_KEY", "LANGFLOW_API_KEY"]:
        env_key = os.environ.get(env_var)
        if env_key:
            return env_key

    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    clean = line.strip()
                    if clean.startswith("LANGFLOW_BOT_API_KEY=") or clean.startswith("LANGFLOW_API_KEY="):
                        val = clean.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass

    mcp_path = os.path.join(BASE_DIR, ".bob", "mcp.json")
    if os.path.isfile(mcp_path):
        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                mcp_cfg = json.load(f)
            args = (
                mcp_cfg.get("mcpServers", {})
                .get("lf-ibmsb", {})
                .get("args", [])
            )
            if "x-api-key" in args:
                idx = args.index("x-api-key")
                if idx + 1 < len(args):
                    return str(args[idx + 1])
        except Exception:
            pass
    return None


def _try_langflow_narrative(invoice_dict: dict, fallback_narrative: str) -> str:
    """Queries Langflow v2 (/api/v2/workflows) or v1 (/api/v1/run/{flow_id}) with x-api-key."""
    import uuid

    flow_id = (
        os.environ.get("LANGFLOW_AUDIT_FLOW_ID")
        or os.environ.get("LANGFLOW_FLOW_ID")
        or "d79a75e5-63f9-4da4-ac36-9c7d7d1b9e1b"
    )
    api_key = _get_langflow_api_key()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    input_str = json.dumps(invoice_dict)

    for host in ["langflow", "localhost"]:
        # 1. Try Langflow v2 workflows endpoint
        v2_url = f"http://{host}:7860/api/v2/workflows"
        v2_payload = json.dumps(
            {
                "flow_id": flow_id,
                "input_value": input_str,
            }
        ).encode("utf-8")
        try:
            req = urllib.request.Request(v2_url, data=v2_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                v2_text = data.get("output", {}).get("text")
                if v2_text:
                    return str(v2_text)
        except Exception:
            pass

        # 2. Fallback to Langflow v1 run endpoint
        v1_url = f"http://{host}:7860/api/v1/run/{flow_id}"
        v1_payload = json.dumps(
            {
                "output_type": "chat",
                "input_type": "chat",
                "input_value": input_str,
                "session_id": str(uuid.uuid4()),
            }
        ).encode("utf-8")
        try:
            req = urllib.request.Request(v1_url, data=v1_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                outputs = data.get("outputs", [])
                if outputs:
                    text = (
                        outputs[0]
                        .get("outputs", [{}])[0]
                        .get("results", {})
                        .get("message", {})
                        .get("text")
                    )
                    if text:
                        return str(text)
        except Exception:
            continue
    return fallback_narrative


def _try_langflow_assistant(prompt: str, timeout_seconds: float = 30.0) -> Optional[str]:
    """Queries dedicated Langflow Regulatory Assistant flow with augmented context."""
    import uuid

    flow_id = (
        os.environ.get("LANGFLOW_ASSISTANT_FLOW_ID")
        or "5ca6e9b6-937c-4ab3-a95e-f4d3a5ff9818"
    )
    api_key = _get_langflow_api_key()
    if not api_key:
        return None

    headers = {"Content-Type": "application/json", "x-api-key": api_key}
    augmented_prompt = prompt

    # Retrieve relevant tariff records from local database if relevant keywords present
    q_lower = prompt.lower()
    matched_records = []
    if os.path.isfile(TARIFF_DB_PATH):
        try:
            with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
                tariffs = json.load(f)
            for entry in tariffs:
                hs = str(entry.get("hs_code", "")).lower()
                desc = str(entry.get("search_text", "")).lower()
                if (hs and hs in q_lower) or any(
                    w in desc
                    for w in q_lower.split()
                    if len(w) >= 4
                    and w not in {"what", "which", "import", "indonesia", "tariff", "rate"}
                ):
                    matched_records.append(entry)
                    if len(matched_records) >= 3:
                        break
        except Exception:
            pass

    if matched_records:
        context_snippets = []
        for r in matched_records:
            context_snippets.append(
                f"- HS {r.get('hs_code')}: {r.get('description')} (MFN Duty: {r.get('official_mfn_duty', 0.0)}%, "
                f"Lartas Restricted: {'YES' if r.get('restricted') else 'NO'}, "
                f"Required Permits: {', '.join(r.get('required_permits', [])) or 'None'})"
            )
        augmented_prompt = (
            f"{prompt}\n\n"
            f"[Official Indonesian Customs Knowledge Grounding]:\n"
            + "\n".join(context_snippets)
        )

    connect_timeout = float(timeout_seconds)
    for host in ["langflow", "localhost"]:
        # 1. Primary: Langflow v1 chat run endpoint with session_id
        v1_url = f"http://{host}:7860/api/v1/run/{flow_id}"
        v1_payload = json.dumps(
            {
                "output_type": "chat",
                "input_type": "chat",
                "input_value": augmented_prompt,
                "session_id": str(uuid.uuid4()),
            }
        ).encode("utf-8")
        try:
            req = urllib.request.Request(v1_url, data=v1_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=connect_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                outputs = data.get("outputs", [])
                if outputs:
                    text = (
                        outputs[0]
                        .get("outputs", [{}])[0]
                        .get("results", {})
                        .get("message", {})
                        .get("text")
                    )
                    if text:
                        return str(text)
        except Exception:
            pass

        # 2. Fallback: Langflow v2 workflows endpoint
        v2_url = f"http://{host}:7860/api/v2/workflows"
        v2_payload = json.dumps({"flow_id": flow_id, "input_value": augmented_prompt}).encode("utf-8")
        try:
            req = urllib.request.Request(v2_url, data=v2_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=connect_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                v2_text = data.get("output", {}).get("text")
                if v2_text:
                    return str(v2_text)
        except Exception:
            continue
    return None


def _try_langflow_ingest_flow(extracted_text: str, timeout_seconds: float = 30.0) -> Optional[str]:
    """Queries dedicated Langflow Ingestion Flow to extract and verify invoice line items."""
    import uuid

    flow_id = os.environ.get("LANGFLOW_INGEST_FLOW_ID")
    if not flow_id:
        return None

    api_key = _get_langflow_api_key()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    connect_timeout = float(timeout_seconds)
    for host in ["langflow", "localhost"]:
        # 1. Try Langflow v1 run endpoint
        v1_url = f"http://{host}:7860/api/v1/run/{flow_id}"
        v1_payload = json.dumps(
            {
                "output_type": "chat",
                "input_type": "chat",
                "input_value": extracted_text,
                "session_id": str(uuid.uuid4()),
            }
        ).encode("utf-8")
        try:
            req = urllib.request.Request(v1_url, data=v1_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=connect_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                outputs = data.get("outputs", [])
                if outputs:
                    text = (
                        outputs[0]
                        .get("outputs", [{}])[0]
                        .get("results", {})
                        .get("message", {})
                        .get("text")
                    )
                    if text:
                        return str(text)
        except Exception:
            pass

        # 2. Try Langflow v2 workflows endpoint
        v2_url = f"http://{host}:7860/api/v2/workflows"
        v2_payload = json.dumps({"flow_id": flow_id, "input_value": extracted_text}).encode("utf-8")
        try:
            req = urllib.request.Request(v2_url, data=v2_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=connect_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                v2_text = data.get("output", {}).get("text")
                if v2_text:
                    return str(v2_text)
        except Exception:
            continue
    return None


def _extract_text_from_file_bytes(content: bytes, filename: str) -> str:
    """Extracts raw text content from DOCX, PDF, or text files using lightweight native parsers."""
    name_lower = filename.lower()

    if name_lower.endswith(".docx"):
        try:
            import docx

            doc = docx.Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        paragraphs.append(" | ".join(row_cells))
            return "\n".join(paragraphs).strip()
        except Exception as exc:
            return f"Error reading DOCX: {exc}"

    if name_lower.endswith(".pdf"):
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt and txt.strip():
                    pages_text.append(txt.strip())
            return "\n\n--- Page Break ---\n\n".join(pages_text).strip()
        except Exception as exc:
            return f"Error reading PDF: {exc}"

    if any(name_lower.endswith(ext) for ext in [".txt", ".csv", ".tsv", ".md"]):
        try:
            return content.decode("utf-8", errors="replace").strip()
        except Exception as exc:
            return f"Error reading text file: {exc}"

    return ""


def _deterministic_text_invoice_parser(text: str) -> Optional[Dict[str, Any]]:
    """Deterministic local parser that extracts structured line items from document text if LLM is offline."""
    import re

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    items = []
    # Pattern for HS code: 4 to 6 digits, optionally with dot (e.g. 8517.13, 8471.30, 851713)
    hs_pattern = re.compile(r"\b(\d{4}\.\d{2}|\d{6})\b")
    # Pattern for currency value: $500.00, 50,000.00, etc.
    value_pattern = re.compile(r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|\d+(?:\.[0-9]+)?)")

    for idx, line in enumerate(lines, start=1):
        hs_match = hs_pattern.search(line)
        if hs_match:
            raw_hs = hs_match.group(1)
            norm_hs = raw_hs if "." in raw_hs else f"{raw_hs[:4]}.{raw_hs[4:]}"

            # Extract line text excluding the HS code for description
            desc_candidate = hs_pattern.sub("", line).strip()
            desc_candidate = re.sub(r"^[0-9]+[\.\)\s\-]+", "", desc_candidate).strip()
            desc_candidate = re.sub(r"[\$\|\,]", " ", desc_candidate).strip()

            # Find numeric amounts in line
            vals = [float(v.replace(",", "")) for v in value_pattern.findall(line) if float(v.replace(",", "")) > 0]
            val = vals[-1] if vals else 1000.0

            items.append(
                {
                    "item_id": len(items) + 1,
                    "declared_description": desc_candidate or f"Declared Commodity Line {len(items) + 1}",
                    "declared_hs_code": norm_hs,
                    "quantity": 1,
                    "unit_price": val,
                    "total_value": val,
                    "declared_duty_rate": 0.0,
                }
            )

    if not items:
        return None

    return {
        "status": "complete",
        "error_message": None,
        "missing_fields": [],
        "invoice_data": {
            "shipment_id": "UNSPECIFIED",
            "invoice_number": "UNSPECIFIED",
            "carrier": "CMA CGM",
            "importer_name": "UNSPECIFIED",
            "exporter_name": "UNSPECIFIED",
            "country_of_origin": "UNSPECIFIED",
            "destination_port": "Tanjung Priok, Jakarta (IDTPP)",
            "container_count": 1,
            "container_size": "40",
            "container_type": "DRY",
            "days_held_projected": 10,
            "currency": "USD",
            "items": items,
        },
    }


def _terminate_process_group(proc: asyncio.subprocess.Process) -> None:
    """Terminates the entire process group of an asynchronous subprocess to prevent zombie processes."""
    if proc.pid is None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except Exception:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except Exception:
        pass


def _local_regulatory_assistant_fallback(prompt: str) -> str:
    """Deterministic local knowledge base and CMA CGM tariff fallback for regulatory Q&A."""
    q_lower = prompt.lower()
    exact_matches = []
    keyword_matches = []

    stop_words = {
        "what",
        "which",
        "how",
        "many",
        "much",
        "for",
        "the",
        "and",
        "are",
        "into",
        "indonesia",
        "import",
        "tariff",
        "duty",
        "rate",
        "permits",
        "required",
        "explain",
        "cma",
        "cgm",
        "demurrage",
        "detention",
        "slab",
        "slabs",
        "container",
        "containers",
        "code",
        "codes",
    }

    if os.path.isfile(TARIFF_DB_PATH):
        try:
            with open(TARIFF_DB_PATH, "r", encoding="utf-8") as f:
                tariffs = json.load(f)
            keywords = [
                w.strip("?.,():;\"'")
                for w in q_lower.split()
                if len(w.strip("?.,():;\"'")) >= 3
                and w.strip("?.,():;\"'") not in stop_words
            ]
            for entry in tariffs:
                hs = str(entry.get("hs_code", "")).lower()
                search_text = str(entry.get("search_text", "")).lower()
                if hs and hs in q_lower:
                    exact_matches.append(entry)
                elif len(keyword_matches) < 5 and any(
                    k in search_text for k in keywords
                ):
                    keyword_matches.append(entry)
        except Exception:
            pass

    matched_records = (exact_matches + keyword_matches)[:5]

    sections = ["### CustomsGuard Regulatory Intelligence Response"]

    if any(
        term in q_lower
        for term in ["demurrage", "detention", "cma", "cgm", "reefer", "container", "free days", "slab"]
    ):
        dry_sample = calculate_cma_cgm_demurrage(
            container_count=1,
            container_size="40",
            container_type="DRY",
            days_held_projected=10,
            container_detention_risk=True,
        )
        reefer_sample = calculate_cma_cgm_demurrage(
            container_count=1,
            container_size="40",
            container_type="REEFER",
            days_held_projected=6,
            container_detention_risk=True,
        )
        sections.append(
            "#### CMA CGM Indonesia Merged Import Demurrage & Detention Schedule (Effective July 1, 2026)\n"
            "- **Standard Dry Containers (5 Free Days)**:\n"
            "  - Days 1 to 5: `$0/day`\n"
            "  - Days 6 to 10: `$66/day` (20ft), `$101/day` (40ft), `$141/day` (45ft)\n"
            "  - Days 11 to 15: `$86/day` (20ft), `$121/day` (40ft), `$171/day` (45ft)\n"
            "  - Days 16 to 20: `$96/day` (20ft), `$151/day` (40ft), `$181/day` (45ft)\n"
            "  - Days 21+: `$106/day` (20ft), `$161/day` (40ft), `$191/day` (45ft)\n"
            "- **Reefer Containers (3 Free Days)**:\n"
            "  - Days 1 to 3: `$0/day`\n"
            "  - Days 4 to 5: `$89/day` (20ft), `$141/day` (40ft)\n"
            "  - Days 6 to 7: `$126/day` (20ft), `$176/day` (40ft)\n"
            "  - Days 8+: `$130/day` (20ft), `$180/day` (40ft)\n"
            f"- **Benchmark Example**: 1x 40ft Dry held 10 days = `${dry_sample['projected_cumulative_liability_usd']:,.2f} USD`; "
            f"1x 40ft Reefer held 6 days = `${reefer_sample['projected_cumulative_liability_usd']:,.2f} USD`."
        )

    if matched_records:
        rows = [
            "#### Matched Indonesian HS-6 Tariff & Lartas Schedule",
            "| HS-6 Code | Description | Official MFN Duty | Restricted (Lartas) | Mandatory Permits |",
            "| :---: | :--- | :---: | :---: | :--- |",
        ]
        for rec in matched_records[:5]:
            permits = ", ".join(rec.get("required_permits") or []) or "None"
            rows.append(
                f"| `{rec['hs_code']}` | {rec['description']} | {float(rec['duty_rate']):.1f}% | "
                f"{'Yes' if rec.get('restricted') else 'No'} | {permits} |"
            )
        sections.append("\n".join(rows))
    elif len(sections) == 1:
        sections.append(
            "#### Indonesian Import Regulatory Summary\n"
            "- **Telecommunications & RF Apparatus (e.g., HS `8517.11`, `8517.13`, `8517.62`)**: Restricted under Lartas; requires **SDPPI Type Approval Certification (Kemkominfo)** prior to port arrival.\n"
            "- **Medical Diagnostic Equipment (e.g., HS `9018.12` Ultrasonic Scanners)**: Restricted under Lartas; requires **Kemenkes RI Medical Device Distribution License (Izin Edar Alat Kesehatan)**.\n"
            "- **Food, Pharmaceuticals & Cosmetics (Chapters 16-22, 30, 33)**: Restricted under Lartas; requires **BPOM Import Notification (SKI BPOM)**.\n"
            "- **Enterprise Computing Units (e.g., HS `8471.30`, `8471.50`)**: 0.0% MFN import duty; eligible for duty restitution if over-declared."
        )

    return "\n\n".join(sections)


@app.get(
    "/api/v1/health",
    response_model=HealthStatus,
    summary="Verify connectivity to Qdrant, Langflow, and Mailpit services",
)
def health_check() -> HealthStatus:
    qdrant_check = _check_http_service(
        [
            "http://qdrant:6333/collections",
            "http://localhost:6333/collections",
        ]
    )
    langflow_check = _check_http_service(
        [
            "http://langflow:7860/health",
            "http://localhost:7860/health",
        ]
    )
    mailpit_check = _check_tcp_service(["mailpit", "localhost"], 1025)

    overall = (
        "healthy"
        if (qdrant_check.reachable and mailpit_check.reachable)
        else "degraded"
    )
    return HealthStatus(
        status=overall,
        qdrant=qdrant_check,
        langflow=langflow_check,
        mailpit=mailpit_check,
    )


@app.post(
    "/api/v1/ingest/document",
    response_model=IngestionResponse,
    summary="Ingest commercial invoice from PDF, DOCX, Images, or JSON and verify completeness",
)
async def ingest_document(file: UploadFile = File(...)) -> IngestionResponse:
    filename = file.filename or "unknown_file"
    name_lower = filename.lower()
    content = await file.read()

    if not content:
        return IngestionResponse(
            status="failed",
            error_message="Uploaded file is empty (0 bytes).",
            missing_fields=["file_content"],
            filename=filename,
        )

    # 1. Direct JSON bypass: instant parsing with zero latency
    if name_lower.endswith(".json"):
        try:
            parsed = json.loads(content.decode("utf-8"))
            if isinstance(parsed, list) and parsed:
                parsed = parsed[0]
            if not isinstance(parsed, dict):
                return IngestionResponse(
                    status="rejected",
                    error_message="JSON file does not contain a valid invoice object.",
                    filename=filename,
                )

            validation = parse_and_validate_ingestion_json(json.dumps(parsed))
            if validation["status"] == "complete":
                validated_payload = InvoicePayload.model_validate(
                    parsed.get("invoice_data") or parsed
                )
                return IngestionResponse(
                    status="complete",
                    invoice_data=validated_payload,
                    filename=filename,
                )
            else:
                return IngestionResponse(
                    status="rejected",
                    error_message=validation.get("message", "Incomplete invoice data."),
                    missing_fields=validation.get("missing_fields", []),
                    filename=filename,
                )
        except Exception as exc:
            return IngestionResponse(
                status="failed",
                error_message=f"Failed to parse JSON file: {exc}",
                filename=filename,
            )

    # 2. Extract text from DOCX, PDF, or text documents
    extracted_text = _extract_text_from_file_bytes(content, filename)

    # 3. Process via Langflow Ingestion Flow if configured
    llm_raw_response = None
    if extracted_text:
        llm_raw_response = _try_langflow_ingest_flow(extracted_text, timeout_seconds=30.0)

    # 4. If Langflow output received, validate outermost JSON and line-item completeness
    if llm_raw_response:
        validation = parse_and_validate_ingestion_json(llm_raw_response)
        if validation["status"] == "complete":
            try:
                candidate = validation["extracted_data"]
                inv_dict = candidate.get("invoice_data") or candidate
                validated_payload = InvoicePayload.model_validate(inv_dict)
                return IngestionResponse(
                    status="complete",
                    invoice_data=validated_payload,
                    filename=filename,
                )
            except Exception as exc:
                return IngestionResponse(
                    status="rejected",
                    error_message=f"Invoice schema validation failed: {exc}",
                    filename=filename,
                )
        elif validation["status"] == "rejected":
            return IngestionResponse(
                status="rejected",
                error_message=validation.get("error_message") or validation.get("message"),
                missing_fields=validation.get("missing_fields", []),
                filename=filename,
            )

    # 5. Fallback deterministic text parser for document text (e.g. DOCX or text PDF)
    if extracted_text and not extracted_text.startswith("Error"):
        det_parsed = _deterministic_text_invoice_parser(extracted_text)
        if det_parsed and det_parsed.get("status") == "complete":
            try:
                validated_payload = InvoicePayload.model_validate(det_parsed["invoice_data"])
                return IngestionResponse(
                    status="complete",
                    invoice_data=validated_payload,
                    filename=filename,
                )
            except Exception:
                pass

    # 6. Fallback rejection if file could not be parsed into valid line items
    return IngestionResponse(
        status="rejected",
        error_message=(
            f"Unable to extract required customs line items from '{filename}'. "
            "Please ensure the document contains commodity descriptions, 6-digit HS codes, and commercial values."
        ),
        missing_fields=["items", "declared_hs_code", "total_value"],
        filename=filename,
    )


@app.post(
    "/api/v1/audit",
    response_model=AuditResponse,
    summary="Execute deterministic customs tariff audit, dossier export, and Mailpit alert",
)
def run_audit(payload: InvoicePayload) -> AuditResponse:
    tools = _get_toolkit_map()
    audit_tool = tools["audit_shipment_compliance"]
    export_tool = tools["export_compliance_report"]
    alert_tool = tools["send_compliance_alert"]

    invoice_dict = payload.model_dump(exclude={"include_narrative"})
    invoice_json_str = json.dumps(invoice_dict)

    raw_audit_str = audit_tool.invoke({"invoice_json": invoice_json_str})
    if raw_audit_str.startswith("Error parsing invoice JSON"):
        raise HTTPException(status_code=400, detail=raw_audit_str)

    audit_data = json.loads(raw_audit_str)
    audit_model = AuditResult.model_validate(audit_data)

    export_msg = export_tool.invoke(
        {
            "shipment_id": audit_model.shipment_id,
            "audit_summary_json": raw_audit_str,
        }
    )
    report_path = export_msg.split("Audit report successfully exported to:")[-1].strip()

    if os.path.isfile(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            markdown_dossier = f.read()
    else:
        markdown_dossier = format_markdown_dossier(
            shipment_id=audit_model.shipment_id,
            audit_summary_json=raw_audit_str,
            generated_at=datetime.datetime.now().isoformat(),
            md_path=report_path,
        )

    if (
        audit_model.overall_status in ("NON_COMPLIANT_HIGH_RISK", "WARNING_DISCREPANCY")
        or audit_model.container_detention_risk
    ):
        alert_status = alert_tool.invoke(
            {
                "shipment_id": audit_model.shipment_id,
                "verdict": audit_model.overall_status,
                "alert_details": raw_audit_str,
            }
        )
    else:
        alert_status = "No alert required (Shipment is COMPLIANT with zero detention risk)."

    fallback_narrative = _build_executive_narrative(audit_model)
    if payload.include_narrative:
        executive_narrative = _try_langflow_narrative(invoice_dict, fallback_narrative)
    else:
        executive_narrative = fallback_narrative

    return AuditResponse(
        audit=audit_model,
        markdown_dossier=markdown_dossier,
        report_path=report_path,
        alert_status=alert_status,
        executive_narrative=executive_narrative,
    )


@app.get(
    "/api/v1/reports",
    response_model=List[ReportItem],
    summary="List archived compliance dossiers from ./data/reports",
)
def list_reports() -> List[ReportItem]:
    candidate_roots = []
    if os.path.exists("/app/reports"):
        candidate_roots.append("/app/reports")
    local_reports = os.path.join(BASE_DIR, "data", "reports")
    if os.path.exists(local_reports) and local_reports not in candidate_roots:
        candidate_roots.append(local_reports)

    seen_keys = set()
    items: List[ReportItem] = []

    for root_dir in candidate_roots:
        try:
            date_dirs = sorted(os.listdir(root_dir), reverse=True)
        except OSError:
            continue

        for date_str in date_dirs:
            date_path = os.path.join(root_dir, date_str)
            if not os.path.isdir(date_path):
                continue
            try:
                shipment_dirs = sorted(os.listdir(date_path), reverse=True)
            except OSError:
                continue

            for shp_id in shipment_dirs:
                shp_path = os.path.join(date_path, shp_id)
                if not os.path.isdir(shp_path):
                    continue
                dedup_key = f"{date_str}/{shp_id}"
                if dedup_key in seen_keys:
                    continue

                json_file = os.path.join(shp_path, "audit_report.json")
                md_file = os.path.join(shp_path, "audit_report.md")
                if not os.path.isfile(json_file):
                    continue

                try:
                    with open(json_file, "r", encoding="utf-8") as jf:
                        json_content = jf.read()
                    parsed_json = json.loads(json_content)
                except Exception:
                    continue

                if os.path.isfile(md_file):
                    with open(md_file, "r", encoding="utf-8") as mf:
                        md_content = mf.read()
                    if (
                        ("```json" in md_content and "Executive Summary" not in md_content)
                        or md_content.startswith("# ")
                    ):
                        md_content = format_markdown_dossier(
                            shipment_id=shp_id,
                            audit_summary_json=json_content,
                            generated_at=date_str,
                            md_path=md_file,
                        )
                else:
                    md_content = format_markdown_dossier(
                        shipment_id=shp_id,
                        audit_summary_json=json_content,
                        generated_at=date_str,
                        md_path=md_file,
                    )

                seen_keys.add(dedup_key)
                items.append(
                    ReportItem(
                        shipment_id=parsed_json.get("shipment_id", shp_id),
                        date=date_str,
                        importer=parsed_json.get("importer")
                        or parsed_json.get("importer_name")
                        or "UNKNOWN",
                        overall_status=parsed_json.get("overall_status", "UNKNOWN"),
                        container_count=int(parsed_json.get("container_count") or 1),
                        total_duty_shortfall_usd=float(
                            parsed_json.get("total_duty_shortfall_usd") or 0.0
                        ),
                        total_restitution_usd=float(
                            parsed_json.get("total_restitution_usd") or 0.0
                        ),
                        estimated_demurrage_per_day_usd=float(
                            parsed_json.get("estimated_demurrage_per_day_usd") or 0.0
                        ),
                        report_dir=shp_path,
                        json_content=json_content,
                        markdown_content=md_content,
                    )
                )

    return items


@app.post(
    "/api/v1/assistant",
    response_model=AssistantResponse,
    summary="Execute stateless one-shot IBM Bob CLI regulatory query with bounded pool and process-group cleanup",
)
async def ask_assistant(query: AssistantQuery) -> AssistantResponse:
    start_ts = time.monotonic()

    try:
        await asyncio.wait_for(BOB_SEMAPHORE.acquire(), timeout=2.0)
    except asyncio.TimeoutError:
        elapsed_ms = int((time.monotonic() - start_ts) * 1000)
        return AssistantResponse(
            status="busy",
            engine="ibm-bob-cli",
            answer=(
                "The IBM Bob CLI assistant worker pool is currently at maximum capacity "
                f"({MAX_CONCURRENT_BOB_WORKERS} concurrent sessions). Please retry in a few moments."
            ),
            duration_ms=elapsed_ms,
        )

    proc: Optional[asyncio.subprocess.Process] = None
    try:
        env = os.environ.copy()
        nvm_node_path = "/home/rafif/.nvm/versions/node/v24.21.0/bin"
        pnpm_path = "/home/rafif/.local/share/pnpm/bin"
        env["PATH"] = f"{nvm_node_path}:{pnpm_path}:{env.get('PATH', '')}"

        cmd = [
            "bob",
            "run",
            "--trust",
            "--max-turns",
            "4",
            "--format",
            "json",
            query.prompt,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=BASE_DIR,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
        except FileNotFoundError:
            lf_ans = _try_langflow_assistant(query.prompt, float(query.timeout_seconds))
            elapsed_ms = int((time.monotonic() - start_ts) * 1000)
            if lf_ans:
                return AssistantResponse(
                    status="online",
                    engine="langflow-regulatory-agent",
                    answer=lf_ans,
                    duration_ms=elapsed_ms,
                )
            return AssistantResponse(
                status="fallback",
                engine="local-tariff-rag-fallback",
                answer=_local_regulatory_assistant_fallback(query.prompt),
                duration_ms=elapsed_ms,
            )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(query.timeout_seconds),
            )
        except asyncio.TimeoutError:
            _terminate_process_group(proc)
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except Exception:
                pass
            elapsed_ms = int((time.monotonic() - start_ts) * 1000)
            return AssistantResponse(
                status="timeout",
                engine="ibm-bob-cli",
                answer=(
                    f"IBM Bob CLI subprocess exceeded hard timeout of {query.timeout_seconds}s. "
                    "Process group was terminated cleanly via SIGKILL."
                ),
                duration_ms=elapsed_ms,
            )
        except asyncio.CancelledError:
            _terminate_process_group(proc)
            raise

        stdout_text = (stdout_bytes or b"").decode("utf-8", errors="replace").strip()
        stderr_text = (stderr_bytes or b"").decode("utf-8", errors="replace").strip()
        elapsed_ms = int((time.monotonic() - start_ts) * 1000)

        if proc.returncode == 0 and stdout_text:
            bob_answer = ""
            for line in stdout_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict) and parsed.get("last_message"):
                        bob_answer = str(parsed["last_message"])
                except json.JSONDecodeError:
                    continue

            if not bob_answer:
                bob_answer = stdout_text

            return AssistantResponse(
                status="success",
                engine="ibm-bob-cli",
                answer=bob_answer,
                duration_ms=elapsed_ms,
            )

        fallback_text = _local_regulatory_assistant_fallback(query.prompt)
        return AssistantResponse(
            status="fallback",
            engine="local-tariff-rag-fallback",
            answer=fallback_text,
            duration_ms=elapsed_ms,
        )
    finally:
        BOB_SEMAPHORE.release()
