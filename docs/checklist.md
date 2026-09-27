# CustomsGuard Master Project Checklist & Roadmap

This document tracks all project milestones, from technical implementation and cleanup to public documentation and hackathon submission.

## Phase 1: Core Infrastructure & MCP Pipeline (Completed)

- [x] **Local Container Infrastructure**
  - [x] Create multi-service `docker-compose.yml` (Langflow, Qdrant, Mailpit, Postgres).
  - [x] Configure persistent data volumes and environment configurations.
  - [x] Launch and verify zero runtime errors across all container logs.

- [x] **Customs Knowledge Base & Seeding**
  - [x] Parse 5,612 Indonesian HS codes and import duties from `docs/macmap.xlsx`.
  - [x] Generate structured database in `data/seed/tariff_database.json`.
  - [x] Create test scenarios in `data/seed/sample_invoices.json` (High Risk, Discrepancy Warning, Compliant).
  - [x] Seed Qdrant collection `customs_tariffs` with full-text search indexes.

- [x] **Langflow Toolkit Component & MCP Integration**
  - [x] Implement `CustomsGuardToolkitComponent` returning callable LangChain `@tool` instances.
  - [x] Wire Langflow canvas (Model -> Agent -> CustomsGuard Tools -> Chat Input/Output).
  - [x] Configure `.bob/mcp.json` with local `uvx` binary path.
  - [x] Verify MCP protocol initialization and tool listing (`customsguard`) in IBM Bob.
  - [x] Verify local file report generation (`./data/reports/`) and Mailpit email alerting (`localhost:8025`).

## Phase 2: Codebase Cleanup & Toolchain Standardization (Completed)

- [x] **Source Code Sync**
  - [x] Synchronize `scripts/customs_components.py` with the active `CustomsGuardToolkitComponent`.

- [x] **Remove Obsolete Scaffolding Artifacts**
  - [x] Delete `scripts/setup_langflow_flow.py` (obsolete programmatic canvas generator).
  - [x] Delete `scripts/rebuild_customsguard_flow.py` (obsolete schema injector).
  - [x] Delete `docs/langflow_pipeline_guide.md` (superseded by direct UI setup).

- [x] **Toolchain Standardization (`uv`)**
  - [x] Initialize `pyproject.toml` with `uv` for reproducible local Python dependencies.
  - [x] Standardize on direct `docker compose up -d` and `uv run python scripts/seed_qdrant.py` without wrapper overhead.

## Phase 3: Automated Testing & Production Readiness (Completed)

- [x] **Automated `pytest` Test Suite**
  - [x] Create `tests/test_tariff_database.py` to validate HS code schema and duty values.
  - [x] Create `tests/test_audit_engine.py` for deterministic discrepancy detection and duty shortfall calculation.
  - [x] Implement Feature B (scaled multi-container demurrage) and Feature C (duty overpayment restitution advisory).
  - [x] Create `tests/test_alert_system.py` to test Mailpit SMTP dispatch.
  - [x] Create `tests/test_report_exporter.py` to verify Markdown and JSON report disk persistence.
  - [x] Create `tests/test_e2e_pipeline.py` verifying full pipeline from invoice to disk report and Mailpit API.
  - [x] Run test suite and confirm 13/13 passing tests with zero warnings.

## Phase 4: Public Documentation & Bob Orchestration (Completed)

- [x] **Create Initial `README.md`**
  - [x] High-impact executive summary and value proposition.
  - [x] System architecture diagram (IBM Bob -> MCP -> Langflow Agent -> CustomsGuard Tools).
  - [x] One-command quickstart guide (`docker compose up -d`, seeding, Bob configuration).
  - [x] Test invoice execution instructions for evaluators.

- [x] **IBM Bob Agent & Skill Orchestration**
  - [x] Create `AGENTS.md` in project root defining CustomsGuard trade compliance persona and MCP guidelines.
  - [x] Create `.bob/skills/audit-shipment/SKILL.md` enabling `$audit-shipment` workflow invocations.

- [x] **Documentation Retention**
  - [x] Maintain `docs/blueprint.md` for technical system architecture references.
  - [x] Maintain `docs/draft.md` for rubrics and narrative draft.
  - [x] Maintain `docs/cleanup_and_refinement_plan.md` for technical maintenance.
  - [x] Maintain `docs/hackathon_outlook_and_scope.md` for scoring and business scope.
  - [x] Maintain `docs/edge_cases_implementation.md` for trade compliance features B and C.

## Phase 5: Submission Deliverables & Pitch Deck Preparation

- [ ] **Pitch Deck Formulation**
  - [ ] Create presentation deck covering Problem, Solution, Agent Architecture, ROI, and Budget Planning.
  - [ ] Capture 3 to 5 high-resolution proof screenshots:
    - [ ] Langflow Canvas with CustomsGuard Tools.
    - [ ] IBM Bob Desktop running compliance audit via MCP.
    - [ ] Generated Markdown audit report on disk.
    - [ ] Mailpit Web UI showing urgent alert email.

- [ ] **Submission Form Preparation (Slide 86)**
  - [ ] Section 1: Team Information & IBM SkillsBuild certificates.
  - [ ] Section 2: Project Overview & Problem Statement.
  - [ ] Section 3: Technical Proof (Langflow + Bob MCP integration).
  - [ ] Section 4: Pitch Deck upload & screenshot attachments.
  - [ ] Section 5: Final declarations and originality signoff.

- [ ] **Final Repository Polish**
  - [ ] Perform Git history squashing or cleaning to ensure a pristine, professional commit log.
