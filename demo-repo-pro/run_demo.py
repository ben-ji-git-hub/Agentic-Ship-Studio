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
