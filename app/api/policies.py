from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.db.models import Company, CompanyPolicy
from app.db.session import get_db
from app.enums import Department, EvidenceType, ProcessingStatus
from app.schemas.models import PolicyRead
from app.security.company_scope import get_company_id
from app.security.uploads import UploadRejected, validate_pdf_upload
from app.services.hashing import sha256_bytes
from app.services.queue import enqueue_ingest_policy
from app.services.storage import delete_object, policy_key, put_private_pdf

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


def _parse_optional_date(value: str | None, field_name: str) -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppError("VALIDATION_ERROR", f"Invalid {field_name}; use YYYY-MM-DD") from exc


def _owned_policy(db: Session, policy_id: UUID, company_id: UUID) -> CompanyPolicy:
    policy = db.get(CompanyPolicy, policy_id)
    if policy is None or policy.company_id != company_id:
        raise AppError("NOT_FOUND", "Policy not found", status_code=404)
    return policy


@router.post("", response_model=PolicyRead, status_code=201)
async def upload_policy(
    file: UploadFile = File(...),
    title: str = Form(...),
    evidence_type: EvidenceType = Form(...),
    version_label: str | None = Form(default=None),
    effective_date: str | None = Form(default=None),
    owner_department: Department | None = Form(default=None),
    approved_by: str | None = Form(default=None),
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> CompanyPolicy:
    if db.get(Company, company_id) is None:
        raise AppError("NOT_FOUND", "Company not found", status_code=404)

    data = await file.read()
    try:
        validated = validate_pdf_upload(file.filename, file.content_type, data)
    except UploadRejected as exc:
        raise AppError(exc.code, exc.message, status_code=exc.status_code) from exc

    content_hash = sha256_bytes(validated.data)
    existing = db.scalar(
        select(CompanyPolicy).where(
            CompanyPolicy.company_id == company_id,
            CompanyPolicy.content_hash == content_hash,
        )
    )
    if existing is not None:
        raise AppError("DUPLICATE_DOCUMENT", "This company document has already been uploaded", status_code=409)

    document_id = uuid4()
    key = policy_key(company_id, document_id, validated.filename)
    put_private_pdf(key, validated.data)

    cleaned_title = title.strip()
    if not cleaned_title:
        raise AppError("VALIDATION_ERROR", "title is required")

    policy = CompanyPolicy(
        id=document_id,
        company_id=company_id,
        title=cleaned_title,
        evidence_type=evidence_type.value,
        version_label=version_label,
        effective_date=_parse_optional_date(effective_date, "effective_date"),
        owner_department=owner_department.value if owner_department else None,
        approved_by=approved_by,
        s3_key=key,
        content_hash=content_hash,
        processing_status=ProcessingStatus.QUEUED.value,
    )
    db.add(policy)
    db.flush()
    enqueue_ingest_policy(policy.id, company_id)
    return policy


@router.get("", response_model=list[PolicyRead])
def list_policies(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[CompanyPolicy]:
    return list(
        db.scalars(
            select(CompanyPolicy)
            .where(CompanyPolicy.company_id == company_id)
            .order_by(CompanyPolicy.created_at.desc())
        ).all()
    )


@router.get("/{policy_id}", response_model=PolicyRead)
def read_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> CompanyPolicy:
    return _owned_policy(db, policy_id, company_id)


@router.delete("/{policy_id}", status_code=204)
def delete_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> None:
    policy = _owned_policy(db, policy_id, company_id)
    delete_object(policy.s3_key)
    db.delete(policy)
    db.flush()
