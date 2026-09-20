from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.db.models import Company
from app.db.session import get_db
from app.schemas.models import CompanyCreate, CompanyRead, CompanyUpdate
from app.security.company_scope import get_company_id

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _get_company(db: Session, company_id: UUID) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError("NOT_FOUND", "Company not found", status_code=404)
    return company


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    data = payload.model_dump()
    data["organization_type"] = payload.organization_type.value
    company = Company(**data)
    db.add(company)
    db.flush()
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def read_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    scoped_company_id: UUID = Depends(get_company_id),
) -> Company:
    if company_id != scoped_company_id:
        raise AppError("NOT_FOUND", "Company not found", status_code=404)
    return _get_company(db, company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    scoped_company_id: UUID = Depends(get_company_id),
) -> Company:
    if company_id != scoped_company_id:
        raise AppError("NOT_FOUND", "Company not found", status_code=404)
    company = _get_company(db, company_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(company, key, value.value if isinstance(value, StrEnum) else value)
    db.flush()
    return company
