# CustomsGuard Implementation Checkpoints & Work Plan

This plan tracks the active refactoring checkpoints to ground demurrage calculations in real CMA CGM tariffs, clean up testing suites, synchronize documentation, and flag unbacked business claims.

## Checkpoint 1: Core Engine Refactoring (CMA CGM Anchor Benchmark)

- [x] **Implement CMA CGM Indonesia D&D Schedule in `scripts/customs_components.py`**
  - Anchor demurrage calculations to the official CMA CGM Indonesia Merged Import Demurrage & Detention Tariff (effective July 1, 2026).
  - Standard Dry containers (5 free days):
    - Days 6 to 10: 20ft = $66/day, 40ft = $101/day, 45ft = $141/day.
    - Days 11 to 15: 20ft = $86/day, 40ft = $121/day, 45ft = $171/day.
    - Days 16 to 20: 20ft = $96/day, 40ft = $151/day, 45ft = $181/day.
    - Days 21+: 20ft = $106/day, 40ft = $161/day, 45ft = $191/day.
  - Reefer containers (3 free days):
    - Days 4 to 5: 20ft = $89/day, 40ft = $141/day.
    - Days 6 to 7: 20ft = $126/day, 40ft = $176/day.
    - Days 8+: 20ft = $130/day, 40ft = $180/day.
  - Calculate active daily burn rate and projected cumulative hold liability (defaulting to 5 detention days, i.e.
    Days 6 to 10).
  - Default gracefully to 40ft Dry Standard if container metadata is omitted.

- [x] **Enrich `data/seed/sample_invoices.json`**
  - Add shipping metadata (`carrier`: "CMA CGM / APL", `container_count`: 4, `container_size`: "40", `container_type`: "DRY") to sample invoices.
  - Align `INV-2026-APL-091` directly with the APL/CMA CGM group tariff.

- [x] **Flow Configuration Note**
  - Do not edit `langflow/CustomsGuard.json` (handled directly by the user in the Langflow UI).

---

## Checkpoint 2: Automated Testing Refactor

- [x] **Update Unit Tests in `tests/test_audit_engine.py`**
  - Add test cases validating CMA CGM progressive day-slabs for 20ft vs 40ft containers.
  - Add test cases verifying 5 free days for Dry containers and 3 free days for Reefer containers.
  - Validate multi-container scaled daily burn rates and cumulative detention totals.

- [x] **Clean Up `tests/test_e2e_pipeline.py`**
  - Remove redundant in-memory test (`test_full_compliance_audit_pipeline_e2e`) that bypasses the protocol stack.
  - Retain and verify `test_bob_shell_orchestrator_cli_e2e` as the single authentic end-to-end test exercising IBM Bob -> MCP -> Langflow.

- [x] **Execute Test Suite**
  - Run `pytest` to confirm 100% passing tests with zero warnings (14/14 passed).

---

## Checkpoint 3: Agent Personas, Skills & Prompt Synchronization

- [x] **Synchronize `AGENTS.md`**
  - Replace the flat $350 rule with the CMA CGM Indonesia benchmark reference and WTO/UNCTAD ITC MAcMap source.

- [x] **Synchronize `.bob/skills/audit-shipment/SKILL.md`**
  - Update skill instructions and expected output formats to present CMA CGM progressive day-slab findings.

- [x] **Update Evaluation Prompts & Sample Dossiers**
  - Update `prompts/02_demurrage_detention_prompt.md`.
  - Update expected dossiers in `expected-outputs/` with updated CMA CGM calculations.

---

## Checkpoint 4: Technical Documentation & CLI Authentication

- [x] **Update `README.md`**
  - Replace flat $350 mentions with the CMA CGM Indonesia tariff model.
  - State that when container size is omitted, the engine defaults to a 40ft Dry Standard container.
  - Attribute tariff schedule to WTO/UNCTAD ITC MAcMap dataset.
  - Update CLI automation examples to include `BOB_API_KEY="your_api_key_here" bob run --trust ...`.

- [x] **Update `docs/technical/mcp_setup.md`**
  - Document explicit `BOB_API_KEY` prefixing for terminal automation.

- [x] **Update `docs/technical/design_decisions.md`**
  - Document the rationale for adopting the CMA CGM Indonesia benchmark over arbitrary flat rates, the 40ft default, and the WTO/UNCTAD ITC MAcMap source.

- [x] **Update `docs/problem_solution.md`**
  - Refine Problem 2 and Solution Capability 2 to reflect progressive carrier day-slabs, 40ft default, and verified 546 permit count.

---

## Checkpoint 5: Business Canvas & Submission Deliverables

- [x] **Update `docs/submission/final_submission_form_answers.md`**
  - Update Indonesian submission answers with CMA CGM benchmark data, 40ft standard default, and realistic demurrage savings.

- [x] **Update `docs/business/pitch_deck_draft.md`**
  - Align Slide 2, Slide 3, and Slide 6 scripts with CMA CGM Indonesia tariff numbers, 40ft default, and WTO/UNCTAD ITC MAcMap source.

---

## Checkpoint 6: Unbacked Claims Audit (Resolved with Empirical Grounding)

All previously unbacked claims have been resolved and grounded in authoritative trade datasets and market intelligence reports:

1. - [x] **Restricted HS Code Count (`docs/problem_solution.md`)**:
   - Resolved with exact database ground truth: exactly 546 of 5,612 HS-6 subheadings (9.73%) require SDPPI, Kemenkes, or BPOM permits in our verified WTO/UNCTAD ITC MAcMap dataset.

2. - [x] **Market Sizing Figures (`docs/business/business_canvas.md`)**:
   - **TAM**: Grounded in ASEAN Freight Forwarding & Logistics Market valued at $31.62B USD in 2025 reaching $41.86B USD by 2031 (4.78% CAGR, Mordor Intelligence), with broader ASEAN logistics reaching $406.10B USD by 2031 (Research and Markets).
   - **SAM**: Grounded in Indonesia Customs Brokerage Market valued at $2.23B USD in 2025 reaching $3.32B USD by 2031 (6.83% CAGR, Mordor Intelligence), with ocean clearance holding 58.67% ($1.31B USD) and 3PL/forwarder-integrated brokers commanding 68.74% ($1.53B USD).
   - **SOM**: Grounded in the digital-first & API-based customs compliance segment in Indonesia, expanding at 15.34% CAGR through 2031 (Mordor Intelligence) to support mandatory CEISA 4.0 and INSW Single Submission, representing an immediate obtainable beachhead of $30M to $60M USD.

3. - [x] **Port Bottleneck & Detention Realities (`docs/business/pitch_deck_draft.md` & `docs/problem_solution.md`)**:
   - Grounded in Tanjung Priok gateway metrics (8.30M TEUs annually) and appointment slot dwell times (7 to 10 days for unbooked or document-flagged containers, Mordor Intelligence).
   - Detention financial exposure grounded in official CMA CGM Indonesia published tariff schedules ($101/day for 40ft standard dry containers in days 6 to 10).

---

### Grounding Principles & Source Citations

- **Container Default**: Explicitly documented that when container size is omitted, the engine defaults to a 40ft Standard Dry container (the international ocean freight workhorse).
- **Tariff Database Origin**: 5,612 Indonesian HS-6 subheadings originate from the official Market Access Map (MAcMap) dataset managed by the International Trade Centre (ITC), a joint agency of the World Trade Organization (WTO) and United Nations (UNCTAD), rather than inaccessible domestic BTKI portals.
- **Market Research Citations**:
  - Mordor Intelligence, "Indonesia Customs Brokerage Market Size & Share Analysis (2026-2031)", 2026.
  - Mordor Intelligence, "ASEAN Freight Forwarding Market Analysis (2026-2031)", 2026.
  - MetaStat Insight, "ASEAN Freight Forwarding Market (2026-2033)", 2026.
  - Research and Markets, "ASEAN Freight and Logistics Market Share Analysis (2026-2031)", Report ID 5759301, 2026.
