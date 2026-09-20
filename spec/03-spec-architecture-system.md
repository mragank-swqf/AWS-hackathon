---
title: RegImpact System Architecture Specification
version: 1.3
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [architecture, system, ai, aws]
---

# Introduction

This spec lists the parts of the system and says what each part does.

## 1. Purpose & Scope

It covers the web app, the API, login, file storage, the background worker, search, the AI steps,
the database, logging, and the review flow.

## 2. Definitions

- **ECS**: Amazon Elastic Container Service. Runs our containers.
- **S3**: Amazon Simple Storage Service. Holds files.
- **SQS**: Amazon Simple Queue Service. Holds a list of jobs to do.
- **RDS**: Amazon Relational Database Service. Runs our database.
- **Bedrock**: Amazon's service for running AI models.
- **pgvector**: An add-on for PostgreSQL that lets it search by meaning.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The web app must talk to the backend API. It must not talk to other services on its own.
- **REQ-002**: Slow work must run in the background, not while the user waits.
- **REQ-003**: Uploaded files must go in file storage.
- **REQ-004**: The state of each analysis must be saved in the database.
- **REQ-005**: Every AI output must be checked against a schema, then checked for sources.
- **SEC-001**: Passwords and keys must come from a secrets service.
- **CON-001**: When there is a choice, take the simpler option.
- **GUD-001**: Use AWS managed services so we have less to run ourselves.

## 4. Interfaces & Data Contracts

```text
React Frontend
    ↓ HTTPS
API Gateway / Load Balancer
    ↓
Backend API  (no login, company scoping only)
    ├── PostgreSQL + pgvector   (entities, chunks, embeddings, full-text index)
    ├── S3                      (original documents, private)
    └── SQS
          ↓
      Worker Service
          ├── pypdf              (text layer only, no OCR)
          ├── Bedrock Titan v2   (embeddings)
          ├── Hybrid Retrieval   (pgvector + Postgres FTS, RRF fused)
          ├── Bedrock LLM        (6 AI steps)
          └── Verification       (citation coverage, unsupported claims)
```

Two things are missing on purpose. There is no login, and there is no OCR. Both are listed as
left for later in their own specs.

There is no separate search service. Both kinds of search are just SQL queries on the same
`document_chunks` table. That way the rule that keeps one company's data away from another sits
in one place.

## 5. Acceptance Criteria

- **AC-001**: A user can upload a document from the web app.
- **AC-002**: The API saves the file and adds a job to the queue.
- **AC-003**: A worker does the job. The user's request does not wait for it.
- **AC-004**: Results are saved and can be read back later.
- **AC-005**: If an analysis fails, the logs are enough to work out why.

## 6. Test Automation Strategy

Test that the parts talk to each other, that jobs reach the queue, that a worker retries, that the
database connects, that file permissions are right, and that a fresh deploy works end to end.

## 7. Rationale & Context

User requests are fast. Reading PDFs and running AI is slow. So we keep them apart, and the slow
work goes in the background. We use managed AWS services so we have less to run ourselves.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Where rule documents come from.
- **EXT-002**: Where company documents come from.

### Third-Party Services
- **SVC-001**: Amazon Bedrock.

### Infrastructure Dependencies
- **INF-001**: S3, RDS PostgreSQL with `pgvector`, SQS, ECS or App Runner, CloudWatch, Secrets Manager, and CloudFront.

### Data Dependencies
- **DAT-001**: Rule documents and company documents.

### Technology Platform Dependencies
- **PLT-001**: A container or serverless runtime on AWS.

### Compliance Dependencies
- **COM-001**: Keep each company's data separate, and let a person review. Logging important actions is left for later.

## 9. Examples & Edge Cases

If Bedrock is down for a while, the worker must mark the analysis as "try again later". It must
keep the text it already found. It must not throw the job away.

## 10. Validation Criteria

The design is good enough when the whole flow works, from upload to report, and when we can show
the system recovering from at least one outside service failing.

## 11. Related Specifications / Further Reading

- `06-spec-infrastructure-aws-deployment.md`
- `08-spec-tool-api-contracts.md`
- `13-spec-process-agent-orchestration.md`
