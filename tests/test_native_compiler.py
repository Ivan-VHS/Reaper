from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from reaper.native_compiler import (
    NativeCompileError,
    NativeToolchainError,
    build_executable,
    compile_source,
    find_c_compiler,
)


PROGRAM = '''\
make seed := 5
vary total := 0
craft add(a, b) {
    yield a + b
}
change total := add(seed, 7)
when total > 10 {
    emit total
} otherwise {
    emit 0
}
loop while total > 10 {
    change total := total - 1
}
emit total
emit "native ✓"
'''


class NativeCompilerTests(unittest.TestCase):
    def test_emits_deterministic_c17(self) -> None:
        first = compile_source(PROGRAM, "native.rpr")
        second = compile_source(PROGRAM, "native.rpr")
        self.assertEqual(first, second)
        self.assertIn("#include <inttypes.h>", first)
        self.assertIn("static int64_t rpr_fn_0", first)
        self.assertIn("rpr_add(", first)
        self.assertIn("rpr_tick()", first)

    def test_compiles_and_runs_native_executable(self) -> None:
        try:
            compiler = find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")
        with tempfile.TemporaryDirectory(prefix="reaper-native-test-") as folder:
            executable = build_executable(PROGRAM, Path(folder) / ("sample.exe" if os.name == "nt" else "sample"), filename="native.rpr", compiler=compiler)
            result = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "12\n10\nnative ✓\n")

    def test_rejects_unknown_names_and_immutable_assignment(self) -> None:
        with self.assertRaisesRegex(NativeCompileError, "unknown name 'missing'"):
            compile_source("emit missing\n", "bad-name.rpr")
        with self.assertRaisesRegex(NativeCompileError, "cannot be changed"):
            compile_source("make fixed := 1\nchange fixed := 2\n", "immutable.rpr")

    def test_rejects_effects_inside_native_functions(self) -> None:
        with self.assertRaisesRegex(NativeCompileError, "cannot emit output"):
            compile_source("craft noisy() { emit 1\n yield 0\n}\n", "effect.rpr")
        with self.assertRaisesRegex(NativeCompileError, "cannot mutate global bindings"):
            compile_source("vary count := 0\ncraft change_count() { change count := 1\n yield count\n}\n", "global-write.rpr")

    def test_rejects_unsupported_dynamic_features_explicitly(self) -> None:
        with self.assertRaisesRegex(NativeCompileError, "outside the native scalar subset"):
            compile_source("emit [1, 2, 3]\n", "list.rpr")

    def test_native_output_cannot_overwrite_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reaper-native-path-") as folder:
            source = Path(folder) / "program.rpr"
            source.write_text(PROGRAM, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                build_executable(PROGRAM, source, filename=str(source))

    def test_floor_division_and_modulo_match_language_semantics(self) -> None:
        try:
            compiler = find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")
        source = "emit -7 // 3\nemit -7 % 3\nemit 7 // -3\nemit 7 % -3\n"
        with tempfile.TemporaryDirectory(prefix="reaper-native-division-") as folder:
            executable = build_executable(source, Path(folder) / "division", filename="division.rpr", compiler=compiler)
            result = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "-3\n2\n-3\n-2\n")

    def test_minimum_signed_integer_literal_is_supported(self) -> None:
        try:
            compiler = find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")
        with tempfile.TemporaryDirectory(prefix="reaper-native-min-i64-") as folder:
            executable = build_executable("emit -9223372036854775808\n", Path(folder) / "minimum", filename="minimum.rpr", compiler=compiler)
            result = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "-9223372036854775808\n")

    def test_overflow_is_reported_at_runtime(self) -> None:
        try:
            compiler = find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")
        source = "emit 9223372036854775807 + 1\n"
        with tempfile.TemporaryDirectory(prefix="reaper-native-overflow-") as folder:
            executable = build_executable(source, Path(folder) / "overflow", filename="overflow.rpr", compiler=compiler)
            result = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("signed integer overflow", result.stderr)


if __name__ == "__main__":
    unittest.main()
