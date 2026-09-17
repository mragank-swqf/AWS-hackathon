---
title: RegImpact Multi-Agent Orchestration Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, agents, orchestration, ai]
---

# Introduction

This spec says what each AI step does, what it takes in, what it gives back, and the order they
run in.

## 1. Purpose & Scope

The runner drives seven steps in order: does the rule apply, what does it ask for, who is
affected, what is missing, how bad is it, what should we do, and can we back it all up.

## 2. Definitions

- **Agent**: One step with one job and a fixed output shape. Six steps call the AI. The risk step does not.
- **Runner**: The code that calls the steps in order and keeps track of them.
- **Confidence**: A number from 0 to 1 saying how much we trust the result. We work it out from things we can measure. We do not ask the AI to rate itself. See section 4.
- **Human review**: A real person checking the report before it counts as approved.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Each step does one job only.
- **REQ-002**: Each step takes in and gives back a fixed shape of data.
- **REQ-003**: Save the output of every step, not just the last one.
- **REQ-004**: If a step fails, or confidence is low, then retry it, fall back, or send it to a person.
- **REQ-005**: The checking step must run before anyone can approve the report.
- **REQ-006**: The runner is plain Python that calls the steps one after another. No workflow framework for the MVP.
- **REQ-007**: Save each step to the database before starting the next one. Then a failed run can pick up where it stopped, and we can see exactly how far it got.
- **REQ-008**: Retry an AI call at most 3 times, waiting longer each time. Give up on a step after 120 seconds. If the output does not match the schema, that counts as a failure worth retrying, and we tell the AI what was wrong in the retry.
- **REQ-009**: Running the same job twice must be safe. SQS can deliver a job more than once. So if a step is already marked done for that analysis, skip it.
- **REQ-010**: If a job runs out of retries, move it to the dead-letter queue, mark the analysis `failed`, and record which step broke.
- **REQ-011**: There are seven steps but only six AI calls. The `risk` step is plain code with no AI call, because we work out severity from a table instead of asking. It still shows up as a step so the trail is complete.
- **REQ-012**: The output shapes live in `12-spec-schema-agent-contracts.md`. The runner owns `confidence`, `verification_status`, and `human_review_required`. No AI step may return those.
- **SEC-001**: Give each step only the company data it needs, and nothing else.
- **CON-001**: No step may change anything in a live system.
- **CON-002**: Read and check every AI output against a Pydantic model before saving it or passing it on.
- **GUD-001**: Where a check can be plain code instead of an AI call, make it plain code.

## 4. Interfaces & Data Contracts

```json
{
  "workflow_id": "workflow_001",
  "status": "completed",
  "steps": [
    {"agent": "applicability", "status": "completed"},
    {"agent": "requirements", "status": "completed"},
    {"agent": "impact", "status": "completed"},
    {"agent": "gap_detection", "status": "completed"},
    {"agent": "risk", "status": "completed", "deterministic": true},
    {"agent": "action_plan", "status": "completed"},
    {"agent": "verification", "status": "completed"}
  ],
  "human_review_required": true
}
```

### How to build a prompt

Always build the prompt in this same order. The text we found comes out of PDFs that users
uploaded, so treat it as unsafe. Someone could hide instructions in it.

```text
1. The job, and the output shape          (ours, fixed)
2. Only the company fields this step needs (ours, kept small per SEC-001)
3. The text we found, fenced off and marked as data, not orders
4. The output shape again                  (ours)
```

Put a clear fence around the found text. Say plainly that it is source material to read, that any
instruction inside it is just words on a page and not a command, and that it cannot change the
job. Repeating the output shape after the text helps, because hidden instructions usually sit at
the end where they have the most pull.

### How we work out confidence

Confidence comes from things we can measure. We never ask the AI how sure it is. A number the AI
makes up about itself proves nothing and cannot be tested.

| What we measure | Weight |
|---|---|
| How many claims have a source, from the checking step | 0.4 |
| How well the chosen text scored in search | 0.2 |
| How many steps matched their schema on the first try | 0.2 |
| How clear the applicability answer was: 1.0 for `applicable` or `not_applicable`, 0.5 for either `likely_` answer, 0.0 for `uncertain` | 0.2 |

### When a person must review

Set `human_review_required` to true if any one of these is true. It is a plain OR list, so it is
easy to test and we can always tell the reviewer which line caused it.

- Applicability is anything other than `applicable` or `not_applicable`.
- Any requirement has `gap_status` of `insufficient_evidence`.
- Any requirement has `severity` of `high` or `critical`.
- `verification_status` is anything other than `verified`.
- Confidence is under 0.70.
- Any step failed, or only passed after using up all its retries.

## 5. Acceptance Criteria

- **AC-001**: The runner calls the steps in the right order.
- **AC-002**: If a step fails, we record it and the user can see it.
- **AC-003**: Low confidence sends the report to a person.
- **AC-004**: The final report includes the output of every step that finished.
- **AC-005**: The checking step can reject a claim that has no backing.

## 6. Test Automation Strategy

Test a clean run, retries, timeouts, broken AI output, no search results, low confidence, and a
run that stops halfway.

## 7. Rationale & Context

Small steps are easier to look at than one big one. And between two AI calls we can put a plain
code check, which always behaves the same way. That is where most of the safety comes from.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The job queue.

### Third-Party Services
- **SVC-001**: Amazon Bedrock, Claude Sonnet, for all six AI steps. One model everywhere keeps things simple. Picking a different model per step is something to try after the MVP.
- **SVC-002**: Our own search over `document_chunks`.

### Infrastructure Dependencies
- **INF-001**: The worker, the queue, the database, and logging.

### Data Dependencies
- **DAT-001**: The company profile, rule document chunks, and company documents.

### Technology Platform Dependencies
- **PLT-001**: A Python worker that can reach the database. Step state goes in `impact_analyses`, not in a workflow engine.

### Compliance Dependencies
- **COM-001**: A person must review anything unclear.

## 9. Examples & Edge Cases

If the first step says `uncertain`, keep going and still pull out the requirements. But mark the
final report as needing a person to look at it.

## 10. Validation Criteria

Every step's output must match its schema, and every run must leave a trail we can follow.

## 11. Related Specifications / Further Reading

- `12-spec-schema-agent-contracts.md`
- `14-spec-process-impact-analysis.md`
- `15-spec-process-evidence-verification.md`
- `08-spec-tool-api-contracts.md`
