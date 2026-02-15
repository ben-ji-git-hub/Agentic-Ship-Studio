from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vibe_sentinel.coach import write_coach


class CoachTests(unittest.TestCase):
    def test_write_coach_generates_action_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "report.json"
            coach_path = root / "coach.md"

            payload = {
                "scorecard": {"overall": 61.5},
                "checks": [
                    {
                        "check_id": "tests_present",
                        "title": "Automated Tests",
                        "status": "fail",
                        "severity": "high",
                        "category": "execution",
                        "recommendation": "Add tests.",
                    },
                    {
                        "check_id": "ci_present",
                        "title": "Continuous Integration",
                        "status": "warn",
                        "severity": "medium",
                        "category": "execution",
                        "recommendation": "Add CI.",
                    },
                ],
            }
            report_path.write_text(json.dumps(payload), encoding="utf-8")

            output_path, applied = write_coach(report_path, coach_path, root, apply_safe=False)
            self.assertEqual(output_path, coach_path)
            self.assertEqual(applied, [])

            content = coach_path.read_text(encoding="utf-8")
            self.assertIn("Beginner Fix Coach", content)
            self.assertIn("Automated Tests", content)
            self.assertIn("Continuous Integration", content)

    def test_apply_safe_creates_missing_baselines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "report.json"
            coach_path = root / "coach.md"

            payload = {
                "scorecard": {"overall": 40.0},
                "checks": [
                    {
                        "check_id": "tests_present",
                        "title": "Automated Tests",
                        "status": "fail",
                        "severity": "high",
                        "category": "execution",
                        "recommendation": "Add tests.",
                    },
                    {
                        "check_id": "ci_present",
                        "title": "Continuous Integration",
                        "status": "warn",
                        "severity": "medium",
                        "category": "execution",
                        "recommendation": "Add CI.",
                    },
                    {
                        "check_id": "submission_template",
                        "title": "Submission Metadata",
                        "status": "warn",
                        "severity": "medium",
                        "category": "impact",
                        "recommendation": "Add submission file.",
                    },
                ],
            }
            report_path.write_text(json.dumps(payload), encoding="utf-8")

            _, applied = write_coach(report_path, coach_path, root, apply_safe=True)

            applied_set = {path.relative_to(root).as_posix() for path in applied}
            self.assertIn("tests/test_smoke.py", applied_set)
            self.assertIn(".github/workflows/ci.yml", applied_set)
            self.assertIn("SUBMISSION.md", applied_set)
            self.assertTrue((root / "tests" / "test_smoke.py").exists())
            self.assertTrue((root / ".github" / "workflows" / "ci.yml").exists())
            self.assertTrue((root / "SUBMISSION.md").exists())


if __name__ == "__main__":
    unittest.main()
