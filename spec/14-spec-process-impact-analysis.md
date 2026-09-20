---
title: RegImpact Regulatory Impact Analysis Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, impact, compliance, risk]
---

# Introduction

This spec says how we work out whether a rule applies, what it asks for, who it hits, what the
company is missing, and what to do about it.

## 1. Purpose & Scope

This runs once for each pair of one company and one rule document. It produces a report where
every point has a source.

## 2. Definitions

- **Applicability**: Whether a rule, or one line in it, applies to this company.
- **Requirement**: One thing the rule says the company must do.
- **Impact**: The work needed to meet that requirement.
- **Remediation**: Fixing a gap.
- **Atomic**: One duty per requirement. Not two duties joined by "and".

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Work out applicability from the company profile and the rule text. Both.
- **REQ-002**: Split requirements so each one is a single duty.
- **REQ-003**: Say which teams each requirement affects.
- **REQ-004**: Compare each requirement against chunks from the company's uploaded documents. Only mark it `compliant` or `partial` if you can point at one of those chunks. What the company typed into its profile never counts.
- **REQ-005**: Each gap needs a status, how bad it is, a plain reason, and what to do.
- **REQ-006**: Keep "must do" and "should do" apart in the report.
- **REQ-007**: Every point that matters needs a source link.
- **REQ-008**: Record applicability per requirement, as well as for the rule as a whole.
- **REQ-009**: Work out `severity` and `overall_risk` in code, using the table in section 4. The AI supplies the facts. It must not pick the score.
- **SEC-001**: Only use documents this company is allowed to see.
- **CON-001**: Never make our own suggestion look like text from the rule.
- **GUD-001**: When we are not sure, say so plainly. Use the `uncertain` labels.

## 4. Interfaces & Data Contracts

```json
{
  "requirement_id": "req_001",
  "requirement_text": "Maintain a documented grievance process.",
  "obligation_type": "mandatory",
  "applicability": "likely_applicable",
  "impact_level": "high",
  "affected_departments": ["Compliance", "Customer Support"],
  "gap_status": "insufficient_evidence",
  "severity": "high",
  "recommended_action": "Upload the current grievance process and approval record.",
  "citations": ["citation_001"]
}
```

### How we score risk

The AI only gives us facts it can back up: `obligation_type`, `gap_status`, `impact_level`, and
the date from the source. Then plain code looks up the score in a table. Same facts in, same
score out, every time. And we can always tell a reviewer why.

Start with this table:

| | `non_compliant` | `insufficient_evidence` | `partial` | `compliant` |
|---|---|---|---|---|
| `mandatory` | high | medium | medium | low |
| `recommended` | medium | low | low | low |

Then bump the score up one level for each of these. Stop at `critical`:

- `impact_level` is `high`.
- The date has already passed, or is less than 30 days away.

For the whole report, `overall_risk` is the worst single score. But if three or more requirements
are `high` or worse, make it `critical`.

## 5. Acceptance Criteria

- **AC-001**: The rule names the company's own type. The report says it applies, and points at that line.
- **AC-002**: A requirement comes out as one duty, not two joined together.
- **AC-003**: The company has uploaded nothing. The status comes out `insufficient_evidence`.
- **AC-004**: The requirement is about systems. Engineering shows up as an affected team.
- **AC-005**: A claim has no source. The checking step flags the report.

## 6. Test Automation Strategy

Write down the right answer for a set of test cases, then check what we produce against it. Cover
applicability, requirements, teams, gaps, severity, and sources. Include rules that are vague,
rules that were replaced, rules with exceptions, and rules with dates.

## 7. Rationale & Context

The value of this product is turning legal wording into real work. But only if we do two things
while we do it: keep saying where each point came from, and admit when we are not sure.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Where rule documents and company documents are stored.

### Third-Party Services
- **SVC-001**: The AI model.
- **SVC-002**: Our search.

### Infrastructure Dependencies
- **INF-001**: The worker, and somewhere to save results.

### Data Dependencies
- **DAT-001**: Rule clauses, the company profile, and company documents.

### Technology Platform Dependencies
- **PLT-001**: Something that can produce JSON and check it.

### Compliance Dependencies
- **COM-001**: A person reviews, and every decision has a source.

## 9. Examples & Edge Cases

A rule can apply to the company but not to one of its products. So we cannot just mark the whole
document as applying or not. We have to do it line by line.

## 10. Validation Criteria

An analysis is done when applicability, requirements, impacts, gaps, risk, tasks, and sources are
all there and they agree with each other.

## 11. Related Specifications / Further Reading

- `13-spec-process-agent-orchestration.md`
- `12-spec-schema-agent-contracts.md`
- `15-spec-process-evidence-verification.md`
- `04-spec-schema-input-contracts.md`
