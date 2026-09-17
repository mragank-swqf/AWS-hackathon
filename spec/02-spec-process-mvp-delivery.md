---
title: RegImpact MVP Delivery and Implementation Process Specification
version: 1.3
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, mvp, delivery, hackathon]
---

# Introduction

This spec says what order we build things in, what is in the MVP and what is not, and what has to
work for the demo.

## 1. Purpose & Scope

The plan is built around getting one whole flow working, start to finish, rather than lots of
half-done parts.

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
- **CON-003**: There is no login in the hackathon build. Use one fixed demo user and one demo company.
- **GUD-001**: Use one fixed demo company and a few chosen documents. Then the demo behaves the same way every time.
- **PAT-001**: Build thin slices that work end to end, early. Do not build each layer on its own and hope they join up at the end.

### Left for later

These are all specified elsewhere and are worth building one day. None of them show up in the
demo, so none of them are in the hackathon build. Each spec that describes one says the same
thing.

| Left out | Why it is safe to skip |
|---|---|
| Login, roles, permissions | The biggest job with the least to show. One fixed demo user does the same demo. |
| OCR through Textract | Pick demo PDFs that already have a text layer, and we never need it. |
| Dashboard | The demo never opens it. The analysis screen is where the story is. |
| Audit log | Good practice, invisible in a demo. |
| Upload caps, paging, duplicate-request handling | Only matter with real users and real load. |
| Tracking replaced rule documents | Only matters once there are many documents. |
| A test coverage target | Keep the quick tests. Drop the number. |

Write these down in the talk as things we know we left out. Saying "we cut login on purpose" is
much stronger than being asked about it and having no answer.

## 4. Interfaces & Data Contracts

### Build order

Build in this order. The order is what matters, not a calendar. Spec filenames are numbered
the same way: `01` first, `17` last. If something has to be cut, cut from the highest number,
not the middle.

| Order | Spec | Stage | What gets done |
|---|---|---|---|
| 01 | `01-spec-schema-product-definition.md` | Plan | What the product is |
| 02 | `02-spec-process-mvp-delivery.md` | Plan | What is in, what is out, this list |
| 03 | `03-spec-architecture-system.md` | Plan | Parts of the system |
| 04 | `04-spec-schema-input-contracts.md` | Plan | Incoming data and fixed value lists |
| 05 | `05-spec-data-database.md` | 1 | Database with `pgvector` |
| 06 | `06-spec-infrastructure-aws-deployment.md` | 1 | AWS hosting, storage, queue, models |
| 07 | `07-spec-security-access-control.md` | 1 | Secrets, private files, `company_id` |
| 08 | `08-spec-tool-api-contracts.md` | 1 | Backend API |
| 09 | `09-spec-design-frontend.md` | 1 | Empty web app, then screens |
| 10 | `10-spec-process-document-ingestion.md` | 2 | PDF upload, text, clause chunks |
| 11 | `11-spec-process-rag-pipeline.md` | 2 | Titan embeddings, both kinds of search |
| 12 | `12-spec-schema-agent-contracts.md` | 3 | Output shape of each AI step |
| 13 | `13-spec-process-agent-orchestration.md` | 3 | Runner, retries, review flag |
| 14 | `14-spec-process-impact-analysis.md` | 3–4 | Applicability, requirements, impact, gaps, risk, tasks |
| 15 | `15-spec-process-evidence-verification.md` | 5 | Source links, checking step, approve |
| 16 | `16-spec-design-demo-flow.md` | 6 | Demo data and the click path |
| 17 | `17-spec-process-testing-evaluation.md` | Gate | Tests that must pass |

Stage 1 and stage 2 are the ones you cannot skip. Nothing else works without upload, chunks, and
search.

Stage 6 is not padding. A demo nobody has run start to finish will break in front of the judges.

## 5. Acceptance Criteria

- **AC-001**: The demo runs without anyone editing the database by hand.
- **AC-002**: A rule document can be uploaded and analysed.
- **AC-003**: The report shows its sources.
- **AC-004**: The report shows at least one real gap with a task attached.
- **AC-005**: A reviewer can approve the report.
- **AC-006**: If an analysis job fails, the app copes.

## 6. Test Automation Strategy

Run a quick smoke test after each stage. Run the full set before the demo. Keep one fixed set
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

- `01-spec-schema-product-definition.md`
- `14-spec-process-impact-analysis.md`
- `06-spec-infrastructure-aws-deployment.md`
