---
title: RegImpact Evidence and Citation Verification Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, evidence, citations, verification, ai-safety]
---

# Introduction

This spec says how we check that every point in a report is really backed up by the source text
or by a company document.

## 1. Purpose & Scope

It covers making source links, matching each point to its source, catching points with no
backing, checking dates, checking applicability, and deciding when a person must step in.

## 2. Definitions

- **Citation**: A link to a document, page, section, or clause.
- **Claim**: Any statement the report makes.
- **Citation coverage**: Out of all the points that matter, how many have a source link. A number from 0 to 1.
- **Unsupported claim**: A point the found text does not back up.
- **Contradicted claim**: A point the source text actually disagrees with. Worse than unsupported.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Every point about what a rule says needs a source link.
- **REQ-002**: A source link must name the document, and the page or clause where we can find it.
- **REQ-003**: Keep source text and our own reading of it clearly apart.
- **REQ-004**: Flag any date we cannot find in the source.
- **REQ-005**: Flag any applicability call we cannot back up.
- **REQ-006**: The result must be data, not prose, so code can act on it.
- **REQ-007**: Set `verification_status` from coverage and the number of bad points. `verified` needs coverage of 0.95 or more and zero unsupported points. `partially_verified` needs 0.80 or more. Below 0.80 it is `unverified`. If even one point is contradicted by the source, it is `failed`, whatever the coverage.
- **REQ-008**: Check that a source link actually fits, not just that it exists. Score each point against the chunk it cites. If the chunk does not say it, report the point as unsupported.
- **REQ-009**: Give the checking step the point and the chunk as two separate fenced inputs, and ask it one thing only: does this chunk say this? Do not show it how the earlier step reasoned. Otherwise a point shaped by hidden text in a PDF could carry that same framing into the check meant to catch it.
- **REQ-010**: Label every date with `date_basis`. A date quoted from the source is `cited_effective` or `cited_compliance`. Any date we came up with ourselves is `inferred_recommendation`, and must never be shown as something the regulator demands.
- **SEC-001**: A source link must never show a document the user is not allowed to see.
- **CON-001**: A link being there does not mean it is right. Those are two different things.
- **GUD-001**: Show the reviewer the actual lines of source text, not just a reference.

## 4. Interfaces & Data Contracts

The checking step only reports what it found. The runner sets `verification_status` using the
REQ-007 cut-offs, and works out `requires_human_review` from the list in
`13-spec-process-agent-orchestration.md`. The step itself returns neither.

```json
{
  "citation_coverage": 0.92,
  "unsupported_claims": [
    "The suggested deadline is not explicitly stated in the source."
  ],
  "missing_evidence": [
    "Current internal grievance policy"
  ]
}
```

For this example the runner would then set `verification_status: "partially_verified"` and
`requires_human_review: true`. The full output shape is in `12-spec-schema-agent-contracts.md`.

## 5. Acceptance Criteria

- **AC-001**: A point with no source link gets flagged.
- **AC-002**: A link pointing at the wrong clause gets flagged.
- **AC-003**: A date that is not in the source gets flagged.
- **AC-004**: Our own suggestion is never shown as a legal must.
- **AC-005**: A reviewer can click a link and see the source text.

## 6. Test Automation Strategy

Build test cases with points that are fully backed, half backed, contradicted, and not backed at
all. Measure how often our links are right, how many we miss, how many points have no backing,
and how long the check takes.

## 7. Rationale & Context

A compliance report has to be checkable by a person. This step is what stops the AI from making
things up, and it helps the reviewer see which parts came from the rule and which parts are our
reading of it.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Where source documents are stored.

### Third-Party Services
- **SVC-001**: An AI model to judge whether a chunk backs a point.

### Infrastructure Dependencies
- **INF-001**: The citations table and the audit log.

### Data Dependencies
- **DAT-001**: Source chunks, the points made, and the reports.

### Technology Platform Dependencies
- **PLT-001**: Something that can check output against a schema.

### Compliance Dependencies
- **COM-001**: A person reviews anything high impact or unclear.

## 9. Examples & Edge Cases

Say a circular gives a date when the rule starts, but never says by when you must have finished
the work. Then we show the start date as a real date from the source, and mark any finish date we
suggest as our own recommendation.

## 10. Validation Criteria

This step works when it catches missing links, wrong links, and points with no backing, and gives
back a clear status.

## 11. Related Specifications / Further Reading

- `11-spec-process-rag-pipeline.md`
- `14-spec-process-impact-analysis.md`
- `08-spec-tool-api-contracts.md`
