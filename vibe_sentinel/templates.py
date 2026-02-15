from __future__ import annotations

from pathlib import Path

FILES: dict[str, str] = {
    "SPEC.md": """# Product Spec\n\n## Problem\nDescribe the pain point for vibe coders in one paragraph.\n\n## Target User\nWho has this pain and how often does it happen?\n\n## Success Metrics\n- Metric 1\n- Metric 2\n\n## Constraints\n- Time\n- Security/privacy\n- Platform\n\n## Acceptance Criteria\n- [ ] Criterion 1\n- [ ] Criterion 2\n\n## Non-Goals\nWhat this project intentionally does not do.\n""",
    "DEMO_SCRIPT.md": """# 3-5 Minute Demo Script\n\n## 0:00 - 0:30 Hook\nState the problem and why current approaches fail.\n\n## 0:30 - 1:30 Product Intro\nShow what makes your solution unique.\n\n## 1:30 - 3:30 Live Workflow\nWalk through a realistic scenario end-to-end.\n\n## 3:30 - 4:30 Reliability and Safety\nHighlight tests, safeguards, and quality controls.\n\n## 4:30 - 5:00 Outcome\nClose with measurable value and who should use it first.\n""",
    "SUBMISSION.md": """# Vibeathon Submission Metadata\n\n- Discord username: \n- GitHub profile link: \n- GitHub repo link: \n- Demo video link (YouTube or Loom): \n\n## One-line Pitch\n\n## Why this is useful\n\n## Why this is different\n""",
    "UNIQUE_EDGE.md": """# Unique Edge\n\n## Existing approaches\nList common alternatives and their tradeoffs.\n\n## What we do differently\nDescribe your non-obvious differentiation.\n\n## Why this matters\nTie differentiation to measurable user outcomes.\n""",
}


def scaffold(output_dir: Path, force: bool = False) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for filename, content in FILES.items():
        destination = output_dir / filename
        if destination.exists() and not force:
            continue
        destination.write_text(content.strip() + "\n", encoding="utf-8")
        written.append(destination)

    return written
