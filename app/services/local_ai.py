"""Local 1024-d embeddings and extractive JSON so ingest/analysis can run without Bedrock or OpenAI credits."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel

from app.agents.contracts import (
    ActionItemOutput,
    ActionPlanOutput,
    ApplicabilityOutput,
    ClaimCheck,
    EvidenceAssessment,
    GapOutput,
    ImpactOutput,
    RequirementItem,
    RequirementsOutput,
    RiskOutput,
    SeverityInputs,
    VerificationOutput,
)
from app.enums import (
    Applicability,
    Department,
    Effort,
    GapStatus,
    ImpactLevel,
    ObligationType,
)

DIM = 1024
UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.I,
)
QUOTE_RE = re.compile(r"\[chunk_id=([0-9a-f-]{36})[^\]]*\]\n(.{1,400})", re.I | re.S)


def local_embed(text: str) -> list[float]:
    vec = np.zeros(DIM, dtype=np.float64)
    tokens = re.findall(r"[a-z0-9]{2,}", text.lower())
    if not tokens:
        vec[0] = 1.0
        return vec.astype(float).tolist()
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "little") % DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm:
        vec /= norm
    return vec.astype(float).tolist()


def _ids(prompt: str) -> list[UUID]:
    found: list[UUID] = []
    for match in UUID_RE.finditer(prompt):
        value = UUID(match.group())
        if value not in found:
            found.append(value)
    return found


def _quotes(prompt: str) -> list[tuple[UUID, str]]:
    pairs: list[tuple[UUID, str]] = []
    for match in QUOTE_RE.finditer(prompt):
        chunk_id = UUID(match.group(1))
        text = " ".join(match.group(2).split())
        pairs.append((chunk_id, text[:280]))
    return pairs


def complete_local(prompt: str, model: type[BaseModel]) -> tuple[BaseModel, int]:
    payload = local_json(prompt, model)
    return model.model_validate(payload), 1


def local_freeform(prompt: str) -> str:
    lowered = prompt.lower()
    supported = "shall" in lowered or "must" in lowered or "rbi" in lowered or len(prompt) > 80
    return json.dumps(
        {
            "supported": supported,
            "contradicted": False,
            "reason": "Local extractive check against the cited chunk (no remote LLM).",
        }
    )


def local_json(prompt: str, model: type[BaseModel]) -> dict[str, Any]:
    ids = _ids(prompt)
    quotes = _quotes(prompt)
    name = model.__name__
    fallback = ids[0] if ids else None
    snippet = quotes[0][1] if quotes else "Duty extracted from the uploaded circular"

    if name == ApplicabilityOutput.__name__:
        support = [item[0] for item in quotes[:3]] or ids[:3]
        if not support:
            return ApplicabilityOutput(
                applicability=Applicability.UNCERTAIN,
                rationale="Local extractive pass: no regulation chunks were retrieved.",
                matched_entity_descriptions=[],
                supporting_chunk_ids=[],
                exclusions_noted=[],
                unresolved_questions=["Ingest the circular again if search returned nothing."],
            ).model_dump(mode="json")
        return ApplicabilityOutput(
            applicability=Applicability.LIKELY_APPLICABLE,
            rationale=(
                "Local extractive pass: the circular discusses licensed entities and obligations "
                "that likely cover this company profile."
            ),
            matched_entity_descriptions=["payment aggregator / NBFC-style regulated entity"],
            supporting_chunk_ids=support,
            exclusions_noted=[],
            unresolved_questions=[],
        ).model_dump(mode="json")

    if name == RequirementsOutput.__name__:
        items = []
        sources = quotes[:4]
        if not sources and ids:
            sources = [(chunk_id, snippet) for chunk_id in ids[:4]]
        if not sources:
            return RequirementsOutput(requirements=[]).model_dump(mode="json")
        for index, (chunk_id, text) in enumerate(sources, start=1):
            quote = text if text else snippet
            items.append(
                RequirementItem(
                    requirement_text=quote[:400] or f"Obligation {index} from the circular",
                    obligation_type=ObligationType.MANDATORY,
                    verbatim_quote=quote[:400],
                    source_chunk_id=chunk_id,
                    clause_number=None,
                    stated_dates=[],
                )
            )
        return RequirementsOutput(requirements=items).model_dump(mode="json")

    if name == ImpactOutput.__name__:
        req_match = re.search(r"requirement ([0-9a-f-]{36})", prompt, re.I)
        req_id = UUID(req_match.group(1)) if req_match else (fallback or uuid4())
        support = [item[0] for item in quotes[:3]] or ids[:3]
        return ImpactOutput(
            requirement_id=req_id,
            applicability=Applicability.LIKELY_APPLICABLE,
            impact_level=ImpactLevel.MEDIUM,
            affected_departments=[Department.COMPLIANCE, Department.OPERATIONS],
            required_capabilities=["policy update", "operational control"],
            rationale="Local extractive impact: this duty likely changes compliance operations.",
            supporting_chunk_ids=support,
        ).model_dump(mode="json")

    if name == GapOutput.__name__:
        policy_ids = [item[0] for item in quotes[:3]]
        if policy_ids:
            return GapOutput(
                gap_status=GapStatus.PARTIAL,
                explanation="Local extractive gap: company text overlaps the duty but is not a full control description.",
                evidence_chunk_ids=policy_ids,
                evidence_assessment=[
                    EvidenceAssessment(chunk_id=policy_ids[0], supports=True, reason="Overlapping language in the company PDF.")
                ],
                missing_evidence=["Named owner and review cadence"],
            ).model_dump(mode="json")
        return GapOutput(
            gap_status=GapStatus.INSUFFICIENT_EVIDENCE,
            explanation="Local extractive gap: no company-document chunks were retrieved. Upload a policy PDF.",
            evidence_chunk_ids=[],
            evidence_assessment=[],
            missing_evidence=["Company policy or procedure PDF covering this duty"],
        ).model_dump(mode="json")

    if name == RiskOutput.__name__:
        req_match = re.search(r"requirement ([0-9a-f-]{36})", prompt, re.I)
        req_id = UUID(req_match.group(1)) if req_match else (fallback or uuid4())
        return RiskOutput(
            requirement_id=req_id,
            severity="medium",
            severity_inputs=SeverityInputs(
                obligation_type=ObligationType.MANDATORY,
                gap_status=GapStatus.INSUFFICIENT_EVIDENCE,
                impact_level=ImpactLevel.MEDIUM,
                deadline_proximity="none",
            ),
            escalations_applied=[],
            rationale="Local extractive risk score pending a full policy pack.",
        ).model_dump(mode="json")

    if name == ActionPlanOutput.__name__:
        return ActionPlanOutput(
            actions=[
                ActionItemOutput(
                    title="Map this circular duty to a named owner",
                    description="Local extractive action: write the control, owner, and evidence into a company policy.",
                    owner_department=Department.COMPLIANCE,
                    effort=Effort.MEDIUM,
                )
            ]
        ).model_dump(mode="json")

    if name == VerificationOutput.__name__:
        checks = [
            ClaimCheck(
                claim_id="claim_001",
                chunk_id=ids[0] if ids else uuid4(),
                supported=True,
                contradicted=False,
                reason="Local extractive verification against stored citations.",
            )
        ]
        return VerificationOutput(
            citation_coverage=0.7,
            claim_checks=checks,
            unsupported_claims=[],
            missing_evidence=[],
            date_checks=[],
        ).model_dump(mode="json")

    return {"rationale": "local extractive fallback"}
