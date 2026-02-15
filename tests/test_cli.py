from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vibe_sentinel.cli import build_parser, main


class CliTests(unittest.TestCase):
    def test_init_audit_and_roadmap_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            out = project / ".vibe-sentinel"

            init_exit = main(["init", "--output", str(out)])
            self.assertEqual(init_exit, 0)
            self.assertTrue((out / "SPEC.md").exists())

            # Minimal project files so audit can run deterministically.
            (project / "README.md").write_text(
                "## Problem\n## Installation\n## Usage\n```bash\nrun\n```\n## Why this is different\nunique",
                encoding="utf-8",
            )
            (project / "LICENSE").write_text("MIT", encoding="utf-8")
            (project / "requirements.txt").write_text("x==1.0\n", encoding="utf-8")
            (project / "DEMO_SCRIPT.md").write_text("word " * 320, encoding="utf-8")
            (project / "SUBMISSION.md").write_text(
                "discord\ngithub profile\ngithub repo\ndemo video\n",
                encoding="utf-8",
            )
            (project / "UNIQUE_EDGE.md").write_text("edge", encoding="utf-8")
            (project / "tests").mkdir()
            (project / "tests" / "test_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            (project / ".github" / "workflows").mkdir(parents=True)
            (project / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

            audit_exit = main(["audit", str(project), "--output-dir", str(out)])
            self.assertEqual(audit_exit, 0)
            report_json = out / "report.json"
            self.assertTrue(report_json.exists())

            payload = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertIn("scorecard", payload)

            roadmap_path = out / "roadmap.md"
            roadmap_exit = main(
                [
                    "roadmap",
                    "--report",
                    str(report_json),
                    "--output",
                    str(roadmap_path),
                ]
            )
            self.assertEqual(roadmap_exit, 0)
            self.assertTrue(roadmap_path.exists())

            coach_path = out / "coach.md"
            coach_exit = main(
                [
                    "coach",
                    "--report",
                    str(report_json),
                    "--output",
                    str(coach_path),
                    "--project",
                    str(project),
                ]
            )
            self.assertEqual(coach_exit, 0)
            self.assertTrue(coach_path.exists())

            pack_path = out / "agent_pack.md"
            pack_tasks_path = out / "agent_tasks.json"
            pack_runbook_path = out / "agent_runbook.md"
            pack_prompts_path = out / "prompts"
            pack_exit = main(
                [
                    "agent-pack",
                    "--report",
                    str(report_json),
                    "--project",
                    str(project),
                    "--output",
                    str(pack_path),
                    "--json-output",
                    str(pack_tasks_path),
                    "--runbook-output",
                    str(pack_runbook_path),
                    "--prompts-dir",
                    str(pack_prompts_path),
                ]
            )
            self.assertEqual(pack_exit, 0)
            self.assertTrue(pack_path.exists())
            self.assertTrue(pack_tasks_path.exists())
            self.assertTrue(pack_runbook_path.exists())
            self.assertTrue(pack_prompts_path.exists())

    def test_studio_parser_accepts_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["studio", "--host", "127.0.0.1", "--port", "9876"])
        self.assertEqual(args.command, "studio")
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 9876)
        self.assertFalse(args.enable_openclaw)
        self.assertEqual(args.openclaw_key, "")

    def test_studio_parser_accepts_openclaw_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["studio", "--enable-openclaw", "--openclaw-key", "demo-key-123"]
        )
        self.assertEqual(args.command, "studio")
        self.assertTrue(args.enable_openclaw)
        self.assertEqual(args.openclaw_key, "demo-key-123")

    def test_ship_parser_accepts_apply_safe(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["ship", ".", "--apply-safe"])
        self.assertEqual(args.command, "ship")
        self.assertEqual(args.path, ".")
        self.assertTrue(args.apply_safe)


if __name__ == "__main__":
    unittest.main()
