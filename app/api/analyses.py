from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.config import get_settings
from app.db.models import (
    ActionItem,
    Citation,
    Company,
    ComplianceGap,
    ImpactAnalysis,
    RegulatoryDocument,
    Review,
)
from app.db.session import get_db
from app.enums import ActionStatus, AnalysisStatus, ReviewStatus
from app.schemas.models import (
    ActionRead,
    ActionUpdate,
    AnalysisCreate,
    AnalysisRead,
    AnalysisStatusRead,
    CitationRead,
    GapRead,
    ReviewDecision,
    SourceLinkRead,
)
from app.security.company_scope import get_company_id
from app.services.queue import enqueue_run_analysis
from app.services.storage import presigned_get_url

router = APIRouter(prefix="/api/v1", tags=["analyses"])


def _analysis_for_company(db: Session, analysis_id: UUID, company_id: UUID) -> ImpactAnalysis:
    analysis = db.get(ImpactAnalysis, analysis_id)
    if analysis is None or analysis.company_id != company_id:
        raise AppError("NOT_FOUND", "Analysis not found", status_code=404)
    return analysis


def _review_status(analysis: ImpactAnalysis) -> str | None:
    if analysis.review is None:
        return None
    return analysis.review.status


@router.post("/analyses", response_model=AnalysisRead, status_code=201)
def start_analysis(
    payload: AnalysisCreate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AnalysisRead:
    if payload.company_id != company_id:
        raise AppError("VALIDATION_ERROR", "company_id does not match the request company")
    if db.get(Company, payload.company_id) is None:
        raise AppError("VALIDATION_ERROR", "Invalid company_id")
    if db.get(RegulatoryDocument, payload.regulation_id) is None:
        raise AppError("VALIDATION_ERROR", "Invalid regulation_id")

    analysis = ImpactAnalysis(
        company_id=payload.company_id,
        regulation_id=payload.regulation_id,
        status=AnalysisStatus.QUEUED.value,
        analysis_depth=payload.analysis_depth.value,
        include_gap_analysis=payload.include_gap_analysis,
        include_action_plan=payload.include_action_plan,
        human_review_required=False,
    )
    db.add(analysis)
    db.flush()
    review = Review(
        analysis_id=analysis.id,
        company_id=payload.company_id,
        status=ReviewStatus.PENDING.value,
    )
    db.add(review)
    db.flush()
    analysis.review = review
    enqueue_run_analysis(analysis.id, payload.company_id)
    return _to_analysis_read(analysis)


def _to_analysis_read(analysis: ImpactAnalysis) -> AnalysisRead:
    return AnalysisRead.model_validate(analysis).model_copy(
        update={"review_status": _review_status(analysis)}
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisRead)
def read_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AnalysisRead:
    analysis = _analysis_for_company(db, analysis_id, company_id)
    return _to_analysis_read(analysis)


@router.get("/analyses/{analysis_id}/status", response_model=AnalysisStatusRead)
def analysis_status(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AnalysisStatusRead:
    analysis = _analysis_for_company(db, analysis_id, company_id)
    step = analysis.status
    if isinstance(analysis.result, dict):
        step = analysis.result.get("current_step") or analysis.result.get("failed_step") or analysis.status
    return AnalysisStatusRead(
        id=analysis.id,
        status=analysis.status,
        step=step,
        human_review_required=analysis.human_review_required,
        review_status=_review_status(analysis),
    )


@router.get("/analyses/{analysis_id}/gaps", response_model=list[GapRead])
def list_gaps(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[ComplianceGap]:
    analysis = _analysis_for_company(db, analysis_id, company_id)
    return list(
        db.scalars(
            select(ComplianceGap)
            .join(ComplianceGap.requirement)
            .where(
                ComplianceGap.company_id == company_id,
                ComplianceGap.requirement.has(analysis_id=analysis.id),
            )
        ).all()
    )


@router.get("/analyses/{analysis_id}/actions", response_model=list[ActionRead])
def list_actions(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[ActionItem]:
    _analysis_for_company(db, analysis_id, company_id)
    return list(
        db.scalars(
            select(ActionItem).where(
                ActionItem.analysis_id == analysis_id,
                ActionItem.company_id == company_id,
            )
        ).all()
    )


@router.patch("/actions/{action_id}", response_model=ActionRead)
def update_action(
    action_id: UUID,
    payload: ActionUpdate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> ActionItem:
    action = db.get(ActionItem, action_id)
    if action is None or action.company_id != company_id:
        raise AppError("NOT_FOUND", "Action not found", status_code=404)
    if payload.status is not None:
        action.status = payload.status.value
    if payload.owner_department is not None:
        action.owner_department = payload.owner_department.value
    db.flush()
    return action


@router.get("/citations/{citation_id}", response_model=CitationRead)
def read_citation(
    citation_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> CitationRead:
    citation = db.get(Citation, citation_id)
    if citation is None:
        raise AppError("NOT_FOUND", "Citation not found", status_code=404)
    _analysis_for_company(db, citation.analysis_id, company_id)
    chunk = citation.chunk
    if chunk is None or (chunk.company_id is not None and chunk.company_id != company_id):
        raise AppError("NOT_FOUND", "Citation not found", status_code=404)
    return CitationRead(
        id=citation.id,
        analysis_id=citation.analysis_id,
        chunk_id=citation.chunk_id,
        claim_text=citation.claim_text,
        excerpt=citation.excerpt,
        from_ocr=citation.from_ocr,
        relevance_verified=citation.relevance_verified,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        clause_number=chunk.clause_number,
        section_title=chunk.section_title,
    )


@router.get("/citations/{citation_id}/source", response_model=SourceLinkRead)
def citation_source(
    citation_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> SourceLinkRead:
    settings = get_settings()
    citation = db.get(Citation, citation_id)
    if citation is None:
        raise AppError("NOT_FOUND", "Citation not found", status_code=404)
    _analysis_for_company(db, citation.analysis_id, company_id)
    chunk = citation.chunk
    if chunk is None:
        raise AppError("NOT_FOUND", "Citation not found", status_code=404)
    if chunk.company_policy_id is not None:
        if chunk.company_id != company_id or chunk.company_policy is None:
            raise AppError("NOT_FOUND", "Citation not found", status_code=404)
        key = chunk.company_policy.s3_key
    elif chunk.regulatory_document is not None:
        key = chunk.regulatory_document.s3_key
    else:
        raise AppError("NOT_FOUND", "Source file not found", status_code=404)
    return SourceLinkRead(
        citation_id=citation.id,
        url=presigned_get_url(key),
        expires_in_seconds=settings.presign_ttl_seconds,
    )


def _pending_review(analysis: ImpactAnalysis) -> Review:
    review = analysis.review
    if review is None:
        raise AppError("NOT_FOUND", "Review not found", status_code=404)
    if review.status != ReviewStatus.PENDING.value:
        raise AppError(
            "REVIEW_CLOSED",
            f"This report is already {review.status}",
            status_code=409,
        )
    return review


@router.post("/analyses/{analysis_id}/approve", response_model=AnalysisRead)
def approve_analysis(
    analysis_id: UUID,
    payload: ReviewDecision | None = None,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AnalysisRead:
    analysis = _analysis_for_company(db, analysis_id, company_id)
    if analysis.status != AnalysisStatus.COMPLETED.value:
        raise AppError(
            "ANALYSIS_NOT_READY",
            "The checking step must finish before a report can be approved",
            status_code=409,
        )
    review = _pending_review(analysis)
    settings = get_settings()
    review.status = ReviewStatus.APPROVED.value
    review.decided_by = settings.demo_user_id
    review.comment = payload.comment if payload else None
    review.decided_at = datetime.now(UTC).replace(tzinfo=None)
    db.flush()
    return _to_analysis_read(analysis)


@router.post("/analyses/{analysis_id}/reject", response_model=AnalysisRead)
def reject_analysis(
    analysis_id: UUID,
    payload: ReviewDecision | None = None,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AnalysisRead:
    analysis = _analysis_for_company(db, analysis_id, company_id)
    review = _pending_review(analysis)
    settings = get_settings()
    review.status = ReviewStatus.REJECTED.value
    review.decided_by = settings.demo_user_id
    review.comment = payload.comment if payload else None
    review.decided_at = datetime.now(UTC).replace(tzinfo=None)
    for action in db.scalars(
        select(ActionItem).where(
            ActionItem.analysis_id == analysis.id,
            ActionItem.company_id == company_id,
        )
    ):
        action.status = ActionStatus.BLOCKED.value
    db.flush()
    return _to_analysis_read(analysis)
