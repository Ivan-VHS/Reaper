from __future__ import annotations

from pathlib import Path
import unittest

from reaper import Interpreter


FRAMEWORK_ROOT = Path(__file__).resolve().parents[1] / "reaper" / "frameworks" / "skeleton"


def run_framework(module: str, expression: str) -> list[str]:
    output: list[str] = []
    source = f'import "{module}.rpr" as framework\nemit {expression}\n'
    runner = FRAMEWORK_ROOT / "_test_runner.rpr"
    Interpreter(output=output.append).run(source, filename=str(runner))
    return output


class FrameManifestTests(unittest.TestCase):
    def test_complete_manifest_accepts_extra_unique_components(self) -> None:
        self.assertEqual(
            run_framework("manifest", 'framework["valid_manifest"](["src", "tests"], ["src", "tests", "docs"])'),
            ["true"],
        )

    def test_missing_component_is_reported_in_required_order(self) -> None:
        self.assertEqual(
            run_framework("manifest", 'framework["missing_components"](["src", "tests", "docs"], ["src"])'),
            ["[tests, docs]"],
        )

    def test_duplicate_or_empty_component_names_are_rejected(self) -> None:
        self.assertEqual(run_framework("manifest", 'framework["valid_manifest"](["src"], ["src", "src"])'), ["false"])
        self.assertEqual(run_framework("manifest", 'framework["valid_manifest"](["src", ""], ["src", ""])'), ["false"])


class FrameLayersTests(unittest.TestCase):
    def test_forward_layer_edges_are_valid(self) -> None:
        self.assertEqual(run_framework("layers", 'framework["valid_layer_graph"](4, [[0, 1], [0, 2], [1, 3], [2, 3]])'), ["true"])

    def test_backward_self_out_of_range_and_duplicate_edges_are_rejected(self) -> None:
        cases = (
            'framework["valid_layer_graph"](3, [[2, 1]])',
            'framework["valid_layer_graph"](3, [[1, 1]])',
            'framework["valid_layer_graph"](3, [[0, 3]])',
            'framework["valid_layer_graph"](3, [[0, 1], [0, 1]])',
            'framework["valid_layer_graph"](3, [[0]])',\n            'framework["valid_layer_graph"](3.5, [[0, 1]])',\n            'framework["valid_layer_graph"](3, [[0, 1.5]])',
        )
        for expression in cases:
            with self.subTest(expression=expression):
                self.assertEqual(run_framework("layers", expression), ["false"])


class FrameLifecycleTests(unittest.TestCase):
    def test_valid_lifecycle_follows_declared_transitions(self) -> None:
        self.assertEqual(run_framework("lifecycle", 'framework["valid_lifecycle"](0, [1, 2, 3], [[0, 1], [1, 2], [2, 3]])'), ["true"])

    def test_undeclared_transition_or_invalid_transition_table_is_rejected(self) -> None:
        self.assertEqual(run_framework("lifecycle", 'framework["valid_lifecycle"](0, [1, 4], [[0, 1], [1, 2]])'), ["false"])
        self.assertEqual(run_framework("lifecycle", 'framework["valid_lifecycle"](0, [1], [[0, 1], [0, 1]])'), ["false"])
        self.assertEqual(run_framework("lifecycle", 'framework["valid_lifecycle"](0, [1], [[0]])'), ["false"])\n        self.assertEqual(run_framework("lifecycle", 'framework["valid_lifecycle"](0, [1.5], [[0, 1.5]])'), ["false"])


class FrameCapabilitiesTests(unittest.TestCase):
    def test_required_grants_inside_policy_are_accepted(self) -> None:
        self.assertEqual(run_framework("capabilities", 'framework["valid_capability_boundary"](["read"], ["read", "clock"], ["read", "clock", "write"])'), ["true"])

    def test_missing_or_policy_forbidden_grants_are_rejected(self) -> None:
        self.assertEqual(run_framework("capabilities", 'framework["valid_capability_boundary"](["read", "write"], ["read"], ["read", "write"])'), ["false"])
        self.assertEqual(run_framework("capabilities", 'framework["valid_capability_boundary"](["read"], ["read", "shell"], ["read", "clock"])'), ["false"])
        self.assertEqual(run_framework("capabilities", 'framework["valid_capability_boundary"](["read", "read"], ["read"], ["read"])'), ["false"])


class FrameExtensionsTests(unittest.TestCase):
    def test_registry_rejects_duplicate_ids_and_invalid_records(self) -> None:
        self.assertEqual(run_framework("extensions", 'framework["valid_extension_registry"]([["codec", 1, 3], ["theme", 2, 4]])'), ["true"])
        self.assertEqual(run_framework("extensions", 'framework["valid_extension_registry"]([["codec", 1, 3], ["codec", 2, 4]])'), ["false"])
        self.assertEqual(run_framework("extensions", 'framework["valid_extension_registry"]([["codec", 4, 2]])'), ["false"])
        self.assertEqual(run_framework("extensions", 'framework["valid_extension_registry"]([["", 1, 3]])'), ["false"])\n        self.assertEqual(run_framework("extensions", 'framework["valid_extension_registry"]([["fractional", 1.5, 3]])'), ["false"])

    def test_compatibility_range_is_inclusive(self) -> None:
        self.assertEqual(run_framework("extensions", 'framework["compatible_extension"](["codec", 2, 4], 2)'), ["true"])
        self.assertEqual(run_framework("extensions", 'framework["compatible_extension"](["codec", 2, 4], 4)'), ["true"])
        self.assertEqual(run_framework("extensions", 'framework["compatible_extension"](["codec", 2, 4], 5)'), ["false"])\n        self.assertEqual(run_framework("extensions", 'framework["compatible_extension"](["codec", 2, 4], 2.5)'), ["false"])

    def test_registry_filters_to_host_compatible_extensions(self) -> None:
        self.assertEqual(
            run_framework("extensions", 'framework["compatible_extensions"]([["old", 1, 1], ["current", 2, 4], ["future", 5, 8]], 3)'),
            ['[[current, 2, 4]]'],
        )


if __name__ == "__main__":
    unittest.main()
