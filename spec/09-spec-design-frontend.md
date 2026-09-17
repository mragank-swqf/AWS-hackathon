---
title: RegImpact Frontend and User Experience Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [design, frontend, ux, app]
---

# Introduction

This spec lists the screens, how a user moves between them, and how we show the results.

## 1. Purpose & Scope

The web app lets a user fill in their company details, upload documents, run an analysis, read
the sources, and track the tasks that come out of it.

## 2. Definitions

- **Dashboard**: The home screen. Shows what is going on right now.
- **Action tracker**: The list of tasks to fix things.
- **Review state**: Whether a report is waiting, approved, or rejected.
- **Result card**: One finding on screen, with its status and what to do.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: There is no login screen. The app opens straight onto the demo company.
- **REQ-002**: The rule library lets a user upload and see a list.
- **REQ-003**: The evidence library lets a user upload company documents, and shows how far each one got.
- **REQ-004**: The analysis screen shows applicability, requirements, who is affected, gaps, risk, tasks, and sources.
- **REQ-005**: A reviewer can approve or reject.
- **REQ-006**: Every screen needs a loading state, a working state, an empty state, and an error state. The analysis screen needs this most, because it is the one the user waits on.
- **REQ-007**: A user can click any finding and see the source: the actual lines, the page range, and the clause number.
- **REQ-008**: Dates must be split by `date_basis` wherever they appear. Only `cited_effective` and `cited_compliance` may be shown as real deadlines. A date we came up with must be clearly marked as a suggestion. Never show a date we made up as something the regulator asked for.
- **SEC-001**: Never put API keys in the web app.
- **CON-001**: One whole working flow beats ten half-built screens.
- **GUD-001**: Say plainly when we are not sure. Never make AI output look like final legal advice.

### Left for later

- **LTR-001**: A login screen.
- **LTR-002**: The dashboard, showing recent analyses, risky findings, open gaps, and dates.
- **LTR-003**: Search and filters on the rule library.
- **LTR-004**: Asking the user for more proof, as a review option.
- **LTR-005**: A warning when the rule document has been replaced by a newer one.
- **LTR-006**: Showing whether a piece of source text came from OCR. Nothing comes from OCR yet.

The dashboard is the one that looks like a loss and is not. The demo never opens it, and a
half-finished dashboard on screen does more harm than no dashboard at all.

## 4. Interfaces & Data Contracts

Screens we need:

```text
Company Profile
Regulation Library
Evidence Library
Analysis Setup
Analysis Results   (includes approve and reject)
Action Tracker
```

Six screens, not nine. Login and the dashboard are gone, and the review screen is folded into the
analysis results page, because approving is one button and does not need its own page.

The Evidence Library is where a user uploads their own policies, and where they see how far each
upload got. We cannot skip it. Without uploaded documents, gap checking has nothing to compare
against, so every finding would come back as `insufficient_evidence`.

What goes on a result card:

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

- **AC-001**: A user can fill in a company profile from the screen.
- **AC-002**: A user can upload a rule document and watch it being processed.
- **AC-003**: A user can upload a company document and watch it being processed.
- **AC-004**: A user can start an analysis and see how it is going.
- **AC-005**: A user can click through to a source and read the actual lines.
- **AC-006**: A reviewer can approve or reject a report, and the status visibly changes.

## 6. Test Automation Strategy

Walk the demo path by hand, several times. If there is time left over, add one Playwright test
that does the same walk. Automated browser tests are the first thing to cut here, because the
demo path gets walked by a person anyway.

## 7. Rationale & Context

A compliance person needs two things from a screen: why does this finding exist, and what do I do
next. So put the sources, the status, and the tasks first. Skip anything that just looks clever.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: The backend API.

### Third-Party Services
- **SVC-001**: None. The web app logs in against our own backend.

### Infrastructure Dependencies
- **INF-001**: Somewhere to host the files, plus a CDN.

### Data Dependencies
- **DAT-001**: Companies, rule documents, analyses, gaps, tasks, and sources.

### Technology Platform Dependencies
- **PLT-001**: A current browser over HTTPS.

### Compliance Dependencies
- **COM-001**: Show sensitive company data only to roles allowed to see it.

## 9. Examples & Edge Cases

If a report only half finished, say `Analysis incomplete` and name the step that broke. Do not
show what looks like a finished report with pieces quietly missing. That is worse than an error.

## 10. Validation Criteria

The web app is done when a user can walk the whole journey, every report section shows up, and
loading and error states behave.

## 11. Related Specifications / Further Reading

- `08-spec-tool-api-contracts.md`
- `14-spec-process-impact-analysis.md`
- `03-spec-architecture-system.md`
