"""Regulator-agnostic applicability using company profile + document metadata."""

from __future__ import annotations

from dataclasses import dataclass

from datetime import UTC, datetime

from app.db.models import Company, RegulatoryDocument
from app.enums import Applicability, RegulatoryDomain


@dataclass(frozen=True)
class ApplicabilityDecision:
    applicability: Applicability
    reason: str
    matched_characteristics: list[str]
    rule_id: str
    human_review_required: bool


def assess_document(company: Company, document: RegulatoryDocument) -> ApplicabilityDecision:
    if not company.organization_type:
        return ApplicabilityDecision(
            applicability=Applicability.UNCERTAIN,
            reason="The company profile does not name an entity type, so applicability cannot be decided.",
            matched_characteristics=[],
            rule_id="missing_entity_type",
            human_review_required=True,
        )
    entities = list(document.applicable_entity_types or [])
    if not entities:
        return ApplicabilityDecision(
            applicability=Applicability.UNCERTAIN,
            reason="This document has no structured entity-type metadata. A person should decide.",
            matched_characteristics=["organization_type"],
            rule_id="missing_document_entities",
            human_review_required=True,
        )
    org = company.organization_type
    if org not in entities:
        return ApplicabilityDecision(
            applicability=Applicability.NOT_APPLICABLE,
            reason=(
                f"This document lists {', '.join(entities)} as in-scope entities. "
                f"The company is typed as {org}."
            ),
            matched_characteristics=["organization_type"],
            rule_id="entity_type_mismatch",
            human_review_required=False,
        )
    domain = document.regulatory_domain
    if domain == RegulatoryDomain.OUTSOURCING.value:
        if company.has_outsourced_operations is False:
            return ApplicabilityDecision(
                applicability=Applicability.NOT_APPLICABLE,
                reason=(
                    "Outsourcing directions apply when the company outsources operations. "
                    "This profile says it does not."
                ),
                matched_characteristics=["organization_type", "has_outsourced_operations"],
                rule_id="outsourcing_not_used",
                human_review_required=False,
            )
        if company.has_outsourced_operations is None:
            return ApplicabilityDecision(
                applicability=Applicability.UNCERTAIN,
                reason=(
                    "Outsourcing directions may apply, but the company profile does not say "
                    "whether operations are outsourced."
                ),
                matched_characteristics=["organization_type"],
                rule_id="outsourcing_unknown",
                human_review_required=True,
            )
    if domain == RegulatoryDomain.DATA.value and company.uses_customer_data is False:
        return ApplicabilityDecision(
            applicability=Applicability.LIKELY_NOT_APPLICABLE,
            reason=(
                "Data-related directions are less likely to apply when the company says it "
                "does not handle customer data."
            ),
            matched_characteristics=["organization_type", "uses_customer_data"],
            rule_id="no_customer_data",
            human_review_required=True,
        )
    matched = ["organization_type"]
    if domain == RegulatoryDomain.OUTSOURCING.value:
        matched.append("has_outsourced_operations")
    return ApplicabilityDecision(
        applicability=Applicability.APPLICABLE,
        reason=(
            f"The company is a {org.replace('_', ' ')} operating in "
            f"{', '.join(company.operating_regions) or 'an unspecified region'}, "
            f"which matches this {document.regulator} {document.document_type.replace('_', ' ')}."
        ),
        matched_characteristics=matched,
        rule_id="entity_type_match",
        human_review_required=False,
    )


REVIEWER_CHOICES = {Applicability.APPLICABLE.value, Applicability.NOT_APPLICABLE.value}


def apply_reviewer_decision(row, applicability: str) -> None:
    if applicability not in REVIEWER_CHOICES:
        raise ValueError("A person can only mark a document as applies or does not apply.")
    label = "applies" if applicability == Applicability.APPLICABLE.value else "does not apply"
    row.reviewer_applicability = applicability
    row.reviewer_decided_at = datetime.now(UTC).replace(tzinfo=None)
    row.applicability = applicability
    row.human_review_required = False
    row.rule_id = "human_decision"
    row.reason = f"A person marked this as {label}."

