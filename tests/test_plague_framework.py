from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter


class PlagueFoundationTests(unittest.TestCase):
    def test_reaper_policy_and_component_registry_smoke(self) -> None:
        program = Path(__file__).resolve().parents[1] / "plague" / "examples" / "policy_smoke.rpr"
        output: list[str] = []
        Interpreter(output=output.append).run(
            program.read_text(encoding="utf-8"),
            str(program),
        )
        self.assertIn("PASS default mode is observe", output)
        self.assertIn("PASS registry contains ten components", output)
        self.assertIn("PASS merge is denied", output)


if __name__ == "__main__":
    unittest.main()
