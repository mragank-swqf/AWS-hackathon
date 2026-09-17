---
title: RegImpact MVP Delivery and Implementation Process Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, mvp, delivery, hackathon]
---

# Introduction

This spec says what order we build things in, what is in the MVP and what is not, and what has to
work by demo day.

## 1. Purpose & Scope

We have two weeks. So the plan is built around getting one whole flow working, start to finish,
rather than lots of half-done parts.

## 2. Definitions

- **MVP**: The smallest version that works.
- **Demo path**: The exact set of clicks we show the judges.
- **Must-have**: Needed for the main flow.
- **Should-have**: Nice, but the demo works without it.
- **Vertical slice**: One thin path through every layer, working end to end.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The MVP must go all the way from uploading a PDF to a finished report.
- **REQ-002**: The MVP must include the company profile and uploading company documents.
- **REQ-003**: The MVP must include search and source links.
- **REQ-004**: The MVP must include a person reviewing the report.
- **REQ-005**: The MVP must include a simple task list.
- **CON-001**: Do not build anything that files reports with a regulator.
- **CON-002**: Do not try to cover every regulator.
- **GUD-001**: Use one fixed demo company and a few chosen documents. Then the demo behaves the same way every time.
- **PAT-001**: Build thin slices that work end to end, early. Do not build each layer on its own and hope they join up at the end.

## 4. Interfaces & Data Contracts

### Plan

| Days | What gets done |
|---|---|
| 1–2 | Backend, database with `pgvector`, login, empty web app, upload for both kinds of document |
| 3–4 | Reading text with OCR fallback, cutting chunks at clauses, Titan embeddings, both kinds of search |
| 5–6 | The applicability step and the requirements step |
| 7–8 | Impact, gaps, risk, tasks |
| 9–10 | Source links, checking, review |
| 11–12 | Dashboard, task list, security |
| 13–14 | Quality checks, polish, practise the demo |

## 5. Acceptance Criteria

- **AC-001**: The demo runs without anyone editing the database by hand.
- **AC-002**: A rule document can be uploaded and analysed.
- **AC-003**: The report shows its sources.
- **AC-004**: The report shows at least one real gap with a task attached.
- **AC-005**: A reviewer can approve the report.
- **AC-006**: If an analysis job fails, the app copes.

## 6. Test Automation Strategy

Run a quick smoke test after each milestone. Run the full set before demo day. Keep one fixed set
of test cases for measuring AI quality, so the numbers mean something across runs.

## 7. Rationale & Context

For a hackathon, one flow that really works beats a wide product where nothing quite connects.
Judges can see the difference in about thirty seconds.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The git repo and issue tracker.

### Third-Party Services
- **SVC-001**: AWS AI and infrastructure services.

### Infrastructure Dependencies
- **INF-001**: A deployed web app, backend, database, storage, queue, and model access.

### Data Dependencies
- **DAT-001**: A few chosen rule documents and made-up company documents.

### Technology Platform Dependencies
- **PLT-001**: The app running on AWS.

### Compliance Dependencies
- **COM-001**: A person reviews, and every point has a source.

## 9. Examples & Edge Cases

If uploading live on stage looks risky, use a document we already loaded, and show its real source
details on screen. The audience should still see where it came from.

## 10. Validation Criteria

The MVP is ready when the demo works several times in a row, every AI point has a source, the
security tests pass, and we have written down what it cannot do.

## 11. Related Specifications / Further Reading

- `spec-schema-product-definition.md`
- `spec-process-impact-analysis.md`
- `spec-infrastructure-aws-deployment.md`
