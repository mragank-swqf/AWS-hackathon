---
title: RegImpact REST API Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [tool, api, backend, rest, contracts]
---

# Introduction

This specification defines the REST API contracts for company management, regulatory documents, analysis jobs, reviews, gaps, and action items.

## 1. Purpose & Scope

The API is the integration boundary between the frontend, backend services, workers, database, and authentication layer.

## 2. Definitions

- **REST**: Representational State Transfer.
- **JWT**: JSON Web Token.
- **RBAC**: Role-Based Access Control.
- **API**: Application Programming Interface.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: APIs shall return JSON unless a file response is explicitly documented.
- **REQ-002**: APIs shall validate authentication and authorization.
- **REQ-003**: APIs shall use consistent status codes.
- **REQ-004**: Long-running analysis shall be asynchronous.
- **REQ-005**: APIs shall return a request ID for troubleshooting.
- **SEC-001**: Authorization shall be checked for every company-scoped resource.
- **SEC-002**: Secrets shall not be accepted as query parameters.
- **CON-001**: API clients shall not call model providers directly.
- **GUD-001**: Use versioned paths such as `/api/v1`.

## 4. Interfaces & Data Contracts

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/companies` | Create company |
| GET | `/api/v1/companies/{id}` | Get company |
| PATCH | `/api/v1/companies/{id}` | Update company |
| POST | `/api/v1/regulations` | Upload regulation |
| GET | `/api/v1/regulations` | List regulations |
| GET | `/api/v1/regulations/{id}` | Get regulation |
| POST | `/api/v1/analyses` | Start analysis |
| GET | `/api/v1/analyses/{id}` | Get analysis |
| GET | `/api/v1/analyses/{id}/status` | Get analysis status |
| GET | `/api/v1/analyses/{id}/actions` | Get action items |
| POST | `/api/v1/analyses/{id}/approve` | Approve analysis |
| POST | `/api/v1/analyses/{id}/request-review` | Request review |

Error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid regulation_id",
    "details": {}
  },
  "request_id": "req_001"
}
```

## 5. Acceptance Criteria

- **AC-001**: Unauthenticated requests receive an authentication error.
- **AC-002**: Unauthorized company access is rejected.
- **AC-003**: Invalid payloads return validation errors.
- **AC-004**: Analysis creation returns a job or analysis identifier.
- **AC-005**: Analysis status can be polled until completion or failure.

## 6. Test Automation Strategy

Use unit tests for validation, integration tests for database behavior, contract tests for request and response schemas, and end-to-end tests for the primary user journey.

## 7. Rationale & Context

A stable API contract allows frontend and worker development to proceed independently and makes the system easier to demonstrate and extend.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Frontend application.
- **EXT-002**: Worker queue.

### Third-Party Services
- **SVC-001**: Authentication provider.

### Infrastructure Dependencies
- **INF-001**: API hosting, database, object storage, and queue.

### Data Dependencies
- **DAT-001**: Company, regulation, analysis, gap, and action records.

### Technology Platform Dependencies
- **PLT-001**: REST-compatible web framework.

### Compliance Dependencies
- **COM-001**: Authentication, authorization, audit logging, and data isolation.

## 9. Examples & Edge Cases

If analysis is already running, a second request for the same company and regulation may return the existing active analysis instead of creating a duplicate.

## 10. Validation Criteria

All endpoints shall have documented request, response, error, authentication, and authorization behavior.

## 11. Related Specifications / Further Reading

- `spec-schema-input-contracts.md`
- `spec-data-database.md`
- `spec-infrastructure-aws-deployment.md`
