from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException, Request

from app.config import get_settings

COMPANY_HEADER = "X-Company-Id"


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def get_company_id(
    x_company_id: str | None = Header(default=None, alias=COMPANY_HEADER),
) -> UUID:
    """Every tenant-scoped request carries company_id (spec 08 REQ-006, spec 07 SEC-008)."""
    settings = get_settings()
    raw = (x_company_id or "").strip()
    if not raw and settings.demo_company_id is not None:
        return settings.demo_company_id
    if not raw:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_COMPANY_ID",
                "message": f"{COMPANY_HEADER} header is required",
            },
        )
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_COMPANY_ID", "message": "company_id must be a UUID"},
        ) from exc
