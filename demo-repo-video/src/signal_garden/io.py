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
