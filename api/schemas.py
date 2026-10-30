"""Strict Pydantic data contracts for the CustomsGuard REST API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class InvoiceItem(BaseModel):
    item_id: int = Field(default=1, description="Sequential line item identifier.")
    declared_description: str = Field(
        ...,
        description="Commercial description of the imported commodity.",
        examples=["Apple iPhone 15 Pro Max 256GB Dual SIM Smartphone"],
    )
    declared_hs_code: str = Field(
        ...,
        description="6-digit Harmonized System code declared by the importer.",
        examples=["8471.30"],
    )
    quantity: int = Field(default=1, ge=1, description="Unit quantity imported.")
    unit_price: float = Field(default=0.0, ge=0.0, description="Declared unit value in USD.")
    total_value: float = Field(
        ...,
        ge=0.0,
        description="Total declared commercial value in USD for this line item.",
        examples=[115000.0],
    )
    declared_duty_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Declared import tariff percentage (e.g., 0.0, 5.0, 15.0).",
        examples=[0.0],
    )


class InvoicePayload(BaseModel):
    shipment_id: str = Field(
        default="SHP-2026-0042",
        description="Unique customs manifest or shipment reference ID.",
    )
    invoice_number: Optional[str] = Field(
        default="INV-2026-001",
        description="Commercial invoice number.",
    )
    carrier: str = Field(
        default="CMA CGM",
        description="Ocean carrier benchmark (defaults to CMA CGM).",
    )
    importer_name: str = Field(
        default="UNSPECIFIED",
        description="Registered Indonesian importing entity.",
    )
    exporter_name: Optional[str] = Field(
        default="UNSPECIFIED",
        description="Foreign exporting entity.",
    )
    country_of_origin: Optional[str] = Field(
        default="UNSPECIFIED",
        description="ISO 2-letter country of origin code.",
    )
    destination_port: str = Field(
        default="Tanjung Priok, Jakarta (IDTPP)",
        description="Indonesian port of entry.",
    )
    container_count: int = Field(
        default=1,
        ge=1,
        description="Number of shipping containers in the consignment.",
    )
    container_size: str = Field(
        default="40",
        description="Equipment container length in feet ('20', '40', or '45'). Defaults to '40'.",
    )
    container_type: str = Field(
        default="DRY",
        description="Equipment container type ('DRY' or 'REEFER'). Defaults to 'DRY'.",
    )
    days_held_projected: int = Field(
        default=10,
        ge=1,
        description="Projected total days in port/detention if held.",
    )
    currency: str = Field(default="USD", description="Invoice currency code.")
    items: List[InvoiceItem] = Field(
        default_factory=list,
        description="List of declared commodity line items.",
    )
    notes: Optional[str] = Field(default=None, description="Optional shipment notes.")
    include_narrative: bool = Field(
        default=False,
        description="Whether to request an additional LLM executive narrative from Langflow.",
    )


class DemurrageAssessment(BaseModel):
    benchmark_carrier: str
    container_size: str
    container_type: str
    container_count: int
    free_days_allowed: int
    days_projected: int
    detention_days: int
    daily_rate_per_container_usd: float
    daily_burn_rate_total_usd: float
    projected_cumulative_liability_usd: float
    applicable_slab: str
    carrier_policy_notes: str


class FindingItem(BaseModel):
    item_id: int
    declared_description: str
    declared_hs: str
    matched_hs: str
    declared_duty: float
    official_duty: float
    duty_shortfall_usd: float
    restitution_usd: float = 0.0
    restricted: bool
    required_permits: List[str]


class AuditResult(BaseModel):
    shipment_id: str
    importer: str
    carrier: str = "CMA CGM"
    destination_port: str = "Tanjung Priok, Jakarta (IDTPP)"
    container_count: int
    overall_status: str
    container_detention_risk: bool
    total_duty_shortfall_usd: float
    total_restitution_usd: float = 0.0
    estimated_demurrage_per_day_usd: float
    demurrage_assessment: DemurrageAssessment
    critical_notes: List[str]
    findings: List[FindingItem]
    tariff_schedule_version: Optional[str] = "BTKI-2022-v2026.1 (WTO/UNCTAD ITC MacMap)"
    tariff_effective_date: Optional[str] = "2026-07-01"
    carrier_tariff_schedule: Optional[str] = "CMA CGM Indonesia Merged Import D&D (Effective July 1, 2026)"


class AuditResponse(BaseModel):
    audit: AuditResult
    markdown_dossier: str
    report_path: str
    alert_status: str
    executive_narrative: str


class ReportItem(BaseModel):
    shipment_id: str
    date: str
    importer: str
    overall_status: str
    container_count: int = 1
    total_duty_shortfall_usd: float = 0.0
    total_restitution_usd: float = 0.0
    estimated_demurrage_per_day_usd: float = 0.0
    report_dir: str
    json_content: str
    markdown_content: str


class AssistantQuery(BaseModel):
    prompt: str = Field(
        ...,
        min_length=2,
        description="One-shot trade compliance or tariff regulatory question.",
        examples=[
            "What permits are required for importing cellular smartphones (HS 8517.11) into Indonesia?"
        ],
    )
    timeout_seconds: int = Field(
        default=240,
        ge=5,
        le=300,
        description="Hard execution timeout in seconds for the IBM Bob CLI subprocess (180s-300s recommended).",
    )


class AssistantResponse(BaseModel):
    status: str = Field(
        ...,
        description="Execution status ('success', 'fallback', 'timeout', 'busy', or 'error').",
    )
    engine: str = Field(
        ...,
        description="Execution channel that answered the query ('ibm-bob-cli' or 'local-tariff-rag-fallback').",
    )
    answer: str = Field(..., description="Formatted regulatory response.")
    duration_ms: int = Field(..., description="Total execution latency in milliseconds.")


class ServiceCheck(BaseModel):
    reachable: bool
    endpoint: str
    detail: str


class HealthStatus(BaseModel):
    status: str
    qdrant: ServiceCheck
    langflow: ServiceCheck
    mailpit: ServiceCheck


class IngestionResponse(BaseModel):
    status: str = Field(
        ...,
        description="Ingestion status ('complete', 'rejected', or 'failed').",
    )
    invoice_data: Optional[InvoicePayload] = Field(
        default=None,
        description="Validated InvoicePayload ready for audit workspace if extraction succeeded.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Descriptive reason why the document was rejected or failed parsing.",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of critical required fields missing from the document.",
    )
    filename: Optional[str] = Field(
        default=None,
        description="Original uploaded document filename.",
    )

