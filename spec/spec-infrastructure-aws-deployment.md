---
title: RegImpact AWS Infrastructure and Deployment Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [infrastructure, aws, deployment, devops]
---

# Introduction

This specification defines the AWS infrastructure required to deploy and operate the RegImpact MVP.

## 1. Purpose & Scope

The specification covers hosting, storage, queues, AI services, networking, secrets, monitoring, deployment, and backup requirements.

## 2. Definitions

- **CI/CD**: Continuous Integration and Continuous Delivery.
- **VPC**: Virtual Private Cloud.
- **IAM**: Identity and Access Management.
- **CloudFront**: AWS content delivery network.
- **CloudWatch**: AWS monitoring and logging service.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Frontend assets shall be hosted using S3 and CloudFront or an equivalent AWS-hosted service.
- **REQ-002**: Backend services shall run on ECS Fargate, App Runner, or an equivalent managed runtime.
- **REQ-003**: Documents shall be stored in private S3 buckets.
- **REQ-004**: Analysis jobs shall use SQS or an equivalent durable queue.
- **REQ-005**: Secrets shall be stored in Secrets Manager or an equivalent secure store.
- **REQ-006**: Logs and errors shall be available through CloudWatch.
- **SEC-001**: Public access to document buckets shall be disabled.
- **SEC-002**: IAM permissions shall follow least privilege.
- **CON-001**: The deployment must be achievable within the MVP schedule.
- **GUD-001**: Infrastructure should be defined as code where practical.

## 4. Interfaces & Data Contracts

| Component | AWS Service |
|---|---|
| Frontend | S3 + CloudFront |
| API | ECS Fargate or App Runner |
| Database | RDS PostgreSQL |
| Files | S3 |
| Queue | SQS |
| OCR | Textract |
| LLM | Bedrock |
| Embeddings | Titan Embeddings or equivalent |
| Search | OpenSearch or pgvector |
| Secrets | Secrets Manager |
| Logs | CloudWatch |
| Authentication | Cognito or backend JWT |

## 5. Acceptance Criteria

- **AC-001**: The frontend is accessible through HTTPS.
- **AC-002**: The backend is accessible only through authenticated API routes.
- **AC-003**: Private documents cannot be accessed without authorization.
- **AC-004**: Queue jobs survive worker restarts.
- **AC-005**: Application errors appear in centralized logs.
- **AC-006**: A deployment can be repeated from a documented process.

## 6. Test Automation Strategy

Run infrastructure validation, container health checks, smoke tests, permission tests, backup tests, and deployment rollback tests.

## 7. Rationale & Context

Managed AWS services provide scalability, security controls, and a credible cloud-native architecture while keeping the MVP operationally simple.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Git repository and CI/CD provider.

### Third-Party Services
- **SVC-001**: Amazon Bedrock.
- **SVC-002**: Amazon Textract.

### Infrastructure Dependencies
- **INF-001**: S3, CloudFront, ECS/App Runner, RDS, SQS, CloudWatch, Secrets Manager, Cognito.

### Data Dependencies
- **DAT-001**: Container images, application configuration, documents, and database backups.

### Technology Platform Dependencies
- **PLT-001**: AWS account with required service access.

### Compliance Dependencies
- **COM-001**: Encryption, access control, auditability, and retention.

## 9. Examples & Edge Cases

If the selected Bedrock model is unavailable in the deployment region, the system shall return a clear configuration error and support a documented fallback model or region.

## 10. Validation Criteria

The deployed system shall pass health checks, upload tests, analysis tests, authorization tests, and log verification.

## 11. Related Specifications / Further Reading

- `spec-architecture-system.md`
- `spec-tool-api-contracts.md`
- `spec-process-document-ingestion.md`
