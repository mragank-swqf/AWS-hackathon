from uuid import uuid4

import pytest
from app.agents.contracts import (
    ApplicabilityOutput,
    GapOutput,
    RequirementItem,
    RequirementsOutput,
    StatedDate,
)
from app.enums import Applicability, DateBasis, GapStatus, ObligationType
from pydantic import ValidationError


def test_missing_supporting_chunks_fails():
    with pytest.raises(ValidationError):
        ApplicabilityOutput(
            applicability=Applicability.APPLICABLE,
            rationale="it applies",
            supporting_chunk_ids=[],
        )


def test_unknown_applicability_fails():
    with pytest.raises(ValidationError):
        ApplicabilityOutput(
            applicability="sometimes",
            rationale="nope",
            supporting_chunk_ids=[uuid4()],
        )


def test_forbidden_confidence_field_fails():
    with pytest.raises(ValidationError):
        ApplicabilityOutput(
            applicability=Applicability.APPLICABLE,
            rationale="ok",
            supporting_chunk_ids=[uuid4()],
            confidence=0.9,
        )


def test_requirement_needs_source():
    with pytest.raises(ValidationError):
        RequirementItem(
            requirement_text="Do the thing",
            obligation_type=ObligationType.MANDATORY,
            verbatim_quote="Do the thing",
        )


def test_inferred_stated_date_fails():
    with pytest.raises(ValidationError):
        StatedDate(
            date="2026-12-01",
            date_basis=DateBasis.INFERRED_RECOMMENDATION,
            source_chunk_id=uuid4(),
        )


def test_compliant_without_evidence_fails():
    with pytest.raises(ValidationError):
        GapOutput(
            requirement_id=uuid4(),
            gap_status=GapStatus.COMPLIANT,
            explanation="looks fine",
            evidence_chunk_ids=[],
        )


def test_severity_on_gap_output_fails():
    with pytest.raises(ValidationError):
        GapOutput(
            requirement_id=uuid4(),
            gap_status=GapStatus.INSUFFICIENT_EVIDENCE,
            explanation="none",
            severity="high",
        )


def test_human_review_flag_on_applicability_fails():
    with pytest.raises(ValidationError):
        ApplicabilityOutput(
            applicability=Applicability.UNCERTAIN,
            rationale="unclear",
            supporting_chunk_ids=[],
            requires_human_review=True,
        )


def test_valid_requirement_passes():
    item = RequirementItem(
        requirement_text="Maintain a documented grievance redressal process.",
        obligation_type=ObligationType.MANDATORY,
        verbatim_quote="Every payment aggregator shall maintain a documented grievance redressal process.",
        source_chunk_id=uuid4(),
        clause_number="3.2",
    )
    output = RequirementsOutput(requirements=[item])
    assert len(output.requirements) == 1
