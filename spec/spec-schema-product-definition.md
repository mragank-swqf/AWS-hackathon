---
title: RegImpact Product Definition Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [schema, product, fintech, compliance, ai]
---

# Introduction

This specification defines the product scope, users, workflows, and functional boundaries of RegImpact, an AI-powered regulatory compliance impact analyzer for Indian fintechs and NBFCs.

## 1. Purpose & Scope

RegImpact shall convert regulatory documents into evidence-backed compliance impact reports. The MVP targets Indian fintechs, NBFCs, payment businesses, lending platforms, and their compliance, legal, risk, operations, product, and engineering teams.

The MVP shall support regulatory document upload, company profiling, applicability analysis, requirement extraction, impact mapping, gap detection, risk classification, citations, action-plan generation, and human review.

## 2. Definitions

- **RegImpact**: The regulatory impact analysis platform.
- **RBI**: Reserve Bank of India.
- **NBFC**: Non-Banking Financial Company.
- **RAG**: Retrieval-Augmented Generation.
- **MVP**: Minimum Viable Product.
- **Compliance gap**: A difference between a regulatory requirement and available company controls or evidence.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The platform shall allow a user to create and maintain a company profile.
- **REQ-002**: The platform shall accept regulatory PDF documents.
- **REQ-003**: The platform shall produce a structured impact report.
- **REQ-004**: The report shall include applicability, requirements, impacted functions, gaps, risk, actions, and citations.
- **REQ-005**: The platform shall support human review before an analysis is treated as approved.
- **CON-001**: The MVP shall not provide final legal advice.
- **CON-002**: The MVP shall not automatically file reports with regulators.
- **GUD-001**: All model-generated conclusions should be traceable to source evidence.
- **PAT-001**: Use structured JSON objects between processing stages.

## 4. Interfaces & Data Contracts

The product shall expose the following primary resources:

| Resource | Purpose |
|---|---|
| Company | Organization profile and controls |
| Regulation | Regulatory source document |
| Analysis | Impact analysis execution and result |
| Gap | Identified compliance issue |
| Action | Remediation task |
| Citation | Source evidence |
| Review | Human approval decision |

## 5. Acceptance Criteria

- **AC-001**: Given a valid company profile, when the user saves it, then the profile is persisted and retrievable.
- **AC-002**: Given a valid regulatory PDF, when the user uploads it, then the document appears in the regulation library.
- **AC-003**: Given a regulation and company profile, when analysis completes, then the report contains all required sections.
- **AC-004**: Given uncertain applicability or missing evidence, when the report is generated, then human review is required.

## 6. Test Automation Strategy

- **Test Levels**: Unit, integration, end-to-end, AI evaluation.
- **Frameworks**: Pytest for backend tests; Playwright for browser tests; contract tests for APIs.
- **Test Data Management**: Use synthetic company profiles and a curated set of public regulatory documents.
- **CI/CD Integration**: Run linting, unit tests, API tests, and security checks in GitHub Actions.
- **Coverage Requirements**: Minimum 70% backend coverage for MVP-critical modules.
- **Performance Testing**: Measure upload, retrieval, and analysis latency using representative PDFs.

## 7. Rationale & Context

Compliance teams need a repeatable way to translate long regulatory documents into operational work. The product focuses on traceability and reviewability rather than fully autonomous legal decisions.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulatory websites - source documents and metadata.
- **EXT-002**: Company document repository - internal policies and controls.

### Third-Party Services
- **SVC-001**: Amazon Bedrock - language model inference and embeddings.
- **SVC-002**: Amazon Textract - OCR for scanned documents.

### Infrastructure Dependencies
- **INF-001**: Object storage, relational database, queue, and application hosting.

### Data Dependencies
- **DAT-001**: Regulatory PDFs, company policies, control descriptions, and evidence files.

### Technology Platform Dependencies
- **PLT-001**: AWS-hosted web application with REST APIs.

### Compliance Dependencies
- **COM-001**: Human review shall be required for uncertain or high-impact findings.

## 9. Examples & Edge Cases

```json
{
  "applicability": "uncertain",
  "human_review_required": true,
  "reason": "The source does not clearly define whether the company's business model is covered."
}
```

## 10. Validation Criteria

The product specification is satisfied when the complete MVP workflow can be demonstrated from document upload through approved action plan.

## 11. Related Specifications / Further Reading

- `spec-schema-input-contracts.md`
- `spec-process-impact-analysis.md`
- `spec-architecture-system.md`
