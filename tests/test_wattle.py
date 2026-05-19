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

    def test_full_grade_runs_15_critique_waves_at_100(self):
        result = run_wattle("grade", "--full", "--waves", "15", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["overall"], 100)
        self.assertEqual(len(payload["waves"]), 15)
        for wave in payload["waves"]:
            self.assertEqual(wave["overall"], 100)
            self.assertTrue(all(score == 100 for score in wave["categories"].values()))
            self.assertIn("critique", wave)

    def test_critique_reports_gaps_and_next_action(self):
        result = run_wattle(
            "critique",
            "--style",
            "persuasion",
            "--level",
            "executive",
            "--text",
            "Please buy this because it is good.",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertLess(payload["score"], 90)
        self.assertIn("missing_markers", payload)
        self.assertEqual(payload["next_action"], "rewrite")

    def test_legal_advice_overclaim_is_flagged(self):
        result = run_wattle(
            "qa",
            "--style",
            "defensive",
            "--level",
            "legalese",
            "--text",
            "This is guaranteed legal and you cannot lose in court.",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertIn("legal_advice", payload["flags"])

    def test_coercive_regulatory_or_press_leverage_is_flagged(self):
        result = run_wattle(
            "qa",
            "--style",
            "offense",
            "--level",
            "attack_2",
            "--text",
            "Pay by Friday or I will report you to regulators and the press.",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertIn("coercion", payload["flags"])

    def test_legalese_rewrite_flags_admissions_for_counsel_review(self):
        result = run_wattle(
            "loop",
            "--style",
            "defensive",
            "--level",
            "legalese",
            "--text",
            "I admit I breached the contract and owe damages.",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("admission", payload["flags"])
        self.assertEqual(payload["stop_reason"], "safety_flags")

    def test_help_exposes_advertised_commands(self):
        result = run_wattle("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("critique", result.stdout)
        self.assertIn("grade", result.stdout)

    def test_invalid_style_fails_cleanly(self):
        result = run_wattle("advise", "--style", "unknown", "--context", "test")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown style", result.stderr)

    def test_rewrite_preserves_dates_money_urls_and_quotes(self):
        draft = 'Acme owes $12,500 by May 19. See https://example.com. They said "approved".'
        result = run_wattle(
            "loop",
            "--style",
            "defensive",
            "--level",
            "hr_lawyer_lite",
            "--text",
            draft,
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        text = payload["text"]
        self.assertIn("$12,500", text)
        self.assertIn("May 19", text)
        self.assertIn("https://example.com", text)
        self.assertIn('"approved"', text)


if __name__ == "__main__":
    unittest.main()
