from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Status = Literal["pass", "warn", "fail"]
Severity = Literal["low", "medium", "high"]
Category = Literal["usefulness", "impact", "execution", "innovation"]


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    title: str
    category: Category
    weight: int


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    title: str
    category: Category
    weight: int
    status: Status
    severity: Severity
    detail: str
    recommendation: str

    def points(self) -> float:
        multiplier = {"pass": 1.0, "warn": 0.5, "fail": 0.0}[self.status]
        return self.weight * multiplier

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["points"] = round(self.points(), 2)
        return payload


@dataclass(frozen=True)
class ScoreCard:
    usefulness: float
    impact: float
    execution: float
    innovation: float
    overall: float

    def to_dict(self) -> dict[str, float]:
        return {
            "usefulness": round(self.usefulness, 2),
            "impact": round(self.impact, 2),
            "execution": round(self.execution, 2),
            "innovation": round(self.innovation, 2),
            "overall": round(self.overall, 2),
        }


@dataclass(frozen=True)
class AuditReport:
    project_path: str
    generated_at: str
    scorecard: ScoreCard
    checks: list[CheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_path": self.project_path,
            "generated_at": self.generated_at,
            "scorecard": self.scorecard.to_dict(),
            "checks": [check.to_dict() for check in self.checks],
        }
