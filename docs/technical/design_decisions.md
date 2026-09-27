# Architectural Decisions & Scope Boundaries

This document details key engineering decisions, operational rationale, and intentional scope boundaries in CustomsGuard.
It highlights how the architecture balances long-term maintainability, deterministic reliability, and enterprise confidentiality.

## 1. Flexible Agent Reasoning vs. Rigid JSON Schemas

### The Architectural Decision

The core Python toolkit (`audit_shipment_compliance`) is intentionally designed with a resilient, open input contract rather than enforcing an exhaustive, rigid JSON schema for shipping manifests and supplementary regulatory permits.

### Contract Fields & Deterministic Fallbacks

The input contract accepts standard commercial invoice JSON while gracefully defaulting missing parameters to protect against schema validation crashes:

| Field                 | Type   | Expected Value                               | Graceful Fallback Default    | Rationale                                                     |
| :-------------------- | :----- | :------------------------------------------- | :--------------------------- | :------------------------------------------------------------ |
| `shipment_id`         | `str`  | Unique shipment code (e.g. `SHP-2026-0042`)  | Required                     | Mandatory for report archiving and SMTP alerting              |
| `carrier`             | `str`  | Ocean carrier name (e.g. `CMA CGM / APL`)    | `CMA CGM`                    | Default benchmark carrier for Indonesian ocean imports        |
| `container_count`     | `int`  | Number of physical shipping containers       | `1`                          | Ensures multi-container scaling operates without missing data |
| `container_size`      | `str`  | `"20"`, `"40"`, or `"45"`                    | `"40"` (Standard Dry)        | Global standard workhorse for containerized ocean freight     |
| `container_type`      | `str`  | `"DRY"` or `"REEFER"`                        | `"DRY"`                      | Standard dry cargo benchmark (5 free days)                    |
| `days_held_projected` | `int`  | Projected total days in port terminal        | `10` (5 days post-free-time) | Standard port holding projection for detention modeling       |
| `items`               | `list` | Line items with description, HS, duty, value | `[]`                         | Evaluated line-by-line against Qdrant tariff records          |

### Engineering Rationale

1. **Invoice Heterogeneity**: Commercial invoices, packing lists, and bills of lading arrive in dozens of formats across different freight forwarders.
   Forcing rigid schema validation on supplementary fields (such as permit numbers or container specifications) creates brittle code and high maintenance overhead.
2. **Deprecation of Arbitrary Flat Rates**: Early prototypes relied on a static `$350/day` flat demurrage estimate.
   This has been replaced by the official **CMA CGM Indonesia Merged Import Demurrage & Detention Tariff** (effective July 1, 2026).
   By incorporating intelligent container defaults (40ft Dry Standard), the contract calculates defendable progressive day-slabs even when a legacy user prompt omits container dimensions.
3. **Separation of Concerns**: The Python component acts as a deterministic mathematical and regulatory lookup engine, identifying what the law requires for a matched commodity.
   The conversational agent (IBM Bob / Langflow) acts as the contextual synthesizer, evaluating whether the user's input notes, invoice text, or attachments fulfill those requirements.
4. **Resilience to Varied Data**: An officer can provide a structured JSON payload, a plain-text prompt, or a hybrid prompt stating that a specific permit is already on file.
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

## 4. Localized Air-Gapped Tariff Knowledge Base (WTO/UNCTAD ITC MAcMap)

CustomsGuard indexes 5,612 standardized Indonesian 6-digit Harmonized System (HS) subheadings directly into an on-premise Qdrant vector database.
The underlying tariff data is derived from the Market Access Map (MAcMap), collected and managed by the International Trade Centre (ITC), a joint agency of the World Trade Organization (WTO) and the United Nations (UNCTAD).
Hosting this standardized dataset locally delivers sub-second semantic matching while preserving total enterprise data sovereignty.
Annual schedule updates are managed through straightforward batch re-indexing scripts rather than fragile external dependencies.

## 5. Carrier Demurrage Benchmark: CMA CGM Indonesia Tariff

### The Architectural Decision

Rather than relying on an arbitrary flat rate, CustomsGuard anchors demurrage and detention liabilities to the official published tariff schedule of CMA CGM Indonesia (effective July 1, 2026).
The engine models the carrier's Merged Import Demurrage & Detention clock across progressive day-slabs (Days 6 to 10, Days 11 to 15, Days 16 to 20, and Days 21+), incorporating mandatory free time allowances (5 free days for Standard Dry, 3 free days for Reefer).

### Container Sizing & Intelligent Defaults

The engine evaluates container dimensions (20ft, 40ft, 45ft) and equipment types (Standard Dry vs Reefer).
When container size is not specified in an incoming invoice or manifest, the system intentionally defaults to a **40ft Standard Dry container**.
The 40ft container represents the global standard benchmark for containerized ocean freight, ensuring consistent, defendable liability modeling.

### Strategic Scope Boundary: Multi-Carrier API Adapters

While CMA CGM serves as the production benchmark for Indonesian ocean imports, carrier-specific API adapters for other major lines (such as Maersk, MSC, Hapag-Lloyd, and ONE) are defined as enterprise roadmap milestones.
