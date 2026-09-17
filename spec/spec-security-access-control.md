---
title: RegImpact Security and Access Control Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [security, access-control, privacy, infrastructure]
---

# Introduction

This spec covers keeping the system safe: who can log in, who can see what, keeping companies
apart, keeping the AI from being tricked, and logging what happened.

## 1. Purpose & Scope

It applies to the web app, the API, the database, file storage, the worker, the AI steps, the
logs, and anything an admin can do.

## 2. Definitions

- **RBAC**: Deciding what someone can do based on their role.
- **Least privilege**: Give out only the rights needed for the job. Nothing spare.
- **PII**: Information that identifies a person.
- **Audit log**: A record of who did what and when.
- **Prompt injection**: Hiding instructions inside a document, hoping the AI obeys them.

## 3. Requirements, Constraints & Guidelines

There is no login in the hackathon build. That means most of this spec describes the version we
want later, not the version we are building now. The split is marked below.

### In the hackathon build

- **SEC-001**: Keep files private. Never serve a file from a public link.
- **SEC-002**: Encrypt data on disk and over the network. This is on by default in S3 and RDS, so it costs us nothing.
- **SEC-003**: Never commit a password or key to git. Read them from the environment.
- **SEC-004**: Check the file type and size on every upload.
- **SEC-005**: Do not put sensitive data in an AI prompt unless that step needs it.
- **SEC-006**: Treat text from an uploaded document as data, never as orders. Someone could hide instructions in a PDF. So fence the text off, say plainly that anything inside is just words and cannot change the job, and put it after the job description, not before. This is only prompt wording, so it is nearly free, and it is worth talking about in the demo.
- **SEC-007**: Do not let one AI step's word be enough to say a company is `compliant` or `partial`. It needs a chunk of a company document, and the checking step has to agree that chunk really says it.
- **SEC-008**: Every row that belongs to a company still carries `company_id`, and every search still filters on it. We keep the shape even with one company, so adding real users later is not a rewrite.
- **CON-001**: The MVP must never make a change that cannot be undone.
- **GUD-001**: Anything risky or unclear needs a person to approve it.

### Left for later

- **LTR-001**: A real login. We issue our own tokens, holding the user, their company, and their role, signed with a secret from Secrets Manager. Tokens expire.
- **LTR-002**: These roles: admin, compliance officer, reviewer, analyst, and viewer.
- **LTR-003**: Checking company membership on every request, instead of trusting the token.
- **LTR-004**: An add-only audit log, using the `audit_action` list, with the database stopping any edit.
- **LTR-005**: Virus scanning on uploads.
- **LTR-006**: A set of test documents with hidden instructions in them, to measure how well SEC-006 holds up.

Why these are safe to leave: with one demo user and one demo company, there is nobody to keep
apart and nobody to audit. The moment a second real user exists, all six come back.

## 4. Interfaces & Data Contracts

The hackathon build uses one fixed user and one fixed company, set up when the demo data is
loaded. No login screen, no token.

```json
{
  "user_id": "demo_user",
  "company_id": "company_001"
}
```

The full shape, for later, adds a role and a permission list:

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

For the hackathon build:

- **AC-001**: A private file cannot be opened from a public link.
- **AC-002**: Secrets come from the environment, not from the code.
- **AC-003**: A file type we do not allow gets rejected.
- **AC-004**: A document with hidden instructions gives the same result as the same document without them.
- **AC-005**: Every search query has a `company_id` filter on it.

For later:

- **AC-006**: A user who does not belong to a company cannot see its data.
- **AC-007**: A viewer cannot approve a report.
- **AC-008**: Approvals and blocked attempts both show up in the log.
- **AC-009**: Trying to edit or delete a log row fails in the database.

## 6. Test Automation Strategy

For the hackathon: test the file type check, that no key is committed, and that a document with
hidden instructions changes nothing in the output.

For later: test login, permissions, keeping companies apart, dependency scanning, and people
misusing the API.

## 7. Rationale & Context

Rule documents are public, but a company's own policies are not. They say how the business
actually runs. If we leaked one company's documents to another, nobody would use this. So keeping
them apart is the thing we cannot get wrong.

That is exactly why `company_id` stays on every row and every query even now, with one company
and no login. The column is nearly free to keep and expensive to add back. Dropping login is a
shortcut we can undo in an afternoon. Dropping the data model is not.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: None. There is no identity provider, and no login.

### Third-Party Services
- **SVC-001**: None. `PyJWT` and `passlib` come in later, with LTR-001.
- **SVC-002**: A virus scanner for files, later.

### Infrastructure Dependencies
- **INF-001**: IAM, private storage, encryption keys, network rules, and logs in one place.

### Data Dependencies
- **DAT-001**: Users, who belongs to which company, documents, and log entries.

### Technology Platform Dependencies
- **PLT-001**: Everything served over HTTPS.

### Compliance Dependencies
- **COM-001**: Privacy rules, how long we keep data, and any rules that apply to us.

## 9. Examples & Edge Cases

Later, a user will be able to belong to two companies. Every request will have to use the company
they picked, and check they really belong to that one. Belonging to company A says nothing about
company B. The `company_id` filter we keep now is what makes that a small change rather than a
big one.

## 10. Validation Criteria

For the hackathon: file access, secrets, upload checks, and the hidden-instruction test all pass.

For later: add login, permissions, the audit log, and keeping companies apart.

## 11. Related Specifications / Further Reading

- `spec-infrastructure-aws-deployment.md`
- `spec-data-database.md`
- `spec-tool-api-contracts.md`
