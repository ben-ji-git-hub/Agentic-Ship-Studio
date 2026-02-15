from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from vibe_sentinel.models import AuditReport, CheckResult

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STATUS_ICON = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}


def build_audit_report(project_path: Path, checks: list[CheckResult], scorecard) -> AuditReport:
    return AuditReport(
        project_path=str(project_path.resolve()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        scorecard=scorecard,
        checks=checks,
    )


def markdown_report(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("# Vibe Sentinel Audit Report")
    lines.append("")
    lines.append(f"- Project: `{report.project_path}`")
    lines.append(f"- Generated (UTC): `{report.generated_at}`")
    lines.append("")
    lines.append("## Scorecard")
    lines.append("")
    lines.append(f"- Usefulness: **{report.scorecard.usefulness:.1f}/100**")
    lines.append(f"- Impact: **{report.scorecard.impact:.1f}/100**")
    lines.append(f"- Execution: **{report.scorecard.execution:.1f}/100**")
    lines.append(f"- Innovation: **{report.scorecard.innovation:.1f}/100**")
    lines.append(f"- Projected Vibeathon Score: **{report.scorecard.overall:.1f}/100**")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Status | Category | Check | Detail | Recommendation |")
    lines.append("|---|---|---|---|---|")

    sorted_checks = sorted(
        report.checks,
        key=lambda item: (SEVERITY_ORDER[item.severity], item.category, item.check_id),
    )

    for check in sorted_checks:
        lines.append(
            "| "
            f"{STATUS_ICON[check.status]} | {check.category} | {check.title} | "
            f"{check.detail.replace('|', '/')} | {check.recommendation.replace('|', '/')} |"
        )

    return "\n".join(lines) + "\n"


def console_summary(report: AuditReport) -> str:
    failing = [check for check in report.checks if check.status == "fail"]
    warnings = [check for check in report.checks if check.status == "warn"]
    top = sorted(
        [check for check in report.checks if check.status != "pass"],
        key=lambda item: (SEVERITY_ORDER[item.severity], item.category),
    )[:5]

    lines = [
        f"Projected Vibeathon score: {report.scorecard.overall:.1f}/100",
        (
            "Category scores: "
            f"usefulness {report.scorecard.usefulness:.1f}, "
            f"impact {report.scorecard.impact:.1f}, "
            f"execution {report.scorecard.execution:.1f}, "
            f"innovation {report.scorecard.innovation:.1f}"
        ),
        f"Findings: {len(failing)} fail, {len(warnings)} warn",
    ]

    if top:
        lines.append("Top fixes:")
        for item in top:
            lines.append(f"- [{item.severity}] {item.title}: {item.recommendation}")

    return "\n".join(lines)


def write_report_files(report: AuditReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    markdown_path = output_dir / "report.md"

    json_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")

    return json_path, markdown_path


def _estimate_effort(check: dict) -> str:
    severity = check.get("severity")
    check_id = check.get("check_id", "")
    if severity == "high":
        return "M"
    if check_id in {"ci_present", "demo_script"}:
        return "M"
    return "S"


def roadmap_markdown(report_payload: dict) -> str:
    scorecard = report_payload.get("scorecard", {})
    checks = report_payload.get("checks", [])

    issues = [check for check in checks if check.get("status") != "pass"]
    issues.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(item.get("severity", "low"), 2),
            item.get("category", "zzz"),
            item.get("check_id", ""),
        )
    )

    lines: list[str] = [
        "# Vibe Sentinel Roadmap",
        "",
        f"Current projected score: **{scorecard.get('overall', 0):.1f}/100**",
        "",
        "## Priority Plan",
        "",
    ]

    if not issues:
        lines.append("No blocking or warning findings detected. Keep running `vibe-sentinel audit` after major changes.")
        return "\n".join(lines) + "\n"

    for idx, check in enumerate(issues, start=1):
        effort = _estimate_effort(check)
        lines.append(
            f"{idx}. [{check.get('severity', 'low').upper()} | {effort}] "
            f"{check.get('title', check.get('check_id'))}: {check.get('recommendation', 'Address this finding.')}"
        )

    lines.append("")
    lines.append("## Definition of Done")
    lines.append("")
    lines.append("- Re-run `vibe-sentinel audit` and target 85+ projected score.")
    lines.append("- Ensure no high-severity findings remain.")
    lines.append("- Validate quickstart from a clean environment.")

    return "\n".join(lines) + "\n"


def write_roadmap(report_json_path: Path, output_path: Path) -> Path:
    payload = json.loads(report_json_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(roadmap_markdown(payload), encoding="utf-8")
    return output_path
