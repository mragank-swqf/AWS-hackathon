---
title: RegImpact Regulatory Impact Analysis Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, impact, compliance, risk]
---

# Introduction

This specification defines how RegImpact determines regulatory applicability, extracts obligations, maps impacts, identifies gaps, and generates remediation actions.

## 1. Purpose & Scope

The process applies to each regulation-company analysis and produces a structured, evidence-backed impact report.

## 2. Definitions

- **Applicability**: Whether a regulation or requirement applies to the company.
- **Requirement**: An obligation extracted from regulatory text.
- **Impact**: The business or technical change needed to satisfy a requirement.
- **Remediation**: Action taken to resolve a compliance gap.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Applicability shall be determined using company profile and regulatory evidence.
- **REQ-002**: Requirements shall be extracted as atomic obligations.
- **REQ-003**: Each requirement shall be mapped to affected departments.
- **REQ-004**: Each requirement shall be compared against available policies, controls, and evidence.
- **REQ-005**: Gaps shall include status, severity, explanation, and recommended action.
- **REQ-006**: The report shall distinguish mandatory requirements from recommendations.
- **REQ-007**: Every material conclusion shall include citations.
- **SEC-001**: The analysis shall use only documents authorized for the company.
- **CON-001**: The system shall not represent an inferred recommendation as direct regulatory text.
- **GUD-001**: Use explicit uncertainty labels.

## 4. Interfaces & Data Contracts

```json
{
  "requirement_id": "req_001",
  "requirement_text": "Maintain a documented grievance process.",
  "applicability": "likely_applicable",
  "impact_level": "high",
  "affected_departments": ["Compliance", "Customer Support"],
  "gap_status": "insufficient_evidence",
  "severity": "medium",
  "recommended_action": "Upload the current grievance process and approval record.",
  "citations": ["citation_001"]
}
```

## 5. Acceptance Criteria

- **AC-001**: Given a regulation that explicitly names the company type, when analyzed, then applicability includes the supporting clause.
- **AC-002**: Given a requirement, when extracted, then it is represented as one atomic obligation.
- **AC-003**: Given no internal evidence, when gap analysis runs, then the status is `insufficient_evidence`.
- **AC-004**: Given an engineering-related requirement, when impact mapping runs, then Engineering is included as an affected function.
- **AC-005**: Given unsupported conclusions, when verification runs, then the report is flagged.

## 6. Test Automation Strategy

Use labeled expected outputs for applicability, requirements, departments, gaps, severity, and citations. Test ambiguous, superseded, exception-based, and deadline-based regulations.

## 7. Rationale & Context

The core product value is translating regulatory language into concrete business work without hiding uncertainty or losing source traceability.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulation and company document repositories.

### Third-Party Services
- **SVC-001**: LLM inference.
- **SVC-002**: Retrieval and reranking.

### Infrastructure Dependencies
- **INF-001**: Analysis worker and persistent result store.

### Data Dependencies
- **DAT-001**: Regulation clauses, company profile, policies, and controls.

### Technology Platform Dependencies
- **PLT-001**: Structured JSON generation and validation.

### Compliance Dependencies
- **COM-001**: Human review and evidence-backed decisions.

## 9. Examples & Edge Cases

A regulation may apply to the company but not to a particular product. The system must support requirement-level applicability rather than only document-level applicability.

## 10. Validation Criteria

An analysis is valid when applicability, requirements, impacts, gaps, risks, actions, and citations are present and internally consistent.

## 11. Related Specifications / Further Reading

- `spec-process-agent-orchestration.md`
- `spec-process-evidence-verification.md`
- `spec-schema-input-contracts.md`
