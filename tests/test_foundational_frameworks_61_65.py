from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksSixtyOneToSixtyFiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_61_65.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as platform\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_sixty_five_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('platform["foundation_validate_catalog_65"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(platform["foundation_all_frameworks_65"]())'),
            ["65"],
        )
        self.assertEqual(
            self.run_expression('platform["foundation_all_frameworks_65"]()[64][1]'),
            ["Hardware/Software Base"],
        )

    def test_bridgehead_maturity_and_handoff_authorization(self) -> None:
        self.assertEqual(
            self.run_expression('platform["bridgehead_validate_selection"]("bridge.host-reference")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["bridgehead_validate_selection"]("bridge.embedded-stage")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["bridgehead_validate_handoff"](["bridge.host-reference", "host-python-compat", 1024, false])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["bridgehead_validate_handoff"](["bridge.host-reference", "host-python-compat", 1024, true])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["bridgehead_validate_handoff"](["bridge.host-reference", "wrong-protocol", 1024, false])'),
            ["false"],
        )

    def test_anchors_resolve_by_kind_version_and_stability(self) -> None:
        self.assertEqual(
            self.run_expression('platform["anchor_validate_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["anchor_validate_reference"]("anchor.reaper.system.abi", "interface", 1)'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["anchor_validate_reference"]("anchor.reaper.typed-structs", "capability", 1)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["anchor_validate_replacement"]("anchor.reaper.system.abi", "anchor.reaper.typed-structs")'),
            ["false"],
        )

    def test_baseline_requires_evidence_and_comparable_metrics(self) -> None:
        left = '["before", "rev1", "host-x86_64", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", [["latency", 100, "milliseconds"], ["memory", 1024, "bytes"]], ["tests/test_runtime_platform.py"]]'
        right = '["after", "rev1", "host-x86_64", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", [["latency", 120, "milliseconds"], ["memory", 2048, "bytes"]], ["tests/test_runtime_platform.py"]]'
        self.assertEqual(
            self.run_expression(f'platform["baseline_validate_snapshot"]({left})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'platform["baseline_compare"]({left}, {right})'),
            ["[[latency, 100, 120, 20, milliseconds], [memory, 1024, 2048, 1024, bytes]]"],
        )
        different_target = '["after", "rev1", "armv7m-generic", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", [["latency", 120, "milliseconds"], ["memory", 2048, "bytes"]], ["tests/test_runtime_platform.py"]]'
        self.assertEqual(
            self.run_expression(f'platform["baseline_validate_pair"]({left}, {different_target})'),
            ["false"],
        )
        no_evidence = '["before", "rev1", "host-x86_64", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", [["latency", 100, "milliseconds"]], []]'
        self.assertEqual(
            self.run_expression(f'platform["baseline_validate_snapshot"]({no_evidence})'),
            ["false"],
        )

    def test_supporting_structure_and_recovery_policy(self) -> None:
        structure = '["api-resilience", [["api", "primary", "runtime", "required"], ["replica", "replica", "runtime", "optional"], ["fallback", "fallback", "stub", "optional"]], [["replica", "api", "replicates"], ["fallback", "api", "backs-up"]]]'
        self.assertEqual(
            self.run_expression(f'platform["supporting_validate_structure"]({structure})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["supporting_validate_policy"](["retry-bounded", 3, 5000])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["supporting_validate_policy"](["retry-bounded", 0, 5000])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["supporting_validate_structure"](["invalid", [["one", "primary", "x", "required"], ["two", "primary", "y", "required"]], []])'),
            ["false"],
        )

    def test_hardware_profiles_and_memory_map_safety(self) -> None:
        self.assertEqual(
            self.run_expression('platform["hardware_validate_profile"](platform["hardware_profiles"]()[0])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["hardware_validate_profile"](platform["hardware_profiles"]()[1])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["hardware_validate_memory_map"]([["ram", "ram", 0, 4096, "read-write"], ["mmio", "mmio", 4096, 256, "device"]])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('platform["hardware_validate_memory_map"]([["ram", "ram", 0, 4096, "read-write"], ["mmio", "mmio", 4095, 256, "device"]])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["hardware_validate_memory_map"]([["mmio", "mmio", 4096, 256, "read-write"]])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('platform["hardware_validate_base"](["host-x86_64", [["ram", "ram", 0, 4096, "read-write"]], "reaper-host", "read-only-driver-set"])'),
            ["true"],
        )


if __name__ == "__main__":
    unittest.main()
