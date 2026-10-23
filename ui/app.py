"""CustomsGuard Native Streamlit Compliance Dashboard.

Zero custom CSS injection. Configured declaratively via .streamlit/config.toml
(Dark theme with #0B0B0F sidebar and #A78BFA purple accent).
Uses native st.navigation in the sidebar, st.pills, and st.container(border=True).
"""

import json
import os
import sys
import urllib.request
from typing import Any, Dict, List, Optional
from pathlib import Path

import streamlit as st

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from api.main import ask_assistant, health_check, list_reports, run_audit
from api.schemas import AssistantQuery, InvoicePayload
from scripts.customs_components import CMA_CGM_TARIFFS

SAMPLE_INVOICES_PATH = os.path.join(ROOT_DIR, "data", "seed", "sample_invoices.json")
DEFAULT_ASSISTANT_TIMEOUT = 240

API_CANDIDATE_URLS = [
    os.environ.get("CUSTOMSGUARD_API_URL", "").rstrip("/"),
    "http://customsguard-api:8000",
    "http://localhost:8000",
]
API_CANDIDATE_URLS = [u for u in API_CANDIDATE_URLS if u]

def escape_md_dollars(text: str) -> str:
    """Escapes literal dollar signs so Streamlit Markdown does not trigger KaTeX math."""
    return str(text or "").replace("\\$", "$").replace("$", "\\$")


def render_responsive_markdown(md_text: str) -> None:
    """Renders Markdown inside bordered containers with compact headings and responsive st.dataframe tables."""
    normalized = str(md_text or "")
    normalized = normalized.replace(
        "# CustomsGuard Compliance Audit Report",
        "### CustomsGuard Compliance Audit Report",
    )
    for section_title in (
        "Executive Summary",
        "Critical Discrepancies & Regulatory Violations",
        "Itemized Audit Findings",
        "Automated Actions Taken",
    ):
        normalized = normalized.replace(
            f"\n### {section_title}", f"\n#### {section_title}"
        )

    lines = normalized.splitlines()
    text_buffer: List[str] = []
    table_buffer: List[str] = []

    def _flush_text() -> None:
        if text_buffer:
            chunk = "\n".join(text_buffer).strip()
            if chunk:
                st.markdown(escape_md_dollars(chunk))
            text_buffer.clear()

    def _flush_table() -> None:
        if not table_buffer:
            return
        if len(table_buffer) >= 2:
            headers = [
                c.strip() for c in table_buffer[0].strip().strip("|").split("|")
            ]
            data_rows: List[Dict[str, str]] = []
            for row_line in table_buffer[1:]:
                stripped = row_line.strip().strip("|")
                cells = [c.strip() for c in stripped.split("|")]
                if all(set(c) <= {":", "-", " "} and c for c in cells):
                    continue
                row_dict: Dict[str, str] = {}
                for idx, h in enumerate(headers):
                    col_name = h or f"Col {idx + 1}"
                    val = cells[idx] if idx < len(cells) else ""
                    row_dict[col_name] = val.replace("\\$", "$")
                data_rows.append(row_dict)
            if data_rows:
                st.dataframe(
                    data_rows,
                    use_container_width=True,
                    hide_index=True,
                )
                table_buffer.clear()
                return
        text_buffer.extend(table_buffer)
        table_buffer.clear()

    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and s.count("|") >= 2:
            _flush_text()
            table_buffer.append(line)
        else:
            if table_buffer:
                _flush_table()
            text_buffer.append(line)

    if table_buffer:
        _flush_table()
    _flush_text()


def format_short_verdict(status: str) -> str:
    """Formats a concise metric value that never truncates inside st.metric cards."""
    if status == "NON_COMPLIANT_HIGH_RISK":
        return "HIGH RISK"
    if status == "WARNING_DISCREPANCY":
        return "DISCREPANCY"
    if status == "COMPLIANT":
        return "COMPLIANT"
    return status


def load_sample_invoices() -> List[Dict[str, Any]]:
    if os.path.isfile(SAMPLE_INVOICES_PATH):
        with open(SAMPLE_INVOICES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def api_request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 15.0,
) -> Optional[Any]:
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}

    for base_url in API_CANDIDATE_URLS:
        url = f"{base_url}{path}"
        try:
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers=headers,
                method=method,
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue
    return None


def fetch_health() -> Dict[str, Any]:
    res = api_request("GET", "/api/v1/health", timeout=3.0)
    if res is not None:
        return res
    return health_check().model_dump()


def execute_audit_request(invoice_dict: Dict[str, Any]) -> Dict[str, Any]:
    res = api_request("POST", "/api/v1/audit", payload=invoice_dict, timeout=25.0)
    if res is not None:
        return res
    model_payload = InvoicePayload.model_validate(invoice_dict)
    return run_audit(model_payload).model_dump()


def fetch_reports_archive() -> List[Dict[str, Any]]:
    res = api_request("GET", "/api/v1/reports", timeout=8.0)
    if isinstance(res, list):
        return res
    return [r.model_dump() for r in list_reports()]


def execute_assistant_request(
    prompt: str, timeout_seconds: int = DEFAULT_ASSISTANT_TIMEOUT
) -> Dict[str, Any]:
    res = api_request(
        "POST",
        "/api/v1/assistant",
        payload={"prompt": prompt, "timeout_seconds": timeout_seconds},
        timeout=float(timeout_seconds) + 5.0,
    )
    if res is not None:
        return res
    import asyncio

    query = AssistantQuery(prompt=prompt, timeout_seconds=timeout_seconds)
    return asyncio.run(ask_assistant(query)).model_dump()


def build_cma_cgm_slab_breakdown_rows(
    container_count: int,
    container_size: str,
    container_type: str,
    days_projected: int,
    detention_risk: bool,
) -> List[Dict[str, Any]]:
    norm_type = "REEFER" if "REEF" in str(container_type).upper() else "DRY"
    norm_size = (
        "20"
        if "20" in str(container_size)
        else ("45" if "45" in str(container_size) else "40")
    )
    if norm_type == "DRY":
        slabs_meta = [
            ("Days 1 to 5 (Free)", 1, 5, 0.0),
            (
                "Slab 1: Days 6 to 10",
                6,
                10,
                CMA_CGM_TARIFFS["DRY"]["slabs"][1]["rates"][norm_size],
            ),
            (
                "Slab 2: Days 11 to 15",
                11,
                15,
                CMA_CGM_TARIFFS["DRY"]["slabs"][2]["rates"][norm_size],
            ),
            (
                "Slab 3: Days 16 to 20",
                16,
                20,
                CMA_CGM_TARIFFS["DRY"]["slabs"][3]["rates"][norm_size],
            ),
            (
                "Slab 4: Days 21+",
                21,
                999,
                CMA_CGM_TARIFFS["DRY"]["slabs"][4]["rates"][norm_size],
            ),
        ]
    else:
        slabs_meta = [
            ("Days 1 to 3 (Free)", 1, 3, 0.0),
            (
                "Slab 1: Days 4 to 5",
                4,
                5,
                CMA_CGM_TARIFFS["REEFER"]["slabs"][1]["rates"][norm_size],
            ),
            (
                "Slab 2: Days 6 to 7",
                6,
                7,
                CMA_CGM_TARIFFS["REEFER"]["slabs"][2]["rates"][norm_size],
            ),
            (
                "Slab 3: Days 8+",
                8,
                999,
                CMA_CGM_TARIFFS["REEFER"]["slabs"][3]["rates"][norm_size],
            ),
        ]

    rows = []
    for label, start_day, end_day, rate_per_cntr in slabs_meta:
        if not detention_risk or days_projected < start_day:
            days_in_slab = 0
        else:
            days_in_slab = max(0, min(days_projected, end_day) - start_day + 1)
        fleet_daily_rate = rate_per_cntr * container_count
        slab_subtotal = fleet_daily_rate * days_in_slab
        rows.append(
            {
                "Tariff Tier": label,
                "Equipment": f"{container_count}x {norm_size}ft {norm_type.capitalize()}",
                "Rate / Cntr / Day": rate_per_cntr,
                "Fleet Burn / Day": fleet_daily_rate,
                "Active Days": days_in_slab,
                "Tier Subtotal": slab_subtotal,
            }
        )
    return rows


def ensure_session_defaults() -> None:
    samples = load_sample_invoices()
    if "samples_cache" not in st.session_state:
        st.session_state["samples_cache"] = samples
    if "active_invoice" not in st.session_state:
        default_inv = (
            samples[0]
            if samples
            else {
                "shipment_id": "SHP-2026-0042",
                "invoice_number": "INV-2026-APL-091",
                "carrier": "CMA CGM / APL",
                "importer_name": "PT Nexus Indo Tech",
                "destination_port": "Tanjung Priok, Jakarta (IDTPP)",
                "container_count": 4,
                "container_size": "40",
                "container_type": "DRY",
                "days_held_projected": 10,
                "currency": "USD",
                "items": [
                    {
                        "item_id": 1,
                        "declared_description": "Apple iPhone 15 Pro Max 256GB Dual SIM Smartphone",
                        "declared_hs_code": "8471.30",
                        "quantity": 100,
                        "unit_price": 1150.0,
                        "total_value": 115000.0,
                        "declared_duty_rate": 0.0,
                    }
                ],
            }
        )
        st.session_state["active_invoice"] = json.loads(json.dumps(default_inv))
    if "last_audit_response" not in st.session_state:
        st.session_state["last_audit_response"] = None


def page_audit_workspace() -> None:
    ensure_session_defaults()
    samples = st.session_state["samples_cache"]

    st.title("CustomsGuard Audit Workspace")
    st.write(
        "Audit commercial shipping declarations against 5,612 Indonesian HS-6 tariff records, "
        "Lartas ministry permits, and CMA CGM Indonesia progressive detention schedules."
    )

    scenario_map = {
        "1. Red-Lane Hold (SDPPI)": 0,
        "2. Multi-Cntr Demurrage": 1,
        "3. Duty Restitution": 2,
        "4. Compliant Clearance": 3,
    }

    with st.container(border=True):
        st.markdown("**:material/tune: Scenario Presets & Manifest Input**")
        selected_pill = st.pills(
            "Select a canonical trade compliance scenario",
            options=list(scenario_map.keys()),
            default=st.session_state.get("selected_scenario_pill", "1. Red-Lane Hold (SDPPI)"),
            label_visibility="collapsed",
        )
        if (
            selected_pill
            and selected_pill != st.session_state.get("selected_scenario_pill")
        ):
            st.session_state["selected_scenario_pill"] = selected_pill
            idx = scenario_map[selected_pill]
            if idx < len(samples):
                st.session_state["active_invoice"] = json.loads(
                    json.dumps(samples[idx])
                )
                st.session_state["last_audit_response"] = None
                st.rerun()

        uploaded_file = st.file_uploader(
            "Upload custom commercial invoice JSON",
            type=["json"],
        )
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                if isinstance(uploaded_data, list) and uploaded_data:
                    uploaded_data = uploaded_data[0]
                if isinstance(uploaded_data, dict):
                    st.session_state["active_invoice"] = uploaded_data
                    st.session_state["last_audit_response"] = None
            except Exception as exc:
                st.error(f"Invalid JSON file: {exc}")

    inv = st.session_state["active_invoice"]

    with st.container(border=True):
        st.markdown("**:material/description: Commercial Invoice & Container Parameters**")
        col_a, col_b = st.columns(2)
        with col_a:
            shipment_id = st.text_input(
                "Shipment ID",
                value=str(inv.get("shipment_id", "SHP-2026-0042")),
            )
            importer_name = st.text_input(
                "Importer Name",
                value=str(inv.get("importer_name", "PT Nexus Indo Tech")),
            )
            carrier = st.text_input(
                "Ocean Carrier",
                value=str(inv.get("carrier", "CMA CGM")),
            )
            destination_port = st.text_input(
                "Destination Port",
                value=str(inv.get("destination_port", "Tanjung Priok, Jakarta (IDTPP)")),
            )
        with col_b:
            container_count = st.number_input(
                "Container Count",
                min_value=1,
                max_value=50,
                value=int(inv.get("container_count") or 1),
                step=1,
            )
            size_options = ["20", "40", "45"]
            default_size = str(inv.get("container_size") or "40")
            size_idx = (
                size_options.index(default_size)
                if default_size in size_options
                else 1
            )
            container_size = st.selectbox(
                "Container Size (ft)",
                options=size_options,
                index=size_idx,
            )
            type_options = ["DRY", "REEFER"]
            default_type = (
                "REEFER"
                if "REEF" in str(inv.get("container_type") or "DRY").upper()
                else "DRY"
            )
            container_type = st.selectbox(
                "Equipment Type",
                options=type_options,
                index=type_options.index(default_type),
            )
            days_held_projected = st.slider(
                "Projected Hold Duration (Days)",
                min_value=1,
                max_value=30,
                value=int(inv.get("days_held_projected") or 10),
            )

        st.markdown("**Declared Commodity Line Items**")
        edited_items = st.data_editor(
            inv.get("items", []),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "item_id": st.column_config.NumberColumn("ID", min_value=1, step=1),
                "declared_description": st.column_config.TextColumn(
                    "Commodity Description", width="large"
                ),
                "declared_hs_code": st.column_config.TextColumn("Declared HS"),
                "quantity": st.column_config.NumberColumn("Qty", min_value=1),
                "unit_price": st.column_config.NumberColumn(
                    "Unit Price", format="$%.2f"
                ),
                "total_value": st.column_config.NumberColumn(
                    "Total Value", format="$%.2f"
                ),
                "declared_duty_rate": st.column_config.NumberColumn(
                    "Duty (%)", format="%.1f%%"
                ),
            },
            key="invoice_items_editor",
        )

        run_btn = st.button(
            "Run Autonomous Compliance Audit",
            type="primary",
            use_container_width=True,
        )

    if run_btn:
        payload_to_run = {
            "shipment_id": shipment_id,
            "importer_name": importer_name,
            "carrier": carrier,
            "destination_port": destination_port,
            "container_count": int(container_count),
            "container_size": container_size,
            "container_type": container_type,
            "days_held_projected": int(days_held_projected),
            "currency": "USD",
            "items": edited_items,
        }
        with st.status(
            "Executing deterministic HS-6 RAG & CMA CGM demurrage audit...",
            expanded=False,
        ) as status_box:
            audit_resp = execute_audit_request(payload_to_run)
            st.session_state["last_audit_response"] = audit_resp
            status_box.update(
                label=f"Audit Complete: {audit_resp['audit']['shipment_id']} ({audit_resp['audit']['overall_status']})",
                state="complete",
            )

    resp_data = st.session_state.get("last_audit_response")
    if not resp_data or "audit" not in resp_data:
        with st.container(border=True):
            st.markdown("**:material/fact_check: Audit Pending**")
            st.write(
                "Manifest parameters and line items are loaded. Click "
                "**Run Autonomous Compliance Audit** above to audit tariff classifications, "
                "calculate CMA CGM demurrage exposure, and verify mandatory ministry import permits."
            )
        return

    audit = resp_data["audit"]
    dem = audit["demurrage_assessment"]

    st.subheader("Executive Financial & Liability Summary")
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        with st.container(border=True):
            st.metric(
                label="Official Verdict",
                value=format_short_verdict(audit["overall_status"]),
                delta="Red-Lane Hold" if audit["container_detention_risk"] else "Green-Lane Ready",
                delta_color="inverse" if audit["container_detention_risk"] else "normal",
            )
    with row1_col2:
        with st.container(border=True):
            st.metric(
                label="Total Duty Shortfall",
                value=f"${audit['total_duty_shortfall_usd']:,.2f}",
                delta="Underpayment Fine Risk" if audit["total_duty_shortfall_usd"] > 0 else "Zero Shortfall",
                delta_color="inverse" if audit["total_duty_shortfall_usd"] > 0 else "off",
            )
    with row1_col3:
        with st.container(border=True):
            restitution_val = float(audit.get("total_restitution_usd") or 0.0)
            st.metric(
                label="Duty Restitution Recovery",
                value=f"${restitution_val:,.2f}",
                delta="Refund Eligible" if restitution_val > 0 else "No Overpayment",
                delta_color="normal" if restitution_val > 0 else "off",
            )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        with st.container(border=True):
            st.metric(
                label="CMA CGM Daily Burn Rate",
                value=f"${audit['estimated_demurrage_per_day_usd']:,.2f} / day",
                delta=dem["applicable_slab"],
                delta_color="off",
            )
    with row2_col2:
        with st.container(border=True):
            st.metric(
                label=f"Projected Hold Liability ({dem['days_projected']} Days)",
                value=f"${dem['projected_cumulative_liability_usd']:,.2f}",
                delta=f"{dem['detention_days']} Billable Detention Days ({dem['free_days_allowed']}d Free)",
                delta_color="inverse" if dem["projected_cumulative_liability_usd"] > 0 else "off",
            )

    with st.container(border=True):
        st.markdown("**:material/policy: Executive Synthesis & Discrepancy Alerts**")
        st.markdown(escape_md_dollars(resp_data.get("executive_narrative", "")))
        if audit.get("critical_notes"):
            st.markdown("**Critical Compliance & Regulatory Notes:**")
            for note in audit["critical_notes"]:
                st.markdown(f"- {escape_md_dollars(note)}")
        st.caption(
            f"Dossier Path: `{resp_data.get('report_path', '')}` | "
            f"SMTP Alert: `{resp_data.get('alert_status', '')}`"
        )

    with st.container(border=True):
        st.markdown("**:material/table_chart: Itemized HS-6 & Lartas Permit Comparison**")
        findings_rows = []
        for f_item in audit.get("findings", []):
            findings_rows.append(
                {
                    "ID": f_item["item_id"],
                    "Commodity Description": f_item["declared_description"],
                    "Declared HS": f_item["declared_hs"],
                    "Official HS": f_item["matched_hs"],
                    "Declared Duty": f"{f_item['declared_duty']:.1f}%",
                    "Official Duty": f"{f_item['official_duty']:.1f}%",
                    "Shortfall": f_item["duty_shortfall_usd"],
                    "Restitution": f_item.get("restitution_usd", 0.0),
                    "Restricted": "YES" if f_item["restricted"] else "NO",
                    "Mandatory Permits": ", ".join(
                        f_item.get("required_permits") or []
                    )
                    or "None",
                }
            )
        st.dataframe(
            findings_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Shortfall": st.column_config.NumberColumn(format="$%.2f"),
                "Restitution": st.column_config.NumberColumn(format="$%.2f"),
            },
        )


def page_demurrage_matrix() -> None:
    ensure_session_defaults()
    st.title("CMA CGM Progressive Demurrage Matrix")
    st.write(
        "Official CMA CGM Indonesia Merged Import Demurrage & Detention Tariff Schedule "
        "(Effective July 1, 2026) evaluated for the active shipment."
    )

    resp_data = st.session_state.get("last_audit_response")
    if not resp_data or "audit" not in resp_data:
        with st.container(border=True):
            st.markdown("**:material/info: No Active Audit**")
            st.write(
                "No shipment has been audited yet. Please go to the **Audit Workspace** "
                "and click **Run Autonomous Compliance Audit** to calculate demurrage liabilities."
            )
        return

    audit = resp_data["audit"]
    dem = audit["demurrage_assessment"]

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**:material/directions_boat: Active Equipment Profile**")
            st.markdown(f"- **Shipment ID**: `{audit['shipment_id']}`")
            st.markdown(f"- **Carrier Benchmark**: {dem['benchmark_carrier']}")
            st.markdown(
                f"- **Equipment**: `{audit['container_count']}x {dem['container_size']} {dem['container_type']}`"
            )
            st.markdown(f"- **Free Time Allowed**: `{dem['free_days_allowed']} Days`")
    with col2:
        with st.container(border=True):
            st.markdown("**:material/payments: Detention Exposure**")
            st.markdown(
                f"- **Detention Risk**: `{'ACTIVE' if audit['container_detention_risk'] else 'NONE'}`"
            )
            st.markdown(
                f"- **Active Tier**: {escape_md_dollars(dem['applicable_slab'])}"
            )
            st.markdown(
                f"- **Fleet Burn Rate**: `${audit['estimated_demurrage_per_day_usd']:,.2f} USD/day`"
            )
            st.markdown(
                f"- **Cumulative Hold ({dem['days_projected']}d)**: `${dem['projected_cumulative_liability_usd']:,.2f} USD`"
            )

    with st.container(border=True):
        st.markdown("**:material/view_timeline: Day-Slab Liability Breakdown**")
        slab_rows = build_cma_cgm_slab_breakdown_rows(
            container_count=int(audit["container_count"]),
            container_size=dem["container_size"],
            container_type=dem["container_type"],
            days_projected=int(dem["days_projected"]),
            detention_risk=bool(audit["container_detention_risk"]),
        )
        st.dataframe(
            slab_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rate / Cntr / Day": st.column_config.NumberColumn(format="$%.2f"),
                "Fleet Burn / Day": st.column_config.NumberColumn(format="$%.2f"),
                "Tier Subtotal": st.column_config.NumberColumn(format="$%.2f"),
            },
        )


def page_dossier_archive() -> None:
    st.title("Evidentiary Dossier Archive")
    st.write(
        "Browse timestamped compliance dossiers stored in `./data/reports` and export official Markdown or JSON evidence packages."
    )

    reports_list = fetch_reports_archive()
    if not reports_list:
        st.info(
            "No archived compliance dossiers found yet. Run an audit in the Audit Workspace to generate a dossier."
        )
        return

    summary_rows = [
        {
            "Date": r["date"],
            "Shipment ID": r["shipment_id"],
            "Importer": r["importer"],
            "Verdict": format_short_verdict(r["overall_status"]),
            "Cntr": r.get("container_count", 1),
            "Shortfall": r.get("total_duty_shortfall_usd", 0.0),
            "Restitution": r.get("total_restitution_usd", 0.0),
            "Burn / Day": r.get("estimated_demurrage_per_day_usd", 0.0),
        }
        for r in reports_list
    ]
    with st.container(border=True):
        st.markdown("**:material/history: Archived Shipment Audits**")
        st.dataframe(
            summary_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Shortfall": st.column_config.NumberColumn(format="$%.2f"),
                "Restitution": st.column_config.NumberColumn(format="$%.2f"),
                "Burn / Day": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

    options_map = {
        f"{r['date']} | {r['shipment_id']} ({format_short_verdict(r['overall_status'])})": r
        for r in reports_list
    }
    selected_key = st.selectbox(
        "Select Archived Dossier to Inspect & Export",
        options=list(options_map.keys()),
    )
    if selected_key:
        selected_report = options_map[selected_key]
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label=f"Download Markdown ({selected_report['shipment_id']}.md)",
                data=selected_report["markdown_content"],
                file_name=f"{selected_report['shipment_id']}_audit_report.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                label=f"Download JSON ({selected_report['shipment_id']}.json)",
                data=selected_report["json_content"],
                file_name=f"{selected_report['shipment_id']}_audit_report.json",
                mime="application/json",
                use_container_width=True,
            )

        with st.container(border=True):
            render_responsive_markdown(selected_report["markdown_content"])


def page_bob_assistant() -> None:
    st.title("IBM Bob Regulatory Q&A Assistant")
    st.write(
        "Stateless one-shot trade compliance assistant powered by the bounded IBM Bob CLI worker pool "
        "(240s hard timeout with local HS-6 RAG & CMA CGM fallback)."
    )

    preset_questions = {
        "HS 8517.11 Smartphone Permits": "What mandatory permits and duty rates apply to cellular smartphones under HS 8517.11?",
        "HS 9018.12 Medical Scanners": "What Lartas license is required for medical ultrasonic diagnostic scanners (HS 9018.12)?",
        "CMA CGM July 2026 Slabs": "Explain the CMA CGM Indonesia July 1, 2026 progressive demurrage slabs for Dry and Reefer containers.",
    }

    with st.container(border=True):
        st.markdown("**:material/help: Regulatory Query Console**")
        chosen_q_pill = st.pills(
            "Quick Regulatory Topics",
            options=list(preset_questions.keys()),
            label_visibility="collapsed",
        )
        if chosen_q_pill and chosen_q_pill != st.session_state.get("last_q_pill"):
            st.session_state["last_q_pill"] = chosen_q_pill
            st.session_state["assistant_prompt_input"] = preset_questions[chosen_q_pill]

        prompt_val = st.text_area(
            "Ask a trade compliance, HS-6 classification, Lartas permit, or CMA CGM demurrage question:",
            value=st.session_state.get(
                "assistant_prompt_input",
                preset_questions["HS 8517.11 Smartphone Permits"],
            ),
            height=100,
        )
        ask_btn = st.button(
            "Submit Regulatory Query",
            type="primary",
            use_container_width=True,
        )

    clean_prompt = str(prompt_val or "").strip()
    if ask_btn and clean_prompt:
        with st.status(
            "Dispatching stateless one-shot query to compliance assistant...",
            expanded=True,
        ) as assistant_status:
            ans = execute_assistant_request(
                clean_prompt,
                timeout_seconds=DEFAULT_ASSISTANT_TIMEOUT,
            )
            st.session_state["last_assistant_response"] = ans
            assistant_status.update(
                label=f"Completed via {ans['engine']} ({ans['status'].upper()} in {ans['duration_ms']} ms)",
                state="complete",
            )

    if "last_assistant_response" in st.session_state:
        ans = st.session_state["last_assistant_response"]
        with st.container(border=True):
            st.caption(
                f"Channel: `{ans['engine']}` | Status: `{ans['status']}` | "
                f"Timeout Limit: `{DEFAULT_ASSISTANT_TIMEOUT}s` | Latency: `{ans['duration_ms']} ms`"
            )
            render_responsive_markdown(ans["answer"])


def render_app() -> None:
    current_dir = Path(__file__).parent
    icon_path = current_dir / "icon.png"

    st.set_page_config(
        page_title="CustomsGuard | Autonomous Trade Compliance",
        page_icon=str(icon_path),
        layout="centered",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap');

        /* Apply DM Sans globally across all text and application containers */
        html, body, [class*="css"], .stApp {
            font-family: 'DM Sans', sans-serif;
        }

        /* Protect all Material Symbols icons across status containers, markdown, and navigation */
        span[data-testid*="Icon"],
        span[data-testid*="stIcon"],
        span[data-testid*="stExpanderIcon"],
        [data-testid*="Icon"],
        [class*="material-symbols"],
        [class*="material-icons"],
        span[translate="no"] {
            font-family: "Material Symbols Rounded" !important;
            font-feature-settings: 'liga' !important;
            -webkit-font-feature-settings: 'liga' !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    ensure_session_defaults()

    nav = st.navigation(
        [
            st.Page(
                page_audit_workspace,
                title="Audit Workspace",
                icon=":material/fact_check:",
                default=True,
            ),
            st.Page(
                page_demurrage_matrix,
                title="Demurrage Matrix",
                icon=":material/monitoring:",
            ),
            st.Page(
                page_dossier_archive,
                title="Dossier Archive",
                icon=":material/folder_open:",
            ),
            st.Page(
                page_bob_assistant,
                title="Bob Assistant",
                icon=":material/smart_toy:",
            ),
        ]
    )

    with st.sidebar:
        health = fetch_health()
        resp_data = st.session_state.get("last_audit_response")
        active_inv = st.session_state.get("active_invoice", {})
        if resp_data and "audit" in resp_data:
            active_audit = resp_data["audit"]
            active_shp = active_audit.get("shipment_id", "SHP-2026-0042")
            active_status = format_short_verdict(
                active_audit.get("overall_status", "PENDING AUDIT")
            )
        else:
            active_shp = str(active_inv.get("shipment_id", "SHP-2026-0042"))
            active_status = "PENDING AUDIT"

        with st.container(border=True):
            st.markdown("**:material/shield: CustomsGuard**")
            st.caption(
                f"Manifest: `{active_shp}`  \n"
                f"Status: `{active_status}`"
            )
            q_ok = health.get("qdrant", {}).get("reachable", False)
            m_ok = health.get("mailpit", {}).get("reachable", False)
            l_ok = health.get("langflow", {}).get("reachable", False)
            st.caption(
                f"Qdrant: `{'ON' if q_ok else 'SEED'}`  \n"
                f"Mailpit: `{'ON' if m_ok else 'OFF'}`  \n"
                f"Langflow: `{'ON' if l_ok else 'OFF'}`"
            )
        st.caption(
            "API: [localhost:8000/docs](http://localhost:8000/docs)  \n"
            "Mailpit: [localhost:8025](http://localhost:8025)"
        )

    nav.run()


if __name__ == "__main__":
    render_app()
