# CustomsGuard REST API Reference

The CustomsGuard REST API provides programmatic endpoints for automated trade compliance audits, progressive demurrage calculation, and regulatory knowledge retrieval.
All endpoints are served from the centralized FastAPI gateway running on port 8000.

## Base URL & Interactive Documentation

- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## 1. System Health Check

Inspect the connectivity and readiness of the internal container stack.

- **Endpoint**: `GET /api/v1/health`
- **Authentication**: None required for local perimeter services.

### Example Request

```bash
curl -X GET http://localhost:8000/api/v1/health
```

### Example Response

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-10-23T22:00:00Z",
  "services": {
    "api": { "status": "online", "port": 8000 },
    "qdrant": { "status": "online", "port": 6333, "points_count": 5612 },
    "langflow": { "status": "online", "port": 7860 },
    "mailpit": { "status": "online", "port": 1025 },
    "postgres": { "status": "online", "port": 5432 }
  }
}
```

---

## 2. Autonomous Compliance Audit

Audit an incoming commercial shipping manifest against 5,612 Indonesian HS-6 subheadings, mandatory ministry permits, and CMA CGM demurrage schedules.

- **Endpoint**: `POST /api/v1/audit`
- **Content-Type**: `application/json`

### Request Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `shipment_id` | string | Yes | Unique shipping consignment identifier (e.g., `SHP-2026-0042`). |
| `invoice_number` | string | Yes | Commercial invoice reference number. |
| `importer_name` | string | Yes | Declared importer of record or PPJK broker name. |
| `carrier` | string | No | Ocean carrier benchmark (defaults to `CMA CGM`). |
| `destination_port` | string | No | Indonesian port of discharge (defaults to `Tanjung Priok, Jakarta`). |
| `container_count` | integer | No | Total containers in shipment (defaults to `1`). |
| `container_size` | string | No | Equipment size: `20`, `40`, or `45` (defaults to `40`). |
| `container_type` | string | No | Equipment classification: `DRY` or `REEFER` (defaults to `DRY`). |
| `days_held_projected` | integer | No | Projected duration held at port (defaults to `10`). |
| `items` | array | Yes | Array of commodity items declared on the manifest. |

### Example Request Body

```json
{
  "shipment_id": "SHP-2026-0042",
  "invoice_number": "INV-2026-APL-091",
  "importer_name": "PT Nexus Indo Tech",
  "carrier": "CMA CGM",
  "destination_port": "Tanjung Priok, Jakarta",
  "container_count": 4,
  "container_size": "40",
  "container_type": "DRY",
  "days_held_projected": 10,
  "items": [
    {
      "item_id": 1,
      "declared_description": "Apple iPhone 15 Pro Max 256GB Dual SIM Smartphone",
      "declared_hs": "8471.30",
      "declared_duty": 0.0,
      "total_value": 115000.0
    }
  ]
}
```

### Example Response Body

```json
{
  "shipment_id": "SHP-2026-0042",
  "verdict": "NON_COMPLIANT_HIGH_RISK",
  "container_detention_risk": true,
  "financial_impact": {
    "duty_shortfall_usd": 0.0,
    "duty_restitution_usd": 0.0,
    "statutory_penalty_range": "100% - 1000% under Article 82(5)"
  },
  "demurrage_assessment": {
    "benchmark_carrier": "CMA CGM Indonesia (Merged Import D&D, July 1, 2026)",
    "container_count": 4,
    "container_size": "40",
    "container_type": "DRY",
    "free_days_allowed": 5,
    "detention_days": 5,
    "applicable_slab": "Days 6 to 10 ($120.00/day/cntr)",
    "daily_burn_rate_usd": 480.0,
    "projected_cumulative_liability_usd": 2400.0
  },
  "findings": [
    {
      "item_id": 1,
      "declared_description": "Apple iPhone 15 Pro Max 256GB Dual SIM Smartphone",
      "declared_hs": "8471.30",
      "matched_hs": "8517.11",
      "declared_duty": 0.0,
      "official_duty": 0.0,
      "restricted": true,
      "required_permits": [
        "SDPPI Type Approval Certification (Kemkominfo)"
      ]
    }
  ],
  "dossier_path": "/app/data/reports/SHP-2026-0042_audit.md",
  "alert_status": "DISPATCHED_TO_MAILPIT"
}
```

---

## 3. Compliance Dossier Archive

Retrieve a list of archived compliance reports and audit summaries saved to local disk.

- **Endpoint**: `GET /api/v1/reports`
- **Query Parameters**:
  - `limit` (integer, optional, default: 20): Maximum number of records to return.

### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/reports?limit=10"
```

### Example Response

```json
[
  {
    "shipment_id": "SHP-2026-0042",
    "importer_name": "PT Nexus Indo Tech",
    "verdict": "NON_COMPLIANT_HIGH_RISK",
    "duty_shortfall_usd": 0.0,
    "estimated_demurrage_per_day_usd": 480.0,
    "report_path": "/app/data/reports/SHP-2026-0042_audit.md",
    "created_at": "2026-10-23T20:15:00Z"
  }
]
```

---

## 4. Regulatory Knowledge Assistant

Query Indonesian import regulations, Lartas permit schedules, or carrier tariff rules using bounded natural language intelligence.

- **Endpoint**: `POST /api/v1/assistant`
- **Content-Type**: `application/json`

### Example Request Body

```json
{
  "prompt": "What permits are mandatory for importing ultrasonic diagnostic scanners under HS 9018.12?",
  "session_id": "sess-compliance-01"
}
```

### Example Response Body

```json
{
  "response": "Under Indonesian customs tariff schedule for HS 9018.12, ultrasonic diagnostic scanners require an official Distribution License (Izin Edar Alat Kesehatan) issued by Kemenkes RI prior to customs clearance.",
  "confidence": 0.96,
  "sources": [
    "WTO/UNCTAD ITC Market Access Map (Indonesia HS-6)",
    "Kemenkes Import Regulatory Permit Schedule"
  ],
  "backend_used": "langflow_agent"
}
```

---

## Error Handling

Standard HTTP status codes are returned for all requests:

- `200 OK`: Request succeeded.
- `400 Bad Request`: Invalid payload parameters or malformed JSON structure.
- `422 Unprocessable Entity`: Schema validation failure.
- `500 Internal Server Error`: Internal exception during database retrieval or tool execution.
