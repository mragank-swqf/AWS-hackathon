---
title: RegImpact Evidence and Citation Verification Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, evidence, citations, verification, ai-safety]
---

# Introduction

This specification defines how RegImpact verifies that generated claims are supported by regulatory or internal evidence.

## 1. Purpose & Scope

The process covers citation creation, claim-to-source mapping, unsupported claim detection, date verification, applicability verification, and human-review escalation.

## 2. Definitions

- **Citation**: A reference to a source document, page, section, or clause.
- **Claim**: A factual or interpretive statement in an analysis.
- **Citation coverage**: Proportion of material claims with citations.
- **Unsupported claim**: A claim that cannot be justified by retrieved evidence.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Every material regulatory claim shall have a citation.
- **REQ-002**: Citations shall include document ID and page or clause where available.
- **REQ-003**: The system shall distinguish direct source text from interpretation.
- **REQ-004**: Unsupported deadlines shall be flagged.
- **REQ-005**: Unsupported applicability conclusions shall be flagged.
- **REQ-006**: Verification shall produce a machine-readable result.
- **SEC-001**: Citations shall not expose unauthorized internal documents.
- **CON-001**: Citation presence alone shall not be treated as citation correctness.
- **GUD-001**: Display source excerpts to reviewers.

## 4. Interfaces & Data Contracts

```json
{
  "verification_status": "partially_verified",
  "citation_coverage": 0.92,
  "unsupported_claims": [
    "The suggested deadline is not explicitly stated in the source."
  ],
  "missing_evidence": [
    "Current internal grievance policy"
  ],
  "requires_human_review": true
}
```

## 5. Acceptance Criteria

- **AC-001**: A claim without a citation is flagged.
- **AC-002**: A citation to an irrelevant clause is flagged.
- **AC-003**: A date not present in the source is flagged.
- **AC-004**: A recommendation is not labeled as a mandatory legal requirement.
- **AC-005**: Reviewers can open the cited source location.

## 6. Test Automation Strategy

Create test cases with supported, partially supported, contradicted, and unsupported claims. Measure citation precision, citation recall, unsupported claim rate, and verification latency.

## 7. Rationale & Context

Compliance outputs must be reviewable. Verification reduces hallucinations and helps reviewers distinguish source requirements from model interpretation.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Source document repository.

### Third-Party Services
- **SVC-001**: LLM or entailment model for claim verification.

### Infrastructure Dependencies
- **INF-001**: Citation store and audit log.

### Data Dependencies
- **DAT-001**: Source chunks, claims, and generated reports.

### Technology Platform Dependencies
- **PLT-001**: Structured output validation.

### Compliance Dependencies
- **COM-001**: Human review for high-impact or uncertain claims.

## 9. Examples & Edge Cases

If a circular states an effective date but not an implementation deadline, the system must display the effective date and mark any proposed implementation deadline as a recommendation.

## 10. Validation Criteria

The verification service shall identify missing, irrelevant, and unsupported citations and produce a clear review status.

## 11. Related Specifications / Further Reading

- `spec-process-rag-pipeline.md`
- `spec-process-impact-analysis.md`
- `spec-tool-api-contracts.md`
