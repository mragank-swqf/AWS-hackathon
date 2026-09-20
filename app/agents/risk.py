"""Deterministic severity and overall_risk (spec 14). No AI call."""

from __future__ import annotations

from datetime import date

from app.agents.contracts import RiskOutput, SeverityInputs, StatedDate
from app.enums import DeadlineProximity, GapStatus, ImpactLevel, ObligationType, OverallRisk, Severity

BASE_SEVERITY: dict[tuple[str, str], str] = {
    (ObligationType.MANDATORY.value, GapStatus.NON_COMPLIANT.value): Severity.HIGH.value,
    (ObligationType.MANDATORY.value, GapStatus.INSUFFICIENT_EVIDENCE.value): Severity.MEDIUM.value,
    (ObligationType.MANDATORY.value, GapStatus.PARTIAL.value): Severity.MEDIUM.value,
    (ObligationType.MANDATORY.value, GapStatus.COMPLIANT.value): Severity.LOW.value,
    (ObligationType.RECOMMENDED.value, GapStatus.NON_COMPLIANT.value): Severity.MEDIUM.value,
    (ObligationType.RECOMMENDED.value, GapStatus.INSUFFICIENT_EVIDENCE.value): Severity.LOW.value,
    (ObligationType.RECOMMENDED.value, GapStatus.PARTIAL.value): Severity.LOW.value,
    (ObligationType.RECOMMENDED.value, GapStatus.COMPLIANT.value): Severity.LOW.value,
}

_ORDER = [Severity.LOW.value, Severity.MEDIUM.value, Severity.HIGH.value, Severity.CRITICAL.value]


def bump(level: str) -> str:
    index = _ORDER.index(level)
    return _ORDER[min(index + 1, len(_ORDER) - 1)]


def worse(left: str, right: str) -> str:
    return left if _ORDER.index(left) >= _ORDER.index(right) else right


def deadline_proximity(stated_dates: list[StatedDate], today: date) -> DeadlineProximity:
    cited = [
        item.date
        for item in stated_dates
        if item.date_basis.value in {"cited_effective", "cited_compliance"}
    ]
    if not cited:
        return DeadlineProximity.NONE
    nearest = min(cited)
    delta = (nearest - today).days
    if delta < 0:
        return DeadlineProximity.OVERDUE
    if delta < 30:
        return DeadlineProximity.UNDER_30_DAYS
    if delta < 90:
        return DeadlineProximity.UNDER_90_DAYS
    return DeadlineProximity.BEYOND_90_DAYS


def score_risk(
    requirement_id,
    obligation_type: ObligationType | str,
    gap_status: GapStatus | str,
    impact_level: ImpactLevel | str,
    proximity: DeadlineProximity | str,
) -> RiskOutput:
    obligation = ObligationType(obligation_type)
    gap = GapStatus(gap_status)
    impact = ImpactLevel(impact_level)
    deadline = DeadlineProximity(proximity)
    base = BASE_SEVERITY[(obligation.value, gap.value)]
    severity = base
    escalations: list[str] = []
    if impact == ImpactLevel.HIGH:
        severity = bump(severity)
        escalations.append("impact_level_high")
    if deadline in {DeadlineProximity.OVERDUE, DeadlineProximity.UNDER_30_DAYS}:
        severity = bump(severity)
        escalations.append("deadline_near_or_passed")
    rationale = (
        f"Base severity {base} from {obligation.value} obligation with {gap.value}"
        + (f", escalated for {', '.join(escalations)}" if escalations else "")
        + "."
    )
    return RiskOutput(
        requirement_id=requirement_id,
        severity=severity,
        severity_inputs=SeverityInputs(
            obligation_type=obligation,
            gap_status=gap,
            impact_level=impact,
            deadline_proximity=deadline.value,
        ),
        escalations_applied=escalations,
        rationale=rationale,
    )


def overall_risk(severities: list[str]) -> str:
    if not severities:
        return OverallRisk.LOW.value
    worst = severities[0]
    for item in severities[1:]:
        worst = worse(worst, item)
    high_or_worse = sum(1 for item in severities if _ORDER.index(item) >= _ORDER.index(Severity.HIGH.value))
    if high_or_worse >= 3:
        return OverallRisk.CRITICAL.value
    return worst
