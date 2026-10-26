# Multimodal Document Ingestion Specification

This specification outlines the implementation plan for adding PDF and Image commercial invoice ingestion to CustomsGuard.
Future agents implementing this feature should follow this document to ensure clean architectural alignment without overengineering.

## 1. Objective and Scope

### Goal
Enable customs brokers and evaluators to upload commercial invoices in PDF or image format (.png, .jpg, .jpeg) in addition to raw JSON.
The ingestion pipeline converts the document into a validated `InvoicePayload` JSON object that seamlessly populates the existing audit engine and Streamlit workspace.

### Pragmatic Philosophy (Anti-Overengineering)
* Keep the scope focused strictly on the core hackathon value proposition.
* If extraction succeeds: return the validated `InvoicePayload` JSON and display line items in `st.data_editor` for quick human review.
* If extraction fails or data is insufficient: return a straightforward error status (e.g., `status: "failed", error: "Unable to extract required invoice line items from document"`).
* Avoid building complex intermediate state machines, OCR confidence threshold sliders, or dozens of edge-case recovery screens.

## 2. System Architecture & Flow

Consolidate all document processing through FastAPI to preserve a single point of logging, monitoring, and tracing.

```text
[Streamlit UI / User Upload]
  (.pdf, .png, .jpg, .jpeg, or .json)
              │
              ▼ (Multipart HTTP POST)
[FastAPI: POST /api/v1/ingest/document]
              │
              ├─► PDF to Image Conversion (if PDF)
              │
              ▼ (Image Bytes / Base64 Payload)
[Langflow Document Extraction Flow (or Vision LLM)]
              │
              ▼ (Raw JSON String)
[Pydantic Validation (InvoicePayload)]
              │
              ▼ (JSON Response)
[Streamlit st.data_editor & Audit Workspace]
```

## 3. Data Contracts

The extraction output must adhere strictly to the existing schema defined in `api/schemas.py`.

### Target Output Contract
```json
{
  "shipment_id": "SHP-EXTRACTED-001",
  "invoice_number": "INV-2026-9921",
  "carrier": "CMA CGM",
  "importer_name": "PT Example Importir",
  "exporter_name": "Global Shipper Corp",
  "country_of_origin": "CN",
  "destination_port": "Tanjung Priok, Jakarta (IDTPP)",
  "container_count": 1,
  "container_size": "40",
  "container_type": "DRY",
  "days_held_projected": 10,
  "currency": "USD",
  "items": [
    {
      "item_id": 1,
      "declared_description": "Commodity description extracted from document",
      "declared_hs_code": "8517.13",
      "quantity": 100,
      "unit_price": 500.0,
      "total_value": 50000.0,
      "declared_duty_rate": 0.0
    }
  ]
}
```

### Fallback Defaults
If non-critical invoice metadata is missing from the document:
* `carrier`: Default to `"CMA CGM"`.
* `container_size`: Default to `"40"`.
* `container_type`: Default to `"DRY"`.
* `days_held_projected`: Default to `10`.
* `destination_port`: Default to `"Tanjung Priok, Jakarta (IDTPP)"`.

## 4. Implementation Phases

### Phase 1: Tooling and Dependencies
1. Add lightweight PDF rendering support to `pyproject.toml` (e.g., `pypdfium2` or `pymupdf`).
2. Avoid heavy OCR system packages like Tesseract or Unstructured unless absolutely necessary, as they increase container memory usage.
3. Test PDF page rendering to standard RGB image bytes in memory.

### Phase 2: FastAPI Ingestion Endpoint
1. Add `POST /api/v1/ingest/document` in `api/main.py` accepting `UploadFile = File(...)`.
2. Inspect file extension / MIME type:
   * If `.json`: parse directly with `json.load`.
   * If `.pdf`: convert first page (or top pages) to image.
   * If `.png`, `.jpg`, `.jpeg`: read image bytes directly.
3. Call the extraction engine (Langflow extraction flow or direct multimodal model).
4. Parse and validate the response against `InvoicePayload.model_validate(raw_dict)`.
5. Return standardized `IngestionResponse` containing `status`, `invoice_data`, and optional `error_message`.

### Phase 3: Streamlit UI Integration
1. Update `st.file_uploader` in `ui/app.py` to accept `type=["json", "pdf", "png", "jpg", "jpeg"]`.
2. When a file is uploaded:
   * Display a status spinner (`"Extracting invoice line items from document..."`).
   * Send the file to `POST /api/v1/ingest/document` via `api_request`.
   * If successful: set `st.session_state["active_invoice"] = response["invoice_data"]` and display a success toast.
   * If failed: display `st.error(response["error_message"])` without breaking the UI.
3. The extracted line items automatically populate the existing `st.data_editor` table for manual review.

### Phase 4: Test Suite Verification
1. Create unit and integration tests in `tests/test_document_ingestion.py`.
2. Verify JSON file upload backward compatibility.
3. Verify image and PDF parsing mock scenarios.
4. Verify graceful error handling when an empty or corrupted file is submitted.
5. Run full test suite using host `~/.local/bin/uv run pytest -v`.

## 5. Non-Negotiable Invariants
1. Zero CSS Bloat: Do not introduce raw `<style>` blocks in Streamlit. Use native Streamlit primitives (`st.file_uploader`, `st.status`, `st.error`).
2. Backward Compatibility: Raw JSON upload and existing preset scenario pills must remain 100% operational.
3. Host Test Standard: All automated tests must run from host root using `~/.local/bin/uv run pytest -v`.
4. No Em Dashes: Never use em dashes or en dashes in any documentation or code comments.

