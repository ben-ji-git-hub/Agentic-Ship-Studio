from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vibe_sentinel.checks import compute_scorecard, run_checks


class CheckEngineTests(unittest.TestCase):
    def test_happy_path_scores_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                """
                # Demo

                ## Problem
                We fix a real challenge for vibe coders.

                ## Installation
                pip install vibe-sentinel

                ## Usage
                ```bash
                vibe-sentinel audit .
                ```

                ## Why this is different
                This is unique and innovation-focused.
                """,
                encoding="utf-8",
            )
            (root / "LICENSE").write_text("MIT", encoding="utf-8")
            (root / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")
            (root / "DEMO_SCRIPT.md").write_text("word " * 350, encoding="utf-8")
            (root / "SUBMISSION.md").write_text(
                "Discord\nGitHub profile\nGitHub repo\nDemo video\n",
                encoding="utf-8",
            )
            (root / "UNIQUE_EDGE.md").write_text("Different", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

            checks = run_checks(root)
            score = compute_scorecard(checks)

            self.assertGreaterEqual(score.overall, 90)
            self.assertTrue(all(check.status == "pass" for check in checks))

    def test_secret_scan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("problem install usage example", encoding="utf-8")
            (root / "app.py").write_text('API_KEY="0123456789abcdef0123456789"\n', encoding="utf-8")

            checks = run_checks(root)
            secret_check = [check for check in checks if check.check_id == "secret_scan"][0]
            self.assertEqual(secret_check.status, "fail")
            self.assertEqual(secret_check.severity, "high")

    def test_secret_scan_ignores_test_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("problem install usage example", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "fixture.py").write_text(
                'API_KEY="0123456789abcdef0123456789"\n',
                encoding="utf-8",
            )

            checks = run_checks(root)
            secret_check = [check for check in checks if check.check_id == "secret_scan"][0]
            self.assertEqual(secret_check.status, "pass")

    def test_dependency_check_passes_for_no_runtime_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("problem install usage example", encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")

            checks = run_checks(root)
            dependency_check = [check for check in checks if check.check_id == "dependency_lock"][0]
            self.assertEqual(dependency_check.status, "pass")

    def test_scorecard_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checks = run_checks(root)
            score = compute_scorecard(checks)

            self.assertGreaterEqual(score.overall, 0)
            self.assertLessEqual(score.overall, 100)


if __name__ == "__main__":
    unittest.main()
