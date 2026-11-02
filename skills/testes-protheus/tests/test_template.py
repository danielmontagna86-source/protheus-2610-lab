"""Verifica que um template não exercitado não vira CI verde. author: daniel.montagna."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class TemplateTests(unittest.TestCase):
    def test_no_authorization_does_not_open_tir(self):
        env = dict(os.environ)
        for name in ("PROTHEUS_TEST_EXECUTION_AUTHORIZED", "PROTHEUS_CASE_CONFIG", "PROTHEUS_TIR_PRIVATE_CONFIG"):
            env.pop(name, None)
        script = Path(__file__).resolve().parents[1] / "assets" / "PROTHEUSTESTSUITE.py"
        result = subprocess.run([sys.executable, "-B", str(script)], env=env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertIn("skipped", result.stderr)


if __name__ == "__main__":
    unittest.main()
