"""Runner-owned confidence and human_review_required (spec 13)."""

from __future__ import annotations

from app.enums import Applicability, GapStatus, Severity, VerificationStatus

REVIEW_CONFIDENCE_FLOOR = 0.70


def applicability_clarity(value: str) -> float:
    if value in {Applicability.APPLICABLE.value, Applicability.NOT_APPLICABLE.value}:
        return 1.0
    if value in {Applicability.LIKELY_APPLICABLE.value, Applicability.LIKELY_NOT_APPLICABLE.value}:
        return 0.5
    return 0.0


def compute_confidence(
    *,
    citation_coverage: float,
    mean_search_score: float,
    first_try_schema_rate: float,
    applicability: str,
) -> float:
    score = (
        0.4 * max(0.0, min(citation_coverage, 1.0))
        + 0.2 * max(0.0, min(mean_search_score, 1.0))
        + 0.2 * max(0.0, min(first_try_schema_rate, 1.0))
        + 0.2 * applicability_clarity(applicability)
    )
    return round(score, 4)


def verification_status(*, coverage: float, unsupported: int, contradicted: int) -> VerificationStatus:
    if contradicted:
        return VerificationStatus.FAILED
    if coverage >= 0.95 and unsupported == 0:
        return VerificationStatus.VERIFIED
    if coverage >= 0.80:
        return VerificationStatus.PARTIALLY_VERIFIED
    return VerificationStatus.UNVERIFIED


def human_review_required(
    *,
    applicability: str,
    gap_statuses: list[str],
    severities: list[str],
    verification: str,
    confidence: float,
    step_needed_retry_or_failed: bool,
) -> list[str]:
    """Return the list of reasons a person must review. Empty means no review required."""
    reasons: list[str] = []
    if applicability not in {Applicability.APPLICABLE.value, Applicability.NOT_APPLICABLE.value}:
        reasons.append("applicability_uncertain")
    if any(status == GapStatus.INSUFFICIENT_EVIDENCE.value for status in gap_statuses):
        reasons.append("insufficient_evidence")
    if any(sev in {Severity.HIGH.value, Severity.CRITICAL.value} for sev in severities):
        reasons.append("high_or_critical_severity")
    if verification != VerificationStatus.VERIFIED.value:
        reasons.append("verification_not_verified")
    if confidence < REVIEW_CONFIDENCE_FLOOR:
        reasons.append("low_confidence")
    if step_needed_retry_or_failed:
        reasons.append("step_retry_or_failure")
    return reasons
