---
title: RegImpact Input Schema and Data Contracts Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [schema, data, api, validation]
---

# Introduction

This specification defines the input objects required by RegImpact and the validation rules for company profiles, regulations, analysis requests, policies, controls, and evidence.

## 1. Purpose & Scope

The specification applies to frontend forms, backend APIs, database persistence, background jobs, and AI-agent inputs.

## 2. Definitions

- **JSON Schema**: A machine-readable format for validating JSON objects.
- **Company profile**: Structured description of the organization and its business activities.
- **Evidence**: A document or record supporting a compliance claim.
- **Control**: A policy, process, system, or operational mechanism used to meet a requirement.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: All external inputs shall be validated before persistence or processing.
- **REQ-002**: Required fields shall be explicitly defined.
- **REQ-003**: Enumerated values shall reject unsupported values.
- **REQ-004**: Dates shall use ISO-8601 format.
- **REQ-005**: Every analysis request shall identify exactly one company and one regulation.
- **SEC-001**: Company-owned data shall be scoped by `company_id`.
- **CON-001**: Unknown fields shall either be rejected or explicitly preserved under `metadata`.
- **GUD-001**: Schemas shall remain backward-compatible within a major version.

## 4. Interfaces & Data Contracts

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
  "raw_text": "Extracted document text"
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

- **AC-001**: Invalid organization types are rejected.
- **AC-002**: Missing company name is rejected.
- **AC-003**: Invalid dates are rejected.
- **AC-004**: An analysis request without a company or regulation is rejected.
- **AC-005**: Valid objects pass validation and are persisted.

## 6. Test Automation Strategy

Use schema validation tests for valid, invalid, boundary, null, empty, and oversized values. Include API contract tests for every public endpoint.

## 7. Rationale & Context

Strong input contracts prevent inconsistent agent behavior, invalid database records, and unreliable analysis results.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Frontend forms and API clients.

### Third-Party Services
- **SVC-001**: JSON Schema validation library.

### Infrastructure Dependencies
- **INF-001**: API gateway and backend validation middleware.

### Data Dependencies
- **DAT-001**: Company and regulatory metadata.

### Technology Platform Dependencies
- **PLT-001**: JSON-compatible REST API.

### Compliance Dependencies
- **COM-001**: Data minimization and company-level access control.

## 9. Examples & Edge Cases

```json
{
  "company_name": "",
  "organization_type": "unknown"
}
```

Expected result: validation failure for empty name and unsupported organization type.

## 10. Validation Criteria

All schemas shall have automated positive and negative validation tests. API payloads shall match the documented contracts.

## 11. Related Specifications / Further Reading

- `spec-schema-product-definition.md`
- `spec-tool-api-contracts.md`
- `spec-data-database.md`
