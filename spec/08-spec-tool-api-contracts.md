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
- **REQ-002**: Use the same status codes everywhere for the same kinds of result.
- **REQ-003**: An analysis takes a while, so run it in the background. Do not make the caller wait.
- **REQ-004**: Return a request ID on every response, so we can find it in the logs later.
- **REQ-005**: Only hand out source documents through short-lived signed links. Never a plain public link.
- **REQ-006**: Every request carries a `company_id`, even though there is only one company. Filter on it.
- **CON-001**: The web app must not call the AI service directly. Everything goes through us.
- **CON-002**: There is no login, so there are no auth endpoints and no permission checks. The demo user is fixed.
- **GUD-001**: Put the version in the path, like `/api/v1`.

### Left for later

- **LTR-001**: Auth endpoints: register, login, me, and pick-a-company.
- **LTR-002**: A permission check on every request that touches company data.
- **LTR-003**: Paging on list endpoints, with `limit` and `cursor`, default 25 and maximum 100.
- **LTR-004**: Making a repeat request safe. If an analysis for the same company and rule document is already running, return that one instead of starting another.
- **LTR-005**: Limits: 150 pages per document, 25 MB per file, 50 requirements per analysis, 3 analyses at once per company.
- **LTR-006**: A warning in the response when the rule document has been replaced by a newer one.
- **LTR-007**: The full review flow with `more_evidence_requested`, and the rules about which change is allowed from which state.

## 4. Interfaces & Data Contracts

| Method | Endpoint | What it does |
|---|---|---|
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

### What a review can change to

Only two moves in the hackathon build:

| From | To | Endpoint |
|---|---|---|
| `pending` | `approved` | `approve` |
| `pending` | `rejected` | `reject` |

Once a report is `approved`, that is the end of it. It cannot be changed. Running the analysis
again on the same rule document makes a brand new report. It does not reopen the approved one.
That way the approval stays a true record of what a person actually signed off.

Rejecting a report does not delete its tasks. It marks them `blocked` instead. The finding is no
longer trusted, but someone may already have started the work, so we do not throw it away.

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

- **AC-001**: Bad data in a request comes back with a clear list of what was wrong.
- **AC-002**: Starting an analysis returns an ID.
- **AC-003**: You can keep asking for the status until it says done or failed.
- **AC-004**: A source link returns the text and the page range.
- **AC-005**: Approving a report changes its status, and approving it twice is refused.

## 6. Test Automation Strategy

Unit tests for input checking. One full test that walks the main journey: upload a rule document,
upload a company document, run the analysis, open a source link, approve.

## 7. Rationale & Context

If the API shape is agreed and stays put, the web app and the worker can be built at the same
time without waiting on each other. It also makes the demo easier to run.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The web app.
- **EXT-002**: The job queue.

### Third-Party Services
- **SVC-001**: None. There is no login. See `07-spec-security-access-control.md`.

### Infrastructure Dependencies
- **INF-001**: Somewhere to run the API, plus the database, file storage, and the queue.

### Data Dependencies
- **DAT-001**: Company, rule document, analysis, gap, and task records.

### Technology Platform Dependencies
- **PLT-001**: A web framework that does REST.

### Compliance Dependencies
- **COM-001**: A person approves the report, and every point has a source.

## 9. Examples & Edge Cases

If someone starts a second analysis for the same company and rule document, the hackathon build
will just run it again. That is a known rough edge, listed as LTR-004. It does not break the demo
because the demo only starts one.

## 10. Validation Criteria

Every endpoint needs its request, response, and errors written down.

## 11. Related Specifications / Further Reading

- `04-spec-schema-input-contracts.md`
- `05-spec-data-database.md`
- `06-spec-infrastructure-aws-deployment.md`
