---
title: RegImpact Database and Persistence Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [data, database, persistence, audit]
---

# Introduction

This specification defines the persistent data model for companies, regulations, documents, analyses, gaps, actions, citations, reviews, and audit logs.

## 1. Purpose & Scope

The database shall support multi-company isolation, document traceability, asynchronous analysis, review workflows, and auditability.

## 2. Definitions

- **UUID**: Universally Unique Identifier.
- **JSONB**: Binary JSON storage format supported by PostgreSQL.
- **Tenant**: A company or organization using the platform.
- **Audit log**: Immutable record of a security-sensitive or workflow-sensitive event.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: All primary resources shall use stable unique identifiers.
- **REQ-002**: Company-owned records shall include `company_id` directly or through a verified relationship.
- **REQ-003**: Regulatory chunks shall retain page, clause, and document references.
- **REQ-004**: Analysis results shall preserve intermediate and final outputs.
- **REQ-005**: Audit logs shall record actor, action, resource, timestamp, and outcome.
- **SEC-001**: Database access shall use least privilege.
- **SEC-002**: Sensitive data shall be encrypted at rest and in transit.
- **CON-001**: Deleting a company shall not silently delete regulatory source documents shared by other tenants.
- **GUD-001**: Use normalized tables for frequently queried fields and JSONB for extensible analysis output.

## 4. Interfaces & Data Contracts

Required tables:

```text
companies
users
company_users
regulatory_documents
document_chunks
company_policies
company_controls
impact_analyses
regulatory_requirements
compliance_gaps
action_items
citations
verification_results
reviews
audit_logs
```

Example table:

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

- **AC-001**: Company records can be created and retrieved.
- **AC-002**: Documents can be linked to analyses.
- **AC-003**: Analysis results persist after worker completion.
- **AC-004**: Company A cannot query Company B's policies or analyses.
- **AC-005**: Audit events are created for upload, analysis, approval, and access-denied events.

## 6. Test Automation Strategy

Test migrations, foreign keys, indexes, tenant isolation, transaction rollback, concurrent writes, and backup restoration.

## 7. Rationale & Context

The platform needs durable records for auditability and review. JSONB allows the AI result structure to evolve while core entities remain queryable.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Backend service and worker service.

### Third-Party Services
- **SVC-001**: PostgreSQL-compatible database.

### Infrastructure Dependencies
- **INF-001**: Managed relational database and backup system.

### Data Dependencies
- **DAT-001**: Regulation documents, chunks, company profiles, and analysis outputs.

### Technology Platform Dependencies
- **PLT-001**: PostgreSQL with vector search capability if vectors are stored in the relational database.

### Compliance Dependencies
- **COM-001**: Retention, deletion, and audit requirements.

## 9. Examples & Edge Cases

A shared regulatory document may be referenced by multiple companies. Company-specific analysis results and internal evidence must remain isolated.

## 10. Validation Criteria

The schema shall pass migration tests, referential-integrity tests, tenant-isolation tests, and backup-restore tests.

## 11. Related Specifications / Further Reading

- `spec-schema-input-contracts.md`
- `spec-architecture-system.md`
- `spec-tool-api-contracts.md`
