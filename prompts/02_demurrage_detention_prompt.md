# Prompt: Multi-Container Scaled Demurrage Liability

Use this prompt to test multi-container demurrage penalty scaling (Feature B).
When a multi-container consignment faces customs detention, daily port holding fees accumulate per container ($350.00/day \* container count).

```text
Audit shipment SHP-2026-0089 covering 3 shipping containers.
Evaluate whether restricted medical diagnostic equipment triggers container detention, calculate the total daily demurrage exposure across all 3 containers, and export the audit report:

{
  "shipment_id": "SHP-2026-0089",
  "importer_name": "PT Medika Nusantara Sejahtera",
  "country_of_origin": "DE",
  "destination_port": "Tanjung Perak, Surabaya (IDTPS)",
  "container_count": 3,
  "items": [
    {
      "item_id": 1,
      "declared_description": "Siemens Acuson Ultrasound Diagnostic Scanner",
      "declared_hs_code": "8471.50",
      "quantity": 5,
      "unit_price": 25000.0,
      "total_value": 125000.0,
      "declared_duty_rate": 0.0
    }
  ]
}
```
