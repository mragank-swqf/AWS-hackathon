---
title: RegImpact Multi-Agent Orchestration Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, agents, orchestration, ai]
---

# Introduction

This specification defines the roles, inputs, outputs, and execution order of the specialized AI agents used by RegImpact.

## 1. Purpose & Scope

The orchestration layer coordinates applicability, requirement extraction, impact mapping, gap detection, risk scoring, action planning, and verification.

## 2. Definitions

- **Agent**: A specialized AI component with a defined task and structured output.
- **Orchestrator**: Component responsible for workflow control.
- **Confidence**: A numeric estimate of output reliability.
- **Human review**: Review by an authorized person before approval.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Each agent shall have a single defined responsibility.
- **REQ-002**: Agent inputs and outputs shall use structured schemas.
- **REQ-003**: The orchestrator shall preserve intermediate outputs.
- **REQ-004**: Failed or low-confidence steps shall trigger retry, fallback, or human review.
- **REQ-005**: The verification agent shall run before final approval.
- **SEC-001**: Agents shall receive only the minimum required company data.
- **CON-001**: Agents shall not directly modify production systems.
- **GUD-001**: The orchestrator should prefer deterministic validation around model calls.

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
    {"agent": "risk", "status": "completed"},
    {"agent": "action_plan", "status": "completed"},
    {"agent": "verification", "status": "completed"}
  ],
  "human_review_required": true
}
```

## 5. Acceptance Criteria

- **AC-001**: The orchestrator executes agents in the defined order.
- **AC-002**: An agent failure is recorded and surfaced.
- **AC-003**: Low confidence causes human review.
- **AC-004**: The final report includes outputs from all completed stages.
- **AC-005**: Verification can reject unsupported conclusions.

## 6. Test Automation Strategy

Test successful workflows, retries, timeouts, malformed agent outputs, missing retrieval evidence, low confidence, and partial completion.

## 7. Rationale & Context

Specialized agents make the analysis more inspectable and allow deterministic checks between probabilistic model calls.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Analysis job queue.

### Third-Party Services
- **SVC-001**: LLM inference service.
- **SVC-002**: Retrieval service.

### Infrastructure Dependencies
- **INF-001**: Worker runtime, queue, database, and logging.

### Data Dependencies
- **DAT-001**: Company profile, regulation chunks, policies, and controls.

### Technology Platform Dependencies
- **PLT-001**: Workflow-compatible backend runtime.

### Compliance Dependencies
- **COM-001**: Human review for uncertain legal interpretations.

## 9. Examples & Edge Cases

If the applicability agent returns `uncertain`, the orchestrator shall still extract requirements but must mark the final report as requiring human review.

## 10. Validation Criteria

All agent outputs must validate against their schemas, and every workflow must have an auditable execution trace.

## 11. Related Specifications / Further Reading

- `spec-process-impact-analysis.md`
- `spec-process-evidence-verification.md`
- `spec-tool-api-contracts.md`
