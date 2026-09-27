# Architectural Decisions & Scope Boundaries

This document details key engineering decisions, operational rationale, and intentional scope boundaries in CustomsGuard.
It highlights how the architecture balances long-term maintainability, deterministic reliability, and enterprise confidentiality.

## 1. Flexible Agent Reasoning vs. Rigid JSON Schemas

### The Architectural Decision

The core Python toolkit (`audit_shipment_compliance`) is intentionally designed with a resilient, open input contract rather than enforcing an exhaustive, rigid schema for supplementary documents like regulatory permits.

### Engineering Rationale

1. **Invoice Heterogeneity**: Commercial invoices, packing lists, and bills of lading arrive in dozens of formats across different freight forwarders.
   Forcing strict schema validation on supplementary fields (such as permit numbers or customs declarations) creates brittle code and high maintenance overhead.
2. **Separation of Concerns**: The Python component acts as a deterministic mathematical and regulatory lookup engine, identifying what the law requires for a matched commodity.
   The conversational agent (IBM Bob / Langflow) acts as the contextual synthesizer, evaluating whether the user's input notes, invoice text, or attachments fulfill those requirements.
3. **Resilience to Varied Data**: An officer can provide a structured JSON payload, a plain-text prompt, or a hybrid prompt stating that a specific permit is already on file.
   The agent naturally incorporates this context without requiring breaking changes to backend code.

## 2. Scope Boundaries: Regulatory Permit Verification & Government APIs

### Current Implementation Scope

CustomsGuard deterministically detects when an official tariff line is restricted (Lartas) and specifies the exact ministry license required (such as Kemenkes Distribution Licenses, SDPPI Certifications, or BPOM Approvals).
It calculates port detention exposure if the filing attempts to bypass these restrictions via misdeclaration.

### Strategic Scope Boundary: External Government APIs

Live querying against official Indonesian government single-window portals (such as INSW or Bea Cukai CEISA 4.0) to validate importer tax IDs (NPWP) and live permit databases is intentionally defined as an enterprise roadmap item rather than a local hackathon dependency.

Key reasons for this boundary:

- **Air-Gapped Security**: Keeping the knowledge base completely local ensures zero sensitive trade data or enterprise pricing leaks to external web endpoints.
- **Self-Contained Evaluation**: Evaluators can run the entire solution locally via Docker without requiring government sandbox credentials or live ministry API tokens.
- **Deterministic Reliability**: The system is shielded from external network outages, API downtime, or rate limiting during high-volume document screening.

## 3. Dual-Network Execution Resilience

The toolkit component integrates an automatic connection fallback between Docker container hosts (`qdrant:6333`, `mailpit:1025`) and local host machine addresses (`localhost:6333`, `localhost:1025`).

This ensures seamless execution across two operating environments:

1. **Container Runtime**: When Langflow executes workflows inside its Docker container, it communicates directly with sibling containers on the internal Docker bridge.
2. **Host Runtime**: When developers or CI pipelines execute automated tests (`pytest`) or non-interactive terminal sessions (`bob run`), the tools fall back to host-bound ports without requiring environment re-configuration.

## 4. Localized Air-Gapped Tariff Knowledge Base

CustomsGuard indexes 5,612 standardized Indonesian 6-digit Harmonized System (HS) subheadings directly into an on-premise Qdrant vector database.
While national tariff schedules undergo periodic revisions by the Ministry of Finance, hosting the full schedule locally delivers sub-second semantic matching while preserving total enterprise data sovereignty.
Annual schedule updates are managed through straightforward batch re-indexing scripts rather than fragile external dependencies.

## 5. Demurrage Modeling Baseline vs. Carrier Container Sizing

### Current Implementation Scope

The financial liability engine scales daily port detention exposure based on physical container count (`container_count * $350.00/day`).
The $350.00 daily rate serves as a simulated baseline multiplier to prove multi-container risk accumulation.
The engine does not validate or differentiate container dimensions (such as 20ft vs 40ft vs refrigerated units) in the current build.

### Strategic Scope Boundary: Carrier Tariffs & Container Sizing

Parsing specific container types and carrier-specific tiered detention policies from Bills of Lading (B/L) is intentionally allocated to future carrier integration roadmap milestones.
This design choice keeps the current prototype focused strictly on customs regulatory verification while avoiding unsubstantiated container sizing claims.
