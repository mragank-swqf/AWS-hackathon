"""Compare shall-clauses between two regulation texts. No LLM."""

from __future__ import annotations

from dataclasses import dataclass

from app.enums import RequirementChangeKind
from app.services.local_ai import _shall_clauses


@dataclass(frozen=True)
class ClauseDiff:
    kind: RequirementChangeKind
    clause_number: str | None
    previous_text: str | None
    new_text: str | None


def diff_requirement_text(previous: str, current: str) -> list[ClauseDiff]:
    old_items = {num: body for num, body in _shall_clauses(previous)}
    new_items = {num: body for num, body in _shall_clauses(current)}
    diffs: list[ClauseDiff] = []
    for num in sorted(set(old_items) | set(new_items), key=lambda value: tuple(value.split("."))):
        if num not in new_items:
            diffs.append(
                ClauseDiff(
                    kind=RequirementChangeKind.REMOVED,
                    clause_number=num,
                    previous_text=f"{num} {old_items[num]}",
                    new_text=None,
                )
            )
        elif num not in old_items:
            diffs.append(
                ClauseDiff(
                    kind=RequirementChangeKind.ADDED,
                    clause_number=num,
                    previous_text=None,
                    new_text=f"{num} {new_items[num]}",
                )
            )
        elif old_items[num] != new_items[num]:
            diffs.append(
                ClauseDiff(
                    kind=RequirementChangeKind.MODIFIED,
                    clause_number=num,
                    previous_text=f"{num} {old_items[num]}",
                    new_text=f"{num} {new_items[num]}",
                )
            )
        else:
            diffs.append(
                ClauseDiff(
                    kind=RequirementChangeKind.UNCHANGED,
                    clause_number=num,
                    previous_text=f"{num} {old_items[num]}",
                    new_text=f"{num} {new_items[num]}",
                )
            )
    return diffs
