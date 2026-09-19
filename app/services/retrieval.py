"""Hybrid retrieval over document_chunks (spec 11)."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk, RegulatoryDocument
from app.enums import ANALYSIS_DEPTH_CHUNK_LIMIT, AnalysisDepth
from app.services.embeddings import Embedder, default_embedder

logger = logging.getLogger("regimpact.retrieval")

RRF_K = 60
CLAUSE_QUERY = re.compile(r"^(?:clause|para|paragraph|section)?\s*(\d+(?:\.\d+){0,5})$", re.I)


@dataclass
class SearchFilters:
    company_id: UUID
    regulator: str | None = None
    document_type: str | None = None
    regulation_id: UUID | None = None
    policy_only: bool = False
    regulation_only: bool = False


@dataclass
class SearchHit:
    chunk_id: UUID
    score: float
    text: str
    page_start: int
    page_end: int
    clause_number: str | None
    section_title: str | None
    document_id: UUID | None
    company_id: UUID | None
    source: str


def chunk_visible_to_company(chunk_company_id: UUID | None, viewer_company_id: UUID) -> bool:
    return chunk_company_id is None or chunk_company_id == viewer_company_id


def company_chunk_filter(viewer_company_id: UUID):
    return or_(
        DocumentChunk.company_id.is_(None),
        DocumentChunk.company_id == viewer_company_id,
    )


def chunks_for_company(session: Session, viewer_company_id: UUID) -> Select[tuple[DocumentChunk]]:
    return select(DocumentChunk).where(company_chunk_filter(viewer_company_id))


def list_chunks_for_company(session: Session, viewer_company_id: UUID) -> list[DocumentChunk]:
    return list(session.scalars(chunks_for_company(session, viewer_company_id)).all())


def is_clause_query(query: str) -> bool:
    return bool(CLAUSE_QUERY.match(query.strip()))


def clause_number_from_query(query: str) -> str | None:
    match = CLAUSE_QUERY.match(query.strip())
    return match.group(1) if match else None


def rrf_merge(vector_ids: list[UUID], keyword_ids: list[UUID], k: int = RRF_K) -> dict[UUID, float]:
    scores: dict[UUID, float] = defaultdict(float)
    for rank, chunk_id in enumerate(vector_ids, start=1):
        scores[chunk_id] += 1.0 / (k + rank)
    for rank, chunk_id in enumerate(keyword_ids, start=1):
        scores[chunk_id] += 1.0 / (k + rank)
    return dict(scores)


def lexical_rank(chunks: list[DocumentChunk], query: str) -> list[UUID]:
    """Keyword-style rank used when we already have chunks in memory (tests)."""
    clause = clause_number_from_query(query)
    terms = [part.lower() for part in re.findall(r"[a-z0-9.]+", query.lower()) if part]
    scored: list[tuple[float, UUID]] = []
    for chunk in chunks:
        score = 0.0
        if clause and chunk.clause_number == clause:
            score += 10.0
        haystack = chunk.text.lower()
        score += sum(1.0 for term in terms if term in haystack)
        if score:
            scored.append((score, chunk.id))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk_id for _score, chunk_id in scored]


def _scoped_query(filters: SearchFilters) -> Select:
    stmt = select(DocumentChunk).outerjoin(
        RegulatoryDocument,
        DocumentChunk.regulatory_document_id == RegulatoryDocument.id,
    )
    stmt = stmt.where(company_chunk_filter(filters.company_id))
    if filters.policy_only:
        stmt = stmt.where(DocumentChunk.company_id == filters.company_id)
    if filters.regulation_only:
        stmt = stmt.where(DocumentChunk.company_id.is_(None))
    if filters.regulation_id is not None:
        stmt = stmt.where(DocumentChunk.regulatory_document_id == filters.regulation_id)
    if filters.regulator:
        stmt = stmt.where(
            or_(
                DocumentChunk.regulatory_document_id.is_(None),
                RegulatoryDocument.regulator == filters.regulator,
            )
        )
    if filters.document_type:
        stmt = stmt.where(
            or_(
                DocumentChunk.regulatory_document_id.is_(None),
                RegulatoryDocument.document_type == filters.document_type,
            )
        )
    return stmt


def _as_hit(chunk: DocumentChunk, score: float) -> SearchHit:
    if chunk.regulatory_document_id is not None:
        source = "regulation"
        document_id = chunk.regulatory_document_id
    else:
        source = "policy"
        document_id = chunk.company_policy_id
    return SearchHit(
        chunk_id=chunk.id,
        score=score,
        text=chunk.text,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        clause_number=chunk.clause_number,
        section_title=chunk.section_title,
        document_id=document_id,
        company_id=chunk.company_id,
        source=source,
    )


def hybrid_search(
    session: Session,
    query: str,
    filters: SearchFilters,
    *,
    depth: AnalysisDepth = AnalysisDepth.STANDARD,
    embedder: Embedder | None = None,
    limit: int | None = None,
) -> list[SearchHit]:
    """pgvector + Postgres FTS, fused with RRF. Filters stay inside SQL (spec 11)."""
    limit = limit or ANALYSIS_DEPTH_CHUNK_LIMIT[depth]
    fetch = max(limit * 2, limit)
    embedder = embedder or default_embedder()

    keyword_ids: list[UUID] = []
    clause = clause_number_from_query(query)
    if clause:
        exact = list(
            session.scalars(
                _scoped_query(filters).where(DocumentChunk.clause_number == clause).limit(fetch)
            )
        )
        keyword_ids.extend(chunk.id for chunk in exact)

    tsquery = func.plainto_tsquery("english", query)
    fts_rows = list(
        session.scalars(
            _scoped_query(filters)
            .where(DocumentChunk.text_search.op("@@")(tsquery))
            .order_by(func.ts_rank_cd(DocumentChunk.text_search, tsquery).desc())
            .limit(fetch)
        )
    )
    for chunk in fts_rows:
        if chunk.id not in keyword_ids:
            keyword_ids.append(chunk.id)

    vector_ids: list[UUID] = []
    if not is_clause_query(query):
        embedding = embedder.embed(query)
        vector_rows = list(
            session.scalars(
                _scoped_query(filters)
                .where(DocumentChunk.embedding.is_not(None))
                .order_by(DocumentChunk.embedding.cosine_distance(embedding))
                .limit(fetch)
            )
        )
        vector_ids = [chunk.id for chunk in vector_rows]
    else:
        # Exact legal references: do not let meaning-search drift the clause away.
        vector_ids = []

    scores = rrf_merge(vector_ids, keyword_ids)
    ranked_ids = sorted(scores, key=scores.get, reverse=True)[:limit]
    by_id = {
        chunk.id: chunk
        for chunk in session.scalars(select(DocumentChunk).where(DocumentChunk.id.in_(ranked_ids))).all()
    }
    hits = [_as_hit(by_id[chunk_id], scores[chunk_id]) for chunk_id in ranked_ids if chunk_id in by_id]
    logger.info(
        "search query=%r company=%s keyword=%d vector=%d fused=%d",
        query,
        filters.company_id,
        len(keyword_ids),
        len(vector_ids),
        len(hits),
    )
    return hits
