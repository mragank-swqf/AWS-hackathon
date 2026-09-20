from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.db.models import RegulatoryDocument
from app.db.session import get_db
from app.enums import DocumentType, ProcessingStatus
from app.schemas.models import RegulationRead
from app.security.company_scope import get_company_id
from app.security.uploads import UploadRejected, validate_pdf_upload
from app.services.hashing import sha256_bytes
from app.services.queue import enqueue_ingest_regulation
from app.services.storage import put_private_pdf, regulation_key

router = APIRouter(prefix="/api/v1/regulations", tags=["regulations"])


def _parse_optional_date(value: str | None, field_name: str) -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppError("VALIDATION_ERROR", f"Invalid {field_name}; use YYYY-MM-DD") from exc


@router.post("", response_model=RegulationRead, status_code=201)
async def upload_regulation(
    file: UploadFile = File(...),
    title: str = Form(...),
    regulator: str = Form(...),
    document_type: DocumentType = Form(...),
    reference_number: str | None = Form(default=None),
    publication_date: str | None = Form(default=None),
    effective_date: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    db: Session = Depends(get_db),
    _company_id: UUID = Depends(get_company_id),
) -> RegulatoryDocument:
    data = await file.read()
    try:
        validated = validate_pdf_upload(file.filename, file.content_type, data)
    except UploadRejected as exc:
        raise AppError(exc.code, exc.message, status_code=exc.status_code) from exc

    parsed_publication = _parse_optional_date(publication_date, "publication_date")
    parsed_effective = _parse_optional_date(effective_date, "effective_date")
    cleaned_title = title.strip()
    cleaned_regulator = regulator.strip()
    if not cleaned_title:
        raise AppError("VALIDATION_ERROR", "title is required")
    if not cleaned_regulator:
        raise AppError("VALIDATION_ERROR", "regulator is required")

    content_hash = sha256_bytes(validated.data)
    existing = db.scalar(
        select(RegulatoryDocument).where(RegulatoryDocument.content_hash == content_hash)
    )
    if existing is not None:
        raise AppError("DUPLICATE_DOCUMENT", "This rule document has already been uploaded", status_code=409)

    document_id = uuid4()
    key = regulation_key(document_id, validated.filename)
    put_private_pdf(key, validated.data)

    document = RegulatoryDocument(
        id=document_id,
        title=cleaned_title,
        regulator=cleaned_regulator,
        document_type=document_type.value,
        reference_number=reference_number,
        publication_date=parsed_publication,
        effective_date=parsed_effective,
        source_url=source_url,
        s3_key=key,
        content_hash=content_hash,
        processing_status=ProcessingStatus.QUEUED.value,
        source_kind="uploaded",
        lifecycle_status="active",
        jurisdiction="India",
    )

    db.add(document)
    db.flush()
    enqueue_ingest_regulation(document.id)
    return document


@router.get("", response_model=list[RegulationRead])
def list_regulations(
    db: Session = Depends(get_db),
    _company_id: UUID = Depends(get_company_id),
) -> list[RegulatoryDocument]:
    return list(db.scalars(select(RegulatoryDocument).order_by(RegulatoryDocument.created_at.desc())).all())


@router.get("/{regulation_id}", response_model=RegulationRead)
def read_regulation(
    regulation_id: UUID,
    db: Session = Depends(get_db),
    _company_id: UUID = Depends(get_company_id),
) -> RegulatoryDocument:
    document = db.get(RegulatoryDocument, regulation_id)
    if document is None:
        raise AppError("NOT_FOUND", "Regulation not found", status_code=404)
    return document
