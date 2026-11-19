from __future__ import annotations

import unittest

from reaper.compiler import StaticTypeError, compile_source, optimize, verify_ir


class CompilerFrontEndTests(unittest.TestCase):
    def test_emits_deterministic_source_mapped_ir(self) -> None:
        source = "make answer := 20 + 22\nemit answer\n"
        first = compile_source(source, "example.rpr", strict=True)
        second = compile_source(source, "example.rpr", strict=True)
        self.assertEqual(first.ir_digest, second.ir_digest)
        self.assertEqual(first.source_digest, second.source_digest)
        self.assertEqual(first.root.opcode, "program")
        verify_ir(first.root)

    def test_type_checker_rejects_invalid_numeric_and_text_operations(self) -> None:
        with self.assertRaises(StaticTypeError):
            compile_source('emit "count=" ++ 4', strict=True)
        with self.assertRaises(StaticTypeError):
            compile_source("emit true * 3", strict=True)

    def test_type_checker_accepts_current_language_example(self) -> None:
        source = """
        craft double(value) { yield value * 2 }
        make data := [1, 2, 3]
        make result := data ~> map(double) ~> sum()
        emit result
        """
        unit = compile_source(source, strict=True)
        self.assertEqual(unit.diagnostics, ())

    def test_function_calls_are_checked_for_arity(self) -> None:
        with self.assertRaises(StaticTypeError):
            compile_source("craft add(a, b) { yield a + b }\nemit add(1)", strict=True)

    def test_optimizer_folds_only_safe_literal_expressions(self) -> None:
        unit = compile_source('emit (2 + 3) * 4\nemit 1 / 0')
        optimized, stats = optimize(unit)
        self.assertGreaterEqual(stats.folded_expressions, 2)
        first_emit = optimized.root.children[0].children[0]
        self.assertEqual(first_emit.opcode, "literal")
        self.assertEqual(first_emit.value, 20)
        second_emit = optimized.root.children[1].children[0]
        self.assertEqual(second_emit.opcode, "binary")

    def test_source_digest_changes_with_source(self) -> None:
        self.assertNotEqual(
            compile_source("emit 1").source_digest,
            compile_source("emit 2").source_digest,
        )


if __name__ == "__main__":
    unittest.main()
