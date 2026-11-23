from __future__ import annotations

import unittest

from reaper.native_ir import (
    NativeIRModule,
    NativeIRValue,
    NativeType,
    Ownership,
    NativeIRVerificationError,
    RUNTIME_CALLS,
    allocate_registers,
    optimize_native_ir,
    ownership_drop_plan,
    verify_native_ir,
)


class NativeTypedIRTests(unittest.TestCase):
    def test_runtime_call_table_has_unique_stable_ids_and_c_symbols(self) -> None:
        self.assertEqual(len(RUNTIME_CALLS), len(set(RUNTIME_CALLS)))
        self.assertEqual(RUNTIME_CALLS["i64.add"].c_symbol, "rpr_add")
        self.assertEqual(RUNTIME_CALLS["array.release"].argument_ownership, (Ownership.OWNED,))

    def test_verifier_checks_ssa_order_and_runtime_signatures(self) -> None:
        values = (
            NativeIRValue(0, "CONST", NativeType.I64, symbol="20"),
            NativeIRValue(1, "CONST", NativeType.I64, symbol="22"),
            NativeIRValue(2, "BINARY", NativeType.I64, (0, 1), runtime_call="i64.add"),
        )
        verify_native_ir(NativeIRModule(values, "typed.rpr"))
        bad = (
            values[0], values[1],
            NativeIRValue(2, "BINARY", NativeType.BOOL, (0, 1), runtime_call="i64.add"),
        )
        with self.assertRaisesRegex(NativeIRVerificationError, "result type"):
            verify_native_ir(NativeIRModule(bad, "typed.rpr"))

    def test_verifier_rejects_forward_references_and_bad_collection_ownership(self) -> None:
        with self.assertRaisesRegex(NativeIRVerificationError, "earlier SSA"):
            verify_native_ir(NativeIRModule((
                NativeIRValue(0, "UNARY", NativeType.I64, (1,)),
                NativeIRValue(1, "CONST", NativeType.I64, symbol="1"),
            )))
        with self.assertRaisesRegex(NativeIRVerificationError, "must be owned"):
            verify_native_ir(NativeIRModule((
                NativeIRValue(0, "ARRAY_LITERAL", NativeType.ARRAY, ownership=Ownership.BORROWED),
            )))

    def test_optimizer_folds_checked_integer_constants(self) -> None:
        values = (
            NativeIRValue(0, "CONST", NativeType.I64, symbol="19"),
            NativeIRValue(1, "CONST", NativeType.I64, symbol="23"),
            NativeIRValue(2, "BINARY", NativeType.I64, (0, 1), runtime_call="i64.add"),
        )
        optimized = optimize_native_ir(NativeIRModule(values, "fold.rpr"))
        self.assertEqual(optimized.values[2].operation, "CONST")
        self.assertEqual(optimized.values[2].symbol, "42")

    def test_ownership_plan_releases_owned_aggregate_values(self) -> None:
        values = (
            NativeIRValue(0, "ARRAY_LITERAL", NativeType.ARRAY, ownership=Ownership.OWNED),
            NativeIRValue(1, "CONST", NativeType.I64, symbol="0"),
            NativeIRValue(2, "INDEX", NativeType.I64, (0, 1)),
        )
        plan = ownership_drop_plan(NativeIRModule(values, "drop.rpr"))
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].runtime_call, "array.release")

    def test_linear_scan_allocator_assigns_and_spills(self) -> None:
        values = (
            NativeIRValue(0, "CONST", NativeType.I64, symbol="1"),
            NativeIRValue(1, "CONST", NativeType.I64, symbol="2"),
            NativeIRValue(2, "BINARY", NativeType.I64, (0, 1), runtime_call="i64.add"),
            NativeIRValue(3, "CONST", NativeType.I64, symbol="3"),
        )
        allocation = allocate_registers(NativeIRModule(values, "registers.rpr"), register_limit=1)
        self.assertEqual(allocation.register_count, 1)
        self.assertTrue(allocation.registers)
        self.assertIn(1, allocation.spills)


if __name__ == "__main__":
    unittest.main()
