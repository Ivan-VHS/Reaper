from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from reaper.cli import main
from reaper.native_compiler import NativeToolchainError, find_c_compiler


class NativeCompilerCliTests(unittest.TestCase):
    def test_emit_c_writes_source_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reaper-native-cli-") as folder:
            source = Path(folder) / "program.rpr"
            c_file = Path(folder) / "program.c"
            source.write_text("emit 2 + 3\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main([str(source), "--emit-c", str(c_file)])
            self.assertEqual(result, 0, output.getvalue())
            self.assertIn("int main(void)", c_file.read_text(encoding="utf-8"))

    def test_native_flag_builds_executable(self) -> None:
        try:
            find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")
        with tempfile.TemporaryDirectory(prefix="reaper-native-cli-") as folder:
            source = Path(folder) / "program.rpr"
            executable = Path(folder) / ("program.exe" if os.name == "nt" else "program")
            source.write_text("emit 2 + 3\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main([str(source), "--native", str(executable)])
            self.assertEqual(result, 0, output.getvalue())
            run = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout, "5\n")


if __name__ == "__main__":
    unittest.main()
