"""Initial schema with pgvector, ten tables, and chunk constraints.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-18
"""

from __future__ import annotations

from alembic import op
from app.enums import (
    ActionStatus,
    AnalysisDepth,
    AnalysisStatus,
    Applicability,
    DocumentType,
    Effort,
    EvidenceType,
    ExtractionMethod,
    GapStatus,
    ImpactLevel,
    ObligationType,
    OrganizationType,
    OverallRisk,
    ProcessingStatus,
    ReviewStatus,
    Severity,
    sql_in_list,
)

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"""
        CREATE TABLE companies (
            id UUID PRIMARY KEY,
            company_name TEXT NOT NULL,
            organization_type TEXT NOT NULL,
            business_model TEXT,
            operating_regions TEXT[] NOT NULL DEFAULT '{{}}',
            products TEXT[] NOT NULL DEFAULT '{{}}',
            customer_segments TEXT[] NOT NULL DEFAULT '{{}}',
            regulatory_entities TEXT[] NOT NULL DEFAULT '{{}}',
            uses_customer_data BOOLEAN,
            uses_automated_decisioning BOOLEAN,
            has_outsourced_operations BOOLEAN,
            existing_policies TEXT[] NOT NULL DEFAULT '{{}}',
            internal_controls TEXT[] NOT NULL DEFAULT '{{}}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT companies_name_not_empty CHECK (length(trim(company_name)) > 0),
            CONSTRAINT companies_org_type_valid CHECK (
                organization_type IN ({sql_in_list(OrganizationType)})
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE regulatory_documents (
            id UUID PRIMARY KEY,
            title TEXT NOT NULL,
            regulator TEXT NOT NULL,
            document_type TEXT NOT NULL,
            reference_number TEXT,
            publication_date DATE,
            effective_date DATE,
            source_url TEXT,
            s3_key TEXT NOT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            pages INTEGER,
            processing_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT regulatory_documents_type_valid CHECK (
                document_type IN ({sql_in_list(DocumentType)})
            ),
            CONSTRAINT regulatory_documents_status_valid CHECK (
                processing_status IN ({sql_in_list(ProcessingStatus)})
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE company_policies (
            id UUID PRIMARY KEY,
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            version_label TEXT,
            effective_date DATE,
            owner_department TEXT,
            approved_by TEXT,
            s3_key TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            processing_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (company_id, content_hash),
            CONSTRAINT company_policies_evidence_valid CHECK (
                evidence_type IN ({sql_in_list(EvidenceType)})
            ),
            CONSTRAINT company_policies_status_valid CHECK (
                processing_status IN ({sql_in_list(ProcessingStatus)})
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY,
            regulatory_document_id UUID REFERENCES regulatory_documents(id) ON DELETE CASCADE,
            company_policy_id UUID REFERENCES company_policies(id) ON DELETE CASCADE,
            company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            page_start INTEGER NOT NULL,
            page_end INTEGER NOT NULL,
            section_title TEXT,
            clause_number TEXT,
            extraction_method TEXT,
            embedding VECTOR(1024),
            text_search TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chunk_has_exactly_one_source CHECK (
                (regulatory_document_id IS NOT NULL) <> (company_policy_id IS NOT NULL)
            ),
            CONSTRAINT company_chunk_is_tenant_scoped CHECK (
                company_policy_id IS NULL OR company_id IS NOT NULL
            ),
            CONSTRAINT regulation_chunk_is_shared CHECK (
                regulatory_document_id IS NULL OR company_id IS NULL
            ),
            CONSTRAINT document_chunks_extraction_valid CHECK (
                extraction_method IS NULL OR extraction_method IN ({sql_in_list(ExtractionMethod)})
            )
        )
        """
    )
    op.execute(
        "CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute("CREATE INDEX ON document_chunks USING gin (text_search)")
    op.execute("CREATE INDEX ON document_chunks (regulatory_document_id, page_start)")
    op.execute("CREATE INDEX ON document_chunks (company_id)")
    op.execute(
        f"""
        CREATE TABLE impact_analyses (
            id UUID PRIMARY KEY,
            company_id UUID NOT NULL REFERENCES companies(id),
            regulation_id UUID NOT NULL REFERENCES regulatory_documents(id),
            status TEXT NOT NULL,
            applicability TEXT,
            overall_risk TEXT,
            result JSONB,
            confidence NUMERIC,
            human_review_required BOOLEAN DEFAULT FALSE,
            analysis_depth TEXT NOT NULL,
            include_gap_analysis BOOLEAN DEFAULT TRUE,
            include_action_plan BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            CONSTRAINT impact_analyses_status_valid CHECK (
                status IN ({sql_in_list(AnalysisStatus)})
            ),
            CONSTRAINT impact_analyses_depth_valid CHECK (
                analysis_depth IN ({sql_in_list(AnalysisDepth)})
            ),
            CONSTRAINT impact_analyses_applicability_valid CHECK (
                applicability IS NULL OR applicability IN ({sql_in_list(Applicability)})
            ),
            CONSTRAINT impact_analyses_risk_valid CHECK (
                overall_risk IS NULL OR overall_risk IN ({sql_in_list(OverallRisk)})
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE regulatory_requirements (
            id UUID PRIMARY KEY,
            analysis_id UUID NOT NULL REFERENCES impact_analyses(id) ON DELETE CASCADE,
            requirement_text TEXT NOT NULL,
            obligation_type TEXT NOT NULL,
            applicability TEXT NOT NULL,
            impact_level TEXT,
            affected_departments TEXT[],
            source_chunk_id UUID REFERENCES document_chunks(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT regulatory_requirements_obligation_valid CHECK (
                obligation_type IN ({sql_in_list(ObligationType)})
            ),
            CONSTRAINT regulatory_requirements_applicability_valid CHECK (
                applicability IN ({sql_in_list(Applicability)})
            ),
            CONSTRAINT regulatory_requirements_impact_valid CHECK (
                impact_level IS NULL OR impact_level IN ({sql_in_list(ImpactLevel)})
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE compliance_gaps (
            id UUID PRIMARY KEY,
            requirement_id UUID NOT NULL REFERENCES regulatory_requirements(id) ON DELETE CASCADE,
            company_id UUID NOT NULL REFERENCES companies(id),
            gap_status TEXT NOT NULL,
            severity TEXT NOT NULL,
            explanation TEXT,
            evidence_chunk_ids UUID[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT compliance_gaps_status_valid CHECK (
                gap_status IN ({sql_in_list(GapStatus)})
            ),
            CONSTRAINT compliance_gaps_severity_valid CHECK (
                severity IN ({sql_in_list(Severity)})
            )
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE action_items (
            id UUID PRIMARY KEY,
            analysis_id UUID NOT NULL REFERENCES impact_analyses(id) ON DELETE CASCADE,
            gap_id UUID REFERENCES compliance_gaps(id) ON DELETE SET NULL,
            company_id UUID NOT NULL REFERENCES companies(id),
            title TEXT NOT NULL,
            description TEXT,
            owner_department TEXT,
            status TEXT NOT NULL,
            effort TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT action_items_status_valid CHECK (
                status IN ({sql_in_list(ActionStatus)})
            ),
            CONSTRAINT action_items_effort_valid CHECK (
                effort IS NULL OR effort IN ({sql_in_list(Effort)})
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE citations (
            id UUID PRIMARY KEY,
            analysis_id UUID NOT NULL REFERENCES impact_analyses(id) ON DELETE CASCADE,
            chunk_id UUID NOT NULL REFERENCES document_chunks(id),
            claim_text TEXT NOT NULL,
            excerpt TEXT NOT NULL,
            from_ocr BOOLEAN NOT NULL DEFAULT FALSE,
            relevance_verified BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE reviews (
            id UUID PRIMARY KEY,
            analysis_id UUID NOT NULL UNIQUE REFERENCES impact_analyses(id) ON DELETE CASCADE,
            company_id UUID NOT NULL REFERENCES companies(id),
            status TEXT NOT NULL,
            decided_by TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decided_at TIMESTAMP,
            CONSTRAINT reviews_status_valid CHECK (
                status IN ({sql_in_list(ReviewStatus)})
            )
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reviews")
    op.execute("DROP TABLE IF EXISTS citations")
    op.execute("DROP TABLE IF EXISTS action_items")
    op.execute("DROP TABLE IF EXISTS compliance_gaps")
    op.execute("DROP TABLE IF EXISTS regulatory_requirements")
    op.execute("DROP TABLE IF EXISTS impact_analyses")
    op.execute("DROP TABLE IF EXISTS document_chunks")
    op.execute("DROP TABLE IF EXISTS company_policies")
    op.execute("DROP TABLE IF EXISTS regulatory_documents")
    op.execute("DROP TABLE IF EXISTS companies")
