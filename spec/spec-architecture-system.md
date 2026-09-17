---
title: RegImpact System Architecture Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [architecture, system, ai, aws]
---

# Introduction

This specification defines the logical architecture of RegImpact and the responsibilities of its major components.

## 1. Purpose & Scope

The architecture covers frontend, API, authentication, document storage, processing workers, retrieval, AI agents, database, observability, and review workflows.

## 2. Definitions

- **ECS**: Amazon Elastic Container Service.
- **S3**: Amazon Simple Storage Service.
- **SQS**: Amazon Simple Queue Service.
- **RDS**: Amazon Relational Database Service.
- **Bedrock**: Amazon Bedrock managed foundation-model service.
- **Vector database**: Storage optimized for similarity search over embeddings.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The frontend shall communicate through the backend API.
- **REQ-002**: Long-running work shall run asynchronously.
- **REQ-003**: Documents shall be stored in object storage.
- **REQ-004**: Analysis state shall be persisted.
- **REQ-005**: AI outputs shall pass schema validation and verification.
- **SEC-001**: Secrets shall be managed through a secret-management service.
- **SEC-002**: Internal services shall use authenticated communication.
- **CON-001**: The architecture shall be deployable within a two-week MVP.
- **GUD-001**: Prefer managed AWS services to reduce operational overhead.

## 4. Interfaces & Data Contracts

```text
React Frontend
    ↓ HTTPS
API Gateway / Load Balancer
    ↓
Backend API
    ├── PostgreSQL
    ├── S3
    └── SQS
          ↓
      Worker Service
          ├── Textract
          ├── Bedrock
          ├── Vector Search
          └── Verification
```

## 5. Acceptance Criteria

- **AC-001**: A user can upload a document through the frontend.
- **AC-002**: The API stores the file and creates a processing job.
- **AC-003**: A worker processes the job without blocking the API request.
- **AC-004**: Analysis results are persisted and retrievable.
- **AC-005**: Logs allow a failed analysis to be diagnosed.

## 6. Test Automation Strategy

Test service integration, queue delivery, worker retries, database connectivity, object-storage permissions, and end-to-end deployment.

## 7. Rationale & Context

The architecture separates interactive API requests from expensive document and AI processing. Managed services reduce infrastructure work during the hackathon.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulatory document sources.
- **EXT-002**: Company evidence sources.

### Third-Party Services
- **SVC-001**: Amazon Bedrock.
- **SVC-002**: Amazon Textract.

### Infrastructure Dependencies
- **INF-001**: S3, RDS, SQS, ECS/App Runner, CloudWatch, Secrets Manager, and CloudFront.

### Data Dependencies
- **DAT-001**: Regulatory and company documents.

### Technology Platform Dependencies
- **PLT-001**: AWS-hosted container or serverless runtime.

### Compliance Dependencies
- **COM-001**: Tenant isolation, audit logging, and human review.

## 9. Examples & Edge Cases

If Bedrock is temporarily unavailable, the worker shall mark the analysis as retryable and preserve the retrieved context rather than losing the job.

## 10. Validation Criteria

The architecture shall support the complete upload-to-report flow and demonstrate failure recovery for at least one external-service failure.

## 11. Related Specifications / Further Reading

- `spec-infrastructure-aws-deployment.md`
- `spec-tool-api-contracts.md`
- `spec-process-agent-orchestration.md`
