from __future__ import annotations

import unittest
from dataclasses import replace

from reaper.rfs01 import MAX_TOKENS, RFS01Error, RFSIRInstruction, compile_ir, compile_source, run_source, verify_ir


BASE = """
module TestMesh version "1.0" {
  node a :: Node { layer: Basement, pressure: 20, load_limit: 100, integrity: 0.9, noise_db: -10, core_seed: "root-a" }
  state b <> State { layer: Corridor, pressure: 2, load_limit: 100, integrity: 0.8, noise_db: -10, core_seed: "root-b" }
  link ab :: Link { origin: a, target: b, channel: Bridge, weight: 0.1 }
  signal s1 :: Signal { sequence: 1, origin: a, payload: "trusted", trusted: true, manufactured: false }
  signal s2 :: Signal { sequence: 2, origin: a, payload: "noise", trusted: false, manufactured: true }
  phase p1 on a [pressure >= 0 : integrity > 0]
  flow a >> b
  flow a ~> b
  contrast a || b
  contrast a ^^ b
  cycles 1
  emit "ok"
}
"""


class RFS01Tests(unittest.TestCase):
    def test_compile_and_execute_typed_mesh(self):
        result = run_source(BASE)
        self.assertEqual(result["schema"], "rfs-01.runtime-result.v1")
        self.assertEqual(result["ir_schema"], "rfs-01.typed-ir.v1")
        self.assertGreater(result["ir_instruction_count"], 0)
        self.assertEqual(result["clean_signal_frames"], 1)
        self.assertEqual(result["rejected_signal_frames"], 1)
        self.assertEqual(result["nodes"][1]["pressure"], 4.0)
        self.assertEqual(result["nodes"][1]["active"], True)
        self.assertLess(result["nodes"][1]["noise_db"], -10.0)
        self.assertEqual(len(result["contrasts"]), 2)
        self.assertEqual(result["messages"], ["ok"])


    def test_typed_ir_lowering_and_verifier(self):
        module = compile_ir(BASE)
        self.assertEqual(module.schema, "rfs-01.typed-ir.v1")
        self.assertTrue(any(item.opcode == "FLOW_PRESSURE_FORWARD" for item in module.instructions))
        verify_ir(module)

        instructions = list(module.instructions)
        index = next(i for i, item in enumerate(instructions) if item.opcode == "FLOW_PRESSURE_FORWARD")
        item = instructions[index]
        instructions[index] = RFSIRInstruction(item.sequence, item.opcode, ("a", "missing"), item.span)
        malformed = replace(module, instructions=tuple(instructions))
        with self.assertRaisesRegex(RFS01Error, "RFS-E501"):
            verify_ir(malformed)

        invalid_node = replace(module.nodes[0], integrity=1.1)
        malformed_domain = replace(module, nodes=(invalid_node,) + module.nodes[1:])
        with self.assertRaisesRegex(RFS01Error, "RFS-E501"):
            verify_ir(malformed_domain)

    def test_empty_signal_payload_is_allowed(self):
        result = run_source(BASE.replace('payload: "trusted"', 'payload: ""'))
        self.assertEqual(result["clean_signal_frames"], 1)

    def test_signal_sequence_is_strictly_monotonic_per_origin(self):
        source = BASE.replace("sequence: 1", "sequence: 3")
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(source)


    def test_token_budget_is_enforced(self):
        with self.assertRaisesRegex(RFS01Error, "RFS-E401"):
            compile_source("x " * (MAX_TOKENS + 1))

    def test_invalid_unicode_and_embedded_nul_are_rejected(self):
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(BASE.replace('payload: "trusted"', r'payload: "\ud800"'))
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(BASE.replace('payload: "trusted"', r'payload: "\u0000"'))

    def test_legacy_reaper_parser_is_not_redefined(self):
        from reaper.parser import parse

        tree = parse("make value := 9\nemit value\n")
        self.assertIsNotNone(tree)

    def test_pressure_transfer_is_rejected_at_load_limit(self):
        source = BASE.replace("pressure: 20", "pressure: 200").replace("weight: 0.1", "weight: 1.0")
        result = run_source(source)
        self.assertTrue(any(event["kind"] == "pressure-rejected" for event in result["events"]))
        self.assertEqual(result["nodes"][1]["pressure"], 2.0)

    def test_phase_gate_blocks_forwarding(self):
        source = BASE.replace("pressure >= 0", "pressure < 0")
        result = run_source(source)
        self.assertTrue(any(event["kind"] == "phase-blocked" for event in result["events"]))
        self.assertEqual(result["nodes"][1]["pressure"], 2.0)

    def test_blocked_link_never_forwards(self):
        source = BASE.replace("channel: Bridge, weight: 0.1", "channel: Bridge, weight: 0.1, blocked: true")
        result = run_source(source)
        self.assertTrue(any(event["kind"] == "link-blocked" for event in result["events"]))

    def test_root_and_core_recovery_have_distinct_scope(self):
        source = BASE.replace(
            'flow a >> b',
            'flow a >> b\n  recover b ^core\n  recover b <-root',
        )
        result = run_source(source)
        self.assertTrue(any(event["kind"] == "core-restored" for event in result["events"]))
        self.assertTrue(any(event["kind"] == "root-restored" for event in result["events"]))
        self.assertEqual(result["nodes"][1]["pressure"], 2.0)
        self.assertEqual(result["nodes"][1]["core_seed"], "root-b")

    def test_reverse_flow_uses_reverse_link(self):
        source = BASE.replace(
            'flow a >> b',
            'link ba :: Link { origin: b, target: a, channel: Wire, weight: 0.5 }\n  flow a << b',
        )
        result = run_source(source)
        self.assertEqual(result["nodes"][0]["pressure"], 21.0)

    def test_cycle_limit_is_enforced(self):
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(BASE.replace("cycles 1", "cycles 109"))

    def test_unknown_reference_is_rejected(self):
        with self.assertRaisesRegex(RFS01Error, "RFS-E201"):
            compile_source(BASE.replace("flow a >> b", "flow a >> ghost"))

    def test_unknown_field_is_rejected(self):
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(BASE.replace("pressure: 20", "pressure: 20, magical: true"))

    def test_duplicate_declaration_is_rejected(self):
        duplicated = BASE.replace(
            'state b <> State',
            'node a :: Node { layer: Gate, pressure: 0, load_limit: 1, integrity: 1, noise_db: -20, core_seed: "x" }\n  state b <> State',
        )
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(duplicated)

    def test_non_finite_threshold_is_rejected_by_lexer(self):
        with self.assertRaises(RFS01Error):
            compile_source(BASE.replace("pressure >= 0", "pressure >= nan"))

    def test_wrong_version_is_rejected(self):
        with self.assertRaisesRegex(RFS01Error, "RFS-E101"):
            compile_source(BASE.replace('"1.0"', '"2.0"'))


if __name__ == "__main__":
    unittest.main()
