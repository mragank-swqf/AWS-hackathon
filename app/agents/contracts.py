"""Output shapes for the seven analysis steps (spec 12). extra=forbid."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums import (
    Applicability,
    DateBasis,
    Department,
    Effort,
    GapStatus,
    ImpactLevel,
    ObligationType,
)


class AgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApplicabilityOutput(AgentModel):
    applicability: Applicability
    rationale: str
    matched_entity_descriptions: list[str] = Field(default_factory=list)
    supporting_chunk_ids: list[UUID]
    exclusions_noted: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def backed(self) -> ApplicabilityOutput:
        if not self.supporting_chunk_ids and self.applicability != Applicability.UNCERTAIN:
            raise ValueError("applicability judgements need supporting_chunk_ids")
        return self


class StatedDate(AgentModel):
    date: date
    date_basis: DateBasis
    source_chunk_id: UUID

    @model_validator(mode="after")
    def cited_only(self) -> StatedDate:
        if self.date_basis == DateBasis.INFERRED_RECOMMENDATION:
            raise ValueError("stated dates must be cited from the source, not inferred")
        return self


class RequirementItem(AgentModel):
    requirement_text: str
    obligation_type: ObligationType
    verbatim_quote: str
    source_chunk_id: UUID
    clause_number: str | None = None
    stated_dates: list[StatedDate] = Field(default_factory=list)


class RequirementsOutput(AgentModel):
    requirements: list[RequirementItem]


class ImpactOutput(AgentModel):
    requirement_id: UUID = Field(default_factory=uuid4)
    applicability: Applicability
    impact_level: ImpactLevel
    affected_departments: list[Department]
    required_capabilities: list[str] = Field(default_factory=list)
    rationale: str
    supporting_chunk_ids: list[UUID]


class EvidenceAssessment(AgentModel):
    chunk_id: UUID
    supports: bool
    reason: str


class GapOutput(AgentModel):
    requirement_id: UUID = Field(default_factory=uuid4)
    gap_status: GapStatus
    explanation: str
    evidence_chunk_ids: list[UUID] = Field(default_factory=list)
    evidence_assessment: list[EvidenceAssessment] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def evidence_for_coverage(self) -> GapOutput:
        if self.gap_status in {GapStatus.COMPLIANT, GapStatus.PARTIAL} and not self.evidence_chunk_ids:
            raise ValueError("compliant/partial requires evidence_chunk_ids from a company document")
        return self


class SeverityInputs(AgentModel):
    obligation_type: ObligationType
    gap_status: GapStatus
    impact_level: ImpactLevel
    deadline_proximity: str


class RiskOutput(AgentModel):
    requirement_id: UUID
    severity: str
    severity_inputs: SeverityInputs
    escalations_applied: list[str] = Field(default_factory=list)
    rationale: str


class ActionItemOutput(AgentModel):
    title: str
    description: str
    owner_department: Department
    effort: Effort
    depends_on: list[str] = Field(default_factory=list)
    target_date: date | None = None
    date_basis: DateBasis | None = None

    @model_validator(mode="after")
    def date_with_basis(self) -> ActionItemOutput:
        if self.target_date is None and self.date_basis is None:
            return self
        if self.target_date is None or self.date_basis is None:
            raise ValueError("target_date and date_basis must be sent together")
        return self


class ActionPlanOutput(AgentModel):
    requirement_id: UUID = Field(default_factory=uuid4)
    actions: list[ActionItemOutput]


class ClaimCheck(AgentModel):
    claim_id: str
    chunk_id: UUID
    supported: bool
    contradicted: bool
    reason: str


class DateCheck(AgentModel):
    date: date
    date_basis: DateBasis
    found_in_source: bool


class VerificationOutput(AgentModel):
    citation_coverage: float
    claim_checks: list[ClaimCheck] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    date_checks: list[DateCheck] = Field(default_factory=list)
