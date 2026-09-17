---
title: RegImpact Testing and AI Evaluation Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, testing, evaluation, quality]
---

# Introduction

This spec says what we test and how. It covers the code, the infrastructure, search, the AI
steps, the source links, and the full user journey.

## 1. Purpose & Scope

Two different jobs sit here. One is normal software testing: does the code work. The other is
measuring AI output quality: are the answers any good. Both matter.

## 2. Definitions

- **Recall@K**: Out of all the right chunks, how many showed up in the top K results.
- **Precision@K**: Out of the top K results, how many were actually right.
- **MRR**: On average, how high up the first right answer appeared.
- **End-to-end test**: A test that walks a whole user journey.
- **Regression test**: A test that makes sure something we already fixed stays fixed.
- **Fixture**: A test file or test record we keep around on purpose.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Every important endpoint needs unit tests and tests against a real database.
- **REQ-002**: The main journey, upload to report, needs one full test.
- **REQ-003**: Test search with a list of questions where we already know the right chunks.
- **REQ-004**: Score the AI output on applicability, requirements, sources, gaps, and tasks.
- **REQ-005**: Test that companies stay apart. Include one test where a search run for company A never returns company B's chunks.
- **REQ-006**: Measure how long an analysis takes and how often jobs fail.
- **REQ-007**: Test the risk table and the review rules with a case for every box and every line. Both are plain code, so these tests need no AI call and run in CI.
- **REQ-008**: For every fixed value list in `spec-schema-input-contracts.md`, add a test proving a value not on the list gets rejected.
- **REQ-009**: Test that running a job twice is safe. Send the same job twice and check no step runs again.
- **REQ-010**: Keep a set of documents with hidden instructions in them. Report how often we resist them, next to the search and source numbers.
- **REQ-011**: Test every possible review move, and check that any move not on the list gets refused.
- **REQ-012**: For every output shape in `spec-schema-agent-contracts.md`, add test cases with missing sources, fields the step is not allowed to send, and values not on the list.
- **CON-001**: Never use real customer data in tests.
- **CON-002**: Do not test plain code through the AI. Call the risk table, the review rules, and the merge step directly.
- **GUD-001**: Where we are allowed, save what went into the AI, what came out, and the right answer. Then we can compare runs later.

## 4. Interfaces & Data Contracts

One test case record:

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
- **AC-003**: The full upload-to-report test passes.
- **AC-004**: We have written down the search quality numbers.
- **AC-005**: We know how often the AI makes a point it cannot back up.
- **AC-006**: The security and permission tests pass.
- **AC-007**: The speed numbers are written down.

## 6. Test Automation Strategy

- **Test Levels**: Unit, against a database, full journey, security, speed, and AI quality.
- **Frameworks**: Pytest with `pytest-asyncio` and `pytest-cov` for the backend. Playwright in the frontend for browser tests. Contract tests against the API spec.
- **Test Data Management**: Made-up companies, a few real public rule documents, and written-down right answers.
- **CI/CD Integration**: Run the tests on every pull request and before every deploy.
- **Coverage Requirements**: At least 70% of the important backend code.
- **Performance Testing**: Time the upload, the text extraction, the search, and the whole analysis.

## 7. Rationale & Context

People will make real compliance decisions from this output. So passing tests is not enough. We
also have to measure whether the sources are right and whether the system admits when it does not
know.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The build pipeline.

### Third-Party Services
- **SVC-001**: The AI model and our search.

### Infrastructure Dependencies
- **INF-001**: A test environment, and logs.

### Data Dependencies
- **DAT-001**: The set of test cases with known right answers.

### Technology Platform Dependencies
- **PLT-001**: A test runner.

### Compliance Dependencies
- **COM-001**: Made-up data only, or data we are allowed to use.

## 9. Examples & Edge Cases

Say the AI gives the right advice but links it to the wrong clause. That fails. The advice looking
sensible does not save it. A wrong source is the exact thing this product must not do.

## 10. Validation Criteria

Do not call it ready until the important tests pass and someone has actually looked at the AI
quality numbers.

## 11. Related Specifications / Further Reading

- `spec-process-rag-pipeline.md`
- `spec-process-evidence-verification.md`
- `spec-process-mvp-delivery.md`
