---
title: RegImpact Testing and AI Evaluation Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, testing, evaluation, quality]
---

# Introduction

This specification defines functional, integration, end-to-end, security, performance, retrieval, and AI-output evaluation for RegImpact.

## 1. Purpose & Scope

The specification applies to application code, infrastructure, retrieval, agents, citations, and the final user workflow.

## 2. Definitions

- **Recall@K**: Percentage of relevant items retrieved within the top K results.
- **Precision@K**: Percentage of top K results that are relevant.
- **End-to-end test**: Test of a complete user workflow.
- **Regression test**: Test ensuring previously working behavior remains correct.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Every critical API shall have unit and integration tests.
- **REQ-002**: The main upload-to-report workflow shall have an end-to-end test.
- **REQ-003**: Retrieval shall be evaluated using labeled queries.
- **REQ-004**: AI outputs shall be evaluated for applicability, requirements, citations, gaps, and actions.
- **REQ-005**: Security tests shall cover tenant isolation.
- **REQ-006**: Performance tests shall measure analysis latency and job failure rate.
- **CON-001**: Test data shall not contain real confidential customer information.
- **GUD-001**: Store model inputs, outputs, and evaluation labels for reproducibility where permitted.

## 4. Interfaces & Data Contracts

Evaluation record:

```json
{
  "case_id": "case_001",
  "expected_applicability": "applicable",
  "expected_requirements": ["req_a", "req_b"],
  "expected_departments": ["Compliance", "Engineering"],
  "expected_citations": ["citation_a"],
  "actual_output": {},
  "scores": {
    "applicability": 1.0,
    "citation_correctness": 0.9
  }
}
```

## 5. Acceptance Criteria

- **AC-001**: Unit tests pass in CI.
- **AC-002**: API contract tests pass.
- **AC-003**: End-to-end upload-to-report test passes.
- **AC-004**: Retrieval benchmark results are recorded.
- **AC-005**: Unsupported claim rate is measured.
- **AC-006**: Security and authorization tests pass.
- **AC-007**: Performance results are documented.

## 6. Test Automation Strategy

- **Test Levels**: Unit, integration, end-to-end, security, performance, AI evaluation.
- **Frameworks**: Pytest, Playwright, API contract testing, and standard AWS testing tools.
- **Test Data Management**: Synthetic companies, curated public regulations, and labeled expected outputs.
- **CI/CD Integration**: Run tests on pull requests and before deployment.
- **Coverage Requirements**: Minimum 70% backend coverage for MVP-critical code.
- **Performance Testing**: Measure upload latency, extraction time, retrieval latency, and full analysis duration.

## 7. Rationale & Context

The platform produces high-impact compliance information. Testing must measure not only software correctness but also evidence quality and uncertainty handling.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: CI/CD pipeline.

### Third-Party Services
- **SVC-001**: Model inference and retrieval services.

### Infrastructure Dependencies
- **INF-001**: Test environment and logging.

### Data Dependencies
- **DAT-001**: Labeled evaluation corpus.

### Technology Platform Dependencies
- **PLT-001**: Automated test runner.

### Compliance Dependencies
- **COM-001**: Synthetic or authorized test data only.

## 9. Examples & Edge Cases

A correct answer with an incorrect citation shall fail citation correctness even if the final recommendation appears reasonable.

## 10. Validation Criteria

The release shall not be considered ready until critical tests pass and AI evaluation results are reviewed.

## 11. Related Specifications / Further Reading

- `spec-process-rag-pipeline.md`
- `spec-process-evidence-verification.md`
- `spec-process-mvp-delivery.md`
