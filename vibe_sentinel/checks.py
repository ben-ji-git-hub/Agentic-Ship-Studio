from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from vibe_sentinel.models import CheckResult, CheckSpec, ScoreCard

CHECK_SPECS: tuple[CheckSpec, ...] = (
    CheckSpec("problem_statement", "Problem Statement", "usefulness", 12),
    CheckSpec("quickstart", "Quickstart Instructions", "usefulness", 14),
    CheckSpec("usage_examples", "Usage Examples", "usefulness", 14),
    CheckSpec("tests_present", "Automated Tests", "execution", 12),
    CheckSpec("ci_present", "Continuous Integration", "execution", 10),
    CheckSpec("dependency_lock", "Dependency Reproducibility", "execution", 8),
    CheckSpec("demo_script", "3-5 Minute Demo Script", "execution", 10),
    CheckSpec("secret_scan", "Secret Leak Scan", "impact", 12),
    CheckSpec("license_present", "Open-Source License", "impact", 8),
    CheckSpec("submission_template", "Submission Metadata", "impact", 5),
    CheckSpec("innovation_statement", "Innovation Positioning", "innovation", 10),
    CheckSpec("novelty_artifact", "Differentiation Artifact", "innovation", 5),
)

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".env",
    ".sh",
}

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
}

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
)


@dataclass(slots=True)
class AuditContext:
    root: Path
    files: set[str]
    readme_text: str

    def exists(self, relative_path: str) -> bool:
        return relative_path in self.files

    def find_glob(self, pattern: str) -> list[str]:
        matched: list[str] = []
        for candidate in self.files:
            if Path(candidate).match(pattern):
                matched.append(candidate)
        return sorted(matched)


def _collect_files(root: Path) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        files.add(rel)
    return files


def _read_text_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        if path.stat().st_size > 1_000_000:
            return ""
    except OSError:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def build_context(root: Path) -> AuditContext:
    files = _collect_files(root)
    readme_path = root / "README.md"
    readme_text = _read_text_file(readme_path)
    return AuditContext(root=root, files=files, readme_text=readme_text)


def _check_problem_statement(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    if not ctx.readme_text:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "fail",
            "high",
            "README.md is missing.",
            "Create README.md with a clear problem statement and target user.",
        )
    lowered = ctx.readme_text.lower()
    keywords = ["problem", "pain", "challenge", "target user", "who this is for"]
    if any(keyword in lowered for keyword in keywords):
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Problem framing detected in README.md.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "README.md exists but does not clearly state the problem or target user.",
        "Add a concise 'Problem' section explaining pain points and intended users.",
    )


def _check_quickstart(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    if not ctx.readme_text:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "fail",
            "high",
            "Cannot find quickstart content because README.md is missing.",
            "Add README.md with installation and first-run steps.",
        )
    lowered = ctx.readme_text.lower()
    has_install = "install" in lowered or "setup" in lowered
    has_run = "usage" in lowered or "quickstart" in lowered or "getting started" in lowered
    if has_install and has_run:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Installation and run instructions were detected in README.md.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "README.md lacks full quickstart guidance (install + run).",
        "Add a copy-paste quickstart block that installs and runs the project in under 2 minutes.",
    )


def _check_usage_examples(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    if not ctx.readme_text:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "fail",
            "high",
            "README.md is missing, so usage examples cannot be verified.",
            "Add at least one command example and expected output in README.md.",
        )
    lowered = ctx.readme_text.lower()
    has_example_label = "example" in lowered or "usage" in lowered
    has_code_block = "```" in ctx.readme_text
    if has_example_label and has_code_block:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "README.md includes usage examples with code blocks.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "Usage examples are weak or missing in README.md.",
        "Add a minimal input/output example that new users can immediately test.",
    )


def _check_tests_present(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    test_candidates = [
        path
        for path in ctx.files
        if path.startswith("tests/")
        or path.endswith("_test.py")
        or path.endswith(".test.ts")
        or path.endswith(".test.js")
        or path.endswith(".spec.ts")
        or path.endswith(".spec.js")
    ]
    if test_candidates:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            f"Detected {len(test_candidates)} test file(s).",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "fail",
        "high",
        "No automated tests were detected.",
        "Add at least one smoke test and one behavior test before submission.",
    )


def _check_ci_present(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    workflows = [
        path
        for path in ctx.files
        if path.startswith(".github/workflows/") and (path.endswith(".yml") or path.endswith(".yaml"))
    ]
    if workflows:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Found CI workflow(s) in .github/workflows.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "No CI workflow detected.",
        "Add a CI workflow that runs tests and basic linting on every push.",
    )


def _requirements_are_pinned(content: str) -> bool:
    dependencies = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    if not dependencies:
        return False
    for dep in dependencies:
        if dep.startswith("-e "):
            continue
        if "==" not in dep and "@" not in dep:
            return False
    return True


def _check_dependency_lock(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    lockfiles = {
        "poetry.lock",
        "Pipfile.lock",
        "requirements.lock",
        "uv.lock",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lockb",
    }
    if any(lockfile in ctx.files for lockfile in lockfiles):
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Dependency lockfile detected.",
            "No action required.",
        )
    req_path = ctx.root / "requirements.txt"
    req_content = _read_text_file(req_path)
    if req_content and _requirements_are_pinned(req_content):
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "requirements.txt appears version-pinned.",
            "No action required.",
        )
    pyproject = _read_text_file(ctx.root / "pyproject.toml")
    if pyproject:
        lowered = pyproject.lower()
        if "[project]" in lowered and "dependencies" not in lowered:
            return CheckResult(
                spec.check_id,
                spec.title,
                spec.category,
                spec.weight,
                "pass",
                "low",
                "No runtime dependencies declared in pyproject.toml.",
                "No action required.",
            )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "No lockfile or fully pinned dependency list found.",
        "Add a lockfile (preferred) or pin dependency versions in requirements.txt.",
    )


def _check_demo_script(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    candidates = ["DEMO_SCRIPT.md", "docs/DEMO_SCRIPT.md", ".vibe-sentinel/DEMO_SCRIPT.md"]
    for relative in candidates:
        if relative in ctx.files:
            content = _read_text_file(ctx.root / relative)
            words = len(content.split())
            if 300 <= words <= 900:
                return CheckResult(
                    spec.check_id,
                    spec.title,
                    spec.category,
                    spec.weight,
                    "pass",
                    "low",
                    f"Demo script found at {relative} ({words} words).",
                    "No action required.",
                )
            return CheckResult(
                spec.check_id,
                spec.title,
                spec.category,
                spec.weight,
                "warn",
                "low",
                f"Demo script found at {relative} but length is {words} words.",
                "Aim for a 3-5 minute script (~300-900 words) with clear beats.",
            )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "fail",
        "medium",
        "No demo script file detected.",
        "Add DEMO_SCRIPT.md that walks through the product in 3-5 minutes.",
    )


def _scan_for_secrets(ctx: AuditContext) -> list[str]:
    hits: list[str] = []
    for rel_path in sorted(ctx.files):
        # Test fixtures often contain fake keys. Prioritize source and config paths.
        if rel_path.startswith("tests/") or rel_path.startswith("docs/"):
            continue
        suffix = Path(rel_path).suffix.lower()
        if suffix not in TEXT_SUFFIXES and Path(rel_path).name not in {".env", ".env.local"}:
            continue
        content = _read_text_file(ctx.root / rel_path)
        if not content:
            continue
        if "vibe-sentinel: allow-secret" in content:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                hits.append(rel_path)
                break
    return hits


def _check_secret_scan(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    hits = _scan_for_secrets(ctx)
    if hits:
        listed = ", ".join(hits[:3])
        more = "" if len(hits) <= 3 else f" (+{len(hits) - 3} more)"
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "fail",
            "high",
            f"Potential secrets detected in: {listed}{more}.",
            "Remove hard-coded secrets and rotate any compromised credentials immediately.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "pass",
        "low",
        "No obvious secret patterns were detected in text files.",
        "No action required.",
    )


def _check_license_present(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    has_license = any(name in ctx.files for name in {"LICENSE", "LICENSE.md", "LICENSE.txt"})
    if has_license:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Open-source license file detected.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "fail",
        "medium",
        "No open-source license file detected.",
        "Add LICENSE (MIT/Apache-2.0/etc.) to clarify reuse permissions.",
    )


def _check_submission_template(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    candidates = ["SUBMISSION.md", ".vibe-sentinel/SUBMISSION.md"]
    for relative in candidates:
        if relative in ctx.files:
            content = _read_text_file(ctx.root / relative).lower()
            required = [
                "discord",
                "github profile",
                "github repo",
                "demo video",
            ]
            missing = [item for item in required if item not in content]
            if not missing:
                return CheckResult(
                    spec.check_id,
                    spec.title,
                    spec.category,
                    spec.weight,
                    "pass",
                    "low",
                    f"Submission metadata template detected at {relative}.",
                    "No action required.",
                )
            return CheckResult(
                spec.check_id,
                spec.title,
                spec.category,
                spec.weight,
                "warn",
                "low",
                f"{relative} is missing fields: {', '.join(missing)}.",
                "Add all required fields used by the Vibeathon submission form.",
            )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "No submission metadata file detected.",
        "Create SUBMISSION.md with Discord handle, profile URL, repo URL, and demo URL.",
    )


def _check_innovation_statement(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    if not ctx.readme_text:
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "fail",
            "medium",
            "README.md missing, so innovation positioning cannot be evaluated.",
            "Add README section explaining what makes this project different.",
        )
    lowered = ctx.readme_text.lower()
    markers = ["unique", "different", "innovation", "novel", "not another"]
    if any(marker in lowered for marker in markers):
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Differentiation language detected in README.md.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "medium",
        "README.md does not clearly explain how this differs from alternatives.",
        "Add a short section: 'Why this is different from other vibe tools'.",
    )


def _check_novelty_artifact(ctx: AuditContext, spec: CheckSpec) -> CheckResult:
    if any(name in ctx.files for name in {"UNIQUE_EDGE.md", "docs/ARCHITECTURE.md", "docs/DIFFERENTIATION.md"}):
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "Differentiation artifact file detected.",
            "No action required.",
        )
    if "## why this is different" in ctx.readme_text.lower():
        return CheckResult(
            spec.check_id,
            spec.title,
            spec.category,
            spec.weight,
            "pass",
            "low",
            "README includes a dedicated differentiation section.",
            "No action required.",
        )
    return CheckResult(
        spec.check_id,
        spec.title,
        spec.category,
        spec.weight,
        "warn",
        "low",
        "No dedicated differentiation artifact found.",
        "Add UNIQUE_EDGE.md or a deep-dive architecture/differentiation document.",
    )


def run_checks(root: Path) -> list[CheckResult]:
    ctx = build_context(root)
    checks = [
        _check_problem_statement(ctx, CHECK_SPECS[0]),
        _check_quickstart(ctx, CHECK_SPECS[1]),
        _check_usage_examples(ctx, CHECK_SPECS[2]),
        _check_tests_present(ctx, CHECK_SPECS[3]),
        _check_ci_present(ctx, CHECK_SPECS[4]),
        _check_dependency_lock(ctx, CHECK_SPECS[5]),
        _check_demo_script(ctx, CHECK_SPECS[6]),
        _check_secret_scan(ctx, CHECK_SPECS[7]),
        _check_license_present(ctx, CHECK_SPECS[8]),
        _check_submission_template(ctx, CHECK_SPECS[9]),
        _check_innovation_statement(ctx, CHECK_SPECS[10]),
        _check_novelty_artifact(ctx, CHECK_SPECS[11]),
    ]
    return checks


def compute_scorecard(checks: list[CheckResult]) -> ScoreCard:
    category_max: dict[str, float] = {"usefulness": 0.0, "impact": 0.0, "execution": 0.0, "innovation": 0.0}
    category_points: dict[str, float] = {"usefulness": 0.0, "impact": 0.0, "execution": 0.0, "innovation": 0.0}

    for check in checks:
        category_max[check.category] += check.weight
        category_points[check.category] += check.points()

    def percentage(category: str) -> float:
        max_points = category_max[category]
        if max_points <= 0:
            return 0.0
        return (category_points[category] / max_points) * 100.0

    usefulness = percentage("usefulness")
    impact = percentage("impact")
    execution = percentage("execution")
    innovation = percentage("innovation")
    overall = (usefulness * 0.40) + (impact * 0.25) + (execution * 0.20) + (innovation * 0.15)

    return ScoreCard(
        usefulness=usefulness,
        impact=impact,
        execution=execution,
        innovation=innovation,
        overall=overall,
    )
