---
title: RegImpact Agent Output Contracts Specification
version: 1.1
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [schema, agents, contracts, validation, ai]
---

# Introduction

This spec gives the exact output shape for every step in the analysis. These shapes are what the
worker is built around. `REQ-002` in `spec-process-agent-orchestration.md` asks for them.

## 1. Purpose & Scope

It covers all seven steps, what each one gives back, and the checks we run on that output before
we save it or pass it on.

Six steps call the AI. The risk step is plain code and makes no AI call. It is written up here
anyway, because it is still a step in the run and it still produces output like the rest.

## 2. Definitions

- **Step**: One stage of the run.
- **Atomic requirement**: One duty. Not two duties joined by "and".
- **Verbatim quote**: Words copied from the source exactly, not put in our own words.
- **Backed field**: A field that has to come with the chunk IDs that support it.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Check every step's output against its shape before saving it.
- **REQ-002**: Every fixed value must come from the lists in `spec-schema-input-contracts.md`. No step may invent a new one.
- **REQ-003**: Every field where the AI made a judgement must come with `source_chunk_id` or `supporting_chunk_ids`.
- **REQ-004**: When a step cannot answer, it must say so. If the shape allows `uncertain` or an empty list, that is the right answer. Do not guess.
- **REQ-005**: Every requirement must carry a `verbatim_quote`, so later steps and reviewers can tell the source wording from our wording.
- **CON-001**: No step returns `confidence`. The runner works that out from things it can measure.
- **CON-002**: No step returns `severity` or `overall_risk`. Plain code works those out from the table.
- **CON-003**: No step returns `requires_human_review`. The runner decides that.
- **CON-004**: No step returns a date without a `date_basis` next to it.
- **GUD-001**: Prefer several small backed fields over one long paragraph. We can check a backed field. We cannot check a paragraph.

## 4. Interfaces & Data Contracts

### Step 1: Applicability

Takes in: the company profile fields that matter for scope, plus the rule chunks we found.

```json
{
  "applicability": "likely_applicable",
  "rationale": "The circular names payment aggregators, which matches the company's organization type.",
  "matched_entity_descriptions": ["payment aggregators"],
  "supporting_chunk_ids": ["chunk_001"],
  "exclusions_noted": ["Does not cover cross-border remittance"],
  "unresolved_questions": ["Whether settlement-only operators are in scope"]
}
```

### Step 2: Requirements

One item in the list per duty.

```json
{
  "requirements": [
    {
      "requirement_text": "Maintain a documented grievance redressal process.",
      "obligation_type": "mandatory",
      "verbatim_quote": "Every payment aggregator shall maintain a documented grievance redressal process.",
      "source_chunk_id": "chunk_012",
      "clause_number": "3.2",
      "stated_dates": [
        {
          "date": "2026-12-01",
          "date_basis": "cited_compliance",
          "source_chunk_id": "chunk_012"
        }
      ]
    }
  ]
}
```

### Step 3: Impact

One item per requirement. Applicability shows up again here, per requirement. A rule can apply to
the company while one line in it does not.

```json
{
  "requirement_id": "req_001",
  "applicability": "applicable",
  "impact_level": "high",
  "affected_departments": ["Compliance", "Customer Support"],
  "required_capabilities": ["Ticket audit trail", "48-hour escalation path"],
  "rationale": "The obligation requires a documented process and a traceable escalation record.",
  "supporting_chunk_ids": ["chunk_012"]
}
```

### Step 4: Gap Detection

`evidence_assessment` lists every company chunk we looked at and why we took it or left it. That
way a reviewer can check our "no" and not just read it.

```json
{
  "requirement_id": "req_001",
  "gap_status": "insufficient_evidence",
  "explanation": "No uploaded policy describes an escalation path with a stated turnaround.",
  "evidence_chunk_ids": [],
  "evidence_assessment": [
    {
      "chunk_id": "chunk_501",
      "supports": false,
      "reason": "Describes complaint intake but states no escalation timeline."
    }
  ],
  "missing_evidence": ["Current grievance policy with approval record"]
}
```

To say `compliant` or `partial`, there must be at least one ID in `evidence_chunk_ids`, and each
one must come from a company document. Saying `compliant` with an empty list breaks the schema.
It is not a close call.

### Step 5: Risk (plain code)

No AI call. Worked out from the table in `spec-process-impact-analysis.md`. We copy the inputs
into the output too, so anyone can redo the sum later and see how we got there.

```json
{
  "requirement_id": "req_001",
  "severity": "high",
  "severity_inputs": {
    "obligation_type": "mandatory",
    "gap_status": "insufficient_evidence",
    "impact_level": "high",
    "deadline_proximity": "under_90_days"
  },
  "escalations_applied": ["impact_level_high"],
  "rationale": "Base severity medium from mandatory obligation with insufficient evidence, escalated one level for high impact."
}
```

### Step 6: Action Plan

```json
{
  "requirement_id": "req_001",
  "actions": [
    {
      "title": "Document and publish the grievance escalation matrix",
      "description": "Define escalation tiers with turnaround times and publish to the customer portal.",
      "owner_department": "Compliance",
      "effort": "medium",
      "depends_on": [],
      "target_date": "2026-11-15",
      "date_basis": "inferred_recommendation"
    }
  ]
}
```

Any date we picked ourselves must say `inferred_recommendation`. Only a date quoted from the
source may use a `cited_` value.

### Step 7: Verification

This step only reports what it found. The runner sets `verification_status` using the cut-offs in
`spec-process-evidence-verification.md`, and decides whether a person must review.

```json
{
  "citation_coverage": 0.92,
  "claim_checks": [
    {
      "claim_id": "claim_001",
      "chunk_id": "chunk_012",
      "supported": true,
      "contradicted": false,
      "reason": "The cited clause states the obligation directly."
    }
  ],
  "unsupported_claims": [
    "The suggested implementation deadline is not stated in the source."
  ],
  "missing_evidence": ["Current internal grievance policy"],
  "date_checks": [
    {
      "date": "2026-12-01",
      "date_basis": "cited_compliance",
      "found_in_source": true
    }
  ]
}
```

## 5. Acceptance Criteria

- **AC-001**: Output missing a required backed field fails the check.
- **AC-002**: Output with a value not on the list fails the check.
- **AC-003**: A requirement with two duties in it gets split into two.
- **AC-004**: A `compliant` result with no evidence chunk fails the check.
- **AC-005**: A date we made up, without `inferred_recommendation`, fails the check.
- **AC-006**: Output that includes `confidence`, `severity`, or `requires_human_review` fails the check.
- **AC-007**: The risk step gives the same answer every time for the same inputs.

## 6. Test Automation Strategy

For each shape, test data that should pass and data that should fail. Include requirements with
two duties, empty evidence, values not on the list, points with no source, and fields the step is
not allowed to send. The risk step gets a test for every box in the table. None of these tests
call the AI, so they all run in CI.

## 7. Rationale & Context

These shapes are where the "show your sources" promise actually gets enforced. By making chunk
IDs a required field, a point with no source becomes a failed check, instead of something a
reviewer has to notice on their own.

And by banning the AI from setting confidence, severity, and the review flag, we keep the guessy
part and the certain part apart. The code that decides whether a person must read a report can
then be tested without calling the AI at all.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The worker and the runner.

### Third-Party Services
- **SVC-001**: Amazon Bedrock, Claude Sonnet, for the six AI steps.

### Infrastructure Dependencies
- **INF-001**: The worker, and somewhere to save results.

### Data Dependencies
- **DAT-001**: Rule chunks and company document chunks, with their source info.

### Technology Platform Dependencies
- **PLT-001**: Pydantic models that match these shapes.

### Compliance Dependencies
- **COM-001**: Sources must be traceable, and a person must be able to review.

## 9. Examples & Edge Cases

Take a line that reads "maintain a grievance process and publish quarterly complaint data". That
is two duties, not one. So step 2 returns two items that share the same `source_chunk_id`. They
have different impacts, they may belong to different teams, and one can be done without the
other.

If a requirement has no date in it, `stated_dates` is an empty list. That is the right answer.
Do not fill it with a date we guessed.

## 10. Validation Criteria

Every step's output must match its shape, must back up its judgement calls, and must leave out
the fields the runner owns.

## 11. Related Specifications / Further Reading

- `spec-process-agent-orchestration.md`
- `spec-schema-input-contracts.md`
- `spec-process-impact-analysis.md`
- `spec-process-evidence-verification.md`
