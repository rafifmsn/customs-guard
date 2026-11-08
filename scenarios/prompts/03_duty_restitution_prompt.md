# Prompt: Tariff Overpayment Restitution Recovery

Use this prompt to test duty overpayment detection and restitution advisory (Feature C).
When an importer over-declares tariff rates compared to the official customs schedule, CustomsGuard calculates potential duty refund savings.

```text
Audit shipment SHP-2026-0099 where the importer over-declared import duty.
Verify if the official tariff rate is lower than declared, ensure zero duty shortfall is assessed, and calculate potential customs duty refund restitution:

{
  "shipment_id": "SHP-2026-0099",
  "invoice_number": "INV-2026-SRV-990",
  "carrier": "CMA CGM",
  "importer_name": "PT Cloud Data Raya",
  "country_of_origin": "US",
  "destination_port": "Tanjung Priok, Jakarta (IDTPP)",
  "container_count": 1,
  "container_size": "40",
  "container_type": "DRY",
  "days_held_projected": 5,
  "currency": "USD",
  "items": [
    {
      "item_id": 1,
      "declared_description": "Enterprise Processing Server Rack Unit",
      "declared_hs_code": "8471.50",
      "quantity": 10,
      "unit_price": 10000.0,
      "total_value": 100000.0,
      "declared_duty_rate": 15.0
    }
  ]
}
```
