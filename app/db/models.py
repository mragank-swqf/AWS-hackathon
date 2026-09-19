from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("length(trim(company_name)) > 0", name="companies_name_not_empty"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    organization_type: Mapped[str] = mapped_column(Text, nullable=False)
    business_model: Mapped[str | None] = mapped_column(Text)
    operating_regions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    products: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    customer_segments: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    regulatory_entities: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    uses_customer_data: Mapped[bool | None] = mapped_column(Boolean)
    uses_automated_decisioning: Mapped[bool | None] = mapped_column(Boolean)
    has_outsourced_operations: Mapped[bool | None] = mapped_column(Boolean)
    existing_policies: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    internal_controls: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    policies: Mapped[list[CompanyPolicy]] = relationship(back_populates="company")
    analyses: Mapped[list[ImpactAnalysis]] = relationship(back_populates="company")


class RegulatoryDocument(Base):
    __tablename__ = "regulatory_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    regulator: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[str | None] = mapped_column(Text)
    publication_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    pages: Mapped[int | None] = mapped_column(Integer)
    processing_status: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(Text)
    regulatory_domain: Mapped[str | None] = mapped_column(Text)
    applicable_entity_types: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    lifecycle_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="active", server_default=text("'active'")
    )
    version_label: Mapped[str | None] = mapped_column(Text)
    corpus_key: Mapped[str | None] = mapped_column(Text)
    source_kind: Mapped[str] = mapped_column(
        Text, nullable=False, default="uploaded", server_default=text("'uploaded'")
    )
    supersedes_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id")
    )
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="regulatory_document")
    analyses: Mapped[list[ImpactAnalysis]] = relationship(back_populates="regulation")
    supersedes: Mapped[RegulatoryDocument | None] = relationship(
        remote_side="RegulatoryDocument.id",
        foreign_keys=[supersedes_document_id],
    )


class CompanyPolicy(Base):
    __tablename__ = "company_policies"
    __table_args__ = (UniqueConstraint("company_id", "content_hash", name="uq_policy_company_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(Text, nullable=False)
    version_label: Mapped[str | None] = mapped_column(Text)
    effective_date: Mapped[date | None] = mapped_column(Date)
    owner_department: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[str | None] = mapped_column(Text)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    processing_status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    company: Mapped[Company] = relationship(back_populates="policies")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="company_policy")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        CheckConstraint(
            "(regulatory_document_id IS NOT NULL) <> (company_policy_id IS NOT NULL)",
            name="chunk_has_exactly_one_source",
        ),
        CheckConstraint(
            "company_policy_id IS NULL OR company_id IS NOT NULL",
            name="company_chunk_is_tenant_scoped",
        ),
        CheckConstraint(
            "regulatory_document_id IS NULL OR company_id IS NULL",
            name="regulation_chunk_is_shared",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulatory_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id", ondelete="CASCADE")
    )
    company_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("company_policies.id", ondelete="CASCADE")
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str | None] = mapped_column(Text)
    clause_number: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    text_search: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', text)", persisted=True)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    regulatory_document: Mapped[RegulatoryDocument | None] = relationship(back_populates="chunks")
    company_policy: Mapped[CompanyPolicy | None] = relationship(back_populates="chunks")


class ImpactAnalysis(Base):
    __tablename__ = "impact_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id"), nullable=False
    )
    portfolio_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_runs.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    applicability: Mapped[str | None] = mapped_column(Text)
    overall_risk: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    analysis_depth: Mapped[str] = mapped_column(Text, nullable=False)
    include_gap_analysis: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    include_action_plan: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    company: Mapped[Company] = relationship(back_populates="analyses")
    regulation: Mapped[RegulatoryDocument] = relationship(back_populates="analyses")
    requirements: Mapped[list[RegulatoryRequirement]] = relationship(back_populates="analysis")
    citations: Mapped[list[Citation]] = relationship(back_populates="analysis")
    review: Mapped[Review | None] = relationship(back_populates="analysis")
    actions: Mapped[list[ActionItem]] = relationship(back_populates="analysis")
    portfolio_run: Mapped[PortfolioRun | None] = relationship(back_populates="analyses")


class RegulatoryRequirement(Base):
    __tablename__ = "regulatory_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False
    )
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    obligation_type: Mapped[str] = mapped_column(Text, nullable=False)
    applicability: Mapped[str] = mapped_column(Text, nullable=False)
    impact_level: Mapped[str | None] = mapped_column(Text)
    affected_departments: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    analysis: Mapped[ImpactAnalysis] = relationship(back_populates="requirements")
    gaps: Mapped[list[ComplianceGap]] = relationship(back_populates="requirement")


class ComplianceGap(Base):
    __tablename__ = "compliance_gaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regulatory_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    gap_status: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    evidence_chunk_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    requirement: Mapped[RegulatoryRequirement] = relationship(back_populates="gaps")
    actions: Mapped[list[ActionItem]] = relationship(back_populates="gap")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False
    )
    gap_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_gaps.id", ondelete="SET NULL")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_department: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    effort: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    analysis: Mapped[ImpactAnalysis] = relationship(back_populates="actions")
    gap: Mapped[ComplianceGap | None] = relationship(back_populates="actions")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id"), nullable=False
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    from_ocr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    relevance_verified: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    analysis: Mapped[ImpactAnalysis] = relationship(back_populates="citations")
    chunk: Mapped[DocumentChunk] = relationship()


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("impact_analyses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)

    analysis: Mapped[ImpactAnalysis] = relationship(back_populates="review")


class PortfolioRun(Base):
    __tablename__ = "portfolio_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    overall_risk: Mapped[str | None] = mapped_column(Text)
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    result: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    analyses: Mapped[list[ImpactAnalysis]] = relationship(back_populates="portfolio_run")


class RegulationApplicability(Base):
    __tablename__ = "regulation_applicability"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id", ondelete="CASCADE"), nullable=False
    )
    applicability: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    matched_characteristics: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    rule_id: Mapped[str | None] = mapped_column(Text)
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    reviewer_applicability: Mapped[str | None] = mapped_column(Text)
    reviewer_decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    regulation: Mapped[RegulatoryDocument] = relationship()


class RegulatoryChange(Base):
    __tablename__ = "regulatory_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    corpus_key: Mapped[str] = mapped_column(Text, nullable=False)
    previous_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id")
    )
    new_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_documents.id"), nullable=False
    )
    change_kind: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    previous_document: Mapped[RegulatoryDocument | None] = relationship(
        foreign_keys=[previous_document_id]
    )
    new_document: Mapped[RegulatoryDocument] = relationship(foreign_keys=[new_document_id])
    requirement_changes: Mapped[list[RequirementChange]] = relationship(back_populates="change")


class RequirementChange(Base):
    __tablename__ = "requirement_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulatory_changes.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    clause_number: Mapped[str | None] = mapped_column(Text)
    previous_text: Mapped[str | None] = mapped_column(Text)
    new_text: Mapped[str | None] = mapped_column(Text)

    change: Mapped[RegulatoryChange] = relationship(back_populates="requirement_changes")


class CorpusIngestRun(Base):
    __tablename__ = "corpus_ingest_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulator: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    updated_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    failed_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
