---
title: RegImpact Hackathon Demo and Demonstration Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [design, demo, hackathon, presentation]
---

# Introduction

This specification defines the repeatable demonstration flow for RegImpact.

## 1. Purpose & Scope

The demo shall show how a fintech can move from a regulatory PDF to an evidence-backed compliance action plan.

## 2. Definitions

- **Demo company**: Fictional company used to demonstrate the product.
- **Demo path**: Ordered sequence of interactions shown to judges.
- **Evidence-backed**: Supported by source citations and excerpts.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The demo shall use a prepared fictional payment aggregator profile.
- **REQ-002**: The demo shall use at least one source-linked regulatory document.
- **REQ-003**: The demo shall show extraction, applicability, impact, gaps, actions, and citations.
- **REQ-004**: The demo shall show human-review status.
- **REQ-005**: The demo shall complete within approximately five minutes.
- **CON-001**: Do not depend on unstable live web scraping during the demo.
- **GUD-001**: Preload documents and use live analysis only where reliable.

## 4. Interfaces & Data Contracts

Demo company:

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

Demo sequence:

```text
Create company
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

## 5. Acceptance Criteria

- **AC-001**: The demo can be run from a clean browser session.
- **AC-002**: All screens load without manual backend intervention.
- **AC-003**: At least one finding includes a visible citation.
- **AC-004**: At least one gap generates an action item.
- **AC-005**: The reviewer approval state changes visibly.
- **AC-006**: Known limitations are stated in the presentation.

## 6. Test Automation Strategy

Run the complete demo path at least five times before submission. Test with a clean account, slow network simulation, and failed model-job simulation.

## 7. Rationale & Context

The strongest demonstration is a clear transformation from a long regulatory document into concrete, reviewable work for a compliance team.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Deployed RegImpact application.

### Third-Party Services
- **SVC-001**: AWS AI services.

### Infrastructure Dependencies
- **INF-001**: Stable demo deployment and seeded data.

### Data Dependencies
- **DAT-001**: Fictional company and curated regulation.

### Technology Platform Dependencies
- **PLT-001**: Browser and HTTPS.

### Compliance Dependencies
- **COM-001**: Clearly state that output supports, but does not replace, human compliance review.

## 9. Examples & Edge Cases

If analysis takes longer than expected, the UI shall show progress and the presenter shall explain the agent stages rather than displaying a blank screen.

## 10. Validation Criteria

The demo shall demonstrate the core value proposition, source traceability, human review, and action tracking in a repeatable manner.

## 11. Related Specifications / Further Reading

- `spec-schema-product-definition.md`
- `spec-design-frontend.md`
- `spec-process-mvp-delivery.md`
