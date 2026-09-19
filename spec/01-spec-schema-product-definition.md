---
title: RegImpact Product Definition Specification
version: 1.3
date_created: 2026-09-17
last_updated: 2026-09-19
owner: RegImpact Team
tags: [schema, product, fintech, compliance, ai, rbi]
---

# Introduction

RegImpact is an RBI-first regulatory intelligence and compliance-impact engine. It automatically
connects official RBI publications to a company's policies, evidence, risks, and remediation
actions. The reasoning engine stays regulator-agnostic so a later SEBI or IRDAI pack can plug in.

It is not positioned as "the first RBI compliance product." The point of view is: the user should
not hunt for circulars. The corpus is maintained from official RBI sources; the user's job is to
provide company context and internal evidence.

## 1. Purpose & Scope

RegImpact maintains an indexed RBI regulatory corpus (discover, download, version, chunk, embed).
A company profile plus structured applicability rules decide which documents apply. The existing
seven-step compliance pipeline then runs against those documents and the company's uploaded
evidence.

The MVP is for Indian fintechs, NBFCs, payment aggregators, banks, and lending platforms.

The MVP must do all of this:

- Let a user create a company profile with a regulated entity type.
- Maintain an RBI corpus from official sources, with a seeded pack so the demo does not depend on
  live downloads.
- Decide applicable / not applicable / uncertain without treating uncertain as applicable.
- Still allow a secondary upload of a regulatory PDF.
- Extract requirements, find evidence-backed gaps, score risk, and propose actions.
- Detect version changes between RBI documents and show added / modified / removed clauses.
- Let a person review uncertain applicability and high-risk conclusions.

Manual regulation upload is no longer the main path.

## 2. Definitions

- **RegImpact**: This product.
- **RBI**: Reserve Bank of India. The main regulator here.
- **NBFC**: Non-Banking Financial Company.
- **RAG**: Retrieval-Augmented Generation. Finding the right text first, then asking the AI about it.
- **MVP**: Minimum Viable Product. The smallest version that works.
- **Compliance gap**: Something the rule asks for that the company cannot show it has.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: A user must be able to create and edit a company profile.
- **REQ-002**: The system must accept rule documents and company documents as PDF files.
- **REQ-003**: The system must produce a report with a fixed set of sections.
- **REQ-004**: The report must cover these things: does the rule apply, what it asks for, which teams are affected, what is missing, how risky it is, what to do, and where each point came from.
- **REQ-005**: A person must be able to check a report before it counts as approved.
- **REQ-006**: The system must also spot the controls a company already has. It must not only list gaps.
- **CON-001**: The MVP does not give legal advice.
- **CON-002**: The MVP does not send anything to a regulator.
- **GUD-001**: Every point the AI makes should link back to the source text.
- **PAT-001**: Pass data between steps as JSON.

## 4. Interfaces & Data Contracts

The product works with these things:

| Thing | What it is |
|---|---|
| Company | A company and the controls it has |
| Regulation | A rule document from a regulator |
| Policy | A company document uploaded as proof |
| Analysis | One run of the report, and its result |
| Gap | Something the company is missing |
| Action | A task to fix a gap |
| Citation | A link to the source text |
| Review | A person's decision on a report |

## 5. Acceptance Criteria

- **AC-001**: A user fills in a company profile, saves it, and can open it again later.
- **AC-002**: A user uploads a rule PDF and sees it in the list of rules.
- **AC-003**: An analysis finishes and the report has every section filled in.
- **AC-004**: If the system is not sure the rule applies, or proof is missing, the report is marked as needing a person to check it.

## 6. Test Automation Strategy

- **Test Levels**: Small unit tests, tests across parts, full user journey tests, and tests of AI output quality.
- **Frameworks**: Pytest for the backend. Playwright for the browser. Contract tests for the API.
- **Test Data Management**: Use made-up companies and a small set of real public rule documents.
- **CI/CD Integration**: Run linting, unit tests, API tests, and security checks in GitHub Actions.
- **Coverage Requirements**: At least 70% of the important backend code covered by tests.
- **Performance Testing**: Time how long upload, search, and a full analysis take on real PDFs.

## 7. Rationale & Context

Rule documents are long and hard to read. Compliance teams need a repeatable way to turn them
into real work. So this product is built to show its sources and to be checked by a person. It is
not built to make legal calls on its own.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulator websites. Where the rule documents come from.
- **EXT-002**: The company's own files. Its policies and controls.

### Third-Party Services
- **SVC-001**: Amazon Bedrock. Runs the AI model and makes embeddings.
- **SVC-002**: Amazon Textract. Reads text from scanned pages.

### Infrastructure Dependencies
- **INF-001**: File storage, a database, a job queue, and somewhere to run the app.

### Data Dependencies
- **DAT-001**: Rule PDFs, company policies, control write-ups, and proof files.

### Technology Platform Dependencies
- **PLT-001**: A web app on AWS with a REST API.

### Compliance Dependencies
- **COM-001**: A person must check any finding that is unclear or high impact.

## 9. Examples & Edge Cases

```json
{
  "applicability": "uncertain",
  "human_review_required": true,
  "reason": "The source does not clearly define whether the company's business model is covered."
}
```

## 10. Validation Criteria

This spec is met when we can show the whole flow working, from uploading a document to an
approved list of tasks.

## 11. Related Specifications / Further Reading

- `04-spec-schema-input-contracts.md`
- `12-spec-schema-agent-contracts.md`
- `14-spec-process-impact-analysis.md`
- `03-spec-architecture-system.md`
