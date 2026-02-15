from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    title: str
    impact: str
    duration_minutes: int


def _impact_weight(value: str) -> int:
    mapping = {"high": 3, "medium": 2, "low": 1}
    return mapping.get(value.strip().lower(), 1)


def rank_tasks(tasks: list[Task]) -> list[Task]:
    return sorted(
        tasks,
        key=lambda item: (_impact_weight(item.impact), -item.duration_minutes),
        reverse=True,
    )


def build_focus_plan(tasks: list[Task], max_blocks: int = 5) -> list[str]:
    ranked = rank_tasks(tasks)[:max_blocks]
    lines: list[str] = []
    for idx, item in enumerate(ranked, start=1):
        lines.append(f"{idx}. {item.title} ({item.duration_minutes}m, {item.impact})")
    return lines
