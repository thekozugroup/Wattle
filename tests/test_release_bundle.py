import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "scripts" / "build_skill_bundle.py"
BUNDLE = ROOT / "dist" / "Wattle.skill"


class TestReleaseBundle(unittest.TestCase):
    def test_bundle_builds_single_skill_file(self):
        result = subprocess.run(
            [sys.executable, str(BUILD)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(BUNDLE.exists())
        self.assertGreater(BUNDLE.stat().st_size, 1000)
        self.assertTrue(BUNDLE.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash"))

    def test_bundle_contains_installable_payload_only(self):
        if not BUNDLE.exists():
            subprocess.run([sys.executable, str(BUILD)], cwd=ROOT, check=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(BUNDLE), "--extract", tmp],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            extracted = Path(tmp) / "wattle"
            self.assertTrue((extracted / "SKILL.md").exists())
            self.assertTrue((extracted / "agents" / "openai.yaml").exists())
            self.assertTrue((extracted / "scripts" / "wattle.py").exists())
            self.assertTrue((extracted / "references" / "rubric.md").exists())
            self.assertFalse((extracted / "README.md").exists())
            self.assertFalse(any("__pycache__" in str(path) for path in extracted.rglob("*")))


if __name__ == "__main__":
    unittest.main()
