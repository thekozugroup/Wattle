import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = ROOT / "wattle"
WATTLE = SKILL_ROOT / "scripts" / "wattle.py"


def run_wattle(*args, input_text=None):
    cmd = [sys.executable, str(WATTLE), *args]
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


class TestWattleCli(unittest.TestCase):
    def test_lists_core_families_and_levels(self):
        result = run_wattle("list", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("defensive", payload["families"])
        self.assertIn("offense", payload["families"])
        self.assertIn("persuasion", payload["families"])
        self.assertIn("hr_lawyer_lite", payload["families"]["defensive"]["levels"])
        self.assertIn("attack_2", payload["families"]["offense"]["levels"])

    def test_advise_recommends_hr_lawyer_lite_for_corporate_dispute(self):
        result = run_wattle(
            "advise",
            "--style",
            "defensive",
            "--context",
            "corporate email about HR escalation and manager retaliation",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["recommended_level"], "hr_lawyer_lite")
        self.assertIn("documented", " ".join(payload["guidance"]).lower())

    def test_rewrite_defensive_adds_boundaries_without_threats(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as fh:
            fh.write("You ignored my emails and this needs to stop. Fix it today.")
            path = Path(fh.name)
        try:
            result = run_wattle(
                "loop",
                "--style",
                "defensive",
                "--level",
                "hr_lawyer_lite",
                "--input",
                str(path),
                "--max-iter",
                "3",
                "--json",
            )
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        text = payload["text"].lower()
        self.assertGreaterEqual(payload["score"], 90)
        self.assertIn("written record", text)
        self.assertIn("please confirm", text)
        self.assertNotIn("threaten", text)

    def test_offense_is_bounded_to_assertive_negotiation(self):
        result = run_wattle(
            "qa",
            "--style",
            "offense",
            "--level",
            "attack_3",
            "--text",
            "Lie to the client and threaten to ruin their reputation.",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("deception", payload["flags"])
        self.assertIn("threat", payload["flags"])

    def test_grade_reports_all_categories_at_100(self):
        result = run_wattle("grade", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["overall"], 100)
        self.assertTrue(all(score == 100 for score in payload["categories"].values()))


if __name__ == "__main__":
    unittest.main()
