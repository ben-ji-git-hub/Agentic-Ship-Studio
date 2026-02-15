from __future__ import annotations

import argparse
from pathlib import Path

from vibe_sentinel.agent_pack import write_agent_pack
from vibe_sentinel.checks import compute_scorecard, run_checks
from vibe_sentinel.coach import write_coach
from vibe_sentinel.gui import StudioConfig, launch_studio, run_ship_flow
from vibe_sentinel.report import build_audit_report, console_summary, write_report_files, write_roadmap
from vibe_sentinel.templates import scaffold


def _cmd_init(args: argparse.Namespace) -> int:
    output_dir = Path(args.output).resolve()
    written = scaffold(output_dir, force=args.force)

    if written:
        print(f"Scaffolded {len(written)} file(s) in {output_dir}")
        for path in written:
            print(f"- {path}")
    else:
        print(f"No files written. Use --force to overwrite existing templates in {output_dir}.")

    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    project_path = Path(args.path).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: project path does not exist or is not a directory: {project_path}")
        return 2

    checks = run_checks(project_path)
    scorecard = compute_scorecard(checks)
    report = build_audit_report(project_path, checks, scorecard)

    output_dir = Path(args.output_dir).resolve()
    json_path, markdown_path = write_report_files(report, output_dir)

    print(console_summary(report))
    print("")
    print(f"Wrote JSON report to {json_path}")
    print(f"Wrote Markdown report to {markdown_path}")

    return 0


def _cmd_roadmap(args: argparse.Namespace) -> int:
    report_path = Path(args.report).resolve()
    if not report_path.exists():
        print(f"Error: report file not found: {report_path}")
        return 2

    output_path = Path(args.output).resolve()
    written_path = write_roadmap(report_path, output_path)
    print(f"Wrote roadmap to {written_path}")
    return 0


def _cmd_coach(args: argparse.Namespace) -> int:
    report_path = Path(args.report).resolve()
    if not report_path.exists():
        print(f"Error: report file not found: {report_path}")
        return 2

    project_path = Path(args.project).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: project path does not exist or is not a directory: {project_path}")
        return 2

    output_path = Path(args.output).resolve()
    coach_path, applied_files = write_coach(
        report_json_path=report_path,
        output_path=output_path,
        project_path=project_path,
        apply_safe=args.apply_safe,
    )
    print(f"Wrote beginner fix coach to {coach_path}")
    if applied_files:
        print("Applied safe starter files:")
        for path in applied_files:
            print(f"- {path}")
    return 0


def _cmd_studio(args: argparse.Namespace) -> int:
    openclaw_key = args.openclaw_key.strip() if isinstance(args.openclaw_key, str) else ""
    config = StudioConfig(
        host=args.host,
        port=args.port,
        openclaw_enabled=bool(args.enable_openclaw or openclaw_key),
        openclaw_api_key=(openclaw_key or None),
    )
    launch_studio(config)
    return 0


def _cmd_agent_pack(args: argparse.Namespace) -> int:
    report_path = Path(args.report).resolve()
    if not report_path.exists():
        print(f"Error: report file not found: {report_path}")
        return 2

    project_path = Path(args.project).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: project path does not exist or is not a directory: {project_path}")
        return 2

    output_path = Path(args.output).resolve()
    json_output_path = Path(args.json_output).resolve()
    runbook_path = Path(args.runbook_output).resolve()
    prompts_dir = Path(args.prompts_dir).resolve()
    markdown_path, tasks_path, runbook_path, task_count, _ = write_agent_pack(
        report_json_path=report_path,
        output_markdown_path=output_path,
        output_json_path=json_output_path,
        project_path=project_path,
        runbook_path=runbook_path,
        prompts_dir=prompts_dir,
    )
    print(f"Wrote agent sprint pack to {markdown_path}")
    print(f"Wrote agent task JSON to {tasks_path}")
    print(f"Wrote agent runbook to {runbook_path}")
    print(f"Prompt files directory: {prompts_dir}")
    print(f"Open tasks in pack: {task_count}")
    return 0


def _cmd_ship(args: argparse.Namespace) -> int:
    project_path = Path(args.path).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: project path does not exist or is not a directory: {project_path}")
        return 2

    result = run_ship_flow(project_path, apply_safe=args.apply_safe)
    before_score = float(result["before"].get("scorecard", {}).get("overall", 0.0))
    after_score = float(result["after"].get("scorecard", {}).get("overall", 0.0))
    delta = float(result.get("improvement", 0.0))
    task_count = int(result.get("task_count", 0))

    print(f"Ship sequence completed for {project_path}")
    print(f"Score: {before_score:.1f} -> {after_score:.1f} ({delta:+.1f})")
    print(f"Agent tasks generated: {task_count}")
    if result.get("applied_files"):
        print("Applied safe files:")
        for path in result["applied_files"]:
            print(f"- {path}")
    print("Artifacts:")
    for key, value in result.get("artifacts", {}).items():
        print(f"- {key}: {value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vibe-sentinel",
        description=(
            "Audit vibe-coded projects for Vibeathon readiness, "
            "then generate a prioritized quality roadmap."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Scaffold Vibeathon submission templates")
    init_parser.add_argument("--output", default=".vibe-sentinel", help="Directory for generated templates")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    init_parser.set_defaults(func=_cmd_init)

    audit_parser = subparsers.add_parser("audit", help="Run repository quality audit")
    audit_parser.add_argument("path", nargs="?", default=".", help="Project directory to audit")
    audit_parser.add_argument(
        "--output-dir",
        default=".vibe-sentinel",
        help="Directory for generated report artifacts",
    )
    audit_parser.set_defaults(func=_cmd_audit)

    roadmap_parser = subparsers.add_parser("roadmap", help="Generate prioritized roadmap from report JSON")
    roadmap_parser.add_argument(
        "--report",
        default=".vibe-sentinel/report.json",
        help="Path to report.json generated by `vibe-sentinel audit`",
    )
    roadmap_parser.add_argument(
        "--output",
        default=".vibe-sentinel/roadmap.md",
        help="Output markdown path for generated roadmap",
    )
    roadmap_parser.set_defaults(func=_cmd_roadmap)

    coach_parser = subparsers.add_parser(
        "coach",
        help="Generate beginner-friendly fix guidance from an audit report",
    )
    coach_parser.add_argument(
        "--report",
        default=".vibe-sentinel/report.json",
        help="Path to report.json generated by `vibe-sentinel audit`",
    )
    coach_parser.add_argument(
        "--output",
        default=".vibe-sentinel/coach.md",
        help="Output markdown path for the coaching plan",
    )
    coach_parser.add_argument(
        "--project",
        default=".",
        help="Project directory where safe starter files can be applied",
    )
    coach_parser.add_argument(
        "--apply-safe",
        action="store_true",
        help="Create missing baseline files (tests/CI/templates) without overwriting existing files",
    )
    coach_parser.set_defaults(func=_cmd_coach)

    studio_parser = subparsers.add_parser(
        "studio",
        help="Launch visual GUI for audit, coaching, and agentic auto-improvement",
    )
    studio_parser.add_argument("--host", default="127.0.0.1", help="Host address for the local server")
    studio_parser.add_argument("--port", default=8765, type=int, help="Port for the local server")
    studio_parser.add_argument(
        "--enable-openclaw",
        action="store_true",
        help="Enable OpenClaw bridge endpoints (/api/openclaw/*).",
    )
    studio_parser.add_argument(
        "--openclaw-key",
        default="",
        help="Optional API key required by OpenClaw bridge (sent in X-OpenClaw-Key).",
    )
    studio_parser.set_defaults(func=_cmd_studio)

    pack_parser = subparsers.add_parser(
        "agent-pack",
        help="Generate an agent-ready task pack from audit findings",
    )
    pack_parser.add_argument(
        "--report",
        default=".vibe-sentinel/report.json",
        help="Path to report.json generated by `vibe-sentinel audit`",
    )
    pack_parser.add_argument(
        "--project",
        default=".",
        help="Project directory referenced in generated prompts",
    )
    pack_parser.add_argument(
        "--output",
        default=".vibe-sentinel/agent_pack.md",
        help="Output markdown path for the agent sprint pack",
    )
    pack_parser.add_argument(
        "--json-output",
        default=".vibe-sentinel/agent_tasks.json",
        help="Output JSON path for structured agent tasks",
    )
    pack_parser.add_argument(
        "--runbook-output",
        default=".vibe-sentinel/agent_runbook.md",
        help="Output markdown path for the execution runbook",
    )
    pack_parser.add_argument(
        "--prompts-dir",
        default=".vibe-sentinel/prompts",
        help="Directory for per-task prompt text files",
    )
    pack_parser.set_defaults(func=_cmd_agent_pack)

    ship_parser = subparsers.add_parser(
        "ship",
        help="Run audit, agent-pack, coach, roadmap, and re-audit in one sequence",
    )
    ship_parser.add_argument("path", nargs="?", default=".", help="Project directory to process")
    ship_parser.add_argument(
        "--apply-safe",
        action="store_true",
        help="Allow coach step to create missing baseline files",
    )
    ship_parser.set_defaults(func=_cmd_ship)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
