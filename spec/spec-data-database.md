---
title: RegImpact Database and Persistence Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [data, database, persistence, audit]
---

# Introduction

This spec lists the database tables and what goes in them. It covers companies, rule documents,
uploaded files, analyses, gaps, tasks, sources, reviews, and the action log.

## 1. Purpose & Scope

The database has to do five things. Keep each company's data apart. Let us trace any point back to
its source. Hold the state of background jobs. Support the review flow. Keep a log of who did
what.

## 2. Definitions

- **UUID**: A long random ID. No two are the same.
- **JSONB**: A way PostgreSQL stores JSON so you can still search inside it.
- **Tenant**: One company using the product.
- **Audit log**: A record of an important action. Once written, it cannot be changed.
- **Chunk**: A small piece of a document that we can search.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Every main record must have its own unique ID.
- **REQ-002**: Any record that belongs to a company must have a `company_id`, either on the row or through a row that has one.
- **REQ-003**: Every chunk must keep its page, its clause number, and which document it came from.
- **REQ-004**: We must save the output of each step, not just the final report.
- **REQ-005**: The audit log must record who did it, what they did, what they did it to, when, and whether it worked.
- **REQ-006**: A chunk row must hold the chunk text, its source info, its embedding, and its keyword index. All on the same row.
- **REQ-007**: A chunk must come from one source only. Either a rule document or a company document. Never both.
- **REQ-008**: Chunks from rule documents must have an empty `company_id`, because all companies share them. Chunks from company documents must have a `company_id`.
- **REQ-009**: Each source link must record whether we checked that the source really says what we claim.
- **SEC-001**: Give the database user only the rights it needs, nothing more.
- **SEC-002**: Data must be encrypted on disk and while moving over the network.
- **CON-001**: Deleting a company must not delete rule documents. Other companies use those too.
- **GUD-001**: Use normal columns for things we search on. Use JSONB for the AI output, which will keep changing shape.
- **GUD-002**: Where we can, make the database enforce the rules. Do not rely on app code alone.

### Left for later

- **LTR-001**: The `users` and `company_users` tables. There is no login yet, so there is one fixed demo user.
- **LTR-002**: The `audit_logs` table, add-only, with `UPDATE` and `DELETE` taken away from the app's database user.
- **LTR-003**: `lifecycle_status` and `superseded_by` on rule documents, for tracking which ones have been replaced.
- **LTR-004**: The `verification_results` table. For now the checking step's output goes in the `result` JSONB column on the analysis.

Note what is not on this list. `company_id` stays on every row it belongs on, and so do the
constraints on `document_chunks`. Those cost nothing to keep now and are painful to add back
later.

## 4. Interfaces & Data Contracts

Tables we need:

```text
companies
regulatory_documents
document_chunks
company_policies
impact_analyses
regulatory_requirements
compliance_gaps
action_items
citations
reviews
```

Ten tables, not fifteen. Left out for now: `users`, `company_users`, `audit_logs`,
`verification_results`, and `company_controls`. See the list above.

Search runs in the database. The `vector` add-on handles search by meaning. A generated
`TSVECTOR` column handles search by keyword. Both live on the same row. That means one query, one
transaction, and one place where we filter by company.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    regulatory_document_id UUID REFERENCES regulatory_documents(id) ON DELETE CASCADE,
    company_policy_id UUID REFERENCES company_policies(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
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
    )
);

CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON document_chunks USING gin (text_search);
CREATE INDEX ON document_chunks (regulatory_document_id, page_start);
CREATE INDEX ON document_chunks (company_id);
```

We cut chunks at clause boundaries, so a chunk can run across a page break. That is why we store
a page range and not one page number. When both ends are the same page, show just that page.
Otherwise show the range.

Whether a rule applies is stored per requirement, not only per analysis. A rule can apply to a
company even when one line in it does not.

```sql
CREATE TABLE regulatory_requirements (
    id UUID PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES impact_analyses(id) ON DELETE CASCADE,
    requirement_text TEXT NOT NULL,
    obligation_type TEXT NOT NULL,
    applicability TEXT NOT NULL,
    impact_level TEXT,
    affected_departments TEXT[],
    source_chunk_id UUID REFERENCES document_chunks(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE compliance_gaps (
    id UUID PRIMARY KEY,
    requirement_id UUID NOT NULL REFERENCES regulatory_requirements(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id),
    gap_status TEXT NOT NULL,
    severity TEXT NOT NULL,
    explanation TEXT,
    evidence_chunk_ids UUID[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

A company's own documents are stored as real uploads. They have to be, so that gap checking can
point at them.

```sql
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
    UNIQUE (company_id, content_hash)
);
```

The rule document table. `lifecycle_status` and `superseded_by` are left for later, per LTR-003.

```sql
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

A source link holds the claim, the chunk that backs it, the bit of text we show the reviewer,
whether that text came from OCR, and whether we checked it. That last column is the important
one. A link can be there and still point at the wrong place.

```sql
CREATE TABLE citations (
    id UUID PRIMARY KEY,
    analysis_id UUID NOT NULL REFERENCES impact_analyses(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id),
    claim_text TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    from_ocr BOOLEAN NOT NULL DEFAULT FALSE,
    relevance_verified BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

One more table, as an example of the pattern:

```sql
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 5. Acceptance Criteria

- **AC-001**: You can create a company and read it back.
- **AC-002**: You can link a document to an analysis.
- **AC-003**: Results are still there after the worker finishes.
- **AC-004**: The database refuses a chunk row that points at both a rule document and a company document.
- **AC-005**: Both kinds of search return rows from the same chunk table.
- **AC-006**: A search for one company never returns another company's chunks.

## 6. Test Automation Strategy

Test that the migrations run, that the `document_chunks` constraints hold, and that both kinds of
search return something. Backup and restore testing is left for later.

## 7. Rationale & Context

We need records that last, so that anything can be audited and reviewed later. We use JSONB for
the AI output because its shape will keep changing, while the main tables stay easy to query.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The backend and the worker.

### Third-Party Services
- **SVC-001**: A PostgreSQL database.

### Infrastructure Dependencies
- **INF-001**: A managed database with backups.

### Data Dependencies
- **DAT-001**: Rule documents, chunks, company profiles, and analysis output.

### Technology Platform Dependencies
- **PLT-001**: PostgreSQL 15 or newer with the `pgvector` add-on turned on. Embeddings and keyword indexes live in the database. There is no separate search service.

### Compliance Dependencies
- **COM-001**: Rules about how long we keep data, how we delete it, and what we log.

## 9. Examples & Edge Cases

Many companies can point at the same rule document. That is fine and expected. But each company's
own documents and its analysis results must stay private to it.

## 10. Validation Criteria

The schema is done when migration tests, foreign key tests, company separation tests, and
backup restore tests all pass.

## 11. Related Specifications / Further Reading

- `spec-schema-input-contracts.md`
- `spec-architecture-system.md`
- `spec-tool-api-contracts.md`
