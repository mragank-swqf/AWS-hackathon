---
title: RegImpact REST API Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [tool, api, backend, rest, contracts]
---

# Introduction

This spec lists the API endpoints and how they behave. It covers companies, rule documents,
company documents, analyses, reviews, gaps, and tasks.

## 1. Purpose & Scope

The API sits in the middle. The web app, the worker, the database, and login all meet here.

## 2. Definitions

- **REST**: The usual style of web API, built on HTTP verbs and URLs.
- **JWT**: A signed token the client sends to prove who it is.
- **RBAC**: Deciding what someone can do based on their role.
- **Cursor**: A marker that says "carry on from here" when reading a long list.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Return JSON, unless we have said an endpoint returns a file.
- **REQ-002**: Check who the caller is and what they are allowed to do.
- **REQ-003**: Use the same status codes everywhere for the same kinds of result.
- **REQ-004**: An analysis takes a while, so run it in the background. Do not make the caller wait.
- **REQ-005**: Return a request ID on every response, so we can find it in the logs later.
- **REQ-006**: For any endpoint that returns a list, use `limit` and `cursor` to page through it.
- **REQ-007**: Starting the same analysis twice must be safe. If one is already `queued` or `processing` for that company and rule document, return the existing one with a 200. Do not make a second.
- **REQ-008**: Only hand out source documents through short-lived signed links, and only after checking the caller is allowed. Never a plain public link.
- **REQ-009**: Enforce these limits, and when a request goes over, say clearly which limit it hit: 150 pages per document, 25 MB per file, 50 requirements per analysis, and 3 analyses running at once per company.
- **REQ-010**: Starting an analysis on a rule document that is no longer `active` is allowed. But return a warning in the response so the web app can show it.
- **SEC-001**: Check permission on every request that touches company data.
- **SEC-002**: Never accept a password or token in the URL.
- **CON-001**: The web app must not call the AI service directly. Everything goes through us.
- **GUD-001**: Put the version in the path, like `/api/v1`.

## 4. Interfaces & Data Contracts

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/v1/auth/register` | Make a user |
| POST | `/api/v1/auth/login` | Swap a password for a token |
| GET | `/api/v1/auth/me` | Who am I, which companies, what role |
| POST | `/api/v1/auth/select-company` | Pick which company I am working in |
| POST | `/api/v1/companies` | Make a company |
| GET | `/api/v1/companies/{id}` | Read a company |
| PATCH | `/api/v1/companies/{id}` | Edit a company |
| POST | `/api/v1/regulations` | Upload a rule document |
| GET | `/api/v1/regulations` | List rule documents |
| GET | `/api/v1/regulations/{id}` | Read a rule document |
| POST | `/api/v1/policies` | Upload a company document |
| GET | `/api/v1/policies` | List company documents |
| GET | `/api/v1/policies/{id}` | Read a company document and how far it got |
| DELETE | `/api/v1/policies/{id}` | Delete a company document |
| POST | `/api/v1/analyses` | Start an analysis |
| GET | `/api/v1/analyses/{id}` | Read an analysis |
| GET | `/api/v1/analyses/{id}/status` | How far along it is, and which step |
| GET | `/api/v1/analyses/{id}/gaps` | List the gaps |
| GET | `/api/v1/analyses/{id}/actions` | List the tasks |
| PATCH | `/api/v1/actions/{id}` | Change a task's status or who owns it |
| GET | `/api/v1/citations/{id}` | Read a source link, with the text and page range |
| GET | `/api/v1/citations/{id}/source` | A signed link to the source file, good for a short time |
| POST | `/api/v1/analyses/{id}/approve` | Approve |
| POST | `/api/v1/analyses/{id}/reject` | Reject |
| POST | `/api/v1/analyses/{id}/request-review` | Ask for more proof |

List endpoints take `limit` and `cursor`, and return `next_cursor`. Default `limit` is 25. The
most you can ask for is 100.

### What a review can change to

These are the only moves allowed. Anything else gets a conflict error.

| From | To | Endpoint | Who can do it |
|---|---|---|---|
| `pending` | `approved` | `approve` | admin, compliance_officer, reviewer |
| `pending` | `rejected` | `reject` | admin, compliance_officer, reviewer |
| `pending` | `more_evidence_requested` | `request-review` | admin, compliance_officer, reviewer, analyst |
| `more_evidence_requested` | `pending` | re-run the analysis | admin, compliance_officer, analyst |
| `rejected` | `pending` | re-run the analysis | admin, compliance_officer, analyst |

Once a report is `approved`, that is the end of it. It cannot be changed. Running the analysis
again on the same rule document makes a brand new report. It does not reopen the approved one.
That way the approval stays a true record of what a person actually signed off.

Rejecting a report does not delete its tasks. It marks them `blocked` instead. The finding is no
longer trusted, but someone may already have started the work, so we do not throw it away.
`more_evidence_requested` records what proof was asked for, so the Evidence Library can ask the
user for it.

Error shape:

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

- **AC-001**: A request with no token gets a login error.
- **AC-002**: A request for another company's data gets refused.
- **AC-003**: Bad data in a request comes back with a clear list of what was wrong.
- **AC-004**: Starting an analysis returns an ID.
- **AC-005**: You can keep asking for the status until it says done or failed.

## 6. Test Automation Strategy

Unit tests for input checking. Tests against a real database for the data parts. Contract tests
so requests and responses match this spec. And one full test that walks the main user journey.

## 7. Rationale & Context

If the API shape is agreed and stays put, the web app and the worker can be built at the same
time without waiting on each other. It also makes the demo easier to run.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The web app.
- **EXT-002**: The job queue.

### Third-Party Services
- **SVC-001**: None. We issue our own tokens. See `spec-security-access-control.md`.

### Infrastructure Dependencies
- **INF-001**: Somewhere to run the API, plus the database, file storage, and the queue.

### Data Dependencies
- **DAT-001**: Company, rule document, analysis, gap, and task records.

### Technology Platform Dependencies
- **PLT-001**: A web framework that does REST.

### Compliance Dependencies
- **COM-001**: Login, permissions, the audit log, and keeping companies apart.

## 9. Examples & Edge Cases

If an analysis is already running for that company and rule document, a second request just gets
back the one already running. It does not start another.

## 10. Validation Criteria

Every endpoint needs its request, response, errors, login rule, and permission rule written down.

## 11. Related Specifications / Further Reading

- `spec-schema-input-contracts.md`
- `spec-data-database.md`
- `spec-infrastructure-aws-deployment.md`
