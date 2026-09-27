# Prompt: Fully Compliant Trade Declaration

Use this prompt to audit a standard, fully compliant commercial invoice where the declared HS code and tariff rate perfectly match the official schedule.

```text
Audit shipment SHP-2026-0105 for enterprise computing equipment.
Confirm that declared classification matches official schedules, verify zero duty shortfall, and confirm no port detention risks:

{
  "shipment_id": "SHP-2026-0105",
  "importer_name": "PT Cloud Infrastruktur Indonesia",
  "country_of_origin": "SG",
  "destination_port": "Tanjung Priok, Jakarta (IDTPP)",
  "container_count": 2,
  "items": [
    {
      "item_id": 1,
      "declared_description": "Enterprise Processing Server Rack Unit",
      "declared_hs_code": "8471.50",
      "quantity": 10,
      "unit_price": 4500.0,
      "total_value": 45000.0,
      "declared_duty_rate": 0.0
    }
  ]
}
```
