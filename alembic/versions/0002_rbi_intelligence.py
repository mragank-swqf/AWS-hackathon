"""RBI corpus metadata, applicability, portfolio runs, and change events.

Revision ID: 0002_rbi_intelligence
Revises: 0001_initial
Create Date: 2026-09-19
"""

from __future__ import annotations

from alembic import op
from app.enums import (
    LifecycleStatus,
    OrganizationType,
    RegulatoryDomain,
    RequirementChangeKind,
    SourceKind,
    sql_in_list,
)

revision = "0002_rbi_intelligence"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE companies DROP CONSTRAINT IF EXISTS companies_org_type_valid")
    op.execute(
        f"""
        ALTER TABLE companies ADD CONSTRAINT companies_org_type_valid CHECK (
            organization_type IN ({sql_in_list(OrganizationType)})
        )
        """
    )
    op.execute(
        f"""
        ALTER TABLE regulatory_documents
            ADD COLUMN IF NOT EXISTS jurisdiction TEXT,
            ADD COLUMN IF NOT EXISTS regulatory_domain TEXT,
            ADD COLUMN IF NOT EXISTS applicable_entity_types TEXT[],
            ADD COLUMN IF NOT EXISTS lifecycle_status TEXT NOT NULL DEFAULT 'active',
            ADD COLUMN IF NOT EXISTS version_label TEXT,
            ADD COLUMN IF NOT EXISTS corpus_key TEXT,
            ADD COLUMN IF NOT EXISTS source_kind TEXT NOT NULL DEFAULT 'uploaded',
            ADD COLUMN IF NOT EXISTS supersedes_document_id UUID REFERENCES regulatory_documents(id),
            ADD COLUMN IF NOT EXISTS metadata JSONB,
            ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMP
        """
    )
    op.execute(
        f"""
        ALTER TABLE regulatory_documents
            DROP CONSTRAINT IF EXISTS regulatory_documents_lifecycle_valid
        """
    )
    op.execute(
        f"""
        ALTER TABLE regulatory_documents ADD CONSTRAINT regulatory_documents_lifecycle_valid CHECK (
            lifecycle_status IN ({sql_in_list(LifecycleStatus)})
        )
        """
    )
    op.execute(
        f"""
        ALTER TABLE regulatory_documents ADD CONSTRAINT regulatory_documents_source_kind_valid CHECK (
            source_kind IN ({sql_in_list(SourceKind)})
        )
        """
    )
    op.execute(
        f"""
        ALTER TABLE regulatory_documents ADD CONSTRAINT regulatory_documents_domain_valid CHECK (
            regulatory_domain IS NULL OR regulatory_domain IN ({sql_in_list(RegulatoryDomain)})
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_regulatory_documents_corpus_key ON regulatory_documents (corpus_key)"
    )
    op.execute(
        """
        CREATE TABLE portfolio_runs (
            id UUID PRIMARY KEY,
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            overall_risk TEXT,
            human_review_required BOOLEAN NOT NULL DEFAULT false,
            result JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
        """
    )
    op.execute(
        """
        ALTER TABLE impact_analyses
            ADD COLUMN IF NOT EXISTS portfolio_run_id UUID REFERENCES portfolio_runs(id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        CREATE TABLE regulation_applicability (
            id UUID PRIMARY KEY,
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            regulation_id UUID NOT NULL REFERENCES regulatory_documents(id) ON DELETE CASCADE,
            applicability TEXT NOT NULL,
            reason TEXT NOT NULL,
            matched_characteristics TEXT[],
            rule_id TEXT,
            human_review_required BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (company_id, regulation_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE regulatory_changes (
            id UUID PRIMARY KEY,
            corpus_key TEXT NOT NULL,
            previous_document_id UUID REFERENCES regulatory_documents(id),
            new_document_id UUID NOT NULL REFERENCES regulatory_documents(id),
            change_kind TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE requirement_changes (
            id UUID PRIMARY KEY,
            change_id UUID NOT NULL REFERENCES regulatory_changes(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            clause_number TEXT,
            previous_text TEXT,
            new_text TEXT,
            CONSTRAINT requirement_changes_kind_valid CHECK (
                kind IN ({sql_in_list(RequirementChangeKind)})
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE corpus_ingest_runs (
            id UUID PRIMARY KEY,
            regulator TEXT NOT NULL,
            status TEXT NOT NULL,
            created_count INTEGER NOT NULL DEFAULT 0,
            updated_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS requirement_changes")
    op.execute("DROP TABLE IF EXISTS regulatory_changes")
    op.execute("DROP TABLE IF EXISTS regulation_applicability")
    op.execute("ALTER TABLE impact_analyses DROP COLUMN IF EXISTS portfolio_run_id")
    op.execute("DROP TABLE IF EXISTS portfolio_runs")
    op.execute("DROP TABLE IF EXISTS corpus_ingest_runs")
