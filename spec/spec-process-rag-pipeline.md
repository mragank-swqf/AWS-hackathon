---
title: RegImpact Retrieval-Augmented Generation Pipeline Specification
version: 1.2
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, rag, retrieval, embeddings, search]
---

# Introduction

This spec says how we find the right bits of text to show the AI. The AI never reads a whole
document. It only reads the pieces we hand it.

## 1. Purpose & Scope

It covers cleaning up the question, the two kinds of search, filtering, merging the two result
lists, sorting them, picking what to send, and carrying the source info along.

## 2. Definitions

- **RAG**: Find the right text first, then ask the AI about it.
- **Search by meaning**: Finds text that means the same thing, even in different words. Uses `pgvector`.
- **Search by keyword**: Finds the exact words. Uses PostgreSQL full-text search with `ts_rank_cd`.
- **Reranking**: Taking the results and sorting them again, more carefully.
- **RRF**: Reciprocal Rank Fusion. A simple way to merge two ranked lists into one.
- **pgvector**: The PostgreSQL add-on that makes search by meaning possible.
- **Embedding**: A list of numbers that stands for the meaning of a piece of text.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Support both kinds of search. Search by meaning uses `pgvector`. Search by keyword uses PostgreSQL full-text search. Both run against `document_chunks`.
- **REQ-002**: Support filters for regulator, date, document type, and company. Put the filters inside the SQL query. Do not fetch everything and filter after.
- **REQ-003**: Every chunk we return must still carry its source info.
- **REQ-004**: Merge the two result lists with RRF, then sort the merged list more carefully before picking what to send.
- **REQ-005**: Cap how much text we send, both by size and by how relevant it is.
- **REQ-006**: Log what each search returned, so we can measure how good it is later.
- **REQ-007**: Make embeddings with Amazon Bedrock Titan Text Embeddings V2, at 1024 numbers each. Call it through a small wrapper, so tests can swap in a fake one.
- **REQ-008**: If someone searches for a clause number, lean on keyword search and weight exact matches. Search by meaning drifts, and we must never lose an exact legal reference that way.
- **SEC-001**: Never return one company's documents to another company. Every search must limit `company_id` to the caller's company, or to empty for shared rule documents.
- **CON-001**: Never hand the AI a whole pile of raw documents.
- **CON-002**: Do not change the embedding size without rebuilding the index. The column has a fixed width.
- **GUD-001**: Use both kinds of search together. Legal wording, dates, and clause numbers need exact matching. Ideas need meaning.

## 4. Interfaces & Data Contracts

```json
{
  "query": "What grievance redressal requirements apply to this payment aggregator?",
  "filters": {
    "regulator": "RBI",
    "company_id": "company_001"
  },
  "results": [
    {
      "chunk_id": "chunk_001",
      "score": 0.91,
      "text": "Relevant clause text",
      "page_start": 5,
      "page_end": 5,
      "clause_number": "3.2",
      "section_title": "Grievance Redressal",
      "document_id": "reg_001"
    }
  ]
}
```

## 5. Acceptance Criteria

- **AC-001**: Search for an exact clause number. Keyword search returns that clause.
- **AC-002**: Search for an idea in your own words. We get back text that is about the same thing.
- **AC-003**: Search with a company filter. Only that company's data comes back.
- **AC-004**: Pass chunks to the AI. The source info is still attached.
- **AC-005**: We measure search quality against a list of questions with known right answers.

## 6. Test Automation Strategy

Measure Recall@K, Precision@K, and MRR. Check we find the right source, that filters hold, and
how long a search takes. Throw in hard questions with vague words and exact references.

## 7. Rationale & Context

Rule documents have two kinds of content. There are ideas, which you might describe in your own
words. And there is exact legal wording, like "clause 3.2". One kind of search is good at each.
Using both means we miss less.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Where rule documents are stored.
- **EXT-002**: Where company documents are stored.

### Third-Party Services
- **SVC-001**: Amazon Bedrock Titan Text Embeddings V2, 1024 numbers per chunk.
- **SVC-002**: A model for reranking. Not picked yet. See section 9.

### Infrastructure Dependencies
- **INF-001**: RDS PostgreSQL, with an HNSW index for meaning and a GIN index for keywords, both on `document_chunks`.

### Data Dependencies
- **DAT-001**: Chunked documents with their embeddings and source info.

### Technology Platform Dependencies
- **PLT-001**: PostgreSQL with `pgvector`, handling both kinds of search. There is no separate search service.

### Compliance Dependencies
- **COM-001**: Keep companies apart, and keep sources traceable.

## 9. Examples & Edge Cases

Say search by meaning finds a long general passage, and keyword search finds the exact clause
number. Keep both. Do not throw either away before the sorting step.

### Still to decide: the reranking model

We have not picked one yet. The choices are asking a Bedrock model to score the merged list, or
using a ready-made rerank model if our region has one. Until we decide, just use the RRF order
with no extra sorting step. So REQ-004 is only half done for now.

## 10. Validation Criteria

Search is good enough when it returns text that is relevant, that we can trace to a source, and
that respects the company and document filters.

## 11. Related Specifications / Further Reading

- `spec-process-document-ingestion.md`
- `spec-process-agent-orchestration.md`
- `spec-process-evidence-verification.md`
