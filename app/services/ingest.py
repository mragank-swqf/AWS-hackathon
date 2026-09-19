"""Ingest a PDF from S3 into document_chunks (spec 10)."""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CompanyPolicy, DocumentChunk, RegulatoryDocument
from app.enums import ExtractionMethod, ProcessingStatus
from app.services.chunking import chunk_pages
from app.services.embeddings import Embedder, default_embedder
from app.services.pdf import extract_pages
from app.services.storage import get_object_bytes

logger = logging.getLogger("regimpact.ingest")


def _set_status(session: Session, document: RegulatoryDocument | CompanyPolicy, status: ProcessingStatus) -> None:
    document.processing_status = status.value
    session.commit()


def _replace_chunks(session: Session, *, regulation_id: UUID | None, policy_id: UUID | None) -> None:
    stmt = select(DocumentChunk)
    if regulation_id is not None:
        stmt = stmt.where(DocumentChunk.regulatory_document_id == regulation_id)
    else:
        stmt = stmt.where(DocumentChunk.company_policy_id == policy_id)
    for row in session.scalars(stmt):
        session.delete(row)
    session.flush()


def _save_chunks(
    session: Session,
    drafts,
    embedder: Embedder,
    *,
    regulation_id: UUID | None,
    policy_id: UUID | None,
    company_id: UUID | None,
) -> int:
    created = 0
    for draft in drafts:
        embedding = None
        if draft.extraction_method == ExtractionMethod.TEXT.value:
            embedding = embedder.embed(draft.text)
        session.add(
            DocumentChunk(
                id=uuid4(),
                regulatory_document_id=regulation_id,
                company_policy_id=policy_id,
                company_id=company_id,
                chunk_index=draft.chunk_index,
                text=draft.text,
                page_start=draft.page_start,
                page_end=draft.page_end,
                section_title=draft.section_title,
                clause_number=draft.clause_number,
                extraction_method=draft.extraction_method,
                embedding=embedding,
            )
        )
        created += 1
    session.flush()
    return created


def ingest_bytes(data: bytes, embedder: Embedder | None = None) -> tuple[list, int, list[int]]:
    embedder = embedder or default_embedder()
    pages = extract_pages(data)
    drafts = chunk_pages(pages)
    unreadable = [page.page_number for page in pages if page.unreadable]
    return drafts, len(pages), unreadable


def ingest_regulation(
    session: Session,
    document_id: UUID,
    embedder: Embedder | None = None,
) -> None:
    document = session.get(RegulatoryDocument, document_id)
    if document is None:
        logger.warning("Regulation %s is gone; dropping ingest job", document_id)
        return
    if document.processing_status == ProcessingStatus.COMPLETED.value:
        logger.info("Regulation %s already ingested; skipping", document_id)
        return
    embedder = embedder or default_embedder()
    try:
        _set_status(session, document, ProcessingStatus.EXTRACTING)
        data = get_object_bytes(document.s3_key)
        _set_status(session, document, ProcessingStatus.CHUNKING)
        drafts, page_count, _unreadable = ingest_bytes(data, embedder)
        document.pages = page_count
        _replace_chunks(session, regulation_id=document.id, policy_id=None)
        _set_status(session, document, ProcessingStatus.EMBEDDING)
        _save_chunks(
            session,
            drafts,
            embedder,
            regulation_id=document.id,
            policy_id=None,
            company_id=None,
        )
        _set_status(session, document, ProcessingStatus.COMPLETED)
    except Exception:
        _set_status(session, document, ProcessingStatus.FAILED)
        raise


def ingest_policy(
    session: Session,
    document_id: UUID,
    embedder: Embedder | None = None,
) -> None:
    policy = session.get(CompanyPolicy, document_id)
    if policy is None:
        logger.warning("Policy %s is gone; dropping ingest job", document_id)
        return
    if policy.processing_status == ProcessingStatus.COMPLETED.value:
        logger.info("Policy %s already ingested; skipping", document_id)
        return
    embedder = embedder or default_embedder()
    try:
        _set_status(session, policy, ProcessingStatus.EXTRACTING)
        data = get_object_bytes(policy.s3_key)
        _set_status(session, policy, ProcessingStatus.CHUNKING)
        drafts, _page_count, _unreadable = ingest_bytes(data, embedder)
        _replace_chunks(session, regulation_id=None, policy_id=policy.id)
        _set_status(session, policy, ProcessingStatus.EMBEDDING)
        _save_chunks(
            session,
            drafts,
            embedder,
            regulation_id=None,
            policy_id=policy.id,
            company_id=policy.company_id,
        )
        _set_status(session, policy, ProcessingStatus.COMPLETED)
    except Exception:
        _set_status(session, policy, ProcessingStatus.FAILED)
        raise
