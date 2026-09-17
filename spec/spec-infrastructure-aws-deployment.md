---
title: RegImpact AWS Infrastructure and Deployment Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [infrastructure, aws, deployment, devops]
---

# Introduction

This spec lists the AWS pieces we need to run RegImpact, and how we deploy it.

## 1. Purpose & Scope

It covers hosting, file storage, the queue, the AI services, networking, secrets, logging,
deploying, and backups.

## 2. Definitions

- **CI/CD**: Build and deploy automatically when code changes.
- **VPC**: Our own private network inside AWS.
- **IAM**: AWS permissions.
- **CloudFront**: Serves our web files fast from nearby locations.
- **CloudWatch**: Where AWS keeps our logs.
- **Region**: Which part of the world our AWS stuff runs in.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Serve the web app from S3 with CloudFront in front.
- **REQ-002**: Run the backend on ECS Fargate or App Runner.
- **REQ-003**: Keep documents in private S3 buckets.
- **REQ-004**: Use SQS for the job queue, so jobs are not lost.
- **REQ-005**: Keep secrets in Secrets Manager.
- **REQ-006**: Send logs and errors to CloudWatch.
- **REQ-007**: The database must run a PostgreSQL version that supports `pgvector`. The first migration turns the add-on on.
- **REQ-008**: Deploy to `us-east-1`. It has the most Bedrock models. Turn on both Claude Sonnet and Titan Text Embeddings V2 in the account before we start building.
- **SEC-001**: Turn off all public access to the document buckets.
- **SEC-002**: Give each IAM role only what it needs.
- **CON-001**: We have to be able to deploy all of this inside the two weeks.
- **CON-002**: Using `us-east-1` means Indian rule documents and company documents get stored outside India. That is fine for a hackathon, but write it down as a known limit. A real deployment for RBI-regulated companies would probably have to use `ap-south-1` so the data stays in India.
- **GUD-001**: Write the infrastructure as code where we can.

## 4. Interfaces & Data Contracts

| Piece | AWS service |
|---|---|
| Web app | S3 + CloudFront |
| API | ECS Fargate or App Runner |
| Database | RDS PostgreSQL 15+ with `pgvector` |
| Files | S3 |
| Queue | SQS |
| OCR | Textract, one page at a time, only when needed |
| AI model | Bedrock, Claude Sonnet, for every AI step |
| Embeddings | Bedrock Titan Text Embeddings V2, 1024 numbers |
| Search | `pgvector` for meaning, PostgreSQL full-text for keywords |
| Secrets | Secrets Manager |
| Logs | CloudWatch |
| Login | Tokens we issue ourselves |

## 5. Acceptance Criteria

- **AC-001**: The web app loads over HTTPS.
- **AC-002**: The backend can only be reached through routes that need a login.
- **AC-003**: A private document cannot be opened without permission.
- **AC-004**: Restarting a worker does not lose queued jobs.
- **AC-005**: Errors show up in the logs.
- **AC-006**: Anyone on the team can deploy again by following written steps.

## 6. Test Automation Strategy

Check the infrastructure comes up, the containers report healthy, a quick smoke test passes,
permissions are right, a backup restores, and a rollback works.

## 7. Rationale & Context

We use managed AWS services because we do not have time to run our own. They also give us
security and scaling for free, and it is an AWS hackathon, so using them is the point.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The git repo and whatever runs our builds.

### Third-Party Services
- **SVC-001**: Amazon Bedrock.
- **SVC-002**: Amazon Textract.

### Infrastructure Dependencies
- **INF-001**: S3, CloudFront, ECS or App Runner, RDS PostgreSQL with `pgvector`, SQS, CloudWatch, Secrets Manager.

### Data Dependencies
- **DAT-001**: Container images, app config, documents, and database backups.

### Technology Platform Dependencies
- **PLT-001**: An AWS account with these services turned on.

### Compliance Dependencies
- **COM-001**: Encryption, permissions, logging, and how long we keep data.

## 9. Examples & Edge Cases

If the Bedrock model we asked for is not available in our region, fail with a clear message
saying so. Do not fail with something vague. And write down which model or region to fall back
to.

## 10. Validation Criteria

The deployed system must pass health checks, an upload test, an analysis test, a permission test,
and a check that logs are arriving.

## 11. Related Specifications / Further Reading

- `spec-architecture-system.md`
- `spec-tool-api-contracts.md`
- `spec-process-document-ingestion.md`
