from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vibe_sentinel.agent_pack import build_agent_tasks, write_agent_pack


class AgentPackTests(unittest.TestCase):
    def test_build_agent_tasks_from_open_findings(self) -> None:
        payload = {
            "scorecard": {"overall": 64.0},
            "checks": [
                {
                    "check_id": "tests_present",
                    "title": "Automated Tests",
                    "status": "fail",
                    "severity": "high",
                    "detail": "No tests detected.",
                    "recommendation": "Add tests.",
                },
                {
                    "check_id": "ci_present",
                    "title": "Continuous Integration",
                    "status": "warn",
                    "severity": "medium",
                    "detail": "No CI.",
                    "recommendation": "Add CI.",
                },
                {
                    "check_id": "problem_statement",
                    "title": "Problem Statement",
                    "status": "pass",
                    "severity": "low",
                    "detail": "ok",
                    "recommendation": "n/a",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tasks = build_agent_tasks(payload, Path(tmp))
            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0]["check_id"], "tests_present")
            self.assertIn("agent_prompt", tasks[0])
            self.assertIn("verification_commands", tasks[0])

    def test_write_agent_pack_outputs_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "report.json"
            pack_path = root / "agent_pack.md"
            tasks_path = root / "agent_tasks.json"
            runbook_path = root / "agent_runbook.md"
            prompts_dir = root / "prompts"

            report_payload = {
                "scorecard": {"overall": 50.0},
                "checks": [
                    {
                        "check_id": "secret_scan",
                        "title": "Secret Leak Scan",
                        "status": "fail",
                        "severity": "high",
                        "detail": "Potential secret detected.",
                        "recommendation": "Remove hard-coded secrets.",
                    }
                ],
            }
            report_path.write_text(json.dumps(report_payload), encoding="utf-8")

            _, _, runbook_written, count, tasks = write_agent_pack(
                report_json_path=report_path,
                output_markdown_path=pack_path,
                output_json_path=tasks_path,
                project_path=root,
                runbook_path=runbook_path,
                prompts_dir=prompts_dir,
            )

            self.assertEqual(count, 1)
            self.assertTrue(pack_path.exists())
            self.assertTrue(tasks_path.exists())
            self.assertTrue(runbook_written.exists())
            self.assertIn("Master Prompt", pack_path.read_text(encoding="utf-8"))
            tasks_payload = json.loads(tasks_path.read_text(encoding="utf-8"))
            self.assertEqual(len(tasks_payload["tasks"]), 1)
            self.assertEqual(len(tasks), 1)
            prompt_file = Path(tasks[0]["prompt_file"])
            self.assertTrue(prompt_file.exists())


if __name__ == "__main__":
    unittest.main()
