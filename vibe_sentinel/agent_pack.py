from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

TASK_PLAYBOOK: dict[str, dict[str, Any]] = {
    "problem_statement": {
        "files": ["README.md"],
        "outcome": "README has a clear Problem and Target User section.",
        "checks": ["Re-run vibe-sentinel audit and ensure Problem Statement is PASS."],
    },
    "quickstart": {
        "files": ["README.md"],
        "outcome": "README has copy-paste install and quickstart commands.",
        "checks": ["A clean shell can run quickstart in under 2 minutes."],
    },
    "usage_examples": {
        "files": ["README.md"],
        "outcome": "README has a realistic usage example with expected output.",
        "checks": ["Usage Examples check returns PASS."],
    },
    "tests_present": {
        "files": ["tests/", "src/", "vibe_sentinel/"],
        "outcome": "At least one smoke test and one behavior test exist.",
        "checks": ["python -m unittest discover -s tests -p 'test_*.py' exits 0."],
    },
    "ci_present": {
        "files": [".github/workflows/ci.yml"],
        "outcome": "CI runs install + tests on push and PR.",
        "checks": ["Push branch and confirm CI succeeds."],
    },
    "dependency_lock": {
        "files": ["requirements.txt", "pyproject.toml", "lockfile"],
        "outcome": "Dependencies are reproducible via lockfile or pinned versions.",
        "checks": ["Fresh clone install reproduces same behavior."],
    },
    "demo_script": {
        "files": ["DEMO_SCRIPT.md"],
        "outcome": "Demo script covers hook, workflow, reliability, and close in 3-5 minutes.",
        "checks": ["Script length roughly 300-900 words."],
    },
    "secret_scan": {
        "files": ["source files", ".env.example", "config files"],
        "outcome": "Hard-coded secrets removed and moved to environment variables.",
        "checks": ["Secret Leak Scan returns PASS."],
    },
    "license_present": {
        "files": ["LICENSE", "README.md"],
        "outcome": "Open-source license exists and is referenced in README.",
        "checks": ["LICENSE exists at repo root."],
    },
    "submission_template": {
        "files": ["SUBMISSION.md"],
        "outcome": "Submission metadata file includes all required links and handles.",
        "checks": ["SUBMISSION.md contains Discord, GitHub profile, repo, and demo URL."],
    },
    "innovation_statement": {
        "files": ["README.md"],
        "outcome": "README clearly explains why this project is different.",
        "checks": ["Innovation Positioning returns PASS."],
    },
    "novelty_artifact": {
        "files": ["UNIQUE_EDGE.md"],
        "outcome": "Dedicated differentiation artifact exists and is linked.",
        "checks": ["Differentiation Artifact returns PASS."],
    },
}


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


def _estimate_minutes(severity: str) -> int:
    if severity == "high":
        return 30
    if severity == "medium":
        return 20
    return 10


def _default_check_commands(project_path: Path) -> list[str]:
    commands = [
        "python -m unittest discover -s tests -p 'test_*.py'",
        "vibe-sentinel audit . --output-dir .vibe-sentinel",
    ]
    if (project_path / ".github" / "workflows" / "ci.yml").exists():
        commands.append("git add -A && git commit -m 'Apply agent task fixes'  # optional")
    return commands


def _task_card(issue: dict[str, Any], idx: int, project_path: Path) -> dict[str, Any]:
    check_id = issue.get("check_id", "")
    title = issue.get("title", check_id)
    severity = issue.get("severity", "low")
    playbook = TASK_PLAYBOOK.get(
        check_id,
        {
            "files": ["project files"],
            "outcome": issue.get("recommendation", "Resolve this finding."),
            "checks": ["Re-run vibe-sentinel audit and confirm this check passes."],
        },
    )

    files = playbook["files"]
    outcome = playbook["outcome"]
    checks = playbook["checks"]

    prompt = (
        "You are fixing a repository quality finding.\n"
        f"Task: {title}\n"
        f"Severity: {severity.upper()}\n"
        f"Context: {issue.get('detail', '').strip()}\n"
        f"Goal: {outcome}\n"
        f"Files to touch (preferred): {', '.join(files)}\n"
        "Constraints: make minimal, safe edits; do not break existing behavior; keep style consistent.\n"
        "After editing, run verification commands and summarize exactly what changed."
    )

    return {
        "task_id": f"agent-task-{idx:02d}",
        "check_id": check_id,
        "title": title,
        "severity": severity,
        "estimated_minutes": _estimate_minutes(severity),
        "objective": outcome,
        "files_to_touch": files,
        "recommendation": issue.get("recommendation", ""),
        "verification_checks": checks,
        "agent_prompt": prompt,
        "verification_commands": _default_check_commands(project_path),
        "prompt_file": "",
    }


def build_agent_tasks(report_payload: dict[str, Any], project_path: Path) -> list[dict[str, Any]]:
    issues = _sorted_issues(report_payload)
    tasks: list[dict[str, Any]] = []
    for idx, issue in enumerate(issues, start=1):
        tasks.append(_task_card(issue, idx, project_path))
    return tasks


def master_prompt(tasks: list[dict[str, Any]], project_path: Path) -> str:
    if not tasks:
        return "Audit has no open findings. Validate tests and docs still pass, then prepare demo artifacts."

    lines = [
        "You are an autonomous coding agent improving this repository.",
        f"Repository path: {project_path}",
        "Execute tasks in order, commit-safe and minimal changes only.",
        "For each task: edit files, run verification commands, then report changed files and outcomes.",
        "Do not skip verification.",
        "",
        "Task queue:",
    ]

    for task in tasks:
        lines.append(f"- {task['task_id']} [{task['severity'].upper()}] {task['title']}: {task['objective']}")

    lines.append("")
    lines.append("At the end, run: vibe-sentinel audit . --output-dir .vibe-sentinel")
    return "\n".join(lines)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "task"


def write_prompt_files(tasks: list[dict[str, Any]], prompts_dir: Path, project_path: Path) -> list[dict[str, Any]]:
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        slug = _safe_slug(task.get("title", task["task_id"]))
        filename = f"{task['task_id']}-{slug}.txt"
        path = prompts_dir / filename
        content = [
            f"Repository: {project_path}",
            f"Task ID: {task['task_id']}",
            "",
            task["agent_prompt"],
            "",
            "Verification commands:",
        ]
        for command in task["verification_commands"]:
            content.append(f"- {command}")

        path.write_text("\n".join(content) + "\n", encoding="utf-8")
        task["prompt_file"] = str(path)

    return tasks


def agent_runbook_markdown(tasks: list[dict[str, Any]], project_path: Path) -> str:
    lines = [
        "# Agent Runbook",
        "",
        f"Project path: `{project_path}`",
        "",
        "Use this runbook to execute Agent Sprint Pack tasks in strict priority order.",
        "",
        "## Execution Protocol",
        "",
        "1. Start with all HIGH severity tasks.",
        "2. For each task, paste its prompt file into your coding agent.",
        "3. After each task, run verification commands and save output.",
        "4. Re-run `vibe-sentinel audit` after each 2 tasks.",
        "",
        "## Task Queue",
        "",
    ]

    if not tasks:
        lines.append("No open tasks. Keep this runbook for maintenance cycles.")
    else:
        for task in tasks:
            lines.append(
                f"- [ ] {task['task_id']} [{task['severity'].upper()}] {task['title']} "
                f"({task['estimated_minutes']} min)"
            )
            lines.append(f"  Prompt file: `{task['prompt_file']}`")

    lines.append("")
    lines.append("## Final Verification")
    lines.append("")
    lines.append("```bash")
    lines.append("python -m unittest discover -s tests -p 'test_*.py'")
    lines.append("vibe-sentinel audit . --output-dir .vibe-sentinel")
    lines.append("vibe-sentinel roadmap --report .vibe-sentinel/report.json --output .vibe-sentinel/roadmap.md")
    lines.append("```")

    return "\n".join(lines) + "\n"


def agent_pack_markdown(
    report_payload: dict[str, Any],
    tasks: list[dict[str, Any]],
    project_path: Path,
    runbook_path: Path,
) -> str:
    scorecard = report_payload.get("scorecard", {})
    current_score = float(scorecard.get("overall", 0.0))

    lines: list[str] = [
        "# Agent Sprint Pack",
        "",
        "This pack converts audit findings into a task queue that coding agents can execute immediately.",
        "",
        f"- Project: `{project_path}`",
        f"- Current projected score: **{current_score:.1f}/100**",
        f"- Open agent tasks: **{len(tasks)}**",
        f"- Runbook: `{runbook_path}`",
        "",
        "## Master Prompt (Copy/Paste)",
        "",
        "```text",
        master_prompt(tasks, project_path),
        "```",
        "",
    ]

    if not tasks:
        lines.append("No open findings. Use this pack as a maintenance checklist after major changes.")
        return "\n".join(lines) + "\n"

    lines.append("## Task Cards")
    lines.append("")

    for task in tasks:
        lines.append(f"### {task['task_id']} - {task['title']} ({task['severity'].upper()})")
        lines.append("")
        lines.append(f"- Objective: {task['objective']}")
        lines.append(f"- Estimated effort: {task['estimated_minutes']} min")
        lines.append(f"- Files to touch: {', '.join(task['files_to_touch'])}")
        lines.append(f"- Prompt file: `{task['prompt_file']}`")
        lines.append("")
        lines.append("Verification checks:")
        for check in task["verification_checks"]:
            lines.append(f"- {check}")
        lines.append("")
        lines.append("Agent prompt:")
        lines.append("```text")
        lines.append(task["agent_prompt"])
        lines.append("```")
        lines.append("")

    lines.append("## Finish Line")
    lines.append("")
    lines.append("```bash")
    lines.append("vibe-sentinel audit . --output-dir .vibe-sentinel")
    lines.append("vibe-sentinel roadmap --report .vibe-sentinel/report.json --output .vibe-sentinel/roadmap.md")
    lines.append("```")

    return "\n".join(lines) + "\n"


def write_agent_pack(
    report_json_path: Path,
    output_markdown_path: Path,
    output_json_path: Path,
    project_path: Path,
    runbook_path: Path,
    prompts_dir: Path,
) -> tuple[Path, Path, Path, int, list[dict[str, Any]]]:
    payload = json.loads(report_json_path.read_text(encoding="utf-8"))
    tasks = build_agent_tasks(payload, project_path)
    tasks = write_prompt_files(tasks, prompts_dir, project_path)

    runbook = agent_runbook_markdown(tasks, project_path)
    markdown = agent_pack_markdown(payload, tasks, project_path, runbook_path)

    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    runbook_path.parent.mkdir(parents=True, exist_ok=True)

    output_markdown_path.write_text(markdown, encoding="utf-8")
    output_json_path.write_text(json.dumps({"project": str(project_path), "tasks": tasks}, indent=2) + "\n", encoding="utf-8")
    runbook_path.write_text(runbook, encoding="utf-8")

    return output_markdown_path, output_json_path, runbook_path, len(tasks), tasks
