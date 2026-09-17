---
title: RegImpact Retrieval-Augmented Generation Pipeline Specification
version: 1.0
date_created: 2026-09-17
last_updated: 2026-09-17
owner: RegImpact Team
tags: [process, rag, retrieval, embeddings, search]
---

# Introduction

This specification defines the retrieval pipeline used to provide relevant regulatory and company evidence to AI agents.

## 1. Purpose & Scope

The pipeline covers query normalization, dense retrieval, sparse retrieval, metadata filtering, rank fusion, reranking, context selection, and citation propagation.

## 2. Definitions

- **RAG**: Retrieval-Augmented Generation.
- **Dense retrieval**: Semantic retrieval using vector embeddings.
- **Sparse retrieval**: Keyword-based retrieval such as BM25.
- **Reranking**: Reordering retrieved results using a more accurate relevance model.
- **RRF**: Reciprocal Rank Fusion.

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: The system shall support semantic and keyword retrieval.
- **REQ-002**: Retrieval shall support regulator, date, document type, and company filters.
- **REQ-003**: Retrieved chunks shall retain source metadata.
- **REQ-004**: The system shall rerank candidate chunks before final context selection.
- **REQ-005**: The final context shall be bounded by token and relevance limits.
- **REQ-006**: Retrieval results shall be logged for evaluation.
- **SEC-001**: Company documents shall never be retrieved across company boundaries.
- **CON-001**: The model shall not receive unbounded raw document collections.
- **GUD-001**: Use hybrid retrieval for legal terms, dates, clause numbers, and semantic concepts.

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
      "page_number": 5,
      "clause_number": "3.2",
      "document_id": "reg_001"
    }
  ]
}
```

## 5. Acceptance Criteria

- **AC-001**: Given an exact clause number, when searched, then keyword retrieval returns the matching clause.
- **AC-002**: Given a semantic query, when searched, then relevant conceptually similar chunks are returned.
- **AC-003**: Given a company filter, when searched, then only authorized company data is returned.
- **AC-004**: Given retrieved chunks, when passed to an agent, then source metadata is preserved.
- **AC-005**: Retrieval quality is measured using a labeled benchmark.

## 6. Test Automation Strategy

Measure Recall@K, Precision@K, MRR, citation retrieval accuracy, filter isolation, and latency. Include adversarial queries with ambiguous terms and exact references.

## 7. Rationale & Context

Regulatory text contains both semantic concepts and exact legal terminology. Hybrid retrieval reduces the risk of missing either type.

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Regulatory document store.
- **EXT-002**: Company policy store.

### Third-Party Services
- **SVC-001**: Embedding model.
- **SVC-002**: Vector search service.
- **SVC-003**: Reranking model.

### Infrastructure Dependencies
- **INF-001**: Vector index, keyword index, and retrieval service.

### Data Dependencies
- **DAT-001**: Chunked documents with embeddings and metadata.

### Technology Platform Dependencies
- **PLT-001**: Search service supporting vector and keyword queries.

### Compliance Dependencies
- **COM-001**: Tenant isolation and source traceability.

## 9. Examples & Edge Cases

If dense retrieval returns a broad policy discussion but BM25 returns the exact clause number, both candidates must be retained before reranking.

## 10. Validation Criteria

The pipeline shall return relevant, source-traceable context while respecting company and document filters.

## 11. Related Specifications / Further Reading

- `spec-process-document-ingestion.md`
- `spec-process-agent-orchestration.md`
- `spec-process-evidence-verification.md`
