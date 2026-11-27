from __future__ import annotations

import unittest

from reaper.ir import CanonicalIR, verify
from reaper.runtime import Interpreter
from reaper.vm import VirtualMachine, assemble
from reaper.pytyliki_hardware_ir import (
    PytylikiHardwareIRError,
    import_hardware_ir,
    lower_pure,
)


def span(start: int = 1, end: int = 4, line: int = 1, column: int = 1) -> dict[str, int]:
    return {"start": start, "end": end, "line": line, "column": column}


def sample_payload() -> dict:
    return {
        "schema": "reaper.typed-hardware-ir.v1",
        "producer": "pytyliki",
        "module": "kinematics",
        "source_name": "kinematics.shw",
        "target": "host",
        "source_bytes": 160,
        "type_system": "pytyliki.dimension-vector.v1",
        "result_value": 7,
        "effects": {"allowed": 0, "inferred": 0},
        "types": [
            {"id": 0, "kind": "f64", "width": 64, "dimensions": [0, 0, 0, 0, 0, 0, 0, 0]},
            {"id": 1, "kind": "quantity", "width": 0, "dimensions": [1, 0, 0, 0, 0, 0, 0, 0]},
            {"id": 2, "kind": "quantity", "width": 0, "dimensions": [0, 0, 1, 0, 0, 0, 0, 0]},
            {"id": 3, "kind": "quantity", "width": 0, "dimensions": [1, 0, -1, 0, 0, 0, 0, 0]},
        ],
        "values": [
            {"id": 0, "op": "const.f64", "type": 1, "lhs": None, "rhs": None, "symbol": None, "immediate": 1.2, "effect": "pure", "span": span(54, 57, 4, 22)},
            {"id": 1, "op": "const.f64", "type": 2, "lhs": None, "rhs": None, "symbol": None, "immediate": 4.0, "effect": "pure", "span": span(78, 79, 5, 20)},
            {"id": 2, "op": "input", "type": 1, "lhs": 0, "rhs": None, "symbol": 0, "immediate": 0.0, "effect": "pure", "span": span(101, 109, 6, 21)},
            {"id": 3, "op": "input", "type": 2, "lhs": 1, "rhs": None, "symbol": 1, "immediate": 0.0, "effect": "pure", "span": span(112, 119, 6, 32)},
            {"id": 4, "op": "div", "type": 3, "lhs": 2, "rhs": 3, "symbol": None, "immediate": 0.0, "effect": "pure", "span": span(110, 119, 6, 30)},
            {"id": 5, "op": "input", "type": 3, "lhs": 4, "rhs": None, "symbol": 2, "immediate": 0.0, "effect": "pure", "span": span(143, 148, 7, 23)},
            {"id": 6, "op": "input", "type": 2, "lhs": 1, "rhs": None, "symbol": 1, "immediate": 0.0, "effect": "pure", "span": span(151, 158, 7, 31)},
            {"id": 7, "op": "mul", "type": 1, "lhs": 5, "rhs": 6, "symbol": None, "immediate": 0.0, "effect": "pure", "span": span(149, 158, 7, 29)},
        ],
        "symbols": [
            {"name": "distance", "kind": "input", "type": 1, "access": "none", "value": 0, "span": span(0, 25)},
            {"name": "elapsed", "kind": "input", "type": 2, "access": "none", "value": 2, "span": span(35, 50)},
            {"name": "speed", "kind": "derive", "type": 3, "access": "none", "value": 4, "span": span(59, 70)},
            {"name": "travelled", "kind": "derive", "type": 1, "access": "none", "value": 7, "span": span(71, 88)},
        ],
    }


def mmio_payload() -> dict:
    return {
        "schema": "reaper.typed-hardware-ir.v1",
        "producer": "pytyliki",
        "module": "probe",
        "source_name": "mmio_probe.shw",
        "target": "sim",
        "source_bytes": 96,
        "type_system": "pytyliki.dimension-vector.v1",
        "result_value": 0,
        "effects": {"allowed": 4, "inferred": 4},
        "types": [{"id": 0, "kind": "u32", "width": 32, "dimensions": [0] * 8},
                  {"id": 1, "kind": "unit", "width": 0, "dimensions": [0] * 8}],
        "values": [
            {"id": 0, "op": "mmio.read", "type": 0, "lhs": None, "rhs": None, "symbol": 0, "immediate": 0.0, "effect": "mmio.read", "span": span(60, 88)}
        ],
        "symbols": [
            {"name": "status", "kind": "register", "type": 0, "access": "read_only", "value": None, "span": span(25, 55)},
            {"name": "status_value", "kind": "operation", "type": 0, "access": "none", "value": 0, "span": span(60, 88)},
        ],
    }


class PytylikiHardwareIRAdapterTests(unittest.TestCase):
    def test_import_preserves_dimension_effect_and_source_metadata(self) -> None:
        module = import_hardware_ir(sample_payload())
        self.assertEqual(module.schema, "reaper.typed-hardware-ir.v1")
        self.assertEqual(module.types[3].dimensions, (1, 0, -1, 0, 0, 0, 0, 0))
        self.assertEqual(module.values[4].span.line, 6)
        self.assertEqual(module.inferred_effects, 0)

    def test_pure_subset_lowers_and_executes_in_reaper_vm(self) -> None:
        module = import_hardware_ir(sample_payload())
        lowering = lower_pure(module, emit_result=True)
        self.assertIsInstance(lowering.canonical_ir, CanonicalIR)
        verify(lowering.canonical_ir)
        self.assertEqual(lowering.hardware.types[3].dimensions[2], -1)

        output: list[str] = []
        interpreter = Interpreter(output=output.append)
        machine = VirtualMachine(interpreter, assemble(lowering.canonical_ir))
        machine.run()
        self.assertEqual(len(output), 1)
        self.assertAlmostEqual(float(output[0]), 1.2)

    def test_fixed_width_integer_module_is_not_lowered_to_untyped_stack_ir(self) -> None:
        integer = {
            "schema": "reaper.typed-hardware-ir.v1", "producer": "pytyliki",
            "module": "integer_probe", "source_name": "integer.shw", "target": "host",
            "source_bytes": 32, "type_system": "pytyliki.dimension-vector.v1",
            "result_value": 0, "effects": {"allowed": 0, "inferred": 0},
            "types": [{"id": 0, "kind": "u32", "width": 32, "dimensions": [0] * 8}],
            "values": [{"id": 0, "op": "const.f64", "type": 0, "lhs": None, "rhs": None,
                        "symbol": None, "immediate": 7.0, "effect": "pure", "span": span(0, 4)}],
            "symbols": [{"name": "mask", "kind": "input", "type": 0, "access": "none",
                         "value": 0, "span": span(0, 4)}],
        }
        with self.assertRaisesRegex(PytylikiHardwareIRError, "no matching overflow/width semantics"):
            lower_pure(import_hardware_ir(integer))

    def test_mmio_hir_imports_but_cannot_enter_pure_interpreter(self) -> None:
        module = import_hardware_ir(mmio_payload())
        with self.assertRaisesRegex(PytylikiHardwareIRError, "effectful hardware IR"):
            lower_pure(module)

    def test_register_write_type_and_access_are_validated(self) -> None:
        bad = mmio_payload()
        bad["values"][0].update({"op": "mmio.write", "lhs": None, "effect": "mmio.write"})
        bad["effects"] = {"allowed": 8, "inferred": 8}
        bad["symbols"][0]["access"] = "read_only"
        with self.assertRaisesRegex(PytylikiHardwareIRError, "malformed MMIO write|violates register access"):
            import_hardware_ir(bad)

    def test_derived_symbol_reference_is_preserved_and_lowered(self) -> None:
        module = import_hardware_ir(sample_payload())
        self.assertEqual(module.values[5].op, "input")
        self.assertEqual(module.symbols[2].kind, "derive")
        lowered = lower_pure(module, emit_result=True)
        verify(lowered.canonical_ir)

    def test_forward_reference_is_rejected(self) -> None:
        bad = sample_payload()
        bad["values"][4]["lhs"] = 4
        with self.assertRaisesRegex(PytylikiHardwareIRError, "earlier HIR value"):
            import_hardware_ir(bad)

    def test_dimension_mismatch_is_rejected(self) -> None:
        bad = sample_payload()
        bad["values"][4]["op"] = "add"
        with self.assertRaisesRegex(PytylikiHardwareIRError, "identical operand and result types"):
            import_hardware_ir(bad)

    def test_invalid_span_and_effect_summary_are_rejected(self) -> None:
        bad_span = sample_payload()
        bad_span["values"][0]["span"]["end"] = 999
        with self.assertRaisesRegex(PytylikiHardwareIRError, "end"):
            import_hardware_ir(bad_span)
        bad_effects = mmio_payload()
        bad_effects["effects"]["allowed"] = 0
        with self.assertRaisesRegex(PytylikiHardwareIRError, "inferred effects exceed"):
            import_hardware_ir(bad_effects)

    def test_schema_and_payload_limits_are_enforced(self) -> None:
        bad = sample_payload()
        bad["schema"] = "reaper.typed-hardware-ir.v99"
        with self.assertRaisesRegex(PytylikiHardwareIRError, "unsupported schema|producer"):
            import_hardware_ir(bad)
        with self.assertRaisesRegex(PytylikiHardwareIRError, "2 MiB"):
            import_hardware_ir(" " * (2 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
