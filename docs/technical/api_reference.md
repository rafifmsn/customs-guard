# CustomsGuard API & MCP Reference

CustomsGuard exposes two complementary programmatic integration channels:

1. **Langflow Execution & MCP Server (`:7860`)**: Direct access to the autonomous `customsguard` agent workflow and the `CustomsGuard Bot` regulatory assistant via the Model Context Protocol (MCP) and Langflow REST endpoints.
2. **FastAPI Deterministic Gateway (`:8000`)**: Sub-50ms deterministic vector auditing, progressive CMA CGM demurrage modeling, and compliance dossier archiving.

## Part I: Langflow Execution & MCP Endpoints (`:7860`)

The core `customsguard` compliance flow and `CustomsGuard Bot` assistant flow run directly inside the Langflow engine and can be invoked independently of the FastAPI gateway.

- **Local Base URL**: `http://localhost:7860`
- **Authentication Header**: `x-api-key: <YOUR_LANGFLOW_API_KEY>`
- **Primary Audit Flow ID (`customsguard`)**: `d79a75e5-63f9-4da4-ac36-9c7d7d1b9e1b`
- **Regulatory Assistant Flow ID (`CustomsGuard Bot`)**: `5ca6e9b6-937c-4ab3-a95e-f4d3a5ff9818`

### 1. Model Context Protocol (MCP) Streamable Server

Expose the `customsguard` workflow directly to MCP-compliant hosts such as IBM Bob Desktop, IBM Bob CLI, or Claude Desktop.

- **Endpoint**: `http://localhost:7860/api/v1/mcp/project/{project_id}/streamable`
- **Transport**: `streamablehttp`
- **Tool Exposed**: `customsguard`
- **Input Parameters**:
  - `input_value` (string, required): Raw invoice JSON string or natural language trade audit instruction.
  - `session_id` (string, optional): Session identifier to persist multi-turn audit context.

#### Example MCP Client Configuration (`.bob/mcp.json`)

```json
{
  "mcpServers": {
    "lf-ibmsb": {
      "command": "uvx",
      "args": [
        "--with",
        "mcp<2.0.0",
        "mcp-proxy",
        "--transport",
        "streamablehttp",
        "--headers",
        "x-api-key",
        "YOUR_LANGFLOW_API_KEY",
        "http://localhost:7860/api/v1/mcp/project/PROJECT_ID/streamable"
      ]
    }
  }
}
```

### 2. Langflow v2 Workflow Execution API

Execute the primary `customsguard` flow or the `CustomsGuard Bot` assistant flow via Langflow's v2 workflow endpoint.

- **Endpoint**: `POST /api/v2/workflows`
- **Headers**:
  - `Content-Type: application/json`
  - `x-api-key: <YOUR_LANGFLOW_API_KEY>`

#### Example Request

```bash
curl -X POST "http://localhost:7860/api/v2/workflows" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGFLOW_API_KEY" \
  -d '{
    "flow_id": "d79a75e5-63f9-4da4-ac36-9c7d7d1b9e1b",
    "input_value": "Audit shipment SHP-2026-0042 for tariff discrepancies and Lartas permits."
  }'
```

#### Example Response

```json
{
  "flow_id": "d79a75e5-63f9-4da4-ac36-9c7d7d1b9e1b",
  "output": {
    "text": "### Executive Compliance Audit Summary\n- **Shipment ID**: SHP-2026-0042\n- **Verdict**: NON-COMPLIANT (HIGH RISK)\n- **Matched HS**: 8517.11 (Mandatory SDPPI Kemkominfo Permit Required)"
  }
}
```

### 3. Langflow v1 Run API (Chat & Multi-Turn Sessions)

Invoke either flow using the standard Langflow v1 run endpoint with session state persistence.

- **Endpoint**: `POST /api/v1/run/{flow_id}`
- **Headers**:
  - `Content-Type: application/json`
  - `x-api-key: <YOUR_LANGFLOW_API_KEY>`

#### Example Request (`customsguard` Audit Flow)

```bash
curl -X POST "http://localhost:7860/api/v1/run/d79a75e5-63f9-4da4-ac36-9c7d7d1b9e1b" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGFLOW_API_KEY" \
  -d '{
    "input_value": "{\"shipment_id\": \"SHP-2026-0042\", \"importer_name\": \"PT Nexus Indo Tech\", \"container_count\": 4, \"items\": [{\"item_id\": 1, \"declared_description\": \"Apple iPhone 15 Pro Max 256GB\", \"declared_hs\": \"8471.30\", \"declared_duty\": 0.0, \"total_value\": 115000.0}]}",
    "input_type": "chat",
    "output_type": "chat",
    "session_id": "audit-session-0042"
  }'
```

#### Example Request (`CustomsGuard Bot` Regulatory Assistant Flow)

```bash
curl -X POST "http://localhost:7860/api/v1/run/5ca6e9b6-937c-4ab3-a95e-f4d3a5ff9818" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGFLOW_API_KEY" \
  -d '{
    "input_value": "What Lartas permits are required for importing diagnostic medical imaging apparatus under HS 9018.12?",
    "input_type": "chat",
    "output_type": "chat",
    "session_id": "assistant-session-01"
  }'
```

#### Example v1 Run Response Structure

```json
{
  "session_id": "assistant-session-01",
  "outputs": [
    {
      "inputs": {
        "input_value": "What Lartas permits are required for importing diagnostic medical imaging apparatus under HS 9018.12?"
      },
      "outputs": [
        {
          "results": {
            "message": {
              "text": "Importing ultrasonic diagnostic scanners under HS 9018.12 requires a Kemenkes RI Medical Device Distribution License (Izin Edar Alat Kesehatan) prior to customs clearance."
            }
          }
        }
      ]
    }
  ]
}
```

## Part II: FastAPI Deterministic Gateway Endpoints (`:8000`)

The FastAPI controller provides high-speed deterministic auditing for the Streamlit operator dashboard and enterprise webhook integrations, while orchestrating Langflow synthesis with automatic local fallback.

- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 1. System Health Check

Inspect the connectivity and readiness of the internal container stack.

- **Endpoint**: `GET /api/v1/health`
- **Authentication**: None required for local perimeter services.

#### Example Request

```bash
curl -X GET http://localhost:8000/api/v1/health
```

#### Example Response

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

### 2. Autonomous Compliance Audit

Audit an incoming commercial shipping manifest against 5,612 Indonesian HS-6 subheadings, mandatory ministry permits, and CMA CGM demurrage schedules.

- **Endpoint**: `POST /api/v1/audit`
- **Content-Type**: `application/json`

#### Request Parameters

| Parameter             | Type    | Required | Description                                                          |
| :-------------------- | :------ | :------- | :------------------------------------------------------------------- |
| `shipment_id`         | string  | Yes      | Unique shipping consignment identifier (e.g., `SHP-2026-0042`).      |
| `invoice_number`      | string  | Yes      | Commercial invoice reference number.                                 |
| `importer_name`       | string  | Yes      | Declared importer of record or PPJK broker name.                     |
| `carrier`             | string  | No       | Ocean carrier benchmark (defaults to `CMA CGM`).                     |
| `destination_port`    | string  | No       | Indonesian port of discharge (defaults to `Tanjung Priok, Jakarta`). |
| `container_count`     | integer | No       | Total containers in shipment (defaults to `1`).                      |
| `container_size`      | string  | No       | Equipment size: `20`, `40`, or `45` (defaults to `40`).              |
| `container_type`      | string  | No       | Equipment classification: `DRY` or `REEFER` (defaults to `DRY`).     |
| `days_held_projected` | integer | No       | Projected duration held at port (defaults to `10`).                  |
| `items`               | array   | Yes      | Array of commodity items declared on the manifest.                   |

#### Example Request Body

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

#### Example Response Body

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
      "required_permits": ["SDPPI Type Approval Certification (Kemkominfo)"]
    }
  ],
  "dossier_path": "/app/data/reports/SHP-2026-0042_audit.md",
  "alert_status": "DISPATCHED_TO_MAILPIT"
}
```

### 3. Compliance Dossier Archive

Retrieve a list of archived compliance reports and audit summaries saved to local disk.

- **Endpoint**: `GET /api/v1/reports`
- **Query Parameters**:
  - `limit` (integer, optional, default: 20): Maximum number of records to return.

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/reports?limit=10"
```

#### Example Response

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

### 4. Regulatory Knowledge Assistant

Query Indonesian import regulations, Lartas permit schedules, or carrier tariff rules using bounded natural language intelligence.

- **Endpoint**: `POST /api/v1/assistant`
- **Content-Type**: `application/json`

#### Example Request Body

```json
{
  "prompt": "What permits are mandatory for importing ultrasonic diagnostic scanners under HS 9018.12?",
  "session_id": "sess-compliance-01"
}
```

#### Example Response Body

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

## Error Handling

Standard HTTP status codes are returned across both FastAPI and Langflow endpoints:

- `200 OK`: Request succeeded.
- `400 Bad Request`: Invalid payload parameters or malformed JSON structure.
- `401 Unauthorized` / `403 Forbidden`: Missing or invalid `x-api-key` header on protected Langflow endpoints.
- `422 Unprocessable Entity`: Schema validation failure.
- `500 Internal Server Error`: Internal exception during database retrieval or tool execution.
