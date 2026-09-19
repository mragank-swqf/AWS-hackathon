---
title: RegImpact Hackathon Demo and Demonstration Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [design, demo, hackathon, presentation]
---

# Introduction

This spec is the demo script. It says exactly what we show, in what order, so it comes out the
same every time.

## 1. Purpose & Scope

The demo shows one thing: a fintech starts with a long rule PDF and ends up with a list of tasks,
where every point links back to the source.

## 2. Definitions

- **Demo company**: A made-up company we use for the demo.
- **Demo path**: The exact order of clicks we show the judges.
- **Backed by sources**: Every point links to the lines it came from.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Use a made-up payment aggregator, set up in advance.
- **REQ-002**: The RBI corpus is already indexed. Show official source URLs. Do not live-download during the five-minute talk.
- **REQ-003**: Show profile → applicable RBI set → evidence → impact → gaps → risk → actions → sources.
- **REQ-004**: Show a seeded regulatory update (48-hour escalation added) and that the company is affected.
- **REQ-005**: Finish in about five minutes.
- **REQ-006**: The demo company must already have at least two policy PDFs uploaded.
- **CON-001**: Do not rely on downloading anything live during the demo.
- **GUD-001**: Seed the corpus and policies beforehand. Only run live the portfolio impact if it has been timed.

## 4. Interfaces & Data Contracts

The demo company:

```json
{
  "company_name": "PayFlow Technologies",
  "organization_type": "payment_aggregator",
  "products": [
    "Online payments",
    "Merchant settlements",
    "Refund processing",
    "Customer grievance handling"
  ],
  "regulatory_entities": ["RBI"]
}
```

The order of clicks:

```text
Create company
→ Upload company evidence (grievance policy, KYC policy)
→ Upload regulation
→ Start analysis
→ Show applicability
→ Show requirements
→ Show impacted departments
→ Show compliance gaps
→ Show risk
→ Show action plan
→ Open citation
→ Approve analysis
→ View action tracker
```

Set up the demo data so the findings differ from each other. At least one requirement must come
back `compliant` or `partial`, pointing at a policy the company uploaded. At least one must come
back as a real gap.

This matters more than it sounds. If every single requirement says `insufficient_evidence`, it
looks like our product cannot spot anything a company already has. The contrast is the story.

## 5. Acceptance Criteria

- **AC-001**: The demo runs from a fresh browser with nothing cached.
- **AC-002**: Every screen loads without anyone touching the backend.
- **AC-003**: At least one finding shows a source you can click.
- **AC-004**: At least one gap creates a task.
- **AC-005**: The approval status visibly changes on screen.
- **AC-006**: We say out loud what the product cannot do.

## 6. Test Automation Strategy

Run the whole demo path at least five times before we submit. Try it on a clean account, on a slow
network, and with an AI job forced to fail.

## 7. Rationale & Context

The strongest thing we can show is the before and after: a long document nobody wants to read,
turned into a short list of jobs a compliance team can actually work through.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The deployed app.

### Third-Party Services
- **SVC-001**: AWS AI services.

### Infrastructure Dependencies
- **INF-001**: A stable demo deployment with the data already loaded.

### Data Dependencies
- **DAT-001**: The made-up company and the chosen rule document.

### Technology Platform Dependencies
- **PLT-001**: A browser over HTTPS.

### Compliance Dependencies
- **COM-001**: Say clearly that this helps a compliance review. It does not replace one.

## 9. Examples & Edge Cases

If the analysis takes longer than we expect, the screen should show progress, and the presenter
should talk through what each step is doing. Never sit in front of a blank screen.

## 10. Validation Criteria

The demo is ready when it shows the point of the product, shows its sources, shows a person
reviewing, shows the task list, and does all of that the same way every time.

## 11. Related Specifications / Further Reading

- `01-spec-schema-product-definition.md`
- `09-spec-design-frontend.md`
- `02-spec-process-mvp-delivery.md`
