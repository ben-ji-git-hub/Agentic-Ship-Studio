from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vibe_sentinel.report import SEVERITY_ORDER
from vibe_sentinel.templates import scaffold

PLAYBOOK: dict[str, dict[str, Any]] = {
    "problem_statement": {
        "plain": "Your README does not clearly explain the problem and target user.",
        "why": "Judges and users decide quickly. If the pain is unclear, they bounce.",
        "steps": [
            "Add a `## Problem` section in README with one concrete pain point.",
            "Add a `## Target User` section and name one primary audience.",
            "Keep it under 8 lines so it is skimmable.",
        ],
        "verify": "Re-run `vibe-sentinel audit .` and confirm Problem Statement is PASS.",
    },
    "quickstart": {
        "plain": "A new user cannot install and run your project quickly.",
        "why": "Fast onboarding increases usefulness and reduces demo friction.",
        "steps": [
            "Add `## Installation` and `## Quickstart` sections.",
            "Include copy-paste commands from a clean environment.",
            "Limit quickstart to 3 commands max.",
        ],
        "verify": "Follow the quickstart in a clean shell and verify it works end-to-end.",
    },
    "usage_examples": {
        "plain": "The README does not show practical input/output examples.",
        "why": "Examples convert readers into users by making value obvious.",
        "steps": [
            "Add one real usage example with command and expected output.",
            "Use fenced code blocks for readability.",
            "Prefer a realistic scenario over synthetic text.",
        ],
        "verify": "Confirm `Usage Examples` becomes PASS after re-audit.",
    },
    "tests_present": {
        "plain": "No automated tests were detected.",
        "why": "Without tests, regressions show up during demos or judging.",
        "steps": [
            "Create `tests/test_smoke.py` with at least one passing smoke test.",
            "Add one behavior test for your core value path.",
            "Run tests locally before every commit.",
        ],
        "verify": "Run your test command and ensure it exits with code 0.",
    },
    "ci_present": {
        "plain": "No CI workflow was found.",
        "why": "CI proves your project runs outside your machine.",
        "steps": [
            "Add `.github/workflows/ci.yml`.",
            "Run install + tests in the workflow.",
            "Enable branch checks if using pull requests.",
        ],
        "verify": "Push a branch and confirm the CI job succeeds.",
    },
    "dependency_lock": {
        "plain": "Dependencies are not fully reproducible.",
        "why": "Unpinned dependencies can break demos unexpectedly.",
        "steps": [
            "Add a lockfile for your package manager when possible.",
            "If using requirements.txt, pin versions exactly.",
            "Document Python/Node runtime versions in README.",
        ],
        "verify": "Fresh clone + install should produce identical behavior.",
    },
    "demo_script": {
        "plain": "Demo script is missing or not in a clear 3-5 minute structure.",
        "why": "Strong demos raise execution scores and improve story clarity.",
        "steps": [
            "Use `DEMO_SCRIPT.md` with hook, workflow, and close.",
            "Keep script around 300-900 words.",
            "Include measurable outcome in the last 30 seconds.",
        ],
        "verify": "Time your dry run and keep it between 3 and 5 minutes.",
    },
    "secret_scan": {
        "plain": "Potential secret leakage was detected.",
        "why": "Leaked keys can cause account compromise and instant trust loss.",
        "steps": [
            "Remove hard-coded secrets from source files.",
            "Move secrets to environment variables and `.env.example`.",
            "Rotate any exposed credentials immediately.",
        ],
        "verify": "Re-run audit and confirm Secret Leak Scan is PASS.",
    },
    "license_present": {
        "plain": "No open-source license was detected.",
        "why": "Without a license, others cannot safely reuse your project.",
        "steps": [
            "Add `LICENSE` (MIT is common for hackathon projects).",
            "Mention the license in README.",
        ],
        "verify": "Confirm `LICENSE` exists at repo root.",
    },
    "submission_template": {
        "plain": "Submission metadata is missing or incomplete.",
        "why": "Missing form details can delay or invalidate submission.",
        "steps": [
            "Fill Discord username, profile URL, repo URL, and demo URL.",
            "Keep this in `SUBMISSION.md` for final copy/paste.",
        ],
        "verify": "Open `SUBMISSION.md` and confirm all required fields are filled.",
    },
    "innovation_statement": {
        "plain": "Your differentiation story is not explicit enough.",
        "why": "Innovation score depends on clear, specific uniqueness.",
        "steps": [
            "Add `## Why this is different` in README.",
            "Name two alternatives and your concrete edge.",
            "Tie edge to measurable user outcome.",
        ],
        "verify": "Ask a new reader to explain your edge in one sentence.",
    },
    "novelty_artifact": {
        "plain": "No dedicated differentiation artifact was found.",
        "why": "A dedicated artifact gives judges proof of thought depth.",
        "steps": [
            "Create `UNIQUE_EDGE.md` with alternatives, differences, and value.",
            "Reference it from README.",
        ],
        "verify": "Ensure `UNIQUE_EDGE.md` is committed and linked.",
    },
}

BASE_README = """# Your Project Name

## Problem
Describe one painful workflow your user has today.

## Target User
Name who this is for.

## Installation
```bash
# add install commands
```

## Quickstart
```bash
# add minimal run commands
```

## Usage Example
```bash
# add one realistic example
```

## Why this is different
Explain your non-obvious edge.
"""

BASE_TEST = """def test_smoke() -> None:
    assert True
"""

BASE_CI = """name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          python -m pip install --upgrade pip
          pip install -e .
          python -m unittest discover -s tests -p 'test_*.py'
"""


def _sorted_issues(report_payload: dict[str, Any]) -> list[dict[str, Any]]:
    checks = report_payload.get("checks", [])
    issues = [check for check in checks if check.get("status") != "pass"]
    issues.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(item.get("severity", "low"), 2),
            item.get("category", "zzz"),
            item.get("check_id", ""),
        )
    )
    return issues


def _maybe_write(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return True


def _apply_safe_starters(project_path: Path, issues: list[dict[str, Any]]) -> list[Path]:
    written: list[Path] = []
    issue_ids = {issue.get("check_id", "") for issue in issues}

    if issue_ids & {"submission_template", "demo_script", "novelty_artifact"}:
        for path in scaffold(project_path, force=False):
            written.append(path)

    if "tests_present" in issue_ids:
        test_path = project_path / "tests" / "test_smoke.py"
        if _maybe_write(test_path, BASE_TEST):
            written.append(test_path)

    if "ci_present" in issue_ids:
        ci_path = project_path / ".github" / "workflows" / "ci.yml"
        if _maybe_write(ci_path, BASE_CI):
            written.append(ci_path)

    if issue_ids & {"problem_statement", "quickstart", "usage_examples"}:
        readme_path = project_path / "README.md"
        if _maybe_write(readme_path, BASE_README):
            written.append(readme_path)

    return written


def _coach_block(idx: int, issue: dict[str, Any]) -> list[str]:
    check_id = issue.get("check_id", "")
    title = issue.get("title", check_id)
    severity = issue.get("severity", "low").upper()
    recommendation = issue.get("recommendation", "Address this finding.")

    recipe = PLAYBOOK.get(
        check_id,
        {
            "plain": recommendation,
            "why": "This issue blocks confidence and submission quality.",
            "steps": [recommendation],
            "verify": "Re-run `vibe-sentinel audit .` and confirm this check passes.",
        },
    )

    lines = [
        f"## {idx}. {title} ({severity})",
        "",
        f"**Plain English:** {recipe['plain']}",
        "",
        f"**Why it matters:** {recipe['why']}",
        "",
        "**Do this now:**",
    ]

    for step_idx, step in enumerate(recipe["steps"], start=1):
        lines.append(f"{step_idx}. {step}")

    lines.append("")
    lines.append(f"**Verify:** {recipe['verify']}")
    lines.append("")
    return lines


def coach_markdown(
    report_payload: dict[str, Any],
    issues: list[dict[str, Any]],
    applied_files: list[Path],
) -> str:
    scorecard = report_payload.get("scorecard", {})

    lines: list[str] = [
        "# Vibe Sentinel Beginner Fix Coach",
        "",
        "This guide translates audit findings into plain-English actions you can execute immediately.",
        "",
        f"Current projected score: **{scorecard.get('overall', 0):.1f}/100**",
        "",
        "## Fast Path",
        "",
        "1. Fix all HIGH findings first.",
        "2. Re-run `vibe-sentinel audit . --output-dir .vibe-sentinel`.",
        "3. Repeat until no FAIL checks remain.",
        "",
    ]

    if not issues:
        lines.append("No warnings or failures found. Keep running audits after major changes.")
    else:
        lines.append("## Action Cards")
        lines.append("")
        for idx, issue in enumerate(issues, start=1):
            lines.extend(_coach_block(idx, issue))

    if applied_files:
        lines.append("## Safe Starter Files Applied")
        lines.append("")
        lines.append("The following files were created because they were missing:")
        lines.append("")
        for path in applied_files:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.append("## One-Command Recheck")
    lines.append("")
    lines.append("```bash")
    lines.append("vibe-sentinel audit . --output-dir .vibe-sentinel && vibe-sentinel roadmap --report .vibe-sentinel/report.json --output .vibe-sentinel/roadmap.md")
    lines.append("```")

    return "\n".join(lines) + "\n"


def write_coach(
    report_json_path: Path,
    output_path: Path,
    project_path: Path,
    apply_safe: bool = False,
) -> tuple[Path, list[Path]]:
    payload = json.loads(report_json_path.read_text(encoding="utf-8"))
    issues = _sorted_issues(payload)

    applied: list[Path] = []
    if apply_safe:
        applied = _apply_safe_starters(project_path, issues)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(coach_markdown(payload, issues, applied), encoding="utf-8")
    return output_path, applied
