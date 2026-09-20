---
title: RegImpact Regulatory Document Ingestion Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, ingestion, documents, ocr, rag]
---

# Introduction

This spec says what happens to a document after someone uploads it: how we check it, read the
text out of it, cut it into pieces, and make it searchable.

## 1. Purpose & Scope

It covers PDF upload, pulling out the text, reading the document details, spotting sections,
cutting into chunks, and saving it all.

The MVP takes PDF files only. We do not download anything from regulator websites. The user pastes
in the source web address when they upload, so we can still show where the document came from.

## 2. Definitions

- **OCR**: Reading text out of a picture of a page.
- **Chunk**: A small piece of a document that we can search.
- **Metadata**: Details about a document, like its title and date.
- **Annexure**: An extra section at the end of a rule document.
- **Token**: Roughly a word. How we measure chunk size.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Check the file type and size before doing anything. Accept PDF only.
- **REQ-002**: Keep the document ID, page number, section title, and clause number where we can find them.
- **REQ-003**: Use `pypdf` to read the text. There is no OCR in the hackathon build, so pick demo PDFs that already have a real text layer.
- **REQ-004**: If a page gives back almost no text, do not pretend it worked. Record the page as unread and show that on screen.
- **REQ-005**: Spot duplicate uploads using a hash of the file and its details.
- **REQ-006**: Keep the original file. Store the text we pulled out somewhere else.
- **REQ-007**: Save any errors, and save how far the job got.
- **REQ-008**: Company documents go through this same process. A company upload creates `document_chunks` rows with `company_policy_id` and `company_id` filled in, so gap checking can search and cite them.
- **CON-001**: Never quietly skip a page we could not read.
- **GUD-001**: Try to cut chunks at headings, clauses, tables, and paragraph breaks.

### Left for later

- **LTR-001**: OCR. Send any page that comes back with almost no text to Amazon Textract, one page at a time. Then a scanned PDF works too.
- **LTR-002**: Recording how each page was read, so a source link can say the text came from OCR.
- **LTR-003**: Virus scanning on upload.

Dropping OCR is the single biggest saving here, and it costs us nothing in the demo as long as we
choose the demo PDFs ourselves. Most RBI circulars are published with a text layer already.

### How to cut chunks

Cut at clause boundaries first. Only fall back to size limits if a clause is too big. A clause is
the thing a compliance person quotes, so cutting there is what makes a source link useful.

- Look for numbered clauses (`3`, `3.2`, `3.2.1`), lettered or roman sub-parts (`(a)`, `(iv)`),
  heading words (`Para`, `Paragraph`, `Clause`, `Section`, `Annexure`, `Schedule`), and lines in
  all capitals.
- Aim for 800 tokens per chunk. Never go past 1200.
- If a section is bigger than 1200, cut it into pieces that overlap by 100 tokens.
- Do not add overlap when a section already fits. It would just return the same text twice.
- If a section is under 100 tokens, glue it onto the chunk before it. Do not make tiny chunks.
- Keep a table in one chunk if it fits. Never cut in the middle of a table row.
- Give each chunk the nearest heading above it as `section_title`, and the clause it sits in as
  `clause_number`.
- A chunk can run across a page break. Store `page_start` and `page_end`. Never drop the page
  number just to hit a size target.

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

- **AC-001**: Upload a normal PDF. We get the text and the document details.
- **AC-002**: Upload a scanned PDF. The job does not crash, and it says the pages could not be read.
- **AC-003**: Upload a broken file. The job fails and the user can see why.
- **AC-004**: Upload the same file twice. The system points at the copy it already has.
- **AC-005**: Upload a document with numbered clauses. The chunks keep their page and clause numbers.

## 6. Test Automation Strategy

Test normal PDFs, tables, two-column pages, blank pages, broken files, and duplicate files. A
scanned PDF is a test too, but the expected result is a clear "could not read this", not text.

## 7. Rationale & Context

The whole product rests on being able to say "this came from here". If we lose the page and
clause along the way, we cannot show our sources, and the report is worth much less.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulator websites. A person downloads from them and uploads to us. Our code never fetches from them.

### Third-Party Services
- **SVC-001**: None. Amazon Textract comes in later, with LTR-001.

### Infrastructure Dependencies
- **INF-001**: Amazon S3, the job queue, the worker, and the database.

### Data Dependencies
- **DAT-001**: Rule PDFs and their details.

### Technology Platform Dependencies
- **PLT-001**: `pypdf` to read text.

### Compliance Dependencies
- **COM-001**: The source must stay intact and checkable.

## 9. Examples & Edge Cases

```text
A PDF where most pages have real text, but page 7 is just an image:
1. Keep the normal text from the other pages.
2. Record page 7 as unread.
3. Show on screen that page 7 could not be read.
4. Do not act as if the document is complete.
```

Later, with LTR-001, step 2 becomes "run OCR on page 7" instead.

## 10. Validation Criteria

A document is only done when we have kept the original file, recorded how far the job got, and
can trace every bit of text back to a page.

## 11. Related Specifications / Further Reading

- `11-spec-process-rag-pipeline.md`
- `05-spec-data-database.md`
- `03-spec-architecture-system.md`
