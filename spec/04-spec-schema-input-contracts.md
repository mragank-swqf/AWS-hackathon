---
title: RegImpact Input Schema and Data Contracts Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [schema, data, api, validation]
---

# Introduction

This spec lists the data the system takes in, and the rules for checking it. It covers company
profiles, rule documents, analysis requests, company documents, and controls.

## 1. Purpose & Scope

These rules apply everywhere data comes in: web forms, the API, the database, background jobs,
and the input we hand to the AI.

## 2. Definitions

- **JSON Schema**: A way to write down the shape of a JSON object so code can check it.
- **Company profile**: What the company is and what it does.
- **Evidence**: A document that shows the company does what it says.
- **Control**: A policy, process, or system the company uses to meet a rule.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Check all incoming data before saving it or acting on it.
- **REQ-002**: Say which fields are required.
- **REQ-003**: If a field has a fixed list of allowed values, reject anything not on the list.
- **REQ-004**: Write dates as `YYYY-MM-DD`.
- **REQ-005**: An analysis request must name exactly one company and one rule document.
- **REQ-006**: All the fixed value lists live in section 4 below, and only there. No other spec or module may invent a new status value.
- **REQ-007**: What a company types about itself is not proof. Only an uploaded document counts as proof.
- **REQ-008**: `affected_departments` and `owner_department` must use the `department` list, not free text. That way we can group and route findings.
- **SEC-001**: Anything that belongs to a company must be tagged with `company_id`.
- **CON-001**: If a field arrives that we do not know, either reject it or keep it under `metadata`. Do not silently drop it.
- **GUD-001**: Do not break old clients within the same major version.

## 4. Interfaces & Data Contracts

### Fixed value lists

This is the only place these lists are written down. REQ-003 has nothing to check against without
it. Database columns, Pydantic models, and AI output schemas all check against these.

```text
organization_type:    payment_aggregator | payment_gateway | nbfc | lending_platform |
                      prepaid_instrument_issuer | account_aggregator | other
document_type:        circular | master_direction | notification | guideline | faq |
                      press_release
processing_status:    queued | extracting | chunking | embedding | completed | failed
extraction_method:    text | unreadable
analysis_status:      queued | processing | completed | failed | cancelled
analysis_depth:       quick | standard | deep
applicability:        applicable | likely_applicable | uncertain |
                      likely_not_applicable | not_applicable
obligation_type:      mandatory | recommended
impact_level:         high | medium | low | none
gap_status:           compliant | partial | non_compliant | insufficient_evidence
severity:             critical | high | medium | low
overall_risk:         critical | high | medium | low
verification_status:  verified | partially_verified | unverified | failed
review_status:        pending | approved | rejected
action_status:        open | in_progress | blocked | done
evidence_type:        policy | procedure | control_description | audit_report | other
date_basis:           cited_effective | cited_compliance | inferred_recommendation
deadline_proximity:   overdue | under_30_days | under_90_days | beyond_90_days | none
effort:               low | medium | high
department:           Compliance | Legal | Risk | Operations | Product | Engineering |
                      Finance | Customer Support | Information Security |
                      Internal Audit | Human Resources
```

Left for later, along with the features that use them: `role`, `lifecycle_status`,
`audit_outcome`, `audit_action`, and the `more_evidence_requested` value on `review_status`.

`analysis_depth` changes how much text we search and how much it costs. Nothing else.

| Depth | Chunks per search | Search again per requirement |
|---|---|---|
| `quick` | 10 | No |
| `standard` | 25 | Yes, but only for `mandatory` ones |
| `deep` | 50 | Yes, for all of them |

### Company Profile

```json
{
  "company_name": "PayFlow Technologies",
  "organization_type": "payment_aggregator",
  "business_model": "Online merchant payment processing",
  "operating_regions": ["India"],
  "products": ["Payments", "Refunds", "Settlements"],
  "customer_segments": ["Merchants", "Consumers"],
  "regulatory_entities": ["RBI"],
  "uses_customer_data": true,
  "uses_automated_decisioning": false,
  "has_outsourced_operations": true,
  "existing_policies": ["KYC Policy", "Grievance Policy"],
  "internal_controls": ["Access reviews", "Audit logging"]
}
```

### Regulation

```json
{
  "title": "Example Regulatory Circular",
  "regulator": "RBI",
  "document_type": "circular",
  "publication_date": "2026-09-01",
  "effective_date": "2026-12-01",
  "reference_number": "RBI/2026/001",
  "source_url": "https://example.gov.in/document.pdf",
  "lifecycle_status": "active",
  "supersedes_document_id": null,
  "raw_text": "Extracted document text"
}
```

### Company Policy Document

This is real proof. Note the difference from the profile: `existing_policies` and
`internal_controls` above are just lists of names the company typed in. We use them to help work
out if a rule applies. They are not proof. Gap checking can only mark a requirement as covered if
it can point at a chunk of an uploaded document.

```json
{
  "company_id": "company_001",
  "title": "Customer Grievance Redressal Policy",
  "evidence_type": "policy",
  "version_label": "v3.1",
  "effective_date": "2026-04-01",
  "owner_department": "Compliance",
  "approved_by": "Board",
  "covers_controls": ["Grievance intake", "Escalation matrix"]
}
```

### Analysis Request

```json
{
  "company_id": "company_001",
  "regulation_id": "regulation_001",
  "analysis_depth": "standard",
  "include_gap_analysis": true,
  "include_action_plan": true
}
```

## 5. Acceptance Criteria

- **AC-001**: An organization type not on the list is rejected.
- **AC-002**: A missing company name is rejected.
- **AC-003**: A bad date is rejected.
- **AC-004**: An analysis request with no company or no rule document is rejected.
- **AC-005**: Good data passes the check and gets saved.

## 6. Test Automation Strategy

Write tests for good data, bad data, edge values, null, empty, and far too long. Add a contract
test for every public endpoint.

## 7. Rationale & Context

If we check input properly, the AI behaves the same way every time, the database stays clean, and
the reports can be trusted. If we do not, all three go wrong at once.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Web forms and API clients.

### Third-Party Services
- **SVC-001**: A JSON Schema checking library.

### Infrastructure Dependencies
- **INF-001**: The API gateway and the checking layer in the backend.

### Data Dependencies
- **DAT-001**: Company details and rule document details.

### Technology Platform Dependencies
- **PLT-001**: A REST API that speaks JSON.

### Compliance Dependencies
- **COM-001**: Collect only what we need, and keep company data locked to that company.

## 9. Examples & Edge Cases

```json
{
  "company_name": "",
  "organization_type": "unknown"
}
```

This must fail twice: the name is empty, and `unknown` is not on the list.

## 10. Validation Criteria

Every schema needs tests for data that should pass and data that should fail. What the API sends
and receives must match what is written here.

## 11. Related Specifications / Further Reading

- `01-spec-schema-product-definition.md`
- `12-spec-schema-agent-contracts.md`
- `08-spec-tool-api-contracts.md`
- `05-spec-data-database.md`
