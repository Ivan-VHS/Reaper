from __future__ import annotations

import unittest

from reaper.ir import (
    CanonicalIR,
    IRFunction,
    IRInstruction,
    IRVerificationError,
    lower,
    verify,
)
from reaper.lexer import Token
from reaper.parser import parse


TOKEN = Token("EOF", "", 1, 1)


class CanonicalIRVerificationTests(unittest.TestCase):
    def test_lowered_program_passes_operand_validation(self) -> None:
        tree = parse(
            "craft double(value) { yield value * 2 }\n"
            "emit [1, 2, 3] :: map(double)"
        )
        module = lower(tree, "sample.rpr")
        verify(module)
        self.assertGreater(len(module.code), 0)

    def test_jump_target_rejects_boolean_and_out_of_range_values(self) -> None:
        for target in (True, -1, 2):
            with self.subTest(target=target):
                with self.assertRaisesRegex(IRVerificationError, "jump target"):
                    verify(CanonicalIR((IRInstruction("JUMP", target, TOKEN),)))

    def test_call_arity_must_be_non_negative_integer(self) -> None:
        for count in (-1, True, 1.5):
            with self.subTest(count=count):
                with self.assertRaisesRegex(IRVerificationError, "argument count"):
                    verify(CanonicalIR((IRInstruction("CALL", count, TOKEN),)))

    def test_definition_requires_a_real_boolean_mutability_flag(self) -> None:
        with self.assertRaisesRegex(IRVerificationError, "mutable flag"):
            verify(CanonicalIR((IRInstruction("DEFINE", ("answer", 1), TOKEN),)))

    def test_iterator_exit_target_is_checked(self) -> None:
        with self.assertRaisesRegex(IRVerificationError, "iterator exit target"):
            verify(CanonicalIR((IRInstruction("ITER_NEXT", ("item", 2), TOKEN),)))

    def test_duplicate_function_parameters_are_rejected(self) -> None:
        function = IRFunction("repeat", ("item", "item"), ())
        with self.assertRaisesRegex(IRVerificationError, "must be unique"):
            verify(CanonicalIR((IRInstruction("MAKE_FUNCTION", function, TOKEN),)))

    def test_import_contract_and_instruction_container_are_checked(self) -> None:
        with self.assertRaisesRegex(IRVerificationError, "IMPORT requires"):
            verify(CanonicalIR((IRInstruction("IMPORT", "module.rpr", TOKEN),)))
        with self.assertRaisesRegex(IRVerificationError, "immutable instruction tuple"):
            verify(CanonicalIR([IRInstruction("CONST", 1, TOKEN)]))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
