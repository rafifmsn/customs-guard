# CustomsGuard

[![X / Twitter](https://img.shields.io/badge/Twitter-@rafifmsn-1DA1F2?logo=x&logoColor=white)](https://x.com/rafifmsn)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

**Autonomous Trade Compliance & Tariff Discrepancy Engine**  
_IBM SkillsBuild x Hacktiv8 National Hackathon 2026 (Productivity & Smart Business)_

CustomsGuard is an autonomous enterprise AI agent designed to audit commercial shipping invoices, eliminate port container detentions, detect customs tariff discrepancies, and protect cross-border businesses from regulatory penalties.

<video src="https://github.com/user-attachments/assets/bacb2242-b02d-41cb-ada0-c51904311d83" controls width="100%"></video>

> 🎬 **Demo Walkthrough**: [Click here to view or download the demo video](https://github.com/user-attachments/assets/bacb2242-b02d-41cb-ada0-c51904311d83).

## The Problem & Strategic Context

Manual paperwork and documentation bottlenecks cost the global shipping ecosystem $6.5 billion in direct costs annually while holding back up to $40 billion in cross-border trade.[^mckinsey-trade] While digital trade initiatives target multi-billion-dollar documentation delays, digitizing manifests does not eliminate the operational burden of verifying trade compliance.

In Indonesia, cross-border clearance aligns with the Directorate General of Customs and Excise (DJBC) regulatory framework, evaluated against 5,612 standardized 6-digit Harmonized System (HS) subheadings sourced from the WTO/UNCTAD International Trade Centre (ITC) Market Access Map (MAcMap) dataset.

- **Manual Verification Bottleneck**: Compliance teams spend 2 to 4 hours per manifest manually verifying invoices against dynamic tariff schedules and ministry import restrictions (Lartas).
- **Catastrophic Port Demurrage**: Documentation errors or missing permits trigger customs "Red Lane" holds, incurring steep daily container detention and port storage penalties.
- **Severe Administrative Surcharges**: Indonesian customs regulations impose fines ranging from **100% to 1,000%** on duty underpayments resulting from misdeclaration.[^uu-kepabeanan]
- **Unclaimed Duty Restitution**: Importers frequently overpay duties due to conservative classifications, losing thousands in unrecovered tax refunds.

CustomsGuard transforms this manual routine into a deterministic, sub-5-second audit pipeline that runs entirely on-premise (air-gapped) for maximum commercial confidentiality.

## System Architecture

CustomsGuard operates via a **split-channel architecture** that separates instant deterministic auditing from conversational agent reasoning:

```mermaid
flowchart LR
    subgraph Clients ["Front-End & Client Layer"]
        direction TB
        WEB["Next.js Landing<br/><code>:3000</code>"]
        BOB["IBM Bob CLI / Desktop"]
    end

    subgraph Appliance ["CustomsGuard Container Appliance"]
        direction LR
        ST["streamlit<br/><code>:8501</code><br/>Compliance Workspace"]
        API["fastapi<br/><code>:8000</code><br/>REST Controller"]
        LF["langflow<br/><code>:7860</code><br/>Langflow & MCP"]
        QD["qdrant<br/><code>:6333</code><br/>Tariff Vector DB"]
        MP["mailpit<br/><code>:1025/:8025</code><br/>Mock SMTP & UI"]
        PG["postgres<br/><code>:5432</code><br/>PostgreSQL 16"]

        ST -->|Direct REST| API
        API -->|Vector Lookup| QD
        API -->|Dispatch Alert| MP
        API -.->|Agent Sync| LF
        LF -->|State Sync| PG
        LF -->|Tariff RAG| QD
        LF -->|Email Alerts| MP
    end

    BOB -->|MCP Protocol| LF
    WEB -.->|Live Workspace| ST
```

**Dual Execution Channels**:

1. **Deterministic Operator Channel (Streamlit & FastAPI)**:
   Direct REST calls (`POST /api/v1/audit`) bypass remote LLM inference loops.
   They execute tariff vector lookups, demurrage calculations, Markdown dossier exports, and Mailpit SMTP dispatches deterministically in under 50ms.
2. **Autonomous Agent Channel (IBM Bob & Langflow)**:
   Interactive prompts and Bob MCP requests route to Langflow (`:7860`) where the LLM reasons across multi-turn queries, invokes the toolkit, and generates conversational synthesis.

## Core Capabilities

1. **Autonomous Tariff RAG**: Matches declared item descriptions against 5,612 official Indonesian HS codes in milliseconds.
2. **Regulatory License Verification**: Cross-references mandatory pre-import approvals (SDPPI Kemkominfo, Kemenkes, BPOM).
3. **Grounded Demurrage & Detention Modeling**: Benchmarks container detention liabilities against the official CMA CGM Indonesia published tariff schedule (5 free days, progressive day-slabs, defaulting to 40ft Dry Standard if container size is omitted).
4. **Duty Restitution Discovery**: Detects over-declared duties, proactively identifying tax refund recovery opportunities.
5. **Automated Evidence Archiving**: Generates timestamped Markdown and JSON dossiers in `./data/reports/YYYY-MM-DD/{shipment_id}/`.
6. **Real-Time SMTP Alerting**: Automatically dispatches detention alert emails to compliance officers when high-risk cargo is flagged.

## Quickstart Guide

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.10+ (or [Astral uv](https://docs.astral.sh/uv/))
- IBM Bob Desktop Application

### 2. Start the Docker Services

Clone the repository and launch the container ecosystem:

```bash
docker compose up -d
```

Service endpoints:

- **CustomsGuard Operator Dashboard**: `http://localhost:8501`
- **Next.js Landing Showcase**: `http://localhost:3000`
- **FastAPI Controller & Swagger UI**: `http://localhost:8000/docs`
- **Langflow Canvas & MCP**: `http://localhost:7860`
- **Mailpit Web UI**: `http://localhost:8025`
- **Qdrant REST API**: `http://localhost:6333`
- **PostgreSQL**: `localhost:5432`

### 3. Import Workflow Templates

CustomsGuard includes two pre-configured Langflow pipeline templates in `./langflow/`:

- [`langflow/CustomsGuard.json`](./langflow/CustomsGuard.json): Primary Autonomous Compliance Audit & MCP Tool Flow (6-node topology with CustomsGuard Toolkit and AI Safety Guardrails).
- [`langflow/CustomsGuard Bot.json`](./langflow/CustomsGuard%20Bot.json): Dedicated Regulatory Knowledge Assistant Flow for conversational HS tariff and Lartas inquiries.

On a fresh environment, navigate to `http://localhost:7860`, go to **My Projects** -> **Import**, and upload both JSON flow templates to load the canvases with all agent nodes, custom tools, and guardrails pre-configured.

### 4. Seed the Customs Tariff Database

Index all 5,612 official Indonesian HS codes, duty rates, and permit regulations into Qdrant:

```bash
uv run python scripts/seed_qdrant.py
```

## Running Automated Tests

CustomsGuard includes an automated test suite verifying database integrity, discrepancy detection logic, multi-container demurrage scaling, duty restitution math, and reporting:

```bash
uv run pytest
```

_Note: Core tariff lookup, arithmetic, and reporting tests run locally against containerized services.
Full live end-to-end conversational CLI tests require configuring the model provider API key in Langflow and setting `BOB_API_KEY` in `.env`._

## Connecting with IBM Bob

1. Launch **IBM Bob Desktop**.
2. Navigate to **Settings** -> **MCP**.
3. Verify or add the configuration from `.bob/mcp.json`.
4. The `customsguard` tool will appear in your active tools list.
5. In IBM Bob, audit shipments using natural language, raw JSON, or the built-in skill:

```text
$audit-shipment SHP-2026-0042
```

6. Or run non-interactive verification directly using Bob CLI:

```bash
BOB_API_KEY="your_api_key_here" bob run --trust "Audit shipment SHP-2026-0042 using customsguard tool"
```

7. Inspect the audit results in Bob, check the exported report in `./data/reports/`, and preview the email alert in Mailpit (`http://localhost:8025`).

## Documentation & Scenarios Directory

### Domain & Business Strategy

- [`docs/domain/problem_solution.md`](./docs/domain/problem_solution.md): Deep analysis of customs bottlenecks, demurrage costs, and our AI solution.
- [`docs/domain/business_canvas.md`](./docs/domain/business_canvas.md): Business model canvas, ROI model, demurrage savings, and ~87% tech cost reduction.
- [`docs/domain/macmap.xlsx`](./docs/domain/macmap.xlsx): Official WTO/UNCTAD International Trade Centre (ITC) Market Access Map (MAcMap) tariff schedule for Indonesia.

### Technical Architecture & Setup

- [`docs/technical/api_reference.md`](./docs/technical/api_reference.md): REST API and Model Context Protocol (MCP) reference for Langflow and FastAPI endpoints.
- [`docs/technical/architecture.md`](./docs/technical/architecture.md): Langflow canvas topology, node specifications, guardrails, and data contracts.
- [`docs/technical/design_decisions.md`](./docs/technical/design_decisions.md): Rationale behind flexible agent reasoning, permit verification, and enterprise roadmap.
- [`docs/technical/mcp_setup.md`](./docs/technical/mcp_setup.md): Step-by-step connection guide for IBM Bob and Langflow MCP proxy.
- [`langflow/CustomsGuard.json`](./langflow/CustomsGuard.json): Pre-configured Langflow visual pipeline export (Audit & MCP Flow).
- [`langflow/CustomsGuard Bot.json`](./langflow/CustomsGuard%20Bot.json): Pre-configured Langflow visual pipeline export (Regulatory Knowledge Assistant Flow).

### Prompts, Test Fixtures & Reference Outputs

- [`scenarios/prompts/`](./scenarios/prompts/): Modular prompts for high-risk audits, demurrage scaling, and duty restitution.
- [`data/seed/sample_invoices.json`](./data/seed/sample_invoices.json): Scenario invoice payloads with carrier, container metadata, and declared commodities.
- [`scenarios/expected-outputs/`](./scenarios/expected-outputs/): Ground-truth reference audit reports matching each test scenario.

[^mckinsey-trade]: Casanova, D., Dierker, D., Jensen, B., Hausmann, L., & Stoffels, J. (2022, November 29). The multi-billion-dollar paper jam: Unlocking trade by digitalizing documentation. McKinsey & Company. https://www.mckinsey.com/industries/logistics/our-insights/the-multi-billion-dollar-paper-jam-unlocking-trade-by-digitalizing-documentation

[^uu-kepabeanan]: Republic of Indonesia. Law No. 17 of 2006 amending Law No. 10 of 1995 on Customs (Undang-Undang Kepabeanan), Article 82(5) and Article 16(4); implemented via Government Regulation (PP) No. 39 of 2019.
