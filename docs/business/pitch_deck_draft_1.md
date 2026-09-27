# CustomsGuard Pitch Deck Structure & Presentation Script

This document provides a comprehensive, information-dense slide-by-slide script, data validation tables, return on investment (ROI) calculations, and formal reference citations for the 5-minute hackathon pitching session.

## Slide 1: Title, Team & Strategic Theme

- **Slide Title**: CustomsGuard: Autonomous Trade Compliance & Tariff Discrepancy Engine
- **Theme**: Productivity & Smart Business
- **Presenter Subtitle**: IBM SkillsBuild x Hacktiv8 National Hackathon 2026
- **Spoken Script (30 seconds)**:
  "Hello judges and fellow participants.
  Today we are presenting CustomsGuard, an autonomous AI engine that safeguards cross-border supply chains by auditing commercial invoices, preventing catastrophic port container detentions, and eliminating customs penalty surcharges."

---

## Slide 2: The Problem: The Customs Hold & Demurrage Bottleneck

- **Visuals**: Port terminal congestion graphic, container shunted to Red Lane, ticking demurrage meter with progressive carrier slabs, and regulatory penalty breakdown.
- **Problem Grounding & Market Context**:

| Problem Metric                | Empirical Grounding                                                                                                                                                   | Domain Consequence                                                                                 | Source Citation                                                        |
| :---------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| **Port Gateway Volume**       | 8.30 million TEUs (5.69 million boxes) and 21.51 million non-container tons processed in 2025 at Tanjung Priok                                                        | Heavy terminal utilization where documentary bottlenecks ripple across domestic supply chains      | PT Pelindo Regional 2 Tanjung Priok / Ocean Week [^pelindo-priok]      |
| **Terminal Congestion Dwell** | Cargo lacking pre-booked appointment slots or flagged by document errors queues 7 to 10 days before terminal clearance                                                | Documentation errors directly push shipments into extended terminal holding                        | Mordor Intelligence (2026) [^mordor-id]                                |
| **Carrier Demurrage Slabs**   | Progressive daily tariffs after 5 free days: $101/day (Days 6-10), $121/day (Days 11-15), $151/day (Days 16-20), $161/day (Days 21+) for standard 40ft dry containers | A 5-day hold on a 4-container consignment inflicts $2,020.00 USD in avoidable cash bleed           | CMA CGM Indonesia Tariff (July 1, 2026) [^cma-cgm]                     |
| **Non-Tariff Permit Traps**   | Exactly 546 of 5,612 HS-6 subheadings (9.73%) require mandatory pre-import approvals (SDPPI, Kemenkes, BPOM)                                                          | Cargo arriving without valid permits cannot be released legally, resulting in indefinite detention | WTO/UNCTAD ITC MAcMap & Ministerial Regulations [^macmap] [^permenkes] |
| **Administrative Fines**      | Underpaid customs duties attract administrative surcharges ranging from 100% up to 1,000% of the duty shortfall                                                       | A minor $5,000 misclassification risks an unexpected $5,000 to $50,000 corporate penalty           | Law No. 17/2006 (UU Kepabeanan) & PP No. 39/2019 [^uu-kepabeanan]      |
| **Manual Audit Latency**      | Compliance teams spend 20 to 30 minutes per line item and 2 to 4 hours per manifest                                                                                   | High labor costs, error-prone manual cross-checks, and missed duty restitution opportunities       | Industry Benchmark [^mordor-id]                                        |

- **Spoken Script (45 seconds)**:
  "Every year, international trade suffers severe friction from customs documentation errors.
  Indonesia's primary gateway, Tanjung Priok, processed 8.30 million TEUs in 2025, where cargo flagged for documentation errors queues 7 to 10 days before terminal clearance.
  A single misclassification shunts cargo into the Red Lane, where carriers like CMA CGM assess escalating demurrage tariffs.
  For a standard 4-container consignment held just 5 days beyond free time, that is over two thousand dollars in avoidable detention penalties.
  Furthermore, missing non-tariff permits across 546 restricted subheadings trigger port cargo seizures and administrative fines up to 1,000% under Indonesian customs law."

---

## Slide 3: The Solution: CustomsGuard Autonomous Engine

- **Visuals**: Invoice payload ingestion into CustomsGuard, sub-5-second semantic vector matching, real-time permit verification, multi-container financial liability assessment, automated dossier export, and SMTP alert dispatch.
- **Core Engine Capabilities**:

| Capability Module                  | Technical Mechanism                                                                         | Operational Performance                                                                          | Practical Benefit                                                                                |
| :--------------------------------- | :------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------- |
| **Autonomous Tariff RAG**          | Vector similarity retrieval across 5,612 Indonesian HS-6 subheadings in local Qdrant        | Vector cosine query takes under 50ms; complete audit executes in 3 to 5 seconds                  | Replaces 2 to 4 hours of manual tariff book searching with instant, deterministic classification |
| **Permit Verification (Lartas)**   | Automated cross-referencing against 546 restricted commodity schedules                      | Instant detection of SDPPI (telecom), Kemenkes (medical), and BPOM (food/pharma) licenses        | Pre-empts Red Lane seizures before ocean cargo arrives at the port                               |
| **Carrier Demurrage Engine**       | Progressive day-slab calculator implementing official CMA CGM Indonesia published schedules | Evaluates container count, size, type, and projected days held (defaulting to 40ft Dry Standard) | Provides actionable dollar burn rates and cumulative detention projections                       |
| **Restitution Discovery**          | Mathematical tariff difference analyzer identifying over-declared duty rates                | Detects items declared at default rates (e.g. 15%) when official tariff is lower (0% or 5%)      | Transforms customs compliance from a cost center into a tax recovery engine                      |
| **Automated Evidentiary Dossiers** | Local filesystem export of timestamped Markdown and JSON dossiers to `./data/reports/`      | Instant programmatic archiving for compliance audits and post-clearance reviews                  | Creates immutable audit trails for internal controllers and customs authorities                  |
| **Instant Incident Alerting**      | Automated SMTP email alert dispatching via Mailpit to logistics coordinators                | Sub-second alert dispatch when high-risk non-compliance is detected                              | Enables operational intervention days before port arrival                                        |

- **Spoken Script (45 seconds)**:
  "CustomsGuard transforms this slow, error-prone manual procedure into an autonomous, deterministic compliance engine.
  Our semantic search queries 5,612 Indonesian tariffs in milliseconds, completing a full audit in 3 to 5 seconds.
  It cross-references line items against mandatory ministerial permits, calculates exact duty shortfalls, uncovers overpayment restitution opportunities, and models carrier demurrage exposure before cargo reaches the terminal.
  Official evidentiary dossiers are archived automatically, and urgent alerts are dispatched instantly to logistics coordinators."

---

## Slide 4: System Architecture & Integration

- **Visuals**: Horizontal architecture workflow diagram detailing the enterprise stack: IBM Bob (Conversational Client) -> Model Context Protocol (MCP) Bridge -> Langflow Agent Runtime -> CustomsGuard Tools -> Qdrant Vector DB & Mailpit SMTP.
- **Enterprise Integration Stack**:

| Architectural Layer         | Component Technology           | Role & Functionality                                                                     | Enterprise Benefit                                                                            |
| :-------------------------- | :----------------------------- | :--------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| **User Interface & Shell**  | IBM Bob CLI / Desktop Co-Pilot | Provides conversational trade compliance interaction via `$audit-shipment` skill         | Seamless copilot experience for logistics officers without requiring custom frontend software |
| **Protocol Integration**    | Model Context Protocol (MCP)   | Exposes Langflow audit execution pipeline as a standardized tool (`customsguard`)        | Universal, vendor-neutral protocol connecting conversational clients to execution engines     |
| **Visual Orchestration**    | Langflow Visual Agent Runtime  | Connects Chat Input, Agent LLM (gpt-4o-mini), Custom Python Component, and Guardrails    | Visual, auditable business logic easily maintained by compliance analysts                     |
| **Tariff Vector Store**     | Qdrant Vector Database         | Stores 5,612 Indonesian HS-6 tariff vectors embedded via FastEmbed                       | High-speed, local on-premise vector search requiring zero cloud API calls                     |
| **Safety & Moderation**     | Langflow Guardrails Node       | Sanitizes PII (NPWP, bank accounts), prevents prompt injections, and masks tokens        | Robust enterprise security preventing data leakage and adversarial manipulation               |
| **Alerting Infrastructure** | Mailpit SMTP Service           | Dispatches real-time HTML/text compliance alerts to operational teams (`localhost:8025`) | Immediate alerting without external third-party mail relay dependencies                       |

- **Spoken Script (60 seconds)**:
  "Our architecture combines the strengths of IBM technology and modern agent protocols.
  IBM Bob serves as the conversational co-pilot for trade compliance officers.
  Through the open Model Context Protocol, Bob invokes our Langflow execution pipeline.
  Langflow queries a self-hosted Qdrant vector database containing all 5,612 Indonesian tariff subheadings, generates timestamped audit dossiers on local storage, and fires real-time SMTP alerts.
  The entire pipeline operates locally in Docker, ensuring sensitive commercial trade data never leaves corporate boundaries."

---

## Slide 5: Responsible AI & Safety Guardrails

- **Visuals**: Dual-path Guardrails diagram illustrating Pass (compliant/audited payload to Chat Output) and Fail (sanitized warning response blocking prompt injection or PII leakage).
- **Safety & Responsible AI Architecture**:

| Guardrail Dimension          | Threat Mitigated                                                                              | Implementation Mechanism                                                             | System Behavior                                                                                               |
| :--------------------------- | :-------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ |
| **PII & Commercial Privacy** | Exposure of Indonesian Tax IDs (NPWP), commercial bank accounts, and personal contact details | Regex and pattern-based redaction in Langflow Guardrails node                        | Automatically masks sensitive corporate and personal identifiers before presentation                          |
| **Adversarial Defense**      | Prompt injection attacks embedded inside supplier invoice commodity descriptions              | Content-safety evaluation node screening incoming payloads for instruction overrides | Blocks adversarial prompts and routes execution to a safe fallback alert path                                 |
| **Credential Protection**    | Accidental exposure of internal database tokens, SMTP passwords, or API keys                  | Outbound payload regex screening preventing credential leakage in chat responses     | Masks internal infrastructure secrets from audit summaries and logs                                           |
| **Air-Gapped Privacy**       | Commercial espionage and leak of confidential supplier pricing or margins                     | 100% self-hosted deployment running inside Docker containers on local infrastructure | Proprietary shipment manifests, unit costs, and trade routes never leave the enterprise                       |
| **Human-in-the-Loop**        | Autonomous over-reliance or unauthorized cargo customs filings                                | Explicit advisory persona design defined in `AGENTS.md`                              | CustomsGuard acts as an evidence and calculation engine; licensed PPJK brokers maintain final release signoff |

- **Spoken Script (45 seconds)**:
  "Responsible AI is built into our core pipeline.
  We implemented an active Guardrails node in Langflow that scrubs personal identifiable information, blocks prompt injections hidden in invoice descriptions, and prevents credential leakage.
  Because the stack runs entirely within self-hosted Docker containers, confidential supplier pricing and trade contracts remain strictly private.
  Most importantly, CustomsGuard upholds the human-in-the-loop principle: it acts as an intelligent evidence engine, while licensed trade professionals maintain final decision-making authority."

---

## Slide 6: Business Model, Market Sizing (TAM/SAM/SOM) & Economic ROI

- **Visuals**: Market sizing concentric circles (TAM -> SAM -> SOM), subscription pricing tiers, cost-engineering comparison chart (~87% annual savings), and direct ROI holding calculation.
- **Market Sizing Validation & Grounding**:

| Market Scope                             | Valuation & Forecast                                                                                                      | Growth Driver & Segment Dynamics                                                                                               | Source Citation                                                                  |
| :--------------------------------------- | :------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
| **Macro Trade Anchor**                   | $3.85 Trillion USD total ASEAN goods trade ($2.35 Trillion USD waterborne); Indonesia Transport GDP at 983.5 Trillion IDR | Massive regional maritime merchandise volume passing through Southeast Asian customs corridors                                 | ASEAN Statistical Yearbook 2023 [^asyb2023]                                      |
| **Total Addressable Market (TAM)**       | $31.62 Billion USD in 2025, growing to $41.86 Billion USD by 2031 (4.78% CAGR)                                            | ASEAN Freight Forwarding & Logistics; broader ASEAN logistics sits at $288.24B (2025) reaching $406.10B (2031)                 | Mordor Intelligence (2026) [^mordor-asean] / Research and Markets [^randm-asean] |
| **Serviceable Addressable Market (SAM)** | $2.23 Billion USD in 2025, expanding to $2.38 Billion USD in 2026 and $3.32 Billion USD by 2031 (6.83% CAGR)              | Indonesian Customs Brokerage; ocean freight accounts for 58.67% ($1.31B USD) and 3PL/forwarders command 68.74% ($1.53B USD)    | Mordor Intelligence (2026) [^mordor-id]                                          |
| **Serviceable Obtainable Market (SOM)**  | $30 Million to $60 Million USD initial obtainable beachhead                                                               | Digital-first and API-based brokerages growing at 15.34% CAGR; capturing 2.5% to 5.0% of digital transactions at Tanjung Priok | Mordor Intelligence (2026) [^mordor-id] / Pelindo [^pelindo-priok]               |

- **Tiered B2B SaaS Subscriptions & Transactional Model**:

| Tier                      | Monthly Price     | Annual Price     | Target Customer                                          | Features & Limits                                                              |
| :------------------------ | :---------------- | :--------------- | :------------------------------------------------------- | :----------------------------------------------------------------------------- |
| **Starter**               | $299 USD / mo     | $3,588 USD / yr  | Independent PPJK brokers & SME freight forwarders        | Up to 500 audits/month, Qdrant tariff lookup, Mailpit SMTP alerts              |
| **Professional**          | $899 USD / mo     | $10,788 USD / yr | Mid-tier logistics firms, 3PLs & trading houses          | Up to 3,000 audits/month, multi-seat human review, automated dossier archiving |
| **Enterprise Air-Gapped** | $2,500 USD / mo   | $30,000 USD / yr | Multinational forwarders, ocean carriers, port terminals | Unlimited audits, dedicated on-premise Docker deployment, custom embeddings    |
| **Transactional API**     | $1.50 USD / audit | Pay-as-you-go    | Low-volume importers & occasional customs filers         | On-demand REST/MCP API compliance audit per commercial invoice                 |

- **Underlying ROI & Economic Validation**:
  1. **Carrier Demurrage Elimination**:
     Under the CMA CGM Indonesia Merged Import Demurrage & Detention Tariff (effective July 1, 2026), importers receive 5 free days for standard dry containers.
     Beginning Day 6, progressive daily rate slabs apply ($101/day for Days 6 to 10 for a 40ft Dry Standard container).
     Preventing a single 5-day hold on a 4-container consignment saves:
     $$4 \text{ containers} \times \$101.00/\text{day} \times 5 \text{ days} = \$2,020.00 \text{ USD in avoided cash bleed.}$$
     Preventing just two delayed consignments per year completely covers the entire annual cost of a Professional subscription ($10,788/yr).
  2. **Customs Surcharge Avoidance**:
     Under Law No. 17/2006 (UU Kepabeanan), tariff misclassifications resulting in duty underpayment attract administrative fines of 100% to 1,000% of the duty shortfall.
     Avoiding a single $5,000 duty error saves an enterprise between $5,000 and $50,000 in direct penalties.
  3. **Cost Engineering (~87% Cost Reduction)**:
     - Cloud SaaS API stack (managed vector DB, proprietary LLM APIs, cloud hosting, egress): ~$7,560 USD / year.
     - CustomsGuard On-Premise Docker stack (local Qdrant, local quantized models, edge compute): ~$980 USD Year 1 (including mini-server hardware) and ~$180 USD / year thereafter.
     - Delivers an immediate ~87% infrastructure cost advantage.

- **Spoken Script (45 seconds)**:
  "Our business model targets a 2.23-billion-dollar Indonesian customs brokerage market, where digital-first compliance adoption is surging at over 15% annually.
  Our pricing ranges from a 299-dollar Starter plan to an Enterprise on-premise deployment.
  The ROI is immediate and undeniable: avoiding just one 5-day delay on a 4-container consignment saves 2,020 dollars in CMA CGM demurrage fees, while eliminating customs fines that can reach 1,000 percent under Indonesian customs law.
  Furthermore, our self-hosted Docker architecture delivers an 87% infrastructure cost reduction compared to fragile cloud API services."

---

## Slide 7: Live Prototype Verification & Roadmap

- **Visuals**: Terminal execution of test suite, IBM Bob CLI conversation screenshot executing `$audit-shipment`, sample generated Markdown report in `./data/reports/`, and Mailpit inbox showing dispatched alerts.
- **Verification Matrix & Test Coverage**:

| Verification Dimension      | Tested Component                | Test Verification Scope                                                                                                        | Status                    |
| :-------------------------- | :------------------------------ | :----------------------------------------------------------------------------------------------------------------------------- | :------------------------ |
| **Core Audit Logic**        | `tests/test_audit_engine.py`    | Validates HS discrepancy detection, permit checking (SDPPI/Kemenkes/BPOM), CMA CGM progressive day-slabs, and duty restitution | 100% Passing (6 tests)    |
| **Alerting Infrastructure** | `tests/test_alert_system.py`    | Validates SMTP dispatching via Mailpit and graceful fallback handling on socket failure                                        | 100% Passing (2 tests)    |
| **Dossier Archiving**       | `tests/test_report_exporter.py` | Verifies export of structured Markdown and JSON audit dossiers with correct directory timestamps                               | 100% Passing (1 test)     |
| **Tariff Vector Store**     | `tests/test_tariff_database.py` | Validates volume and schema of 5,612 Indonesian HS-6 subheadings from WTO/UNCTAD ITC MAcMap                                    | 100% Passing (4 tests)    |
| **End-to-End CLI Pipeline** | `tests/test_e2e_pipeline.py`    | Verifies IBM Bob CLI invoking Langflow via MCP and generating verified output dossiers                                         | 100% Passing (1 test)     |
| **Overall Test Health**     | Complete Pytest Suite           | Comprehensive automated suite validating core compliance logic across all components                                           | **14 / 14 Tests Passing** |

- **Strategic Roadmap**:
  - **Phase 1 (Completed)**: Core audit engine, 5,612 HS codes in Qdrant, CMA CGM progressive demurrage modeling, Mailpit SMTP alerts, and IBM Bob MCP integration.
  - **Phase 2 (Next 6 Months)**: Automated OCR ingestion for scanned commercial invoices and direct API integration with Indonesia National Single Window (INSW) and CEISA 4.0.
  - **Phase 3 (Next 12 Months)**: Expansion across ASEAN Single Window members (Singapore, Malaysia, Thailand, Vietnam) supporting ATIGA preferential trade certificate validation.
- **Spoken Script (30 seconds)**:
  "CustomsGuard is fully built and verified today, backed by 14 comprehensive automated tests covering our core compliance engine, demurrage calculations, and live MCP integration in IBM Bob.
  Looking forward, our roadmap expands CustomsGuard into direct CEISA 4.0 integration, automated OCR invoice ingestion, and pan-ASEAN single-window trade facilitation.
  Thank you, and we welcome your questions."

---

## Authoritative Reference Citations & Source Documentation

[^pelindo-priok]: PT Pelindo Regional 2 Tanjung Priok. "Pelindo Priok Tangani 8,30 Juta TEUs, 21,51 Juta Ton", reported via _Ocean Week_, December 2025 / January 2026. Official operational performance release confirming 8.30 million TEUs (5.69 million boxes) container throughput and 21.51 million non-container tons. https://oceanweek.co.id/pelindo-priok-tangani-830-juta-teus-2151-juta-ton/

[^cma-cgm]: CMA CGM Group. "CMA CGM Indonesia Merged Import Demurrage & Detention Tariff", effective July 1, 2026. Official published tariff schedule establishing 5 free days for standard dry containers, followed by progressive daily rate slabs ($101/day for Days 6 to 10 for 40ft Dry Standard containers, rising to $161/day beyond Day 21).

[^uu-kepabeanan]: Republic of Indonesia. Law No. 17 of 2006 amending Law No. 10 of 1995 on Customs (Undang-Undang Kepabeanan), Article 82(5) and Article 16(4); implemented via Government Regulation (PP) No. 39 of 2019, establishing administrative penalty surcharges from 100% to 1,000% of customs duty shortfalls.

[^macmap]: International Trade Centre (ITC), World Trade Organization (WTO), and United Nations Conference on Trade and Development (UNCTAD). Market Access Map (MAcMap) Tariff Database, 5,612 Indonesian 6-digit Harmonized System subheadings.

[^permenkes]: Ministry of Health, Republic of Indonesia. Regulation Permenkes No. 5 of 2026 on Importation of Medical Devices and Diagnostic In-Vitro Reagents via INSW-integrated pathways; and Ministry of Communication and Digital / SDPPI certification mandates under Law No. 36 of 1999.

[^asyb2023]: ASEAN Secretariat. _ASEAN Statistical Yearbook 2023_, Volume 19, ISSN 2986-3627, Jakarta: ASEAN Secretariat, December 2023. Confirms total ASEAN merchandise trade in goods reached $3.85 trillion USD in 2022 ($2.35 trillion USD transported by waterborne vessels) and Indonesia's Transportation & Storage Sector GDP totaled 983.5 trillion IDR. https://www.asean.org

[^mordor-asean]: Mordor Intelligence. "ASEAN Freight Forwarding Market Analysis (2026-2031)", 2026. Market valuation of $31.62 Billion USD in 2025, reaching $41.86 Billion USD by 2031 at 4.78% CAGR. https://www.mordorintelligence.com/industry-reports/asean-freight-forwarding-market

[^randm-asean]: Research and Markets. "ASEAN Freight and Logistics Market Share Analysis (2026-2031)", Report ID 5759301, 2026. Total ASEAN freight and logistics market size projected at $288.24 Billion USD in 2025, reaching $406.10 Billion USD by 2031 at 5.82% CAGR. https://www.researchandmarkets.com/reports/5759301/asean-freight-logistics-market-share-analysis

[^mordor-id]: Mordor Intelligence. "Indonesia Customs Brokerage Market Size & Share Analysis (2026-2031)", 2026. Market valuation of $2.23 Billion USD in 2025, reaching $3.32 Billion USD by 2031 at 6.83% CAGR, with digital-first brokerages growing at 15.34% CAGR. https://www.mordorintelligence.com/industry-reports/indonesia-customs-brokerage-market

[^metastat-asean]: MetaStat Insight. "ASEAN Freight Forwarding Market Size, Share, Industry Analysis, Growth, Trends, and Forecast 2026-2033", 2026. Market projection of $31.9 Billion USD in 2025 to $46.1 Billion USD by 2033 at 4.7% CAGR. https://metastatinsight.com/press-releases/asean-freight-forwarding-market
