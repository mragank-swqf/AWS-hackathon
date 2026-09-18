"""Seven-step analysis runner (specs 13, 14, 15)."""

from __future__ import annotations

import logging
import time
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.contracts import (
    ActionPlanOutput,
    ApplicabilityOutput,
    GapOutput,
    ImpactOutput,
    RequirementItem,
    RequirementsOutput,
    VerificationOutput,
)
from app.agents.llm import LLM, ClaudeLLM, complete_model, parse_json_object
from app.agents.prompts import build_prompt, claim_check_prompt
from app.agents.review_rules import compute_confidence, human_review_required, verification_status
from app.agents.risk import deadline_proximity, overall_risk, score_risk
from app.db.models import (
    ActionItem,
    Citation,
    Company,
    ComplianceGap,
    DocumentChunk,
    ImpactAnalysis,
    RegulatoryDocument,
    RegulatoryRequirement,
)
from app.enums import (
    ANALYSIS_DEPTH_CHUNK_LIMIT,
    ANALYSIS_DEPTH_RESEARCH,
    ActionStatus,
    AnalysisDepth,
    AnalysisStatus,
    ExtractionMethod,
)
from app.services.embeddings import Embedder, TitanEmbedder
from app.services.retrieval import SearchFilters, SearchHit, hybrid_search

logger = logging.getLogger("regimpact.runner")

STEPS = (
    "applicability",
    "requirements",
    "impact",
    "gap_detection",
    "risk",
    "action_plan",
    "verification",
)

APPLICABILITY_SCHEMA = ApplicabilityOutput.model_json_schema()
REQUIREMENTS_SCHEMA = RequirementsOutput.model_json_schema()
IMPACT_SCHEMA = ImpactOutput.model_json_schema()
GAP_SCHEMA = GapOutput.model_json_schema()
ACTION_SCHEMA = ActionPlanOutput.model_json_schema()


def _company_scope_fields(company: Company) -> dict[str, Any]:
    return {
        "organization_type": company.organization_type,
        "business_model": company.business_model,
        "products": company.products,
        "operating_regions": company.operating_regions,
        "regulatory_entities": company.regulatory_entities,
    }


def _hits_text(hits: list[SearchHit]) -> str:
    parts = []
    for hit in hits:
        parts.append(
            f"[chunk_id={hit.chunk_id} pages={hit.page_start}-{hit.page_end} "
            f"clause={hit.clause_number}]\n{hit.text}"
        )
    return "\n\n".join(parts) or "[no chunks found]"


def _ensure_result(analysis: ImpactAnalysis) -> dict[str, Any]:
    if not isinstance(analysis.result, dict):
        analysis.result = {}
    analysis.result.setdefault("steps", {})
    analysis.result.setdefault("search_log", [])
    analysis.result.setdefault("requirements", [])
    return analysis.result


def _step_done(analysis: ImpactAnalysis, name: str) -> bool:
    steps = (_ensure_result(analysis).get("steps") or {})
    return (steps.get(name) or {}).get("status") == "completed"


def _save_step(session: Session, analysis: ImpactAnalysis, name: str, payload: dict[str, Any]) -> None:
    result = _ensure_result(analysis)
    result["current_step"] = name
    result["steps"][name] = payload
    analysis.result = dict(result)
    session.flush()


def _log_search(analysis: ImpactAnalysis, query: str, hits: list[SearchHit]) -> None:
    result = _ensure_result(analysis)
    result["search_log"].append(
        {
            "query": query,
            "chunk_ids": [str(hit.chunk_id) for hit in hits],
            "scores": [hit.score for hit in hits],
        }
    )


def _mean_search_score(analysis: ImpactAnalysis) -> float:
    logs = _ensure_result(analysis).get("search_log") or []
    scores = [score for entry in logs for score in entry.get("scores") or []]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def run_analysis(
    session: Session,
    analysis_id: UUID,
    *,
    llm: LLM | None = None,
    embedder: Embedder | None = None,
    today: date | None = None,
) -> None:
    llm = llm or ClaudeLLM()
    embedder = embedder or TitanEmbedder()
    today = today or date.today()
    analysis = session.get(ImpactAnalysis, analysis_id)
    if analysis is None:
        raise ValueError(f"Analysis {analysis_id} not found")
    if analysis.status == AnalysisStatus.COMPLETED.value:
        logger.info("Analysis %s already completed; skipping", analysis_id)
        return

    company = session.get(Company, analysis.company_id)
    regulation = session.get(RegulatoryDocument, analysis.regulation_id)
    if company is None or regulation is None:
        analysis.status = AnalysisStatus.FAILED.value
        session.flush()
        return

    analysis.status = AnalysisStatus.PROCESSING.value
    result = _ensure_result(analysis)
    result["failed_step"] = None
    session.flush()

    depth = AnalysisDepth(analysis.analysis_depth)
    limit = ANALYSIS_DEPTH_CHUNK_LIMIT[depth]

    def search(query: str, **kwargs) -> list[SearchHit]:
        filters = SearchFilters(company_id=company.id, **kwargs)
        hits = hybrid_search(session, query, filters, depth=depth, embedder=embedder, limit=limit)
        _log_search(analysis, query, hits)
        return hits

    try:
        _run_steps(
            session,
            analysis,
            company,
            regulation,
            llm,
            search,
            today,
            depth,
            {"ok": 0, "total": 0, "retry": False},
        )
    except Exception:
        logger.exception("Analysis %s failed", analysis_id)
        result = _ensure_result(analysis)
        result["failed_step"] = result.get("current_step")
        analysis.status = AnalysisStatus.FAILED.value
        analysis.human_review_required = True
        session.flush()
        raise


def _run_steps(
    session: Session,
    analysis: ImpactAnalysis,
    company: Company,
    regulation: RegulatoryDocument,
    llm: LLM,
    search,
    today: date,
    depth: AnalysisDepth,
    counters: dict[str, Any],
) -> None:
    company_fields = _company_scope_fields(company)
    req_filters = {"regulation_id": regulation.id, "regulation_only": True}
    policy_filters = {"policy_only": True}

    def call(name: str, prompt: str, model):
        started = time.monotonic()
        counters["total"] += 1
        output, attempts = complete_model(llm, prompt, model, started_at=started)
        if attempts == 1:
            counters["ok"] += 1
        else:
            counters["retry"] = True
        _save_step(
            session,
            analysis,
            name,
            {"status": "completed", "output": output.model_dump(mode="json"), "attempts": attempts},
        )
        return output

    if not _step_done(analysis, "applicability"):
        hits = search(
            f"Does this apply to a {company.organization_type} {company.business_model or ''}",
            **req_filters,
        )
        prompt = build_prompt(
            "Decide if the rule applies to this company. If unsure, use uncertain. Do not guess.",
            str(APPLICABILITY_SCHEMA),
            company_fields,
            _hits_text(hits),
        )
        call("applicability", prompt, ApplicabilityOutput)

    applicability_out = ApplicabilityOutput.model_validate(
        analysis.result["steps"]["applicability"]["output"]
    )
    analysis.applicability = applicability_out.applicability.value

    if not _step_done(analysis, "requirements"):
        hits = search("obligations requirements shall must should compliance duties", **req_filters)
        prompt = build_prompt(
            "Extract atomic requirements. Split duties joined by 'and'. Each needs a verbatim quote "
            "and source_chunk_id. stated_dates only if the source cites a date.",
            str(REQUIREMENTS_SCHEMA),
            {"organization_type": company.organization_type},
            _hits_text(hits),
        )
        call("requirements", prompt, RequirementsOutput)

    req_output = RequirementsOutput.model_validate(analysis.result["steps"]["requirements"]["output"])
    _persist_requirements(session, analysis, req_output.requirements)

    stored_reqs = list(
        session.scalars(
            select(RegulatoryRequirement).where(RegulatoryRequirement.analysis_id == analysis.id)
        )
    )

    if not _step_done(analysis, "impact"):
        impacts = []
        for req in stored_reqs:
            extra = []
            if ANALYSIS_DEPTH_RESEARCH[depth] in {"all"} or (
                ANALYSIS_DEPTH_RESEARCH[depth] == "mandatory" and req.obligation_type == "mandatory"
            ):
                extra = search(req.requirement_text, **req_filters)
            hits = extra or search(req.requirement_text, **req_filters)
            prompt = build_prompt(
                f"Assess impact for requirement {req.id}: {req.requirement_text}",
                str(IMPACT_SCHEMA),
                {"organization_type": company.organization_type, "products": company.products},
                _hits_text(hits),
            )
            started = time.monotonic()
            counters["total"] += 1
            output, attempts = complete_model(llm, prompt, ImpactOutput, started_at=started)
            if attempts == 1:
                counters["ok"] += 1
            else:
                counters["retry"] = True
            output.requirement_id = req.id
            req.applicability = output.applicability.value
            req.impact_level = output.impact_level.value
            req.affected_departments = [item.value for item in output.affected_departments]
            impacts.append(output.model_dump(mode="json"))
        _save_step(session, analysis, "impact", {"status": "completed", "output": impacts, "attempts": 1})

    if analysis.include_gap_analysis and not _step_done(analysis, "gap_detection"):
        gaps = []
        for req in stored_reqs:
            hits = search(req.requirement_text, **policy_filters)
            prompt = build_prompt(
                "Compare the requirement to company document chunks only. "
                "compliant or partial needs evidence_chunk_ids from those chunks. "
                "Typed profile lists are not evidence.",
                str(GAP_SCHEMA),
                {"company_id": str(company.id)},
                _hits_text(hits),
            )
            started = time.monotonic()
            counters["total"] += 1
            output, attempts = complete_model(llm, prompt, GapOutput, started_at=started)
            if attempts == 1:
                counters["ok"] += 1
            else:
                counters["retry"] = True
            output.requirement_id = req.id
            _validate_company_evidence(session, company.id, output)
            gaps.append(output.model_dump(mode="json"))
        _save_step(session, analysis, "gap_detection", {"status": "completed", "output": gaps, "attempts": 1})

    if analysis.include_gap_analysis and not _step_done(analysis, "risk"):
        gap_by_req = {
            item["requirement_id"]: item
            for item in analysis.result["steps"]["gap_detection"]["output"]
        }
        impact_by_req = {
            item["requirement_id"]: item for item in analysis.result["steps"]["impact"]["output"]
        }
        risks = []
        for req in stored_reqs:
            gap = gap_by_req[str(req.id)]
            impact = impact_by_req[str(req.id)]
            original = next(
                (item for item in req_output.requirements if item.requirement_text == req.requirement_text),
                req_output.requirements[0],
            )
            proximity = deadline_proximity(original.stated_dates, today)
            risk = score_risk(
                req.id,
                req.obligation_type,
                gap["gap_status"],
                impact["impact_level"],
                proximity,
            )
            risks.append(risk.model_dump(mode="json"))
        _save_step(
            session,
            analysis,
            "risk",
            {"status": "completed", "output": risks, "attempts": 1, "deterministic": True},
        )

    if analysis.include_action_plan and not _step_done(analysis, "action_plan"):
        plans = []
        for req in stored_reqs:
            prompt = build_prompt(
                "Propose tasks to close the gap. Any date you invent must use date_basis inferred_recommendation.",
                str(ACTION_SCHEMA),
                {"departments": [req.affected_departments]},
                req.requirement_text,
            )
            started = time.monotonic()
            counters["total"] += 1
            output, attempts = complete_model(llm, prompt, ActionPlanOutput, started_at=started)
            if attempts == 1:
                counters["ok"] += 1
            else:
                counters["retry"] = True
            output.requirement_id = req.id
            plans.append(output.model_dump(mode="json"))
        _save_step(session, analysis, "action_plan", {"status": "completed", "output": plans, "attempts": 1})

    _persist_gaps_actions_citations(session, analysis, company.id, req_output)

    if not _step_done(analysis, "verification"):
        verification = _run_verification(session, analysis, llm, counters)
        _save_step(
            session,
            analysis,
            "verification",
            {"status": "completed", "output": verification.model_dump(mode="json"), "attempts": 1},
        )

    _finalize(session, analysis, counters)


def _validate_company_evidence(session: Session, company_id: UUID, gap: GapOutput) -> None:
    for chunk_id in gap.evidence_chunk_ids:
        chunk = session.get(DocumentChunk, chunk_id)
        if chunk is None or chunk.company_id != company_id:
            raise ValueError("evidence_chunk_ids must point at this company's documents")


def _persist_requirements(session: Session, analysis: ImpactAnalysis, items: list[RequirementItem]) -> None:
    existing = list(
        session.scalars(
            select(RegulatoryRequirement).where(RegulatoryRequirement.analysis_id == analysis.id)
        )
    )
    if existing:
        return
    for item in items:
        session.add(
            RegulatoryRequirement(
                analysis_id=analysis.id,
                requirement_text=item.requirement_text,
                obligation_type=item.obligation_type.value,
                applicability=analysis.applicability or "uncertain",
                source_chunk_id=item.source_chunk_id,
            )
        )
    session.flush()


def _persist_gaps_actions_citations(
    session: Session,
    analysis: ImpactAnalysis,
    company_id: UUID,
    req_output: RequirementsOutput,
) -> None:
    reqs = list(
        session.scalars(
            select(RegulatoryRequirement).where(RegulatoryRequirement.analysis_id == analysis.id)
        )
    )
    gap_outputs = (analysis.result.get("steps") or {}).get("gap_detection", {}).get("output") or []
    risk_outputs = (analysis.result.get("steps") or {}).get("risk", {}).get("output") or []
    plan_outputs = (analysis.result.get("steps") or {}).get("action_plan", {}).get("output") or []
    impact_outputs = (analysis.result.get("steps") or {}).get("impact", {}).get("output") or []
    risk_by_req = {item["requirement_id"]: item for item in risk_outputs}
    gap_by_req = {item["requirement_id"]: item for item in gap_outputs}
    plan_by_req = {item["requirement_id"]: item for item in plan_outputs}
    impact_by_req = {item["requirement_id"]: item for item in impact_outputs}

    existing_gaps = session.scalars(
        select(ComplianceGap)
        .join(RegulatoryRequirement)
        .where(RegulatoryRequirement.analysis_id == analysis.id)
    ).first()
    if existing_gaps is None:
        for req in reqs:
            gap = gap_by_req.get(str(req.id))
            risk = risk_by_req.get(str(req.id))
            if not gap:
                continue
            evidence_ids = [UUID(value) for value in gap.get("evidence_chunk_ids") or []]
            row = ComplianceGap(
                requirement_id=req.id,
                company_id=company_id,
                gap_status=gap["gap_status"],
                severity=(risk or {}).get("severity") or "low",
                explanation=gap.get("explanation"),
                evidence_chunk_ids=evidence_ids,
            )
            session.add(row)
            session.flush()
            plan = plan_by_req.get(str(req.id))
            if plan:
                for action in plan.get("actions") or []:
                    session.add(
                        ActionItem(
                            analysis_id=analysis.id,
                            gap_id=row.id,
                            company_id=company_id,
                            title=action["title"],
                            description=action.get("description"),
                            owner_department=action.get("owner_department"),
                            status=ActionStatus.OPEN.value,
                            effort=action.get("effort"),
                        )
                    )

    # Citations from requirement source chunks and applicability support.
    if not list(session.scalars(select(Citation).where(Citation.analysis_id == analysis.id)).all()):
        cited: set[UUID] = set()
        for item in req_output.requirements:
            cited.add(item.source_chunk_id)
        for req in reqs:
            impact = impact_by_req.get(str(req.id)) or {}
            for value in impact.get("supporting_chunk_ids") or []:
                cited.add(UUID(value))
        for chunk_id in cited:
            chunk = session.get(DocumentChunk, chunk_id)
            if chunk is None:
                continue
            session.add(
                Citation(
                    analysis_id=analysis.id,
                    chunk_id=chunk.id,
                    claim_text=chunk.text[:280],
                    excerpt=chunk.text[:800],
                    from_ocr=chunk.extraction_method != ExtractionMethod.TEXT.value,
                    relevance_verified=None,
                )
            )
    session.flush()


def _run_verification(
    session: Session,
    analysis: ImpactAnalysis,
    llm: LLM,
    counters: dict[str, Any],
) -> VerificationOutput:
    citations = list(session.scalars(select(Citation).where(Citation.analysis_id == analysis.id)))
    unsupported: list[str] = []
    contradicted = 0
    covered = 0
    check_payloads: list[dict[str, Any]] = []
    for index, citation in enumerate(citations, start=1):
        chunk = session.get(DocumentChunk, citation.chunk_id)
        if chunk is None:
            unsupported.append(citation.claim_text)
            continue
        prompt = claim_check_prompt(citation.claim_text, chunk.text)
        counters["total"] += 1
        raw = llm.complete(prompt)
        try:
            payload = parse_json_object(raw)
            supported = bool(payload.get("supported"))
            is_contradicted = bool(payload.get("contradicted"))
            reason = str(payload.get("reason") or "")
            if counters:
                counters["ok"] += 1
        except Exception:
            counters["retry"] = True
            supported, is_contradicted, reason = False, False, "checker output was not JSON"
        citation.relevance_verified = supported and not is_contradicted
        if supported:
            covered += 1
        else:
            unsupported.append(citation.claim_text)
        if is_contradicted:
            contradicted += 1
        check_payloads.append(
            {
                "claim_id": f"claim_{index:03d}",
                "chunk_id": str(citation.chunk_id),
                "supported": supported,
                "contradicted": is_contradicted,
                "reason": reason,
            }
        )
    total = max(len(citations), 1)
    coverage = covered / total if citations else 0.0
    return VerificationOutput.model_validate(
        {
            "citation_coverage": coverage,
            "claim_checks": check_payloads,
            "unsupported_claims": unsupported,
            "missing_evidence": [],
            "date_checks": [],
        }
    )


def _finalize(session: Session, analysis: ImpactAnalysis, counters: dict[str, Any]) -> None:
    result = _ensure_result(analysis)
    verification = VerificationOutput.model_validate(result["steps"]["verification"]["output"])
    contradicted = sum(1 for item in verification.claim_checks if item.contradicted)
    status = verification_status(
        coverage=verification.citation_coverage,
        unsupported=len(verification.unsupported_claims),
        contradicted=contradicted,
    )
    result["verification_status"] = status.value
    risks = result["steps"].get("risk", {}).get("output") or []
    severities = [item["severity"] for item in risks]
    analysis.overall_risk = overall_risk(severities) if severities else None
    gaps = result["steps"].get("gap_detection", {}).get("output") or []
    gap_statuses = [item["gap_status"] for item in gaps]
    first_try = (counters["ok"] / counters["total"]) if counters["total"] else 1.0
    confidence = compute_confidence(
        citation_coverage=verification.citation_coverage,
        mean_search_score=_mean_search_score(analysis),
        first_try_schema_rate=first_try,
        applicability=analysis.applicability or "uncertain",
    )
    analysis.confidence = confidence
    reasons = human_review_required(
        applicability=analysis.applicability or "uncertain",
        gap_statuses=gap_statuses,
        severities=severities,
        verification=status.value,
        confidence=confidence,
        step_needed_retry_or_failed=bool(counters["retry"]),
    )
    analysis.human_review_required = bool(reasons)
    result["review_reasons"] = reasons

    citations = list(session.scalars(select(Citation).where(Citation.analysis_id == analysis.id)))
    citation_by_chunk = {row.chunk_id: row.id for row in citations}
    reqs = list(
        session.scalars(
            select(RegulatoryRequirement).where(RegulatoryRequirement.analysis_id == analysis.id)
        )
    )
    gap_by_req = {item["requirement_id"]: item for item in gaps}
    risk_by_req = {item["requirement_id"]: item for item in risks}
    plan_by_req = {
        item["requirement_id"]: item
        for item in (result["steps"].get("action_plan", {}).get("output") or [])
    }
    impact_by_req = {
        item["requirement_id"]: item for item in (result["steps"].get("impact", {}).get("output") or [])
    }
    cards = []
    for req in reqs:
        gap = gap_by_req.get(str(req.id)) or {}
        risk = risk_by_req.get(str(req.id)) or {}
        plan = plan_by_req.get(str(req.id)) or {}
        impact = impact_by_req.get(str(req.id)) or {}
        action_title = (plan.get("actions") or [{}])[0].get("title")
        cards.append(
            {
                "id": str(req.id),
                "requirement_text": req.requirement_text,
                "obligation_type": req.obligation_type,
                "applicability": req.applicability,
                "impact_level": req.impact_level or impact.get("impact_level"),
                "affected_departments": req.affected_departments or impact.get("affected_departments"),
                "gap_status": gap.get("gap_status"),
                "severity": risk.get("severity"),
                "action": action_title,
                "evidence": gap.get("explanation"),
                "citation_id": str(citation_by_chunk[req.source_chunk_id])
                if req.source_chunk_id and req.source_chunk_id in citation_by_chunk
                else None,
            }
        )
    result["requirements"] = cards
    result["current_step"] = "completed"
    analysis.result = dict(result)
    analysis.status = AnalysisStatus.COMPLETED.value
    analysis.completed_at = datetime.now(UTC).replace(tzinfo=None)
    session.flush()
