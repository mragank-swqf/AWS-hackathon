---
title: RegImpact Security and Access Control Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [security, access-control, privacy, infrastructure]
---

# Introduction

This specification defines security, privacy, authorization, data isolation, AI safety, and audit requirements for RegImpact.

## 1. Purpose & Scope

The specification applies to frontend, API, database, object storage, workers, AI agents, logs, and administrative workflows.

## 2. Definitions

- **RBAC**: Role-Based Access Control.
- **Least privilege**: Granting only the permissions required for a task.
- **PII**: Personally Identifiable Information.
- **Audit log**: Record of security or workflow events.

## 3. Requirements, Constraints & Guidelines

- **SEC-001**: All API access shall require authentication except explicitly public health checks.
- **SEC-002**: Every company-scoped request shall verify user membership.
- **SEC-003**: Files shall be stored privately and accessed through authorized routes.
- **SEC-004**: Data shall be encrypted in transit and at rest.
- **SEC-005**: Secrets shall not be committed to source control.
- **SEC-006**: Uploads shall be validated and scanned.
- **SEC-007**: Security-sensitive actions shall be audit logged.
- **SEC-008**: AI prompts shall not contain unnecessary sensitive information.
- **REQ-001**: The system shall support admin, compliance officer, reviewer, analyst, and viewer roles.
- **CON-001**: The MVP shall not make irreversible production changes.
- **GUD-001**: High-risk or uncertain findings shall require human approval.

## 4. Interfaces & Data Contracts

```json
{
  "user_id": "user_001",
  "company_id": "company_001",
  "role": "reviewer",
  "permissions": [
    "analysis.read",
    "analysis.review",
    "action.update"
  ]
}
```

## 5. Acceptance Criteria

- **AC-001**: A user without company membership cannot access company data.
- **AC-002**: A viewer cannot approve an analysis.
- **AC-003**: Private S3 objects cannot be accessed through public URLs.
- **AC-004**: Secrets are loaded from secure configuration.
- **AC-005**: Uploads with disallowed file types are rejected.
- **AC-006**: Approval and access-denied events are logged.

## 6. Test Automation Strategy

Test authentication, authorization, tenant isolation, file validation, secret scanning, dependency scanning, and API abuse cases.

## 7. Rationale & Context

Regulatory documents and internal policies may contain sensitive business information. Strong isolation and review controls are necessary for user trust.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Identity provider.

### Third-Party Services
- **SVC-001**: Cognito or equivalent authentication service.
- **SVC-002**: Malware/file scanning service if required.

### Infrastructure Dependencies
- **INF-001**: IAM, private storage, encryption keys, network controls, and centralized logging.

### Data Dependencies
- **DAT-001**: User identities, company membership, documents, and audit events.

### Technology Platform Dependencies
- **PLT-001**: HTTPS-enabled deployment.

### Compliance Dependencies
- **COM-001**: Applicable privacy, retention, and regulatory obligations.

## 9. Examples & Edge Cases

A user may belong to two companies. Every request must use the company context selected by the user and verify membership for that company.

## 10. Validation Criteria

Security tests shall pass for authentication, authorization, storage access, secrets, uploads, logs, and tenant isolation.

## 11. Related Specifications / Further Reading

- `spec-infrastructure-aws-deployment.md`
- `spec-data-database.md`
- `spec-tool-api-contracts.md`
