# Vibe Sentinel

Build fast. Ship credible.

`vibe-sentinel` is a Vibeathon-focused reliability layer for vibe-coded projects. It audits your repo, predicts judging readiness, and gives you a beginner-friendly fix path.

## Positioning

Most projects in vibe competitions optimize for generation speed. Vibe Sentinel optimizes for shipping confidence: clear docs, test coverage, CI proof, safe secrets handling, and demo readiness.

## Problem

Vibe-coded prototypes often look impressive but fail during evaluation because basics are missing:

- unclear onboarding
- no reproducible setup
- no automated checks
- weak submission artifacts

## Solution

Vibe Sentinel provides a clear loop:

1. Audit quality and submission readiness.
2. Turn findings into prioritized actions.
3. Generate agent-ready tasks and beginner coaching cards with exact next steps.

## Core Features

- Weighted audit across `usefulness`, `impact`, `execution`, and `innovation`.
- Secret leak detection for common API/token patterns.
- Template scaffolding for `SPEC.md`, `DEMO_SCRIPT.md`, `SUBMISSION.md`, and `UNIQUE_EDGE.md`.
- Prioritized roadmap generation from audit findings.
- **Beginner Fix Coach (`coach`)**
- **Killer App: Agent Sprint Pack (`agent-pack`)**
- **One-command shipping pipeline (`ship`)**
- **Visual Studio with artifact explorer and run history**
- **What-If Score Simulator with animated projected lift**
- **Milestone Tracker with celebration effects**
- **Demo Tour mode that auto-highlights the live storytelling flow**

## New Differentiating Feature: Beginner Fix Coach

`vibe-sentinel coach` converts technical findings into plain-English action cards.

Why this matters:

- Beginners get concrete "do this now" steps.
- Each finding includes why it matters and how to verify the fix.
- Optional `--apply-safe` mode creates missing starter files (tests, CI, and submission templates) without overwriting existing work.

## Killer App: Agent Sprint Pack

`vibe-sentinel agent-pack` transforms audit findings into a structured task queue for coding agents.

It generates:

- `.vibe-sentinel/agent_pack.md` with copy/paste master prompt + per-task agent prompts
- `.vibe-sentinel/agent_tasks.json` for machine-readable orchestration
- `.vibe-sentinel/agent_runbook.md` for operator workflow
- `.vibe-sentinel/prompts/*.txt` task-specific prompt files

Why this is instantly useful for agents:

- no manual triage step
- severity-ordered execution plan
- explicit file targets + verification commands
- ready prompts for autonomous coding sessions

## Installation

```bash
python -m pip install -e .
```

If your system Python is externally managed (PEP 668), use a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Quickstart

```bash
vibe-sentinel init
vibe-sentinel audit . --output-dir .vibe-sentinel
vibe-sentinel coach --report .vibe-sentinel/report.json --output .vibe-sentinel/coach.md --project .
```

## Commands

```bash
vibe-sentinel init
vibe-sentinel audit . --output-dir .vibe-sentinel
vibe-sentinel roadmap --report .vibe-sentinel/report.json --output .vibe-sentinel/roadmap.md
vibe-sentinel coach --report .vibe-sentinel/report.json --output .vibe-sentinel/coach.md --project .
vibe-sentinel agent-pack --report .vibe-sentinel/report.json --project . --output .vibe-sentinel/agent_pack.md --json-output .vibe-sentinel/agent_tasks.json
vibe-sentinel ship . --apply-safe
vibe-sentinel studio --host 127.0.0.1 --port 8765
vibe-sentinel studio --enable-openclaw --openclaw-key change-me
```

## Visual GUI: Studio

Launch the local visual interface:

```bash
vibe-sentinel studio
```

Then open `http://127.0.0.1:8765`.

Studio gives you:

- Animated score dashboard with category bars and quality bands
- Streamlined beginner controls: `Run Audit` and `Launch Ship Sequence` first
- In-app Beginner Tutorial with progress tracking and next-step guidance
- Advanced actions (`Agent Pack`, `Coach`, `Roadmap`) behind a toggle to reduce clutter
- Multi-page Studio navigation (`Dashboard` at `/index.html`, `Artifacts` at `/artifacts.html`, `OpenClaw` at `/openclaw.html`, `Tutorial` at `/tutorial.html`)
- Fluid motion design layer (spotlight, reveal-on-scroll, floating cards, animated gradients)
- What-If score simulation by toggling top fixes before coding
- Milestone unlock cards with animated celebration when score thresholds are crossed
- Demo Tour button for guided, auto-scrolling showcase during recording
- Artifact explorer with in-app preview loading
- Agent task queue table and run history timeline
- Safe-apply toggle for structured repo bootstrapping in ship runs
- Optional OpenClaw bridge endpoints: `GET /api/openclaw/status`, `POST /api/openclaw/execute`, `POST /api/openclaw/artifact`

## Submission-Ready Flow (Judge-Friendly)

Run this from a clean clone:

```bash
python -m pip install -e . && \
  vibe-sentinel init && \
  vibe-sentinel ship . --apply-safe
```

Expected output artifacts:

- `.vibe-sentinel/report.json`
- `.vibe-sentinel/report.md`
- `.vibe-sentinel/coach.md`
- `.vibe-sentinel/agent_pack.md`
- `.vibe-sentinel/agent_tasks.json`
- `.vibe-sentinel/agent_runbook.md`
- `.vibe-sentinel/prompts/*.txt`
- `.vibe-sentinel/roadmap.md`

## Video Demo Kit

Use these built-in assets to record a polished demo quickly:

- `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/VIDEO_DEMO_PLAN.md`
- `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/DEMO_SCRIPT.md`
- `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/BEGINNER_TUTORIAL.md`
- `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/CHATGPT_VIDEO_SETUP.md`
- `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/scripts/create_video_demo_repo.sh`
- `/Users/ben/Desktop/Ben's Agentic Projects/BridgeMind Hackathon/scripts/run_video_demo.sh`

Fastest launch command:

```bash
./scripts/run_video_demo.sh ./demo-repo-video 8765 --fresh
```

Use `--no-fresh` to keep the current demo repo state between takes.

## Example Console Output

```text
Projected Vibeathon score: 82.5/100
Category scores: usefulness 90.0, impact 80.0, execution 75.0, innovation 85.0
Findings: 1 fail, 2 warn
Top fixes:
- [high] Automated Tests: Add at least one smoke test and one behavior test before submission.
- [medium] Continuous Integration: Add a CI workflow that runs tests and basic linting on every push.
```

## Scoring Model

Category blend:

- 40% usefulness
- 25% impact
- 20% execution
- 15% innovation

## Project Structure

```text
vibe_sentinel/
  agent_pack.py
  checks.py
  cli.py
  coach.py
  gui.py
  report.py
  templates.py
tests/
  test_agent_pack.py
  test_checks.py
  test_cli.py
  test_coach.py
  test_gui.py
  test_gui_static.py
```

## Testing

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## License

MIT
