from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from vibe_sentinel.agent_pack import write_agent_pack
from vibe_sentinel.checks import compute_scorecard, run_checks
from vibe_sentinel.coach import write_coach
from vibe_sentinel.report import build_audit_report, write_report_files, write_roadmap


@dataclass(frozen=True)
class StudioConfig:
    host: str
    port: int
    openclaw_enabled: bool = False
    openclaw_api_key: str | None = None


def _artifact_dir(project_path: Path) -> Path:
    return project_path / ".vibe-sentinel"


def _audit(project_path: Path) -> tuple[dict[str, Any], Path, Path]:
    checks = run_checks(project_path)
    scorecard = compute_scorecard(checks)
    report = build_audit_report(project_path, checks, scorecard)
    output_dir = _artifact_dir(project_path)
    report_json_path, report_markdown_path = write_report_files(report, output_dir)
    return report.to_dict(), report_json_path, report_markdown_path


def _open_findings(report_payload: dict[str, Any]) -> list[dict[str, Any]]:
    checks = report_payload.get("checks", [])
    findings = [check for check in checks if check.get("status") != "pass"]
    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(
        key=lambda item: (
            severity_order.get(item.get("severity", "low"), 2),
            item.get("category", "zzz"),
            item.get("check_id", ""),
        )
    )
    return findings


def _derive_insights(report_payload: dict[str, Any]) -> dict[str, Any]:
    checks = report_payload.get("checks", [])
    scorecard = report_payload.get("scorecard", {})
    findings = _open_findings(report_payload)

    status_counts = {"pass": 0, "warn": 0, "fail": 0}
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for check in checks:
        status = str(check.get("status", "pass"))
        severity = str(check.get("severity", "low"))
        if status in status_counts:
            status_counts[status] += 1
        if severity in severity_counts:
            severity_counts[severity] += 1

    total = len(checks)
    pass_rate = 0.0 if total == 0 else (status_counts["pass"] / total) * 100.0

    overall = float(scorecard.get("overall", 0.0))
    if overall >= 90:
        band = "excellent"
    elif overall >= 75:
        band = "strong"
    elif overall >= 55:
        band = "needs-work"
    else:
        band = "critical"

    top_actions: list[str] = []
    for finding in findings:
        recommendation = str(finding.get("recommendation", "")).strip()
        if recommendation and recommendation not in top_actions:
            top_actions.append(recommendation)
        if len(top_actions) == 3:
            break

    return {
        "status_counts": status_counts,
        "severity_counts": severity_counts,
        "open_findings": len(findings),
        "pass_rate": round(pass_rate, 1),
        "score_band": band,
        "top_actions": top_actions,
    }


def run_audit_flow(project_path: Path) -> dict[str, Any]:
    report_payload, report_json_path, report_markdown_path = _audit(project_path)
    return {
        "report": report_payload,
        "insights": _derive_insights(report_payload),
        "artifacts": {
            "report_json": str(report_json_path),
            "report_markdown": str(report_markdown_path),
        },
    }


def run_roadmap_flow(project_path: Path) -> dict[str, Any]:
    report_payload, report_json_path, _ = _audit(project_path)
    roadmap_path = _artifact_dir(project_path) / "roadmap.md"
    write_roadmap(report_json_path, roadmap_path)
    content = roadmap_path.read_text(encoding="utf-8")
    return {
        "report": report_payload,
        "insights": _derive_insights(report_payload),
        "roadmap_markdown": content,
        "artifacts": {
            "roadmap_markdown": str(roadmap_path),
            "report_json": str(report_json_path),
        },
    }


def run_coach_flow(project_path: Path, apply_safe: bool) -> dict[str, Any]:
    report_payload, report_json_path, _ = _audit(project_path)
    coach_path = _artifact_dir(project_path) / "coach.md"
    _, applied_files = write_coach(
        report_json_path=report_json_path,
        output_path=coach_path,
        project_path=project_path,
        apply_safe=apply_safe,
    )
    content = coach_path.read_text(encoding="utf-8")
    return {
        "report": report_payload,
        "insights": _derive_insights(report_payload),
        "coach_markdown": content,
        "applied_files": [str(path) for path in applied_files],
        "artifacts": {
            "coach_markdown": str(coach_path),
            "report_json": str(report_json_path),
        },
    }


def run_agent_pack_flow(project_path: Path) -> dict[str, Any]:
    report_payload, report_json_path, _ = _audit(project_path)
    output_dir = _artifact_dir(project_path)
    pack_path = output_dir / "agent_pack.md"
    tasks_path = output_dir / "agent_tasks.json"
    runbook_path = output_dir / "agent_runbook.md"
    prompts_dir = output_dir / "prompts"

    _, _, _, task_count, tasks = write_agent_pack(
        report_json_path=report_json_path,
        output_markdown_path=pack_path,
        output_json_path=tasks_path,
        project_path=project_path,
        runbook_path=runbook_path,
        prompts_dir=prompts_dir,
    )
    content = pack_path.read_text(encoding="utf-8")
    return {
        "report": report_payload,
        "insights": _derive_insights(report_payload),
        "agent_pack_markdown": content,
        "agent_tasks": tasks,
        "task_count": task_count,
        "artifacts": {
            "agent_pack_markdown": str(pack_path),
            "agent_tasks_json": str(tasks_path),
            "agent_runbook_markdown": str(runbook_path),
            "agent_prompts_dir": str(prompts_dir),
            "report_json": str(report_json_path),
        },
    }


def run_ship_flow(project_path: Path, apply_safe: bool = True) -> dict[str, Any]:
    before = run_audit_flow(project_path)
    before_report = before["report"]
    before_score = before_report.get("scorecard", {}).get("overall", 0.0)

    pack = run_agent_pack_flow(project_path)
    coach = run_coach_flow(project_path, apply_safe=apply_safe)
    roadmap = run_roadmap_flow(project_path)

    after = run_audit_flow(project_path)
    after_report = after["report"]
    after_score = after_report.get("scorecard", {}).get("overall", 0.0)

    improvement = round(float(after_score) - float(before_score), 2)

    return {
        "before": before_report,
        "before_insights": before["insights"],
        "after": after_report,
        "after_insights": after["insights"],
        "improvement": improvement,
        "applied_files": coach.get("applied_files", []),
        "task_count": pack.get("task_count", 0),
        "agent_tasks": pack.get("agent_tasks", []),
        "remaining_findings": _open_findings(after_report),
        "agent_pack_markdown": pack.get("agent_pack_markdown", ""),
        "coach_markdown": coach.get("coach_markdown", ""),
        "roadmap_markdown": roadmap.get("roadmap_markdown", ""),
        "artifacts": {
            "report_json": after["artifacts"]["report_json"],
            "report_markdown": after["artifacts"]["report_markdown"],
            "coach_markdown": coach["artifacts"]["coach_markdown"],
            "agent_pack_markdown": pack["artifacts"]["agent_pack_markdown"],
            "agent_tasks_json": pack["artifacts"]["agent_tasks_json"],
            "agent_runbook_markdown": pack["artifacts"]["agent_runbook_markdown"],
            "agent_prompts_dir": pack["artifacts"]["agent_prompts_dir"],
            "roadmap_markdown": roadmap["artifacts"]["roadmap_markdown"],
        },
    }


def run_agentic_cycle(project_path: Path) -> dict[str, Any]:
    return run_ship_flow(project_path, apply_safe=True)


def read_artifact_file(project_path: Path, artifact_path: str) -> dict[str, Any]:
    requested = Path(artifact_path).expanduser()
    resolved = (project_path / requested).resolve() if not requested.is_absolute() else requested.resolve()

    project_root = project_path.resolve()
    if resolved != project_root and project_root not in resolved.parents:
        raise ValueError("Artifact path must stay inside the project directory")
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Artifact not found: {resolved}")

    size = resolved.stat().st_size
    if size > 2_000_000:
        raise ValueError("Artifact is too large to preview (max 2MB)")

    try:
        content = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = resolved.read_text(encoding="utf-8", errors="replace")

    return {
        "path": str(resolved),
        "size_bytes": size,
        "line_count": len(content.splitlines()),
        "content": content,
    }


def _project_path_from_payload(payload: dict[str, Any]) -> tuple[Path | None, str | None]:
    raw = payload.get("project_path")
    if not isinstance(raw, str) or not raw.strip():
        return None, "`project_path` is required"
    project_path = Path(raw).expanduser().resolve()
    if not project_path.exists() or not project_path.is_dir():
        return None, f"Project path does not exist or is not a directory: {project_path}"
    return project_path, None


def _safe_json_load(raw: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "Request body must be valid JSON"
    if not isinstance(payload, dict):
        return None, "Request JSON must be an object"
    return payload, None


def _studio_files() -> dict[str, bytes]:
    root = Path(__file__).resolve().parent / "web"
    assets: dict[str, bytes] = {
        "/": (root / "index.html").read_bytes(),
        "/index.html": (root / "index.html").read_bytes(),
        "/artifacts.html": (root / "artifacts.html").read_bytes(),
        "/openclaw.html": (root / "openclaw.html").read_bytes(),
        "/tutorial.html": (root / "tutorial.html").read_bytes(),
        "/app.js": (root / "app.js").read_bytes(),
        "/artifacts.js": (root / "artifacts.js").read_bytes(),
        "/openclaw.js": (root / "openclaw.js").read_bytes(),
        "/tutorial.js": (root / "tutorial.js").read_bytes(),
        "/fluid.js": (root / "fluid.js").read_bytes(),
        "/styles.css": (root / "styles.css").read_bytes(),
    }
    return assets


def _content_type(path: str) -> str:
    if path in {"/", "/index.html", "/artifacts.html", "/openclaw.html", "/tutorial.html"}:
        return "text/html; charset=utf-8"
    if path.endswith(".js"):
        return "application/javascript; charset=utf-8"
    if path.endswith(".css"):
        return "text/css; charset=utf-8"
    guessed, _ = mimetypes.guess_type(path)
    if guessed:
        return guessed
    return "application/octet-stream"


def _openclaw_auth_error(handler: BaseHTTPRequestHandler, config: StudioConfig) -> tuple[bool, dict[str, Any]]:
    if not config.openclaw_enabled:
        return False, {"error": "OpenClaw bridge is disabled for this Studio session."}

    expected_key = (config.openclaw_api_key or "").strip()
    if expected_key:
        provided_key = handler.headers.get("X-OpenClaw-Key", "").strip()
        if provided_key != expected_key:
            return False, {"error": "Invalid or missing OpenClaw API key."}

    return True, {}


def _openclaw_execute(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action", "")).strip()
    if not action:
        raise ValueError("`action` is required for /api/openclaw/execute")

    if action == "audit":
        return {"action": action, "result": run_audit_flow(project_path)}
    if action == "roadmap":
        return {"action": action, "result": run_roadmap_flow(project_path)}
    if action == "coach":
        apply_safe = bool(payload.get("apply_safe", False))
        return {"action": action, "result": run_coach_flow(project_path, apply_safe=apply_safe)}
    if action == "agent-pack":
        return {"action": action, "result": run_agent_pack_flow(project_path)}
    if action == "ship":
        apply_safe = bool(payload.get("apply_safe", True))
        return {"action": action, "result": run_ship_flow(project_path, apply_safe=apply_safe)}

    raise ValueError(
        "Unsupported action. Valid actions: audit, roadmap, coach, agent-pack, ship."
    )


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(handler: BaseHTTPRequestHandler, status: int, body: bytes, content_type: str) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def create_handler(config: StudioConfig) -> type[BaseHTTPRequestHandler]:
    files = _studio_files()

    class StudioHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/openclaw/status":
                ok, error_payload = _openclaw_auth_error(self, config)
                if not ok:
                    status = (
                        HTTPStatus.UNAUTHORIZED
                        if config.openclaw_enabled and config.openclaw_api_key
                        else HTTPStatus.NOT_FOUND
                    )
                    _json_response(self, status, error_payload)
                    return
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {
                        "bridge": "openclaw",
                        "enabled": True,
                        "requires_api_key": bool(config.openclaw_api_key),
                        "actions": ["audit", "roadmap", "coach", "agent-pack", "ship"],
                        "endpoints": {
                            "execute": "/api/openclaw/execute",
                            "artifact": "/api/openclaw/artifact",
                        },
                    },
                )
                return
            if path in files:
                _text_response(self, HTTPStatus.OK, files[path], _content_type(path))
                return
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            payload, parse_error = _safe_json_load(raw)
            if parse_error:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": parse_error})
                return

            assert payload is not None

            try:
                if path == "/api/openclaw/execute":
                    ok, error_payload = _openclaw_auth_error(self, config)
                    if not ok:
                        status = (
                            HTTPStatus.UNAUTHORIZED
                            if config.openclaw_enabled and config.openclaw_api_key
                            else HTTPStatus.NOT_FOUND
                        )
                        _json_response(self, status, error_payload)
                        return
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    assert project_path is not None
                    result = _openclaw_execute(project_path, payload)
                elif path == "/api/openclaw/artifact":
                    ok, error_payload = _openclaw_auth_error(self, config)
                    if not ok:
                        status = (
                            HTTPStatus.UNAUTHORIZED
                            if config.openclaw_enabled and config.openclaw_api_key
                            else HTTPStatus.NOT_FOUND
                        )
                        _json_response(self, status, error_payload)
                        return
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    artifact_path = payload.get("artifact_path")
                    if not isinstance(artifact_path, str) or not artifact_path.strip():
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "`artifact_path` is required"})
                        return
                    assert project_path is not None
                    result = {
                        "artifact": read_artifact_file(project_path, artifact_path),
                        "project_path": str(project_path),
                    }
                elif path == "/api/audit":
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    assert project_path is not None
                    result = run_audit_flow(project_path)
                elif path == "/api/roadmap":
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    assert project_path is not None
                    result = run_roadmap_flow(project_path)
                elif path == "/api/coach":
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    assert project_path is not None
                    apply_safe = bool(payload.get("apply_safe", False))
                    result = run_coach_flow(project_path, apply_safe=apply_safe)
                elif path == "/api/agent-pack":
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    assert project_path is not None
                    result = run_agent_pack_flow(project_path)
                elif path == "/api/ship":
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    assert project_path is not None
                    result = run_ship_flow(project_path, apply_safe=bool(payload.get("apply_safe", True)))
                elif path == "/api/artifact":
                    project_path, project_error = _project_path_from_payload(payload)
                    if project_error:
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": project_error})
                        return
                    artifact_path = payload.get("artifact_path")
                    if not isinstance(artifact_path, str) or not artifact_path.strip():
                        _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "`artifact_path` is required"})
                        return
                    assert project_path is not None
                    result = read_artifact_file(project_path, artifact_path)
                else:
                    _json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})
                    return
            except Exception as exc:  # noqa: BLE001
                _json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return

            _json_response(self, HTTPStatus.OK, result)

    return StudioHandler


def launch_studio(config: StudioConfig) -> None:
    server = ThreadingHTTPServer((config.host, config.port), create_handler(config))
    url = f"http://{config.host}:{config.port}"
    print(f"Vibe Sentinel Studio running at {url}")
    if config.openclaw_enabled:
        print("OpenClaw bridge: enabled")
        print(f"OpenClaw status endpoint: {url}/api/openclaw/status")
        print(f"OpenClaw execute endpoint: {url}/api/openclaw/execute")
        if config.openclaw_api_key:
            print("OpenClaw key auth: required (send header X-OpenClaw-Key)")
        else:
            print("OpenClaw key auth: not required")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Studio...")
    finally:
        server.server_close()
