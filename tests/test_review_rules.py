from app.agents.review_rules import (
    compute_confidence,
    human_review_required,
    verification_status,
)
from app.enums import Applicability, GapStatus, Severity, VerificationStatus


def test_review_required_for_uncertain_applicability():
    reasons = human_review_required(
        applicability=Applicability.UNCERTAIN.value,
        gap_statuses=[GapStatus.COMPLIANT.value],
        severities=[Severity.LOW.value],
        verification=VerificationStatus.VERIFIED.value,
        confidence=0.9,
        step_needed_retry_or_failed=False,
    )
    assert "applicability_uncertain" in reasons


def test_review_required_for_insufficient_evidence():
    reasons = human_review_required(
        applicability=Applicability.APPLICABLE.value,
        gap_statuses=[GapStatus.INSUFFICIENT_EVIDENCE.value],
        severities=[Severity.LOW.value],
        verification=VerificationStatus.VERIFIED.value,
        confidence=0.9,
        step_needed_retry_or_failed=False,
    )
    assert "insufficient_evidence" in reasons


def test_review_required_for_high_severity():
    reasons = human_review_required(
        applicability=Applicability.APPLICABLE.value,
        gap_statuses=[GapStatus.PARTIAL.value],
        severities=[Severity.CRITICAL.value],
        verification=VerificationStatus.VERIFIED.value,
        confidence=0.9,
        step_needed_retry_or_failed=False,
    )
    assert "high_or_critical_severity" in reasons


def test_review_required_for_unverified():
    reasons = human_review_required(
        applicability=Applicability.APPLICABLE.value,
        gap_statuses=[GapStatus.COMPLIANT.value],
        severities=[Severity.LOW.value],
        verification=VerificationStatus.PARTIALLY_VERIFIED.value,
        confidence=0.9,
        step_needed_retry_or_failed=False,
    )
    assert "verification_not_verified" in reasons


def test_review_required_for_low_confidence():
    reasons = human_review_required(
        applicability=Applicability.APPLICABLE.value,
        gap_statuses=[GapStatus.COMPLIANT.value],
        severities=[Severity.LOW.value],
        verification=VerificationStatus.VERIFIED.value,
        confidence=0.5,
        step_needed_retry_or_failed=False,
    )
    assert "low_confidence" in reasons


def test_review_required_after_retries():
    reasons = human_review_required(
        applicability=Applicability.APPLICABLE.value,
        gap_statuses=[GapStatus.COMPLIANT.value],
        severities=[Severity.LOW.value],
        verification=VerificationStatus.VERIFIED.value,
        confidence=0.9,
        step_needed_retry_or_failed=True,
    )
    assert "step_retry_or_failure" in reasons


def test_no_review_when_all_clear():
    reasons = human_review_required(
        applicability=Applicability.APPLICABLE.value,
        gap_statuses=[GapStatus.COMPLIANT.value],
        severities=[Severity.LOW.value],
        verification=VerificationStatus.VERIFIED.value,
        confidence=0.9,
        step_needed_retry_or_failed=False,
    )
    assert reasons == []


def test_verification_cutoffs():
    assert verification_status(coverage=0.96, unsupported=0, contradicted=0) == VerificationStatus.VERIFIED
    assert verification_status(coverage=0.90, unsupported=1, contradicted=0) == VerificationStatus.PARTIALLY_VERIFIED
    assert verification_status(coverage=0.50, unsupported=1, contradicted=0) == VerificationStatus.UNVERIFIED
    assert verification_status(coverage=0.99, unsupported=0, contradicted=1) == VerificationStatus.FAILED


def test_confidence_weights():
    score = compute_confidence(
        citation_coverage=1.0,
        mean_search_score=1.0,
        first_try_schema_rate=1.0,
        applicability=Applicability.APPLICABLE.value,
    )
    assert score == 1.0
    uncertain = compute_confidence(
        citation_coverage=0.0,
        mean_search_score=0.0,
        first_try_schema_rate=0.0,
        applicability=Applicability.UNCERTAIN.value,
    )
    assert uncertain == 0.0
