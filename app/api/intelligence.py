"""RBI corpus, applicability, dashboard, and portfolio analysis."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.errors import AppError
from app.db.models import (
    Company,
    CorpusIngestRun,
    ImpactAnalysis,
    PortfolioRun,
    RegulationApplicability,
    RegulatoryChange,
    RegulatoryDocument,
)
from app.db.session import get_db
from app.enums import AnalysisStatus, LifecycleStatus
from app.schemas.models import (
    ApplicabilityDecisionWrite,
    ApplicabilityRead,
    DashboardRead,
    PortfolioRunRead,
    RegulationRead,
    RegulatoryChangeRead,
    RequirementChangeRead,
)
from app.security.company_scope import get_company_id
from app.services.applicability import apply_reviewer_decision
from app.services.portfolio import refresh_applicability
from app.services.queue import enqueue_run_portfolio, enqueue_sync_corpus

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


def _company(db: Session, company_id: UUID) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError("NOT_FOUND", "Company not found", status_code=404)
    return company


@router.get("/corpus", response_model=list[RegulationRead])
def list_corpus(
    db: Session = Depends(get_db),
    _company_id: UUID = Depends(get_company_id),
) -> list[RegulatoryDocument]:
    return list(
        db.scalars(
            select(RegulatoryDocument)
            .where(RegulatoryDocument.source_kind.in_(("seeded", "crawled")))
            .order_by(RegulatoryDocument.created_at.desc())
        )
    )


@router.get("/applicable", response_model=list[ApplicabilityRead])
def list_applicable(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[ApplicabilityRead]:
    company = _company(db, company_id)
    rows = refresh_applicability(db, company)
    payload = []
    for row in rows:
        document = db.get(RegulatoryDocument, row.regulation_id)
        if document is None:
            continue
        payload.append(
            ApplicabilityRead(
                id=row.id,
                regulation_id=document.id,
                title=document.title,
                regulator=document.regulator,
                document_type=document.document_type,
                regulatory_domain=document.regulatory_domain,
                source_url=document.source_url,
                lifecycle_status=document.lifecycle_status,
                applicability=row.applicability,
                reason=row.reason,
                matched_characteristics=row.matched_characteristics or [],
                rule_id=row.rule_id,
                human_review_required=row.human_review_required,
                processing_status=document.processing_status,
                reviewer_applicability=row.reviewer_applicability,
            )
        )
    payload.sort(key=lambda item: (item.applicability, item.title))
    return payload


@router.post("/applicable/{row_id}/decide", response_model=ApplicabilityRead)
def decide_applicable(
    row_id: UUID,
    payload: ApplicabilityDecisionWrite,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> ApplicabilityRead:
    _company(db, company_id)
    row = db.get(RegulationApplicability, row_id)
    if row is None or row.company_id != company_id:
        raise AppError("NOT_FOUND", "Applicability row not found", status_code=404)
    try:
        apply_reviewer_decision(row, payload.applicability)
    except ValueError as exc:
        raise AppError("VALIDATION_ERROR", str(exc), status_code=400) from exc
    db.commit()
    db.refresh(row)
    document = db.get(RegulatoryDocument, row.regulation_id)
    if document is None:
        raise AppError("NOT_FOUND", "Regulation not found", status_code=404)
    return ApplicabilityRead(
        id=row.id,
        regulation_id=document.id,
        title=document.title,
        regulator=document.regulator,
        document_type=document.document_type,
        regulatory_domain=document.regulatory_domain,
        source_url=document.source_url,
        lifecycle_status=document.lifecycle_status,
        applicability=row.applicability,
        reason=row.reason,
        matched_characteristics=row.matched_characteristics or [],
        rule_id=row.rule_id,
        human_review_required=row.human_review_required,
        processing_status=document.processing_status,
        reviewer_applicability=row.reviewer_applicability,
    )


@router.get("/changes", response_model=list[RegulatoryChangeRead])
def list_changes(
    db: Session = Depends(get_db),
    _company_id: UUID = Depends(get_company_id),
) -> list[RegulatoryChangeRead]:
    changes = list(
        db.scalars(
            select(RegulatoryChange)
            .options(selectinload(RegulatoryChange.requirement_changes))
            .order_by(RegulatoryChange.created_at.desc())
        )
    )
    payload = []
    for change in changes:
        document = db.get(RegulatoryDocument, change.new_document_id)
        payload.append(
            RegulatoryChangeRead(
                id=change.id,
                corpus_key=change.corpus_key,
                change_kind=change.change_kind,
                summary=change.summary,
                title=document.title if document else change.corpus_key,
                source_url=document.source_url if document else None,
                previous_document_id=change.previous_document_id,
                new_document_id=change.new_document_id,
                created_at=change.created_at,
                requirement_changes=[
                    RequirementChangeRead(
                        id=item.id,
                        kind=item.kind,
                        clause_number=item.clause_number,
                        previous_text=item.previous_text,
                        new_text=item.new_text,
                    )
                    for item in change.requirement_changes
                    if item.kind != "unchanged"
                ],
            )
        )
    return payload


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> DashboardRead:
    company = _company(db, company_id)
    rows = refresh_applicability(db, company)
    applicable = sum(1 for row in rows if row.applicability in {"applicable", "likely_applicable"})
    review = sum(1 for row in rows if row.human_review_required)
    corpus_count = len(
        list(
            db.scalars(
                select(RegulatoryDocument).where(
                    RegulatoryDocument.lifecycle_status == LifecycleStatus.ACTIVE.value
                )
            )
        )
    )
    latest_change = db.scalar(select(RegulatoryChange).order_by(RegulatoryChange.created_at.desc()))
    latest_run = db.scalar(
        select(PortfolioRun)
        .where(PortfolioRun.company_id == company_id)
        .order_by(PortfolioRun.created_at.desc())
    )
    ingest = db.scalar(select(CorpusIngestRun).order_by(CorpusIngestRun.started_at.desc()))
    result = (latest_run.result if latest_run and isinstance(latest_run.result, dict) else {}) or {}
    analysis_ids = [UUID(value) for value in (result.get("analysis_ids") or [])]
    if not analysis_ids and latest_run:
        analysis_ids = list(
            db.scalars(
                select(ImpactAnalysis.id).where(ImpactAnalysis.portfolio_run_id == latest_run.id)
            )
        )
    confidence = result.get("assessment_confidence") or {
        "label": "Assessment confidence",
        "definition": (
            "An internal evidence-quality indicator. It is not a probability that a "
            "compliance conclusion is legally correct."
        ),
        "method": "local_extractive",
    }
    return DashboardRead(
        applicable=result.get("applicable", applicable),
        requirements_assessed=result.get("requirements_assessed", 0),
        fully_evidenced=result.get("fully_evidenced", 0),
        partially_evidenced=result.get("partially_evidenced", 0),
        gaps=result.get("gaps", 0),
        high_risk_gaps=result.get("high_risk_gaps", 0),
        human_review_required=result.get("human_review_required", review),
        overall_risk=result.get("overall_risk") or (latest_run.overall_risk if latest_run else None),
        corpus_documents=corpus_count,
        latest_change_summary=latest_change.summary if latest_change else None,
        assessment_confidence=confidence,
        portfolio_run_id=latest_run.id if latest_run else None,
        analysis_id=analysis_ids[0] if analysis_ids else None,
        analysis_ids=analysis_ids,
        ingest_status=ingest.status if ingest else None,
    )


@router.post("/sync", status_code=202)
def request_sync(
    _db: Session = Depends(get_db),
    _company_id: UUID = Depends(get_company_id),
) -> dict[str, str]:
    enqueue_sync_corpus()
    return {"status": "queued"}


@router.post("/portfolio", response_model=PortfolioRunRead, status_code=201)
def start_portfolio(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> PortfolioRun:
    _company(db, company_id)
    run = PortfolioRun(
        id=uuid4(),
        company_id=company_id,
        status=AnalysisStatus.QUEUED.value,
        human_review_required=False,
    )
    db.add(run)
    db.flush()
    db.commit()
    db.refresh(run)
    enqueue_run_portfolio(run.id, company_id)
    return run
