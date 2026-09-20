"""Persist structured applicability and roll up a company-level portfolio analysis."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.agents.runner import run_analysis
from app.db.models import (
    Company,
    ComplianceGap,
    ImpactAnalysis,
    PortfolioRun,
    RegulationApplicability,
    RegulatoryDocument,
    RegulatoryRequirement,
    Review,
)
from app.enums import (
    AnalysisDepth,
    AnalysisStatus,
    Applicability,
    LifecycleStatus,
    ReviewStatus,
)
from app.services.applicability import assess_document

IN_SCOPE = {Applicability.APPLICABLE.value, Applicability.LIKELY_APPLICABLE.value}


def refresh_applicability(session: Session, company: Company) -> list[RegulationApplicability]:
    documents = list(
        session.scalars(
            select(RegulatoryDocument).where(
                RegulatoryDocument.lifecycle_status == LifecycleStatus.ACTIVE.value
            )
        )
    )
    rows: list[RegulationApplicability] = []
    for document in documents:
        decision = assess_document(company, document)
        existing = session.scalar(
            select(RegulationApplicability).where(
                RegulationApplicability.company_id == company.id,
                RegulationApplicability.regulation_id == document.id,
            )
        )
        if existing is None:
            existing = RegulationApplicability(
                id=uuid4(),
                company_id=company.id,
                regulation_id=document.id,
            )
            session.add(existing)
        if existing.reviewer_applicability:
            existing.applicability = existing.reviewer_applicability
            existing.human_review_required = False
            existing.matched_characteristics = decision.matched_characteristics
            rows.append(existing)
            continue
        existing.applicability = decision.applicability.value
        existing.reason = decision.reason
        existing.matched_characteristics = decision.matched_characteristics
        existing.rule_id = decision.rule_id
        existing.human_review_required = decision.human_review_required
        rows.append(existing)
    session.flush()
    return rows


def applicable_documents(session: Session, company_id: UUID) -> list[RegulatoryDocument]:
    rows = list(
        session.scalars(
            select(RegulationApplicability).where(RegulationApplicability.company_id == company_id)
        )
    )
    ids = [row.regulation_id for row in rows if row.applicability in IN_SCOPE]
    if not ids:
        return []
    return list(session.scalars(select(RegulatoryDocument).where(RegulatoryDocument.id.in_(ids))))


def _dashboard_from_analyses(session: Session, analyses: list[ImpactAnalysis]) -> dict:
    reqs = []
    gaps = []
    for analysis in analyses:
        reqs.extend(
            session.scalars(
                select(RegulatoryRequirement).where(RegulatoryRequirement.analysis_id == analysis.id)
            )
        )
        gaps.extend(
            session.scalars(
                select(ComplianceGap)
                .join(RegulatoryRequirement)
                .where(RegulatoryRequirement.analysis_id == analysis.id)
            )
        )
    gap_by_req = {gap.requirement_id: gap for gap in gaps}
    fully = 0
    partial = 0
    missing = 0
    high = 0
    for req in reqs:
        gap = gap_by_req.get(req.id)
        status = gap.gap_status if gap else None
        if status == "compliant":
            fully += 1
        elif status == "partial":
            partial += 1
        else:
            missing += 1
        if gap and gap.severity in {"high", "critical"}:
            high += 1
    review = sum(1 for analysis in analyses if analysis.human_review_required)
    severities = [analysis.overall_risk for analysis in analyses if analysis.overall_risk]
    order = ["low", "medium", "high", "critical"]
    overall = None
    if severities:
        overall = max(severities, key=lambda item: order.index(item) if item in order else 0)
    return {
        "requirements_assessed": len(reqs),
        "fully_evidenced": fully,
        "partially_evidenced": partial,
        "gaps": missing,
        "high_risk_gaps": high,
        "human_review_required": review,
        "overall_risk": overall,
        "analysis_ids": [str(item.id) for item in analyses],
        "assessment_confidence": {
            "label": "Assessment confidence",
            "definition": (
                "An internal evidence-quality indicator from citation coverage, retrieval scores, "
                "and schema-valid first tries. It is not a probability that the conclusion is legally correct."
            ),
            "method": "local_extractive",
        },
    }


def run_portfolio(session: Session, run_id: UUID) -> None:
    run = session.get(PortfolioRun, run_id)
    if run is None:
        raise ValueError(f"Portfolio run {run_id} not found")
    company = session.get(Company, run.company_id)
    if company is None:
        run.status = AnalysisStatus.FAILED.value
        session.flush()
        return
    run.status = AnalysisStatus.PROCESSING.value
    session.flush()
    refresh_applicability(session, company)
    documents = sorted(
        [
            document
            for document in applicable_documents(session, company.id)
            if document.processing_status == "completed"
        ],
        key=lambda item: item.title.lower(),
    )
    analyses: list[ImpactAnalysis] = []
    for document in documents:
        analysis = ImpactAnalysis(
            id=uuid4(),
            company_id=company.id,
            regulation_id=document.id,
            portfolio_run_id=run.id,
            status=AnalysisStatus.QUEUED.value,
            analysis_depth=AnalysisDepth.STANDARD.value,
            include_gap_analysis=True,
            include_action_plan=True,
            human_review_required=False,
        )
        session.add(analysis)
        session.flush()
        session.add(
            Review(
                analysis_id=analysis.id,
                company_id=company.id,
                status=ReviewStatus.PENDING.value,
            )
        )
        session.flush()
        run_analysis(session, analysis.id)
        session.refresh(analysis)
        analyses.append(analysis)
    rollup = _dashboard_from_analyses(session, analyses)
    uncertain = list(
        session.scalars(
            select(RegulationApplicability).where(
                RegulationApplicability.company_id == company.id,
                RegulationApplicability.human_review_required.is_(True),
            )
        )
    )
    rollup["applicable"] = len(documents)
    rollup["uncertain_applicability"] = len(uncertain)
    run.result = dict(rollup)
    flag_modified(run, "result")
    run.overall_risk = rollup.get("overall_risk")
    run.human_review_required = bool(rollup["human_review_required"] or uncertain)
    run.status = AnalysisStatus.COMPLETED.value
    run.completed_at = datetime.now(UTC).replace(tzinfo=None)
    session.flush()
