# CustomsGuard Pitch Deck Structure & Presentation Script

This document provides a slide-by-slide script and content outline for the 5-minute hackathon pitching session.

## Slide 1: Title, Team & Strategic Theme

- **Slide Title**: CustomsGuard: Autonomous Trade Compliance & Tariff Discrepancy Engine
- **Theme**: Productivity & Smart Business
- **Presenter Subtitle**: IBM SkillsBuild x Hacktiv8 National Hackathon 2026
- **Spoken Script (30 seconds)**:
  "Hello judges and fellow participants.
  Today we are presenting CustomsGuard, an autonomous AI engine that safeguards cross-border supply chains by auditing commercial invoices, preventing catastrophic port container detentions, and eliminating customs penalty surcharges."

## Slide 2: The Problem: The $1.2B Customs Hold Bottleneck

- **Visuals**: Diagram of cargo stopped at port terminal, clock ticking, demurrage accumulating ($350/day).
- **Core Points**:
  - 5,612 dynamic HS codes in the Indonesian tariff book (BTKI).
  - Manual verification takes 2 to 4 hours per manifest.
  - Minor errors lead to customs red-lane holds, accruing $350.00/day per container in port demurrage fees.
  - Missing non-tariff permits (SDPPI, Kemenkes, BPOM) cause indefinite cargo seizures and 100% to 1,000% administrative surcharges.
- **Spoken Script (45 seconds)**:
  "Every year, international trade loses over a billion dollars to customs documentation errors.
  In Indonesia alone, compliance officers must manually navigate 5,612 HS codes.
  A single misclassification shunts cargo into the Red Lane, where demurrage costs $350 dollars per container every day.
  For a 4-container consignment held for a week, that is nearly ten thousand dollars in wasted penalties."

## Slide 3: The Solution: CustomsGuard Autonomous Engine

- **Visuals**: Invoice going in -> 5 seconds -> Audit Dossier & Alerts coming out.
- **Core Capabilities**:
  - **Sub-5-Second Tariff RAG**: Autonomous lookup across 5,612 Indonesian HS-6 codes.
  - **Permit Verification**: Real-time detection of missing SDPPI, Kemenkes, and BPOM licenses.
  - **Financial Risk Modeling**: Exact duty shortfall, multi-container demurrage liability, and overpayment restitution discovery.
  - **Automated Evidence**: Instant Markdown/JSON dossier archiving and SMTP alerts via Mailpit.
- **Spoken Script (45 seconds)**:
  "CustomsGuard replaces hours of manual lookup with a 5-second deterministic audit.
  It cross-references line items against official tariffs, checks mandatory ministry permits, calculates exact duty shortfalls, and evaluates container demurrage exposure before cargo even arrives at the port."

## Slide 4: System Architecture & Integration

- **Visuals**: Horizontal architecture diagram (IBM Bob -> MCP Bridge -> Langflow Agent -> CustomsGuard Tools -> Qdrant & Mailpit).
- **Core Points**:
  - IBM Bob provides conversational co-pilot interaction (`$audit-shipment`).
  - Langflow serves as the visual orchestration runtime.
  - Model Context Protocol (MCP) acts as the bridge connecting Bob to Langflow.
  - Qdrant Vector Store provides on-premise semantic search across 5,612 codes.
- **Spoken Script (60 seconds)**:
  "Our architecture combines the strengths of IBM technology and modern agent protocols.
  IBM Bob acts as the user-facing orchestrator.
  Through the Model Context Protocol, Bob invokes our Langflow execution flow.
  Langflow queries a self-hosted Qdrant database containing all 5,612 Indonesian tariffs, generates audit reports on local disk, and fires urgent alerts to compliance officers."

## Slide 5: Responsible AI & Safety Guardrails

- **Visuals**: Screenshot of Langflow Guardrails node (Pass / Fail paths).
- **Core Points**:
  - **PII Sanitization**: Masks tax IDs (NPWP), commercial bank accounts, and personal signatures.
  - **Adversarial Defense**: Blocks prompt injection attempts hidden in invoice item descriptions.
  - **Air-Gapped Privacy**: Operates fully on-premise in Docker; sensitive pricing never leaves the enterprise.
  - **Human-in-the-Loop**: CustomsGuard advises and calculates; licensed human customs brokers make final release decisions.
- **Spoken Script (45 seconds)**:
  "Responsible AI is built into our core pipeline.
  We implemented an active Guardrails node in Langflow that scrubs personal identifiable information, blocks prompt injections in invoice descriptions, and prevents credential leakage.
  Most importantly, CustomsGuard respects human oversight: it serves as an evidence engine while licensed brokers maintain final signoff."

## Slide 6: Business Model, ROI & Market Feasibility

- **Visuals**: ROI graphic: 1 avoided 5-day hold ($7,000 saved) vs $299/mo subscription. Cost comparison chart (~87% savings).
- **Core Points**:
  - Hybrid B2B SaaS: Starter ($299/mo), Professional ($899/mo), Enterprise Air-Gapped ($2,500/mo).
  - Massive ROI: Preventing a single multi-container delay pays for the software for an entire year.
  - ~87% infrastructure cost reduction by utilizing on-premise open-source Docker deployment.
- **Spoken Script (45 seconds)**:
  "Our business model is built on undeniable ROI.
  Preventing just one 5-day container detention saves a logistics company $7,000 dollars, immediately covering our subscription cost.
  Furthermore, our self-hosted Docker architecture delivers an 87% cost reduction compared to fragile cloud API services."

## Slide 7: Live Prototype Verification & Roadmap

- **Visuals**: Screenshots of IBM Bob executing audit, generated audit report, and passing test suite (14/14 tests).
- **Core Points**:
  - Verified working prototype with 14 automated tests passing in under 3 seconds.
  - Real-time Mailpit SMTP alert dispatch verified.
  - **Roadmap**: Expansion to ASEAN trade agreements (ATIGA/ACFTA), direct INSW EDI integration, and automated OCR waybill ingestion.
- **Spoken Script (30 seconds)**:
  "CustomsGuard is fully built and verified today, backed by 14 passing automated tests and live MCP integration in IBM Bob.
  As we scale, we will integrate direct OCR parsing and expand coverage across ASEAN single-window portals.
  Thank you, and we welcome your questions."
