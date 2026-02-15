from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vibe_sentinel.gui import (
    _openclaw_execute,
    read_artifact_file,
    run_agent_pack_flow,
    run_agentic_cycle,
    run_audit_flow,
    run_coach_flow,
    run_roadmap_flow,
    run_ship_flow,
)


class GuiFlowTests(unittest.TestCase):
    def test_audit_flow_writes_report_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("## Problem\n## Installation\n## Usage\n```bash\nrun\n```", encoding="utf-8")

            payload = run_audit_flow(root)
            self.assertIn("report", payload)
            self.assertTrue(Path(payload["artifacts"]["report_json"]).exists())
            self.assertTrue(Path(payload["artifacts"]["report_markdown"]).exists())

    def test_agentic_cycle_applies_safe_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Tiny demo", encoding="utf-8")

            payload = run_agentic_cycle(root)
            self.assertIn("before", payload)
            self.assertIn("after", payload)
            self.assertIn("improvement", payload)
            self.assertTrue(Path(payload["artifacts"]["coach_markdown"]).exists())

            # At least one safe baseline should be applied on incomplete projects.
            self.assertGreaterEqual(len(payload["applied_files"]), 1)
            self.assertIn("agent_tasks_json", payload["artifacts"])
            self.assertIn("agent_runbook_markdown", payload["artifacts"])

    def test_coach_and_roadmap_flows_return_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Tiny demo", encoding="utf-8")

            coach = run_coach_flow(root, apply_safe=False)
            roadmap = run_roadmap_flow(root)
            pack = run_agent_pack_flow(root)

            self.assertIn("coach_markdown", coach)
            self.assertIn("roadmap_markdown", roadmap)
            self.assertIn("agent_pack_markdown", pack)
            self.assertIn("agent_tasks", pack)
            self.assertTrue(coach["coach_markdown"].startswith("#"))
            self.assertTrue(roadmap["roadmap_markdown"].startswith("#"))
            self.assertTrue(pack["agent_pack_markdown"].startswith("#"))

    def test_ship_flow_returns_before_and_after(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Tiny demo", encoding="utf-8")

            payload = run_ship_flow(root, apply_safe=True)
            self.assertIn("before", payload)
            self.assertIn("after", payload)
            self.assertIn("before_insights", payload)
            self.assertIn("after_insights", payload)

    def test_read_artifact_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / ".vibe-sentinel" / "sample.md"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("# Sample\nBody\n", encoding="utf-8")

            payload = read_artifact_file(root, str(artifact))
            self.assertEqual(payload["line_count"], 2)
            self.assertIn("# Sample", payload["content"])

    def test_openclaw_execute_supports_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Tiny demo", encoding="utf-8")

            payload = _openclaw_execute(root, {"action": "audit"})
            self.assertEqual(payload["action"], "audit")
            self.assertIn("result", payload)
            self.assertIn("report", payload["result"])


if __name__ == "__main__":
    unittest.main()
