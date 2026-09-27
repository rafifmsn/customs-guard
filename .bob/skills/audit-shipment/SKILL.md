---
name: audit-shipment
description: Audit commercial shipping invoices against Indonesian customs tariffs and import regulations.
---

# Audit Shipment Skill

Use this skill to audit commercial shipping manifests, detect HS code misclassifications, calculate duty shortfalls and restitution opportunities, and evaluate container detention risks.

## Usage

```text
$audit-shipment <shipment_id_or_invoice_json>
```

Examples:

- `$audit-shipment SHP-2026-0042`
- `$audit-shipment SHP-2026-0089`
- `$audit-shipment SHP-2026-0105`
- `$audit-shipment {"shipment_id": "SHP-CUSTOM", "items": [...]}`

## Execution Workflow

1. **Input Resolution**:
   If the user provides a shipment identifier (e.g., `SHP-2026-0042`), retrieve the corresponding invoice payload from `data/seed/sample_invoices.json`.
   If the user provides a raw JSON invoice, validate that it contains `shipment_id` and an `items` list.

2. **Invoke CustomsGuard Tool**:
   Call the `customsguard` MCP tool, passing the serialized invoice JSON string in `input_value`.

3. **Format Executive Audit Summary**:
   Present the audit verdict using this standard structure:
   - **Verdict Badge**: `COMPLIANT`, `WARNING_DISCREPANCY`, or `NON_COMPLIANT_HIGH_RISK`.
   - **Financial Breakdown**:
     - Total Declared Value (USD).
     - Net Duty Shortfall (USD).
     - Duty Overpayment Restitution Savings (if applicable).
     - Estimated Daily Demurrage Risk ($350.00/day \* container count).
   - **Discrepancy Details**:
     - Item-by-item comparison showing Declared HS vs Matched HS.
     - Declared Duty Rate vs Official Tariff Rate.
     - Missing mandatory regulatory licenses (SDPPI, Kemenkes, BPOM).
   - **Evidence Verification**:
     - Confirm that the Markdown and JSON audit reports are written to `./data/reports/YYYY-MM-DD/{shipment_id}/`.
     - Confirm alert delivery in Mailpit (`http://localhost:8025`).
