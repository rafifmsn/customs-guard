# CustomsGuard v2: Architecture & Implementation Specification

## 1. Executive Context & Philosophy

CustomsGuard is an air-gapped, on-premise trade compliance and customs tariff discrepancy engine for Indonesian cross-border imports.
It audits commercial shipping invoices against 5,612 Indonesian 6-digit Harmonized System (HS) subheadings sourced from the WTO/UNCTAD ITC Market Access Map (MAcMap) dataset stored in Qdrant, verifies mandatory ministry import permits (Lartas: SDPPI, Kemenkes, BPOM), models container detention exposure using the official CMA CGM Indonesia tariff schedule, identifies duty restitution opportunities, archives evidentiary dossiers, and dispatches SMTP alerts via Mailpit.

The core engineering philosophy for v2 is **clean, deterministic, and zero-bloat**.
Every architectural choice prioritizes maintainability, predictable execution, and strict separation between deterministic math and probabilistic LLM synthesis.

### Legacy Preservation Mandate
Do not delete or break the existing setup.
The legacy workflow where IBM Bob Desktop or CLI connects directly to Langflow via Model Context Protocol (`.bob/mcp.json`) and invokes the `$audit-shipment` skill must remain 100% functional.
All existing unit and integration tests in `tests/`, seed data in `data/seed/`, and benchmark scenarios in `scenarios/` must be preserved.
The new web application and centralized API layer operate alongside the legacy setup as the primary production interface.

---

## 2. Repository Directory Map

The repository has been consolidated into a clean, non-fragmented structure so you do not need to hunt for files:

- `AGENTS.md`: Persona rules, compliance reporting structure, and confidentiality standards.
- `docker-compose.yml`: Local multi-container orchestration for Postgres, Qdrant, Mailpit, Langflow, FastAPI, and Streamlit.
- `scripts/`:
  - `customs_components.py`: Core Langflow custom toolkit (`CustomsGuardToolkitComponent`) containing deterministic tariff RAG, CMA CGM demurrage math, dossier export, and Mailpit SMTP dispatch.
  - `seed_qdrant.py`: Indexes the 5,612 HS-6 records from `data/seed/tariff_database.json` into Qdrant.
  - `parse_macmap.py`: Parses `docs/domain/macmap.xlsx` into the JSON seed database.
- `data/`:
  - `seed/sample_invoices.json`: 4 canonical test shipment manifests covering high-risk holds, multi-container demurrage, duty restitution, and compliant clearance.
  - `seed/tariff_database.json`: Full 5,612 Indonesian HS-6 tariff schedule and Lartas rules.
  - `reports/`: Shared volume (`./data/reports/YYYY-MM-DD/{shipment_id}/`) storing generated `.json` and `.md` audit dossiers.
- `scenarios/`:
  - `prompts/`: Modular test prompts (`01` to `04`) and `system_agent_instruction.md` (the Langflow Agent system prompt).
  - `expected-outputs/`: Ground-truth reference Markdown dossiers (`01` to `04`) showing the exact target format for human-readable reports.
- `docs/`:
  - `domain/`: Domain problem analysis (`problem_solution.md`), commercial ROI model (`business_canvas.md`), and source dataset (`macmap.xlsx`).
  - `technical/`: Current topology (`architecture.md`), engineering trade-offs (`design_decisions.md`), and MCP guide (`mcp_setup.md`).
  - `submission/`: Hackathon submission documentation and visual evidence.
- `tests/`: Automated `pytest` suite validating tariff database integrity, audit arithmetic, report exporting, SMTP alerts, and end-to-end execution.
- `v2/`: Next-generation implementation specs (`implementation-final.md`) and native Streamlit theming reference (`streamlit-theme.md`).

---

## 3. Target System Topology (Split-Channel Architecture)

While the legacy MCP integration works well for interactive desktop sessions, wrapping the IBM Bob CLI (`bob run`) as the primary engine for standard invoice auditing introduces subshell overhead and conversational latency (~44s E2E).
In v2, we decouple the system into a split-channel architecture:

1. **Centralized Backend Controller (`customsguard-api` on `:8000`)**:
   A lightweight FastAPI service that centralizes all execution logic, deterministic compliance checks, Langflow REST invocations, dossier file serving, and bounded IBM Bob CLI subprocess management.
2. **Primary Compliance Dashboard (`customsguard-ui` on `:8501`)**:
   A pure Streamlit frontend client that communicates strictly with the FastAPI backend over HTTP, rendering deterministic JSON metrics and tables without blocking UI re-runs.
3. **Ad-Hoc AI Assistant Channel (`bob-worker` inside FastAPI)**:
   Retains IBM Bob CLI strictly as a stateless, one-shot regulatory Q&A assistant executed inside a bounded asynchronous subprocess pool with hard timeouts and process group cleanup.
4. **Public Marketing & Interactive Demo (`web-landing/`)**:
   A standalone Next.js Static Site Generation (`output: 'export'`) single-page application designed for public web hosting with zero runtime dependency on the local Docker backend.

### Local Docker Services Matrix

| Service Name | Tech Stack | Exposed Ports | Core Responsibility |
| :--- | :--- | :--- | :--- |
| `customsguard-ui` | Python 3.11, Streamlit | `:8501` | Executive compliance dashboard, audit workspace, dossier downloads, Bob Q&A tab |
| `customsguard-api` | Python 3.11, FastAPI, Asyncio | `:8000` | Centralized REST controller, deterministic audit orchestration, bounded Bob CLI pool |
| `langflow` | Langflow Engine | `:7860` | Hosts Pipeline A (Core Audit REST + legacy MCP) and Pipeline B (Assistant MCP) |
| `qdrant` | Qdrant Vector DB | `:6333`, `:6334` | Stores 5,612 Indonesian HS-6 subheading vectors and Lartas metadata |
| `mailpit` | Mock SMTP & Web UI | `:1025`, `:8025` | Captures real-time detention alert emails for compliance review |
| `postgres` | PostgreSQL 16 Alpine | `:5432` | Persists Langflow state and workflow definitions |

---

## 4. Core Engine & Output Consistency Upgrades

Before building the new services, address three specific output quality gaps in the existing toolkit (`scripts/customs_components.py`) and agent prompt (`scenarios/prompts/system_agent_instruction.md`):

### 4.1 Upgrade `export_compliance_report` (True Markdown Dossier vs JSON)
- **Current Issue**: `export_compliance_report` writes `audit_report.json`, and then generates `audit_report.md` by simply wrapping the raw JSON string inside a fenced code block.
This makes the Markdown file redundant.
- **Required Fix**: Keep `audit_report.json` as the machine-readable payload for APIs and automated pipelines, and upgrade `audit_report.md` to generate a structured, human-readable executive dossier matching the layout in `scenarios/expected-outputs/01_high_risk_dossier.md`.
- **Target Markdown Structure**:
  - Header with `# CustomsGuard Compliance Audit Report`, `Shipment ID`, `Generated At`, and `Verdict`.
  - `### Executive Summary` bullet list covering Importer, Container Count/Size/Type, Detention Risk, Total Duty Shortfall, Restitution Savings, Carrier Benchmark, Free Time Allowed, Daily Burn Rate, and Projected Hold Liability.
  - `### Critical Discrepancies & Regulatory Violations` listing specific HS mismatches and missing Lartas permits.
  - `### Itemized Audit Findings` formatted as a clean Markdown table (`Item ID`, `Declared Description`, `Declared HS`, `Matched HS`, `Declared Duty`, `Official Duty`, `Shortfall (USD)`, `Restricted`, `Mandatory Permits`).
  - `### Automated Actions Taken` confirming local dossier path and Mailpit alert status.
- **Backward Compatibility**: Ensure all assertions in `tests/test_report_exporter.py` continue to pass (`# CustomsGuard Compliance Audit Report`, `shipment_id`, and `overall_status` present in `audit_report.md`, plus companion `audit_report.json` on disk).

### 4.2 Upgrade `send_compliance_alert` (Deterministic Email Formatting)
- **Current Issue**: `send_compliance_alert(shipment_id, verdict, alert_details)` relies on whatever unstructured text the LLM passes into `alert_details`, causing inconsistent email layouts in Mailpit.
- **Required Fix**: Standardize the email body generator so that whenever `alert_details` is passed (whether as a JSON string, dictionary summary, or raw text), the function formats a clean, structured notification block displaying the Shipment ID, Official Verdict, Container Specifications, Duty Shortfall, CMA CGM Daily Burn Rate, Critical Discrepancy Notes, and Mailpit preview link.
Ensure existing unit tests in `tests/test_alert_system.py` continue to pass.

### 4.3 Standardize Agent Conversational Output & Decouple UI Rendering
- **Current Issue**: In Langflow (`Chat Input -> Agent -> Guardrails -> Chat Output`), the LLM generates freeform text that fluctuates in structure across runs.
- **Dual Fix**:
  1. **Deterministic UI Rendering**: The FastAPI `/api/v1/audit` endpoint and Streamlit dashboard must never rely on regex-parsing the LLM's conversational prose to populate UI metrics or tables.
  Instead, execute or extract the deterministic dictionary from `audit_shipment_compliance` (and saved `audit_report.json`) to render exact numbers, tables, and demurrage tiers in Streamlit, while displaying the Langflow Agent + Guardrails response below as the executive synthesis commentary.
  2. **Few-Shot Prompt Skeleton**: Update `scenarios/prompts/system_agent_instruction.md` (and the corresponding Agent prompt in `langflow/CustomsGuard.json` if updated) to include a concise, explicit Markdown output skeleton so conversational responses in IBM Bob and Langflow remain visually consistent without restricting tool-calling reliability.

---

## 5. Service Specifications

### 5.1 Centralized Backend API (`customsguard-api` in `api/`)
Why FastAPI is used here: Streamlit re-executes its entire script on every user interaction.
Running multi-minute subprocess calls or heavy network orchestration directly inside Streamlit causes UI lockups and cancelled runs when users switch tabs.
FastAPI isolates all state and process management behind clean REST endpoints without adding heavy message brokers like Celery or Redis.

- **Endpoints**:
  - `GET /api/v1/health`: Checks connectivity to Qdrant (`:6333`), Langflow (`:7860`), and Mailpit (`:1025`).
  - `POST /api/v1/audit`:
    - Accepts a commercial invoice JSON payload (matching the schema in `data/seed/sample_invoices.json`).
    - Runs the deterministic compliance audit (`audit_shipment_compliance`), exports the `.json` and `.md` dossiers (`export_compliance_report`), and dispatches the SMTP alert (`send_compliance_alert`) if high-risk or discrepancy status is triggered.
    - Optionally invokes the Langflow Core Audit REST endpoint (`/api/v1/run/{flow_id}`) to obtain the Guardrails-sanitized executive narrative, returning both the deterministic audit object and the executive summary in a unified JSON response.
  - `GET /api/v1/reports`:
    - Scans `./data/reports/` and returns a sorted list of archived shipment audits with metadata and file contents for instant `.md` and `.json` downloads.
  - `POST /api/v1/assistant`:
    - Manages the IBM Bob CLI (`bob run --trust "<prompt>"`) for ad-hoc trade compliance Q&A.
    - **Stateless One-Shot Execution**: Each request is an independent query with no persistent PTY shell or session memory.
    - **Bounded Concurrency Pool**: Use an `asyncio.Semaphore` (max 2 to 3 concurrent processes).
    If full, queue briefly or return a clean busy status.
    - **Hard Timeout & Process Group Cleanup**: Enforce a strict configurable timeout (default **180 to 300 seconds**).
    Spawn the CLI inside its own process group (`start_new_session=True`) so that if a timeout or cancellation occurs, the runner immediately sends `SIGTERM` / `SIGKILL` to the entire process group (`os.killpg`), guaranteeing zero zombie processes or memory leaks.

### 5.2 Enterprise Streamlit Dashboard (`customsguard-ui` in `ui/`)
- **Zero Custom CSS Bloat**:
  Do not inject raw `<style>` blocks or `unsafe_allow_html=True` CSS hacks.
  Consult `v2/streamlit-theme.md` and configure `.streamlit/config.toml` declaratively using `[theme]` options (`primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`, `baseFontSize`, `borderRadius`, `borderColor`, and `[theme.sidebar]`).
- **Zero RBAC or Paywall Bloat**:
  Do not implement user authentication, login gates, RBAC, or artificial feature paywalls.
  The Streamlit dashboard is a 100% unlocked, full-featured compliance workspace.
  Evaluators and compliance officers must have immediate, friction-free access to all 4 scenarios, progressive demurrage calculations, restitution discovery, dossier exports, and the Bob assistant.
- **Native Layout Primitives**:
  Use `st.container(border=True)`, `st.columns`, `st.metric`, `st.status`, `st.tabs`, and `st.dataframe` with column configurations.
- **Core Views**:
  1. **Invoice Audit Workspace**:
     - One-click preset buttons to load the 4 canonical scenarios from `data/seed/sample_invoices.json`, alongside a JSON file uploader (`st.file_uploader(type=["json"])`) and interactive form inputs (`shipment_id`, `importer_name`, `carrier`, `container_count`, `container_size`, `container_type`, `days_held_projected`, and line items).
     - Note on PDF ingestion: Keep v2 strictly focused on JSON and structured form inputs for 100% deterministic reliability; leave OCR/PDF extraction as a documented roadmap item.
  2. **Financial & Demurrage Liability Breakdown**:
     - Renders top-level `st.metric` cards for Overall Verdict, Total Duty Shortfall, Restitution Recovery, Active Daily Burn Rate, and Projected Hold Liability.
     - Displays the itemized HS comparison table (`st.dataframe`) and CMA CGM progressive day-slab breakdown.
  3. **Dossier Archive & Export**:
     - Browse historical audits from `/api/v1/reports`, preview the formatted Markdown report inline, and provide native `st.download_button` controls for both `audit_report.md` and `audit_report.json`.
  4. **Bob Compliance Assistant Tab**:
     - A clean one-shot Q&A input box calling `POST /api/v1/assistant` wrapped in an `st.status` spinner to query HS classifications, Lartas permit triggers, or tariff rules.

### 5.3 Dual Langflow Pipelines (`langflow/`)
- **Pipeline A (Core Audit Pipeline)**:
  Retains `langflow/CustomsGuard.json` compatibility so both direct REST calls (`/api/v1/run/{flow_id}`) and legacy IBM Bob MCP calls (`customsguard` tool) execute seamlessly through the Agent and Guardrails nodes.
- **Pipeline B (Knowledge & Tariff Assistant MCP)**:
  A lightweight secondary flow or tool configuration exposed via MCP (`mcp<2.0.0` via `mcp-proxy` over `streamablehttp`) equipped with Qdrant tariff lookup and demurrage calculator helpers for fast ad-hoc Q&A.

---

## 6. Public Web Production: Next.js SSG Landing Page (`web-landing/`)

Build a standalone **Next.js (App Router, `output: 'export'`)** single-page application with Tailwind CSS inside `web-landing/`.
It must compile to pure static HTML/CSS/JS with zero runtime dependency on the local Docker stack.

### 6.1 Visual Direction & `inspo` MCP Reference (`dub-co`)
- Use the `inspo` MCP server (`get_screen` and `get_design_system` with slug `dub-co`, corresponding to `https://inspomcp.dev/screens/dub-co`) as the primary design reference.
- **Design System Characteristics**:
  - **Aesthetic**: Minimalist, high-craft digital architecture with stark geometric structure, generous whitespace, crisp `1px` subtle borders, and light mode (`#ffffff` background, `#111111` primary text).
  - **Typography**: Geometric sans-serif display and body pairing (`Satoshi` and `Inter`).
  - **Macrostructure (`feature-stack`)**:
    - Top sticky navigation bar with left logo, center anchor links (Problem, Architecture, Interactive Demo, ROI, Docs), and right CTA pills.
    - Centered Hero with high-contrast sentence-case headline, 2-line subhead framing the Indonesian customs compliance bottleneck, and dual pill CTAs ("Try Interactive Demo" filled black pill + "Read Architecture Docs" ghost pill).
    - **Feature Pill Gateway**: 3 distinct accented feature pills bridging the hero text and the main application showcase container below the fold (e.g., *Autonomous Tariff RAG*, *CMA CGM Demurrage Engine*, *Lartas Permit Guard*).
- **Figma Visual Placeholders**:
  The user will design final custom logos, hero PNG/GIF captures, and custom illustrations in Figma later.
  Build clean, well-proportioned, clearly labeled SVG/CSS placeholder frames (with exact aspect ratios and subtle grid/wireframe styling) for the brand logo, hero dashboard showcase, and architecture diagram so custom Figma assets can be swapped in effortlessly.

### 6.2 Page Sections & 1-Click Scenario Explorer
1. **Hero & Feature-Stack Frame**: Headline, CTAs, 3 feature pills, and main dashboard preview container.
2. **Domain Bottleneck & Value Metrics**: Highlight the 5,612 HS-6 subheadings, 9.73% Lartas permit traps (546 restricted codes), 100% to 1,000% statutory underpayment fines, and ~87% infrastructure cost reduction of self-hosted Docker vs cloud SaaS.
3. **Interactive 1-Click Scenario Explorer (No Drag-and-Drop Bloat)**:
   - Do not build fragile client-side PDF drag-and-drop parsers.
   - Instead, provide 4 interactive scenario selector pills corresponding to the ground-truth cases in `data/seed/sample_invoices.json` and `scenarios/expected-outputs/`:
     1. *High-Risk Red Lane Hold (Missing SDPPI Telecom Permit)*
     2. *Multi-Container Demurrage Bleed (CMA CGM Reefers / Dry Slabs)*
     3. *Duty Restitution Discovery (15% Declared vs 0% Official MFN)*
     4. *Compliant Green-Lane Manifest*
   - Include interactive sliders/toggles for container count (1 to 10), container size (`20ft`, `40ft`, `45ft`), equipment type (`Standard Dry`, `Reefer`), and projected hold duration (1 to 25 days) that compute the exact CMA CGM progressive day-slab math client-side in real time.
   - Selecting a scenario immediately renders the structured liability comparison cards, itemized tariff table, formatted Markdown dossier preview, and simulated Mailpit alert preview.
4. **Air-Gapped Security & Architecture Showcase**: Visual breakdown of the local Docker stack (Streamlit, FastAPI, Langflow, Qdrant, Guardrails, Mailpit) ensuring zero sensitive commercial invoice data leaves the enterprise perimeter.
5. **Commercial Pricing Tiers & Payback Calculator**:
   Render the 4 transparent commercial tiers demonstrating business viability:
   - **Starter ($129/mo, ~2.0M IDR, billed annually)**: Up to 250 audits/mo, full 5,612 HS-6 search, Lartas permit verification (SDPPI, Kemenkes, BPOM), automated incident alerts, standard Markdown & JSON exports.
   - **Professional ($499/mo, ~7.8M IDR, billed annually - Most Popular)**: Up to 2,500 audits/mo, CMA CGM progressive demurrage engine, duty restitution analyzer, multi-seat workspace, direct REST API access.
   - **Enterprise On-Premise (Custom, Starting at $1,499/mo, ~23.5M IDR)**: Unlimited audits, air-gapped on-premise Docker appliance, custom vector embeddings & ERP integration, priority regulatory updates, dedicated SLA.
   - **Developer API ($0.75/audit, Pay-as-you-go)**: Standard Model Context Protocol (MCP) & REST API automated compliance screening.

---

## 7. Non-Negotiable Domain & Engineering Invariants

1. **Graceful Input Contract Fallbacks**:
   Never crash on omitted optional invoice fields.
   Preserve the deterministic defaults: `carrier: "CMA CGM"`, `container_count: 1`, `container_size: "40"`, `container_type: "DRY"`, and `days_held_projected: 10`.
2. **CMA CGM Progressive Day-Slab Arithmetic**:
   Preserve the exact July 1, 2026 CMA CGM Indonesia Merged Import Demurrage & Detention Tariff schedule:
   - **Standard Dry (5 Free Days)**:
     - Days 1 to 5: `$0/day`
     - Days 6 to 10: `$66` (20ft), `$101` (40ft), `$141` (45ft)
     - Days 11 to 15: `$86` (20ft), `$121` (40ft), `$171` (45ft)
     - Days 16 to 20: `$96` (20ft), `$151` (40ft), `$181` (45ft)
     - Days 21+: `$106` (20ft), `$161` (40ft), `$191` (45ft)
   - **Reefer (3 Free Days)**:
     - Days 1 to 3: `$0/day`
     - Days 4 to 5: `$89` (20ft), `$141` (40ft)
     - Days 6 to 7: `$126` (20ft), `$176` (40ft)
     - Days 8+: `$130` (20ft), `$180` (40ft)
3. **Dual-Network Hostname Resolution**:
   Maintain automatic connection fallback between internal Docker service hostnames (`qdrant:6333`, `mailpit:1025`, `langflow:7860`, `customsguard-api:8000`) and local host bindings (`localhost`) so both containerized runs and local host `pytest` runs succeed without manual reconfiguration.
4. **Python Environment & Tooling**:
   Use `uv` (`/home/rafif/.local/bin/uv` or `uv run`) for Python dependency management and test execution.

---

## 8. Execution Sequence for the Implementing Agent

### Phase 1: Core Toolkit & Prompt Refinements
1. Inspect `scripts/customs_components.py` and `scenarios/prompts/system_agent_instruction.md`.
2. Upgrade `export_compliance_report` to output the rich human-readable Markdown dossier alongside `audit_report.json`.
3. Upgrade `send_compliance_alert` to format deterministic, structured email bodies.
4. Add the consistent Markdown response template to `scenarios/prompts/system_agent_instruction.md`.
5. Run `uv run pytest` to verify all existing unit tests pass.

### Phase 2: Centralized FastAPI Backend (`api/`)
1. Create the FastAPI application exposing `/api/v1/health`, `/api/v1/audit`, `/api/v1/reports`, and `/api/v1/assistant`.
2. Implement the bounded `asyncio` subprocess pool for IBM Bob CLI with process-group isolation (`start_new_session=True`), 180s to 300s timeout enforcement, and `os.killpg` cleanup.
3. Add comprehensive API tests in `tests/test_api_endpoints.py` validating audit execution, report listing, and subprocess timeout handling.

### Phase 3: Native Streamlit Compliance Dashboard (`ui/`)
1. Configure `.streamlit/config.toml` following `v2/streamlit-theme.md` (zero custom CSS injection).
2. Build the Streamlit dashboard (`ui/app.py`) connecting to the FastAPI backend with views for the Invoice Audit Workspace, Financial & Demurrage Breakdown, Dossier Archive & Downloads, and Bob Compliance Assistant.

### Phase 4: Docker Compose Integration & Verification
1. Register `customsguard-api` and `customsguard-ui` in `docker-compose.yml` with shared volume mounts (`./data/reports`, `./data/seed`, `./scripts`).
2. Verify full test suite passes via `uv run pytest`.

### Phase 5: Next.js Static Landing Page (`web-landing/`)
1. Query the `inspo` MCP server (`get_screen` / `get_design_system` for `dub-co`) to load exact layout composition and design tokens.
2. Scaffold `web-landing/` using Next.js App Router (`output: 'export'`) and Tailwind CSS.
3. Implement the `dub-co` inspired layout with clearly marked Figma asset placeholders and the client-side 1-Click Scenario Explorer with real-time CMA CGM demurrage calculations.
4. Run `npm run build` inside `web-landing/` to verify clean static export generation.

