"""Official RBI corpus ingest: download or seed, hash-skip, version, enqueue chunking."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CorpusIngestRun, RegulatoryChange, RegulatoryDocument, RequirementChange
from app.enums import LifecycleStatus, ProcessingStatus, SourceKind
from app.regulators.rbi.catalog import ALLOWED_HOSTS, CATALOG, CatalogEntry
from app.services.hashing import sha256_bytes
from app.services.queue import enqueue_ingest_regulation
from app.services.requirement_diff import diff_requirement_text
from app.services.storage import put_private_pdf, regulation_key

logger = logging.getLogger("regimpact.corpus")

DOWNLOAD_TIMEOUT = 20.0
RATE_LIMIT_SECONDS = 1.0


class DownloadFailed(Exception):
    pass


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in ALLOWED_HOSTS


def fetch_official_pdf(url: str, client: httpx.Client | None = None) -> bytes:
    if not _host_allowed(url):
        raise DownloadFailed(f"Refusing non-RBI host for {url}")
    http = client or httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True)
    try:
        response = http.get(url, headers={"User-Agent": "RegImpactCorpus/1.0"})
        if response.status_code >= 400:
            raise DownloadFailed(f"HTTP {response.status_code} for {url}")
        data = response.content
        if not data.startswith(b"%PDF"):
            raise DownloadFailed("Response was not a PDF")
        return data
    except httpx.HTTPError as exc:
        raise DownloadFailed(str(exc)) from exc
    finally:
        if client is None:
            http.close()


def bytes_for_entry(entry: CatalogEntry, client: httpx.Client | None = None) -> tuple[bytes, str]:
    if entry.pdf_url:
        try:
            return fetch_official_pdf(entry.pdf_url, client=client), SourceKind.CRAWLED.value
        except DownloadFailed as exc:
            logger.info("Official PDF unavailable for %s (%s); using seeded extract", entry.corpus_key, exc)
    return entry.seed_pdf(), SourceKind.SEEDED.value


def _document_text(session: Session, document: RegulatoryDocument) -> str:
    chunks = sorted(document.chunks, key=lambda row: row.chunk_index)
    if chunks:
        return "\n".join(chunk.text for chunk in chunks)
    return ""


def _record_change(
    session: Session,
    previous: RegulatoryDocument,
    current: RegulatoryDocument,
    previous_text: str,
    current_text: str,
) -> None:
    diffs = diff_requirement_text(previous_text, current_text)
    meaningful = [item for item in diffs if item.kind.value != "unchanged"]
    added = sum(1 for item in meaningful if item.kind.value == "added")
    modified = sum(1 for item in meaningful if item.kind.value == "modified")
    removed = sum(1 for item in meaningful if item.kind.value == "removed")
    summary = (
        f"{added} added, {modified} modified, {removed} removed"
        if meaningful
        else "New version stored; no shall-clause differences were detected."
    )
    change = RegulatoryChange(
        id=uuid4(),
        corpus_key=current.corpus_key or previous.corpus_key or "",
        previous_document_id=previous.id,
        new_document_id=current.id,
        change_kind="updated",
        summary=summary,
    )
    session.add(change)
    session.flush()
    for item in meaningful:
        session.add(
            RequirementChange(
                id=uuid4(),
                change_id=change.id,
                kind=item.kind.value,
                clause_number=item.clause_number,
                previous_text=item.previous_text,
                new_text=item.new_text,
            )
        )


def upsert_catalog_entry(
    session: Session,
    entry: CatalogEntry,
    data: bytes,
    source_kind: str,
) -> str:
    digest = sha256_bytes(data)
    existing = session.scalar(select(RegulatoryDocument).where(RegulatoryDocument.content_hash == digest))
    now = datetime.now(UTC).replace(tzinfo=None)
    if existing is not None:
        existing.last_checked_at = now
        session.flush()
        return "skipped"

    previous = session.scalar(
        select(RegulatoryDocument)
        .where(
            RegulatoryDocument.corpus_key == entry.corpus_key,
            RegulatoryDocument.lifecycle_status == LifecycleStatus.ACTIVE.value,
        )
        .order_by(RegulatoryDocument.created_at.desc())
    )
    document_id = uuid4()
    key = regulation_key(document_id, f"{entry.corpus_key}-{entry.version_label}.pdf")
    put_private_pdf(key, data)
    document = RegulatoryDocument(
        id=document_id,
        title=entry.title,
        regulator="RBI",
        document_type=entry.document_type.value,
        reference_number=entry.reference_number,
        publication_date=entry.publication_date,
        effective_date=entry.effective_date,
        source_url=entry.source_url,
        s3_key=key,
        content_hash=digest,
        processing_status=ProcessingStatus.QUEUED.value,
        jurisdiction="India",
        regulatory_domain=entry.regulatory_domain.value,
        applicable_entity_types=list(entry.applicable_entity_types),
        lifecycle_status=LifecycleStatus.ACTIVE.value,
        version_label=entry.version_label,
        corpus_key=entry.corpus_key,
        source_kind=source_kind,
        extra_metadata=dict(entry.extra) or None,
        last_checked_at=now,
    )
    outcome = "created"
    if previous is not None:
        previous.lifecycle_status = LifecycleStatus.SUPERSEDED.value
        document.supersedes_document_id = previous.id
        outcome = "updated"
    session.add(document)
    session.flush()
    if previous is not None:
        prev_pages = next(
            (
                item.seed_pages
                for item in CATALOG
                if item.corpus_key == entry.corpus_key and item.version_label == previous.version_label
            ),
            (),
        )
        previous_text = _document_text(session, previous) or "\n".join(prev_pages) or previous.title
        _record_change(
            session,
            previous,
            document,
            previous_text=previous_text,
            current_text="\n".join(entry.seed_pages),
        )
    enqueue_ingest_regulation(document.id)
    return outcome


def sync_rbi_corpus(session: Session, client: httpx.Client | None = None) -> CorpusIngestRun:
    run = CorpusIngestRun(id=uuid4(), regulator="RBI", status="running")
    session.add(run)
    session.flush()
    created = updated = skipped = failed = 0
    error = None
    try:
        http = client or httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True)
        try:
            for entry in CATALOG:
                try:
                    data, source_kind = bytes_for_entry(entry, client=http)
                    outcome = upsert_catalog_entry(session, entry, data, source_kind)
                    if outcome == "created":
                        created += 1
                    elif outcome == "updated":
                        updated += 1
                    else:
                        skipped += 1
                except Exception:
                    logger.exception("Corpus entry failed: %s", entry.corpus_key)
                    failed += 1
                time.sleep(RATE_LIMIT_SECONDS)
        finally:
            if client is None:
                http.close()
        run.status = "completed" if failed == 0 else "completed_with_errors"
    except Exception as exc:
        error = str(exc)
        run.status = "failed"
        raise
    finally:
        run.created_count = created
        run.updated_count = updated
        run.skipped_count = skipped
        run.failed_count = failed
        run.error = error
        run.finished_at = datetime.now(UTC).replace(tzinfo=None)
        session.flush()
    return run
