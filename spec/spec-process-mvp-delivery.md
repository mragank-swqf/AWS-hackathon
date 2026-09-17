---
title: RegImpact MVP Delivery and Implementation Process Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, mvp, delivery, hackathon]
---

# Introduction

This specification defines the implementation order, MVP boundaries, delivery milestones, and demo requirements for RegImpact.

## 1. Purpose & Scope

The process is optimized for a two-week hackathon implementation and prioritizes a complete, demonstrable workflow.

## 2. Definitions

- **MVP**: Minimum Viable Product.
- **Demo path**: The exact sequence shown during judging.
- **Must-have**: Feature required for the core workflow.
- **Should-have**: Feature useful but not essential to the first demo.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The MVP shall support PDF upload through final report generation.
- **REQ-002**: The MVP shall include company profiling.
- **REQ-003**: The MVP shall include retrieval and citations.
- **REQ-004**: The MVP shall include human review.
- **REQ-005**: The MVP shall include a basic action tracker.
- **CON-001**: Do not implement automatic regulatory filing.
- **CON-002**: Do not implement complete regulator coverage.
- **GUD-001**: Use a fixed demo company and curated documents for reliability.
- **PAT-001**: Deliver vertical slices early rather than building all layers independently.

## 4. Interfaces & Data Contracts

### Delivery milestones

| Period | Deliverable |
|---|---|
| Days 1–2 | Backend, database, frontend shell, upload |
| Days 3–4 | Extraction, chunking, embeddings, search |
| Days 5–6 | Applicability and requirement agents |
| Days 7–8 | Impact, gaps, risk, actions |
| Days 9–10 | Citations, verification, review |
| Days 11–12 | Dashboard, tracker, security |
| Days 13–14 | Evaluation, polish, demo rehearsal |

## 5. Acceptance Criteria

- **AC-001**: The core demo can be completed without manual database edits.
- **AC-002**: A regulation can be uploaded and analyzed.
- **AC-003**: The report shows source evidence.
- **AC-004**: The report shows at least one actionable gap.
- **AC-005**: A reviewer can approve the report.
- **AC-006**: The application can recover from a failed analysis job.

## 6. Test Automation Strategy

Use smoke tests after every milestone, regression tests before demo day, and a fixed evaluation dataset for AI quality.

## 7. Rationale & Context

A complete and reliable vertical slice is more valuable for a hackathon than a broad platform with unconnected features.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Git repository and issue tracker.

### Third-Party Services
- **SVC-001**: AWS AI and infrastructure services.

### Infrastructure Dependencies
- **INF-001**: Deployed frontend, backend, database, storage, queue, and model access.

### Data Dependencies
- **DAT-001**: Curated regulatory documents and synthetic company evidence.

### Technology Platform Dependencies
- **PLT-001**: AWS-hosted application.

### Compliance Dependencies
- **COM-001**: Human review and source citation requirements.

## 9. Examples & Edge Cases

If live regulatory ingestion is unstable during the demo, the system shall use a pre-ingested, source-linked document while clearly showing its original source metadata.

## 10. Validation Criteria

The MVP is ready when the demo path works repeatedly, AI outputs are cited, security checks pass, and known limitations are documented.

## 11. Related Specifications / Further Reading

- `spec-schema-product-definition.md`
- `spec-process-impact-analysis.md`
- `spec-infrastructure-aws-deployment.md`
