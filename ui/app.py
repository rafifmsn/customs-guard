"""CustomsGuard v2 Native Streamlit Compliance Dashboard.

Zero custom CSS injection. Configured declaratively via .streamlit/config.toml.
Communicates with the centralized FastAPI backend over HTTP with dual-network
hostname resolution (customsguard-api:8000 -> localhost:8000 -> direct fallback).
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

import streamlit as st

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from api.main import ask_assistant, health_check, list_reports, run_audit
from api.schemas import AssistantQuery, InvoicePayload
from scripts.customs_components import CMA_CGM_TARIFFS

SAMPLE_INVOICES_PATH = os.path.join(ROOT_DIR, "data", "seed", "sample_invoices.json")

API_CANDIDATE_URLS = [
    os.environ.get("CUSTOMSGUARD_API_URL", "").rstrip("/"),
    "http://customsguard-api:8000",
    "http://localhost:8000",
]
API_CANDIDATE_URLS = [u for u in API_CANDIDATE_URLS if u]


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


def execute_assistant_request(prompt: str, timeout_seconds: int) -> Dict[str, Any]:
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
            ("Days 1 to 5 (Free Time)", 1, 5, 0.0),
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
            ("Days 1 to 3 (Free Time)", 1, 3, 0.0),
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
                "CMA CGM Tariff Tier": label,
                "Equipment": f"{container_count}x {norm_size}ft {norm_type.capitalize()}",
                "Rate / Container / Day (USD)": rate_per_cntr,
                "Consignment Burn Rate / Day (USD)": fleet_daily_rate,
                "Active Days in Slab": days_in_slab,
                "Tier Liability Subtotal (USD)": slab_subtotal,
            }
        )
    return rows


def render_app() -> None:
    st.set_page_config(
        page_title="CustomsGuard v2 | Autonomous Trade Compliance",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    samples = load_sample_invoices()
    if "active_invoice" not in st.session_state:
        st.session_state["active_invoice"] = (
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

    with st.sidebar:
        st.title("CustomsGuard v2")
        st.caption(
            "Autonomous Indonesian Trade Compliance, HS-6 Tariff RAG & CMA CGM Demurrage Engine"
        )
        st.divider()

        st.subheader("System Telemetry")
        health = fetch_health()
        with st.container(border=True):
            st.markdown(f"**Overall Status**: `{health.get('status', 'unknown').upper()}`")
            q_ok = health.get("qdrant", {}).get("reachable", False)
            m_ok = health.get("mailpit", {}).get("reachable", False)
            l_ok = health.get("langflow", {}).get("reachable", False)
            st.markdown(f"- **Qdrant (5,612 HS-6)**: `{'ONLINE' if q_ok else 'LOCAL SEED'}`")
            st.markdown(f"- **Mailpit SMTP (:1025)**: `{'ONLINE' if m_ok else 'STANDBY'}`")
            st.markdown(f"- **Langflow Engine (:7860)**: `{'ONLINE' if l_ok else 'STANDBY'}`")

        st.divider()
        st.subheader("Quick Reference")
        st.markdown(
            "- **Tariff Schedule**: WTO/UNCTAD ITC MAcMap Indonesia (5,612 HS-6 codes)\n"
            "- **Lartas Agencies**: SDPPI (Kemkominfo), Kemenkes RI, BPOM\n"
            "- **Demurrage Benchmark**: CMA CGM Indonesia Merged Import D&D (Effective July 1, 2026)\n"
            "- **Swagger API Docs**: `http://localhost:8000/docs`\n"
            "- **Mailpit Web Inbox**: `http://localhost:8025`"
        )

    st.header("CustomsGuard Autonomous Compliance & Tariff Discrepancy Workspace")
    st.caption(
        "Air-gapped commercial invoice verification against 5,612 Indonesian HS-6 subheadings, "
        "Lartas ministry permit schedules, and CMA CGM Indonesia progressive detention slabs."
    )

    tab_audit, tab_archive, tab_assistant = st.tabs(
        [
            "1. Invoice Audit & Liability Breakdown",
            "2. Evidentiary Dossier Archive & Downloads",
            "3. IBM Bob Regulatory Q&A Assistant",
        ]
    )

    with tab_audit:
        with st.container(border=True):
            st.subheader("Canonical Scenario Presets")
            st.caption(
                "Load one of the 4 benchmark trade compliance scenarios or upload a custom commercial invoice JSON below."
            )
            preset_cols = st.columns(4)
            preset_labels = [
                ("Scenario 1: Red-Lane Hold (SDPPI)", 0),
                ("Scenario 2: Multi-Cntr Demurrage", 1),
                ("Scenario 3: Duty Restitution (15%->0%)", 2),
                ("Scenario 4: Compliant Green Lane", 3),
            ]
            for col, (label, idx) in zip(preset_cols, preset_labels):
                with col:
                    if st.button(label, use_container_width=True, key=f"preset_btn_{idx}"):
                        if idx < len(samples):
                            st.session_state["active_invoice"] = json.loads(
                                json.dumps(samples[idx])
                            )
                            st.session_state.pop("last_audit_response", None)
                            st.rerun()

            uploaded_file = st.file_uploader(
                "Or upload a commercial invoice manifest (.json)",
                type=["json"],
            )
            if uploaded_file is not None:
                try:
                    uploaded_data = json.load(uploaded_file)
                    if isinstance(uploaded_data, list) and uploaded_data:
                        uploaded_data = uploaded_data[0]
                    if isinstance(uploaded_data, dict):
                        st.session_state["active_invoice"] = uploaded_data
                except Exception as exc:
                    st.error(f"Invalid JSON file: {exc}")

        inv = st.session_state["active_invoice"]

        with st.container(border=True):
            st.subheader("Commercial Invoice & Container Parameters")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                shipment_id = st.text_input(
                    "Shipment ID",
                    value=str(inv.get("shipment_id", "SHP-2026-0042")),
                )
                importer_name = st.text_input(
                    "Importer Name",
                    value=str(inv.get("importer_name", "PT Nexus Indo Tech")),
                )
            with c2:
                carrier = st.text_input(
                    "Ocean Carrier",
                    value=str(inv.get("carrier", "CMA CGM")),
                )
                destination_port = st.text_input(
                    "Destination Port",
                    value=str(inv.get("destination_port", "Tanjung Priok, Jakarta (IDTPP)")),
                )
            with c3:
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
            with c4:
                type_options = ["DRY", "REEFER"]
                default_type = (
                    "REEFER"
                    if "REEF" in str(inv.get("container_type") or "DRY").upper()
                    else "DRY"
                )
                type_idx = type_options.index(default_type)
                container_type = st.selectbox(
                    "Equipment Type",
                    options=type_options,
                    index=type_idx,
                )
                days_held_projected = st.slider(
                    "Projected Port Hold Duration (Days)",
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
                    "item_id": st.column_config.NumberColumn("Item ID", min_value=1, step=1),
                    "declared_description": st.column_config.TextColumn(
                        "Declared Commodity Description", width="large"
                    ),
                    "declared_hs_code": st.column_config.TextColumn("Declared HS-6 Code"),
                    "quantity": st.column_config.NumberColumn("Qty", min_value=1),
                    "unit_price": st.column_config.NumberColumn(
                        "Unit Price (USD)", format="$%.2f"
                    ),
                    "total_value": st.column_config.NumberColumn(
                        "Total Value (USD)", format="$%.2f"
                    ),
                    "declared_duty_rate": st.column_config.NumberColumn(
                        "Declared Duty (%)", format="%.1f%%"
                    ),
                },
                key="invoice_items_editor",
            )

            run_btn = st.button(
                "Run Autonomous Compliance Audit",
                type="primary",
                use_container_width=True,
            )

        if run_btn or "last_audit_response" not in st.session_state:
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
            with st.status("Executing deterministic HS-6 RAG & CMA CGM demurrage audit...", expanded=False) as status_box:
                audit_resp = execute_audit_request(payload_to_run)
                st.session_state["last_audit_response"] = audit_resp
                status_box.update(
                    label=f"Audit Complete: {audit_resp['audit']['shipment_id']} ({audit_resp['audit']['overall_status']})",
                    state="complete",
                )

        if "last_audit_response" in st.session_state:
            resp_data = st.session_state["last_audit_response"]
            audit = resp_data["audit"]
            dem = audit["demurrage_assessment"]

            st.subheader("Executive Financial & Liability Summary")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                with st.container(border=True):
                    st.metric(
                        label="Official Verdict",
                        value=audit["overall_status"],
                        delta="Detention Risk" if audit["container_detention_risk"] else "Clearance Ready",
                        delta_color="inverse" if audit["container_detention_risk"] else "normal",
                    )
            with m2:
                with st.container(border=True):
                    st.metric(
                        label="Total Duty Shortfall",
                        value=f"${audit['total_duty_shortfall_usd']:,.2f}",
                        delta="Underpayment Liability" if audit["total_duty_shortfall_usd"] > 0 else "Zero Shortfall",
                        delta_color="inverse" if audit["total_duty_shortfall_usd"] > 0 else "off",
                    )
            with m3:
                with st.container(border=True):
                    restitution_val = float(audit.get("total_restitution_usd") or 0.0)
                    st.metric(
                        label="Duty Restitution Recovery",
                        value=f"${restitution_val:,.2f}",
                        delta="Refund Eligible" if restitution_val > 0 else "No Overpayment",
                        delta_color="normal" if restitution_val > 0 else "off",
                    )
            with m4:
                with st.container(border=True):
                    st.metric(
                        label="CMA CGM Daily Burn Rate",
                        value=f"${audit['estimated_demurrage_per_day_usd']:,.2f}/day",
                        delta=dem["applicable_slab"],
                        delta_color="off",
                    )
            with m5:
                with st.container(border=True):
                    st.metric(
                        label=f"Projected Hold ({dem['days_projected']}d)",
                        value=f"${dem['projected_cumulative_liability_usd']:,.2f}",
                        delta=f"{dem['detention_days']} Billable Detention Days",
                        delta_color="inverse" if dem["projected_cumulative_liability_usd"] > 0 else "off",
                    )

            with st.container(border=True):
                st.subheader("Executive Synthesis & Discrepancy Alerts")
                st.markdown(resp_data.get("executive_narrative", ""))
                if audit.get("critical_notes"):
                    st.markdown("**Critical Compliance & Regulatory Notes:**")
                    for note in audit["critical_notes"]:
                        st.markdown(f"- {note}")
                st.caption(
                    f"Evidentiary Dossier Path: `{resp_data.get('report_path', '')}` | "
                    f"SMTP Notification: `{resp_data.get('alert_status', '')}`"
                )

            col_findings, col_demurrage = st.columns([3, 2])
            with col_findings:
                with st.container(border=True):
                    st.subheader("Itemized HS-6 & Lartas Permit Audit")
                    findings_rows = []
                    for f_item in audit.get("findings", []):
                        findings_rows.append(
                            {
                                "Item": f_item["item_id"],
                                "Commodity Description": f_item["declared_description"],
                                "Declared HS": f_item["declared_hs"],
                                "Official HS": f_item["matched_hs"],
                                "Declared Duty": f"{f_item['declared_duty']:.1f}%",
                                "Official Duty": f"{f_item['official_duty']:.1f}%",
                                "Shortfall (USD)": f_item["duty_shortfall_usd"],
                                "Restitution (USD)": f_item.get("restitution_usd", 0.0),
                                "Lartas Restricted": "YES" if f_item["restricted"] else "NO",
                                "Mandatory Ministry Permits": ", ".join(
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
                            "Shortfall (USD)": st.column_config.NumberColumn(format="$%.2f"),
                            "Restitution (USD)": st.column_config.NumberColumn(format="$%.2f"),
                        },
                    )

            with col_demurrage:
                with st.container(border=True):
                    st.subheader("CMA CGM Progressive Day-Slab Schedule")
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
                            "Rate / Container / Day (USD)": st.column_config.NumberColumn(
                                format="$%.2f"
                            ),
                            "Consignment Burn Rate / Day (USD)": st.column_config.NumberColumn(
                                format="$%.2f"
                            ),
                            "Tier Liability Subtotal (USD)": st.column_config.NumberColumn(
                                format="$%.2f"
                            ),
                        },
                    )

    with tab_archive:
        st.subheader("Evidentiary Audit Dossier Archive")
        st.caption(
            "Browse timestamped compliance dossiers stored in ./data/reports and download official Markdown or JSON evidence packages."
        )
        reports_list = fetch_reports_archive()
        if not reports_list:
            st.info("No archived compliance dossiers found yet. Run an audit in Tab 1 to generate a dossier.")
        else:
            summary_rows = [
                {
                    "Date": r["date"],
                    "Shipment ID": r["shipment_id"],
                    "Importer": r["importer"],
                    "Verdict": r["overall_status"],
                    "Containers": r.get("container_count", 1),
                    "Duty Shortfall (USD)": r.get("total_duty_shortfall_usd", 0.0),
                    "Restitution (USD)": r.get("total_restitution_usd", 0.0),
                    "Daily Demurrage (USD)": r.get("estimated_demurrage_per_day_usd", 0.0),
                }
                for r in reports_list
            ]
            with st.container(border=True):
                st.dataframe(
                    summary_rows,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Duty Shortfall (USD)": st.column_config.NumberColumn(format="$%.2f"),
                        "Restitution (USD)": st.column_config.NumberColumn(format="$%.2f"),
                        "Daily Demurrage (USD)": st.column_config.NumberColumn(format="$%.2f"),
                    },
                )

            options_map = {
                f"{r['date']} | {r['shipment_id']} ({r['overall_status']})": r
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
                        label=f"Download Markdown Dossier ({selected_report['shipment_id']}.md)",
                        data=selected_report["markdown_content"],
                        file_name=f"{selected_report['shipment_id']}_audit_report.md",
                        mime="text/markdown",
                        type="primary",
                        use_container_width=True,
                    )
                with dl_col2:
                    st.download_button(
                        label=f"Download Machine-Readable Payload ({selected_report['shipment_id']}.json)",
                        data=selected_report["json_content"],
                        file_name=f"{selected_report['shipment_id']}_audit_report.json",
                        mime="application/json",
                        use_container_width=True,
                    )

                with st.container(border=True):
                    st.markdown(selected_report["markdown_content"])

    with tab_assistant:
        st.subheader("IBM Bob Trade Compliance & Tariff Q&A Assistant")
        st.caption(
            "Stateless one-shot regulatory assistant powered by bounded IBM Bob CLI subprocess pool (with local HS-6 RAG & CMA CGM fallback)."
        )

        with st.container(border=True):
            st.markdown("**Quick Regulatory Queries**")
            q_cols = st.columns(3)
            preset_questions = [
                "What mandatory permits and duty rates apply to cellular smartphones under HS 8517.11?",
                "What Lartas license is required for medical ultrasonic diagnostic scanners (HS 9018.12)?",
                "Explain the CMA CGM Indonesia July 1, 2026 progressive demurrage slabs for Dry and Reefer containers.",
            ]
            for idx, (q_col, q_text) in enumerate(zip(q_cols, preset_questions)):
                with q_col:
                    if st.button(q_text, key=f"bob_q_{idx}", use_container_width=True):
                        st.session_state["assistant_prompt_input"] = q_text

            prompt_val = st.text_area(
                "Ask a trade compliance, HS-6 classification, Lartas permit, or CMA CGM demurrage question:",
                value=st.session_state.get(
                    "assistant_prompt_input",
                    "What mandatory permits and duty rates apply to cellular smartphones under HS 8517.11?",
                ),
                height=100,
            )
            timeout_val = st.slider(
                "Subprocess Execution Timeout (Seconds)",
                min_value=30,
                max_value=300,
                value=240,
                step=30,
            )
            ask_btn = st.button(
                "Submit Regulatory Query",
                type="primary",
                use_container_width=True,
            )

        if ask_btn and prompt_val.strip():
            with st.status(
                "Dispatching stateless one-shot query to compliance assistant...",
                expanded=True,
            ) as assistant_status:
                ans = execute_assistant_request(prompt_val.strip(), int(timeout_val))
                st.session_state["last_assistant_response"] = ans
                assistant_status.update(
                    label=f"Completed via {ans['engine']} ({ans['status'].upper()} in {ans['duration_ms']} ms)",
                    state="complete",
                )

        if "last_assistant_response" in st.session_state:
            ans = st.session_state["last_assistant_response"]
            with st.container(border=True):
                st.caption(
                    f"Channel: `{ans['engine']}` | Status: `{ans['status']}` | Latency: `{ans['duration_ms']} ms`"
                )
                st.markdown(ans["answer"])


if __name__ == "__main__":
    render_app()
