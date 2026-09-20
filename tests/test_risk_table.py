from datetime import date
from uuid import uuid4

import pytest
from app.agents.contracts import StatedDate
from app.agents.risk import BASE_SEVERITY, deadline_proximity, overall_risk, score_risk
from app.enums import (
    DateBasis,
    DeadlineProximity,
    GapStatus,
    ImpactLevel,
    ObligationType,
    OverallRisk,
    Severity,
)


@pytest.mark.parametrize(
    ("obligation", "gap", "expected"),
    [(left, right, score) for (left, right), score in BASE_SEVERITY.items()],
)
def test_every_base_risk_box(obligation, gap, expected):
    result = score_risk(
        uuid4(),
        obligation,
        gap,
        ImpactLevel.LOW,
        DeadlineProximity.NONE,
    )
    assert result.severity == expected
    assert result.escalations_applied == []


def test_high_impact_bumps_one_level():
    result = score_risk(
        uuid4(),
        ObligationType.MANDATORY,
        GapStatus.INSUFFICIENT_EVIDENCE,
        ImpactLevel.HIGH,
        DeadlineProximity.NONE,
    )
    assert result.severity == Severity.HIGH.value
    assert "impact_level_high" in result.escalations_applied


def test_near_deadline_bumps_one_level():
    result = score_risk(
        uuid4(),
        ObligationType.RECOMMENDED,
        GapStatus.NON_COMPLIANT,
        ImpactLevel.LOW,
        DeadlineProximity.UNDER_30_DAYS,
    )
    assert result.severity == Severity.HIGH.value
    assert "deadline_near_or_passed" in result.escalations_applied


def test_both_bumps_stop_at_critical():
    result = score_risk(
        uuid4(),
        ObligationType.MANDATORY,
        GapStatus.NON_COMPLIANT,
        ImpactLevel.HIGH,
        DeadlineProximity.OVERDUE,
    )
    assert result.severity == Severity.CRITICAL.value


def test_overall_risk_is_worst_and_three_highs_are_critical():
    assert overall_risk([Severity.LOW.value, Severity.MEDIUM.value]) == OverallRisk.MEDIUM.value
    assert overall_risk([Severity.HIGH.value] * 3) == OverallRisk.CRITICAL.value


def test_deadline_proximity_uses_cited_dates_only():
    cited = StatedDate(
        date=date(2026, 12, 1),
        date_basis=DateBasis.CITED_COMPLIANCE,
        source_chunk_id=uuid4(),
    )
    assert deadline_proximity([cited], date(2026, 11, 20)) == DeadlineProximity.UNDER_30_DAYS
    assert deadline_proximity([], date(2026, 11, 20)) == DeadlineProximity.NONE
