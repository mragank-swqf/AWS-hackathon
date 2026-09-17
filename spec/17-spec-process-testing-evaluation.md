---
title: RegImpact Testing and AI Evaluation Specification
version: 1.3
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

This list is short on purpose. Every test here is either quick to write or protects something
the demo depends on.

- **REQ-001**: Test the risk table and the review rules with a case for every box and every line. Both are plain code, so these run in seconds with no AI call. Write these first. They are the cheapest tests in the project.
- **REQ-002**: For every output shape in `12-spec-schema-agent-contracts.md`, add test cases with missing sources, fields the step is not allowed to send, and values not on the list.
- **REQ-003**: For every fixed value list in `04-spec-schema-input-contracts.md`, add a test proving a value not on the list gets rejected.
- **REQ-004**: One full test of the main journey: upload a rule document, upload a company document, run the analysis, open a source link, approve.
- **REQ-005**: One test that a search for company A never returns company B's chunks.
- **REQ-006**: Keep a small set of questions where we know the right chunks, and check search finds them. Ten questions is enough to catch a broken search.
- **CON-001**: Never use real customer data in tests.
- **CON-002**: Do not test plain code through the AI. Call the risk table, the review rules, and the merge step directly.
- **GUD-001**: Save what went into the AI and what came out. Even without scoring it, having the record helps when something looks wrong.

### Left for later

- **LTR-001**: A coverage target. We had 70%. Drop the number for now, keep writing the quick tests.
- **LTR-002**: Scoring AI output properly on applicability, requirements, sources, gaps, and tasks.
- **LTR-003**: Measuring Recall@K, Precision@K, and MRR against a proper labelled set.
- **LTR-004**: Speed and failure-rate measurements.
- **LTR-005**: A set of documents with hidden instructions, to measure how well the prompt fencing holds.
- **LTR-006**: Testing every review move, once there is more than approve and reject.
- **LTR-007**: Testing that running a job twice is safe.
- **LTR-008**: Backup and restore testing.

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

- **AC-001**: The risk table and review rule tests pass.
- **AC-002**: The output shape tests pass, including the ones that should fail.
- **AC-003**: The full upload-to-report test passes.
- **AC-004**: The company separation test passes.
- **AC-005**: Search finds the right chunk for the ten known questions.

## 6. Test Automation Strategy

- **Test Levels**: Plain unit tests, shape checks, and one full journey test.
- **Frameworks**: Pytest with `pytest-asyncio`. Skip Playwright for now.
- **Test Data Management**: One made-up company, a few real public rule documents, and ten search questions with known answers.
- **CI/CD Integration**: Run the tests on every push.
- **Coverage Requirements**: No number. Write the cheap tests listed above.
- **Performance Testing**: Left for later.

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

- `11-spec-process-rag-pipeline.md`
- `15-spec-process-evidence-verification.md`
- `02-spec-process-mvp-delivery.md`
