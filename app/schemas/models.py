from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import (
    ActionStatus,
    AnalysisDepth,
    Department,
    DocumentType,
    Effort,
    EvidenceType,
    OrganizationType,
)


class ForbiddenExtraModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompanyCreate(ForbiddenExtraModel):
    company_name: str
    organization_type: OrganizationType
    business_model: str | None = None
    operating_regions: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)
    regulatory_entities: list[str] = Field(default_factory=list)
    uses_customer_data: bool | None = None
    uses_automated_decisioning: bool | None = None
    has_outsourced_operations: bool | None = None
    existing_policies: list[str] = Field(default_factory=list)
    internal_controls: list[str] = Field(default_factory=list)

    @field_validator("company_name")
    @classmethod
    def company_name_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("company_name is required")
        return cleaned


class CompanyUpdate(ForbiddenExtraModel):
    company_name: str | None = None
    organization_type: OrganizationType | None = None
    business_model: str | None = None
    operating_regions: list[str] | None = None
    products: list[str] | None = None
    customer_segments: list[str] | None = None
    regulatory_entities: list[str] | None = None
    uses_customer_data: bool | None = None
    uses_automated_decisioning: bool | None = None
    has_outsourced_operations: bool | None = None
    existing_policies: list[str] | None = None
    internal_controls: list[str] | None = None

    @field_validator("company_name")
    @classmethod
    def company_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("company_name is required")
        return cleaned


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    organization_type: OrganizationType
    business_model: str | None
    operating_regions: list[str]
    products: list[str]
    customer_segments: list[str]
    regulatory_entities: list[str]
    uses_customer_data: bool | None
    uses_automated_decisioning: bool | None
    has_outsourced_operations: bool | None
    existing_policies: list[str]
    internal_controls: list[str]
    created_at: datetime
    updated_at: datetime


class RegulationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    regulator: str
    document_type: DocumentType
    reference_number: str | None
    publication_date: date | None
    effective_date: date | None
    source_url: str | None
    s3_key: str
    content_hash: str
    pages: int | None
    processing_status: str
    jurisdiction: str | None = None
    regulatory_domain: str | None = None
    applicable_entity_types: list[str] | None = None
    lifecycle_status: str = "active"
    version_label: str | None = None
    corpus_key: str | None = None
    source_kind: str = "uploaded"
    created_at: datetime


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    title: str
    evidence_type: EvidenceType
    version_label: str | None
    effective_date: date | None
    owner_department: Department | None
    approved_by: str | None
    s3_key: str
    content_hash: str
    processing_status: str
    created_at: datetime


class AnalysisCreate(ForbiddenExtraModel):
    company_id: UUID
    regulation_id: UUID
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    include_gap_analysis: bool = True
    include_action_plan: bool = True


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    regulation_id: UUID
    status: str
    applicability: str | None
    overall_risk: str | None
    result: dict[str, Any] | None
    confidence: float | None
    human_review_required: bool
    analysis_depth: AnalysisDepth
    include_gap_analysis: bool
    include_action_plan: bool
    created_at: datetime
    completed_at: datetime | None
    review_status: str | None = None
    regulation_title: str | None = None


class AnalysisStatusRead(BaseModel):
    id: UUID
    status: str
    step: str | None
    human_review_required: bool
    review_status: str | None = None


class GapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requirement_id: UUID
    company_id: UUID
    gap_status: str
    severity: str
    explanation: str | None
    evidence_chunk_ids: list[UUID] | None
    created_at: datetime


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID
    gap_id: UUID | None
    company_id: UUID
    title: str
    description: str | None
    owner_department: Department | None
    status: ActionStatus
    effort: Effort | None
    created_at: datetime
    updated_at: datetime


class ActionUpdate(ForbiddenExtraModel):
    status: ActionStatus | None = None
    owner_department: Department | None = None


class CitationRead(BaseModel):
    id: UUID
    analysis_id: UUID
    chunk_id: UUID
    claim_text: str
    excerpt: str
    from_ocr: bool
    relevance_verified: bool | None
    page_start: int
    page_end: int
    clause_number: str | None
    section_title: str | None


class SourceLinkRead(BaseModel):
    citation_id: UUID
    url: str
    expires_in_seconds: int


class ReviewDecision(ForbiddenExtraModel):
    comment: str | None = None


class ApplicabilityRead(BaseModel):
    id: UUID
    regulation_id: UUID
    title: str
    regulator: str
    document_type: str
    regulatory_domain: str | None
    source_url: str | None
    lifecycle_status: str
    applicability: str
    reason: str
    matched_characteristics: list[str]
    rule_id: str | None
    human_review_required: bool
    processing_status: str
    reviewer_applicability: str | None = None


class ApplicabilityDecisionWrite(ForbiddenExtraModel):
    applicability: str


class RequirementChangeRead(BaseModel):
    id: UUID
    kind: str
    clause_number: str | None
    previous_text: str | None
    new_text: str | None


class RegulatoryChangeRead(BaseModel):
    id: UUID
    corpus_key: str
    change_kind: str
    summary: str
    title: str
    source_url: str | None
    previous_document_id: UUID | None
    new_document_id: UUID
    created_at: datetime
    requirement_changes: list[RequirementChangeRead]


class PortfolioRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    status: str
    overall_risk: str | None
    human_review_required: bool
    result: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


class DashboardRead(BaseModel):
    applicable: int
    requirements_assessed: int
    fully_evidenced: int
    partially_evidenced: int
    gaps: int
    high_risk_gaps: int
    human_review_required: int
    overall_risk: str | None
    corpus_documents: int
    latest_change_summary: str | None
    assessment_confidence: dict[str, Any]
    portfolio_run_id: UUID | None
    analysis_id: UUID | None
    analysis_ids: list[UUID] = Field(default_factory=list)
    ingest_status: str | None
