# Prompt: High-Risk Tariff Misclassification & Permit Evasion

Use this prompt to audit an invoice where high-value electronics are declared under a duty-free laptop classification to evade both customs duty and mandatory telecommunication certification.

```text
Audit the following commercial invoice for shipment SHP-2026-0042.
Detect HS code misclassifications, verify whether mandatory SDPPI import permits are required, calculate the duty shortfall, and report container detention risks:

{
  "shipment_id": "SHP-2026-0042",
  "invoice_number": "INV-2026-APL-091",
  "carrier": "CMA CGM / APL",
  "importer_name": "PT Nexus Indo Tech",
  "exporter_name": "Shenzhen Global Electronics Ltd",
  "country_of_origin": "CN",
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
      "declared_duty_rate": 0.0
    }
  ]
}
```
