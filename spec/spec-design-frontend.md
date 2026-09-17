---
title: RegImpact Frontend and User Experience Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [design, frontend, ux, app]
---

# Introduction

This specification defines the frontend screens, user flows, interaction rules, and result presentation for RegImpact.

## 1. Purpose & Scope

The frontend shall allow users to manage a company profile, upload regulations, run analyses, review evidence, and track remediation actions.

## 2. Definitions

- **Dashboard**: Overview of current compliance activity.
- **Action tracker**: List of remediation tasks.
- **Review state**: Status indicating whether a report is pending, approved, or rejected.
- **CTA**: Call to Action.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The frontend shall provide login or demo access.
- **REQ-002**: The dashboard shall show recent analyses, high-risk findings, open gaps, and upcoming deadlines.
- **REQ-003**: The regulation library shall support upload, search, and filtering.
- **REQ-004**: The analysis page shall show applicability, requirements, impacts, gaps, risks, actions, and citations.
- **REQ-005**: Reviewers shall be able to approve, reject, or request more evidence.
- **REQ-006**: The interface shall show loading, success, empty, and error states.
- **SEC-001**: The frontend shall not expose private API credentials.
- **CON-001**: The MVP shall prioritize one complete workflow over numerous incomplete screens.
- **GUD-001**: Use clear uncertainty labels and avoid presenting AI output as final legal advice.

## 4. Interfaces & Data Contracts

Required screens:

```text
Login
Dashboard
Company Profile
Regulation Library
Analysis Setup
Analysis Results
Action Tracker
Review Screen
```

Result card fields:

```text
Requirement
Applicability
Impact
Current Status
Risk
Required Action
Evidence
Reviewer Status
```

## 5. Acceptance Criteria

- **AC-001**: A user can create a company profile from the UI.
- **AC-002**: A user can upload a regulation and see processing status.
- **AC-003**: A user can start and monitor an analysis.
- **AC-004**: A user can open source citations.
- **AC-005**: A reviewer can approve or reject an analysis.
- **AC-006**: The UI remains usable on desktop and mobile widths.

## 6. Test Automation Strategy

Use component tests, API-mocked integration tests, and Playwright end-to-end tests for login, upload, analysis, review, and action tracking.

## 7. Rationale & Context

Compliance users need to understand why a finding exists and what to do next. The UI should prioritize evidence, status, and actions rather than decorative AI output.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Backend REST API.

### Third-Party Services
- **SVC-001**: Authentication provider.

### Infrastructure Dependencies
- **INF-001**: Frontend hosting and CDN.

### Data Dependencies
- **DAT-001**: Company, regulation, analysis, gap, action, and citation objects.

### Technology Platform Dependencies
- **PLT-001**: Modern browser with HTTPS support.

### Compliance Dependencies
- **COM-001**: Role-aware visibility of sensitive company data.

## 9. Examples & Edge Cases

When a report is incomplete, the screen shall show `Analysis incomplete` and identify the failed stage rather than displaying an apparently complete report.

## 10. Validation Criteria

The frontend shall pass the complete user journey and display all required report sections with correct loading and error behavior.

## 11. Related Specifications / Further Reading

- `spec-tool-api-contracts.md`
- `spec-process-impact-analysis.md`
- `spec-architecture-system.md`
