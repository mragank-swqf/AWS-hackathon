---
title: RegImpact Regulatory Document Ingestion Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, ingestion, documents, ocr, rag]
---

# Introduction

This specification defines how RegImpact receives, validates, parses, enriches, chunks, and indexes regulatory documents.

## 1. Purpose & Scope

The process covers PDF uploads, public source URLs, text extraction, OCR fallback, metadata extraction, section detection, chunking, and storage.

## 2. Definitions

- **OCR**: Optical Character Recognition.
- **Chunk**: A searchable segment of a document.
- **Metadata**: Descriptive information about a document.
- **Annexure**: An attachment or supplementary section of a regulation.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The system shall validate file type and size before processing.
- **REQ-002**: The system shall preserve document ID, page number, section title, and clause number where available.
- **REQ-003**: The system shall use OCR when normal text extraction is insufficient.
- **REQ-004**: The system shall detect duplicate documents using hashes and metadata.
- **REQ-005**: The system shall store the original file separately from extracted text.
- **REQ-006**: The system shall retain extraction errors and processing status.
- **SEC-001**: Uploaded files shall be scanned and access-controlled.
- **CON-001**: The system shall not silently discard unreadable pages.
- **GUD-001**: Chunk boundaries should follow headings, clauses, tables, and paragraph groups.

## 4. Interfaces & Data Contracts

```json
{
  "document_id": "reg_001",
  "processing_status": "completed",
  "title": "Example Circular",
  "regulator": "RBI",
  "publication_date": "2026-09-01",
  "effective_date": "2026-12-01",
  "pages": 12,
  "extraction_method": "text_plus_ocr",
  "chunks_created": 48,
  "errors": []
}
```

## 5. Acceptance Criteria

- **AC-001**: Given a valid text PDF, when uploaded, then text and metadata are extracted.
- **AC-002**: Given a scanned PDF, when uploaded, then OCR is attempted.
- **AC-003**: Given a corrupted file, when uploaded, then processing fails with a visible reason.
- **AC-004**: Given a duplicate file, when uploaded, then the system identifies the existing document.
- **AC-005**: Given a document with page-level clauses, when chunked, then page and clause metadata are retained.

## 6. Test Automation Strategy

Test normal PDFs, scanned PDFs, mixed PDFs, tables, multi-column layouts, empty pages, corrupted files, duplicate files, and very large files.

## 7. Rationale & Context

Regulatory analysis is only reliable if source text and location metadata are preserved. Page and clause information is essential for evidence-backed citations.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulatory source websites.

### Third-Party Services
- **SVC-001**: Amazon Textract for OCR.

### Infrastructure Dependencies
- **INF-001**: Amazon S3, queue, worker service, and relational database.

### Data Dependencies
- **DAT-001**: Regulatory PDFs and metadata.

### Technology Platform Dependencies
- **PLT-001**: PDF parser and OCR-compatible runtime.

### Compliance Dependencies
- **COM-001**: Source integrity and auditability.

## 9. Examples & Edge Cases

```text
If 90% of a PDF has extractable text but page 7 is image-only:
1. Preserve normal extraction.
2. Run OCR for page 7.
3. Mark the page extraction method as OCR.
4. Preserve page 7 in citations.
```

## 10. Validation Criteria

A document is valid only when the original file is stored, processing status is recorded, and extracted content is traceable to source pages.

## 11. Related Specifications / Further Reading

- `spec-process-rag-pipeline.md`
- `spec-data-database.md`
- `spec-architecture-system.md`
