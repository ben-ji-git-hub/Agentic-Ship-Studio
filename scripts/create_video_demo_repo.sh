#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-./demo-repo}"
FORCE="${2:-}"

if [ -d "$TARGET_DIR" ] && [ -n "$(ls -A "$TARGET_DIR" 2>/dev/null)" ] && [ "$FORCE" != "--force" ]; then
  echo "Error: target directory is not empty: $TARGET_DIR"
  echo "Use a new directory or pass --force as the second argument."
  exit 2
fi

mkdir -p "$TARGET_DIR"
if [ "$FORCE" = "--force" ]; then
  find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
fi
cd "$TARGET_DIR"

mkdir -p src/signal_garden docs config data scripts

cat > pyproject.toml <<'TOML'
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "signal-garden-demo"
version = "0.1.0"
description = "Prototype for focused planning with lightweight agent hints"
requires-python = ">=3.11"
TOML

cat > LICENSE <<'TXT'
MIT License

Copyright (c) 2026 Demo Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
TXT

cat > PRODUCT_BRIEF.md <<'MD'
# Signal Garden (Prototype Brief)

Signal Garden is a prototype that turns an unstructured list of tasks into a calm, focused day plan.

## Product idea

- Ingest a short JSON inbox
- Assign urgency + effort tags
- Build an ordered list of "focus blocks"

## Why this is a good demo target

- Realistic code structure (not toy single-file)
- Intentional quality gaps so Vibe Sentinel can improve score quickly
- Clear before/after story for a 3-5 minute video
MD

cat > docs/USER_STORY.md <<'MD'
# User Story Notes

Primary user: solo builder juggling roadmap, debugging, and customer follow-ups.

Pain: work sessions are fragmented and context switching burns momentum.

Desired outcome: a short morning routine that outputs a realistic sequence of tasks.
MD

cat > docs/ARCH_OVERVIEW.md <<'MD'
# Architecture Overview

The prototype has three parts:

1. Input parser for inbox JSON
2. Lightweight planner scoring function
3. Console renderer for the day's focus blocks
MD

cat > config/project.toml <<'TOML'
app_name = "Signal Garden"
timezone = "America/Los_Angeles"
max_focus_blocks = 5
TOML

cat > data/inbox.json <<'JSON'
[
  {
    "title": "Fix onboarding bug in settings screen",
    "impact": "high",
    "duration_minutes": 45
  },
  {
    "title": "Draft release note for v0.3",
    "impact": "medium",
    "duration_minutes": 25
  },
  {
    "title": "Respond to pilot user feedback",
    "impact": "high",
    "duration_minutes": 30
  },
  {
    "title": "Refactor stale utility module",
    "impact": "low",
    "duration_minutes": 40
  }
]
JSON

cat > src/signal_garden/__init__.py <<'PY'
"""Signal Garden demo package."""
PY

cat > src/signal_garden/engine.py <<'PY'
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
PY

cat > src/signal_garden/io.py <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from signal_garden.engine import Task


def load_tasks(path: Path) -> list[Task]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    tasks: list[Task] = []
    for item in raw:
        tasks.append(
            Task(
                title=str(item.get("title", "Untitled task")),
                impact=str(item.get("impact", "low")),
                duration_minutes=int(item.get("duration_minutes", 30)),
            )
        )
    return tasks
PY

cat > run_demo.py <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from signal_garden.engine import build_focus_plan
from signal_garden.io import load_tasks


def main() -> None:
    inbox_path = ROOT / "data" / "inbox.json"
    tasks = load_tasks(inbox_path)
    plan = build_focus_plan(tasks)

    print("Signal Garden Focus Plan")
    print("========================")
    for line in plan:
        print(line)


if __name__ == "__main__":
    main()
PY

cat > scripts/sample_run.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
python3 run_demo.py
SH
chmod +x scripts/sample_run.sh

cat > .env.example <<'TXT'
SIGNAL_GARDEN_PROFILE=<set-at-runtime>
TXT

cat > .gitignore <<'TXT'
__pycache__/
.venv/
.vibe-sentinel/
TXT

# Intentionally incomplete for a strong before/after audit demo:
# - no README.md
# - no tests/
# - no .github/workflows/ci.yml
# - no DEMO_SCRIPT.md
# - no SUBMISSION.md
# - no UNIQUE_EDGE.md

echo "Created polished demo repo at: $(pwd)"
echo ""
echo "Quick sanity run:"
echo "  python3 run_demo.py"
echo ""
echo "Video baseline command:"
echo "  vibe-sentinel audit . --output-dir .vibe-sentinel"
