from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter, ReaperRuntimeError
from reaper.fixed_width import fixed_integer_fits
from reaper.ir import lower
from reaper.native_compiler import (
    NativeToolchainError,
    build_executable,
    compile_source,
    find_c_compiler,
)
from reaper.parser import parse
from reaper.typecheck import check_source
from reaper.vm import assemble


U64_MAX = (1 << 64) - 1


class FixedWidthRuntimeTests(unittest.TestCase):
    def run_program(self, source: str, engine: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, "fixed-width.rpr", engine=engine)
        return output

    def test_fixed_width_bindings_run_in_treewalk_and_vm(self) -> None:
        source = f"""
        make low: u8 := 255
        make word: u32 := 4294967295
        make wide: u64 := {U64_MAX}
        make signed: i8 := -128
        emit low
        emit word
        emit wide
        emit signed
        """
        expected = ["255", "4294967295", str(U64_MAX), "-128"]
        self.assertEqual(self.run_program(source, "treewalk"), expected)
        self.assertEqual(self.run_program(source, "vm"), expected)

    def test_arithmetic_keeps_its_width_and_rejects_overflow(self) -> None:
        source = """
        make value: u8 := 254
        emit value + 1
        """
        expected = ["255"]
        self.assertEqual(self.run_program(source, "treewalk"), expected)
        self.assertEqual(self.run_program(source, "vm"), expected)

        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                with self.assertRaisesRegex(ReaperRuntimeError, "overflows u8"):
                    self.run_program("make value: u8 := 255\nemit value + 1", engine)

    def test_unsigned_underflow_and_signed_overflow_are_rejected(self) -> None:
        programs = (
            ("make value: u32 := 0\nemit value - 1", "underflows u32"),
            ("make value: i8 := 127\nemit value + 1", "overflows i8"),
            ("make value: i8 := -128\nemit -value", "overflows i8"),
            ("make value: u8 := 1\nemit -value", "not valid for u8"),
        )
        for source, message in programs:
            for engine in ("treewalk", "vm"):
                with self.subTest(engine=engine, source=source):
                    with self.assertRaisesRegex(ReaperRuntimeError, message):
                        self.run_program(source, engine)

    def test_change_cannot_store_an_out_of_range_literal(self) -> None:
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                with self.assertRaisesRegex(ReaperRuntimeError, "outside the u8 range"):
                    self.run_program("vary value: u8 := 1\nchange value := 256", engine)

    def test_real_division_remains_real_for_fixed_width_inputs(self) -> None:
        source = "make value: u32 := 9\nemit value / 2"
        self.assertEqual(self.run_program(source, "treewalk"), ["4.5"])
        self.assertEqual(self.run_program(source, "vm"), ["4.5"])
 
    def test_checked_exponentiation_stops_at_the_declared_width(self) -> None:
        source = "make value: u8 := 2\nemit value ** 7"
        self.assertEqual(self.run_program(source, "treewalk"), ["128"])
        self.assertEqual(self.run_program(source, "vm"), ["128"])
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                with self.assertRaisesRegex(ReaperRuntimeError, "overflows u8"):
                    self.run_program("make value: u8 := 2\nemit value ** 8", engine)


class FixedWidthTypeCheckerTests(unittest.TestCase):
    def test_accepts_fixed_width_types_and_contextual_integer_literals(self) -> None:
        result = check_source(f"""
        make a: u8 := 255
        make b: u32 := 4294967295
        make c: u64 := {U64_MAX}
        make d: i8 := -128
        vary next: u8 := a + 1
        change next := 1 + next
        emit next > 10
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_rejects_out_of_range_literals(self) -> None:
        for source in (
            "make value: u8 := 256",
            "make value: u8 := -1",
            "make value: i8 := -129",
            "make value: u32 := 4294967296",
            f"make value: u64 := {U64_MAX + 1}",
        ):
            with self.subTest(source=source):
                result = check_source(source)
                self.assertFalse(result.ok, result.as_dict())
                self.assertIn("RPR-T0011", {item.code for item in result.diagnostics})

    def test_rejects_mismatched_fixed_width_arithmetic(self) -> None:
        result = check_source("""
        make byte: u8 := 4
        make word: u32 := 9
        emit byte + word
        """)
        self.assertFalse(result.ok, result.as_dict())
        self.assertIn("RPR-T0012", {item.code for item in result.diagnostics})

    def test_rejects_assignment_between_fixed_width_types(self) -> None:
        result = check_source("""
        vary byte: u8 := 4
        make word: u32 := 9
        change byte := word
        """)
        self.assertFalse(result.ok, result.as_dict())
        self.assertIn("RPR-T0001", {item.code for item in result.diagnostics})

    def test_fixed_width_range_helper_does_not_accept_booleans(self) -> None:
        self.assertTrue(fixed_integer_fits(255, "u8"))
        self.assertFalse(fixed_integer_fits(256, "u8"))
        self.assertFalse(fixed_integer_fits(True, "u8"))


class FixedWidthIrAndNativeTests(unittest.TestCase):
    def test_canonical_ir_keeps_type_metadata_and_source_map(self) -> None:
        module = lower(parse("make value: u32 := 42\nemit value", "map.rpr"), "map.rpr")
        definitions = [item for item in module.code if item.op == "DEFINE"]
        self.assertEqual(definitions[0].argument, ("value", False, "u32"))
        self.assertTrue(module.source_map)
        self.assertTrue(any(entry.operation == "DEFINE" and entry.line == 1 for entry in module.source_map))
        bytecode = assemble(module)
        self.assertEqual(bytecode.source_map, module.source_map)

    def test_native_c17_compiles_unsigned_and_signed_fixed_width_values(self) -> None:
        try:
            compiler = find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")

        source = f"""
        make low: u8 := 255
        vary total: u32 := 40
        change total := total + 2
        make wide: u64 := {U64_MAX}
        make signed: i8 := -128
        emit low
        emit total
        emit wide
        emit signed
        """
        generated = compile_source(source, "fixed-width-native.rpr")
        self.assertIn("rpr_uadd(", generated)
        self.assertIn("rpr_sadd(", generated)
        self.assertIn('#line 2 "fixed-width-native.rpr"', generated)

        with tempfile.TemporaryDirectory(prefix="reaper-fixed-width-") as folder:
            executable = build_executable(
                source,
                Path(folder) / ("fixed-width.exe" if os.name == "nt" else "fixed-width"),
                filename="fixed-width-native.rpr",
                compiler=compiler,
            )
            result = subprocess.run(
                [str(executable)], capture_output=True, text=True, check=False
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"255\n42\n{U64_MAX}\n-128\n")

    def test_native_unsigned_and_signed_overflow_fail_at_runtime(self) -> None:
        try:
            compiler = find_c_compiler()
        except NativeToolchainError:
            self.skipTest("GCC-compatible C compiler is not installed")

        programs = (
            ("make value: u8 := 255\nemit value + 1", "unsigned integer overflow"),
            ("make value: i8 := 127\nemit value + 1", "signed fixed-width overflow"),
        )
        with tempfile.TemporaryDirectory(prefix="reaper-fixed-width-errors-") as folder:
            for index, (source, expected_error) in enumerate(programs):
                with self.subTest(index=index):
                    executable = build_executable(
                        source,
                        Path(folder) / (f"overflow-{index}.exe" if os.name == "nt" else f"overflow-{index}"),
                        filename=f"overflow-{index}.rpr",
                        compiler=compiler,
                    )
                    result = subprocess.run(
                        [str(executable)], capture_output=True, text=True, check=False
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected_error, result.stderr)


if __name__ == "__main__":
    unittest.main()
