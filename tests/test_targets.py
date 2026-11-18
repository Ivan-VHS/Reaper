from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO

from reaper.cli import main
from reaper.targets import detect_target


class TargetInfoTests(unittest.TestCase):
    def test_e2k_target_is_reported_as_vliw_without_claiming_codegen(self) -> None:
        info = detect_target(
            system="Linux",
            machine="e2k",
            python_compiler="GCC 13.2.0",
        )
        self.assertEqual(info.architecture, "e2k")
        self.assertEqual(info.execution_model, "VLIW")
        self.assertEqual(info.interpreter_backend, "python-tree-walk")
        self.assertEqual(info.python_host_compiler, "GCC 13.2.0")
        self.assertFalse(info.native_codegen)
        self.assertTrue(any("not implemented" in note for note in info.notes))

    def test_elbrus_alias_is_normalized(self) -> None:
        info = detect_target(system="Linux", machine="Elbrus")
        self.assertEqual(info.architecture, "e2k")
        self.assertEqual(info.execution_model, "VLIW")

    def test_other_host_does_not_get_an_e2k_label(self) -> None:
        info = detect_target(system="Linux", machine="x86_64")
        self.assertEqual(info.architecture, "x86-64")
        self.assertEqual(info.execution_model, "not-inferred")
        self.assertFalse(info.native_codegen)

    def test_target_info_cli_is_json_and_needs_no_source_file(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            result = main(["--target-info"])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertIn("architecture", payload)
        self.assertEqual(payload["interpreter_backend"], "python-tree-walk")
        self.assertFalse(payload["native_codegen"])


if __name__ == "__main__":
    unittest.main()
