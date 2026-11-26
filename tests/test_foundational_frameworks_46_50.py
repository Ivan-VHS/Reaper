from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksFortySixToFiftyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_46_50.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as graph\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_fifty_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('graph["foundation_validate_catalog_50"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(graph["foundation_all_frameworks_50"]())'),
            ["50"],
        )
        self.assertEqual(
            self.run_expression('graph["foundation_all_frameworks_50"]()[49][1]'),
            ["Protocol"],
        )

    def test_components_validate_descriptors_and_dependency_order(self) -> None:
        self.assertEqual(
            self.run_expression('graph["component_validate_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('graph["component_validate_graph"](graph["component_catalog"]())'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["component_validate_graph"]([["component.parser", "frontend", 1, "token-stream.v1", "syntax-tree.v1", ["component.lexer"], "implemented"], ["component.lexer", "frontend", 1, "source-text.v1", "token-stream.v1", [], "implemented"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["component_validate_descriptor"](["component.x", "unknown-kind", 1, "in.v1", "out.v1", [], "implemented"])'
            ),
            ["false"],
        )

    def test_blocks_validate_operations_effects_and_references(self) -> None:
        self.assertEqual(
            self.run_expression(
                'graph["block_validate_descriptor"](["entry", "input.v1", "output.v1", [["load-x", "load", "u32"]], ["x"], ["pure"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["block_validate_descriptor"](["entry", "input.v1", "output.v1", [["load-x", "unknown", "u32"]], ["x"], ["pure"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["block_validate_descriptor"](["entry", "input.v1", "output.v1", [["call-x", "call", "u32"]], ["x"], ["pure", "filesystem"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["block_validate_branch"]([["a", "in", "out", [["ret", "return", "u32"]], [], ["pure"]], ["b", "in", "out", [["ret", "return", "u32"]], [], ["pure"]]], ["a", "b"])'
            ),
            ["true"],
        )

    def test_node_graph_edges_match_output_and_input_interfaces(self) -> None:
        self.assertEqual(
            self.run_expression(
                'graph["node_validate_descriptor"](["node.parse", "operation", "parser", ["token-stream.v1"], ["syntax-tree.v1"], "implemented"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["node_validate_graph"]([["a", "operation", "producer", [], ["token-stream.v1"], "implemented"], ["b", "operation", "consumer", ["token-stream.v1"], [], "implemented"]], [["a", "b", "token-stream.v1"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["node_validate_graph"]([["a", "operation", "producer", [], ["token-stream.v1"], "implemented"], ["b", "operation", "consumer", ["syntax-tree.v1"], [], "implemented"]], [["a", "b", "token-stream.v1"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["node_validate_graph"]([["a", "operation", "producer", [], ["token-stream.v1"], "implemented"], ["b", "operation", "consumer", ["token-stream.v1"], [], "implemented"]], [["a", "b", "token-stream.v1"], ["a", "b", "token-stream.v1"]])'
            ),
            ["false"],
        )

    def test_interfaces_require_version_format_direction_and_bounds(self) -> None:
        producer = '["token-stream.v1", 1, 0, "provides", "token-array", 1024]'
        consumer = '["token-stream.v1", 1, 0, "consumes", "token-array", 1024]'
        self.assertEqual(
            self.run_expression(f'graph["interface_validate_compatibility"]({producer}, {consumer})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["interface_validate_compatibility"](["token-stream.v1", 2, 0, "provides", "token-array", 1024], ["token-stream.v1", 2, 0, "consumes", "token-array", 1024])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'graph["interface_validate_compatibility"](["token-stream.v1", 1, 0, "consumes", "token-array", 1024], ["token-stream.v1", 1, 0, "provides", "token-array", 1024])'
            ),
            ["false"],
        )

    def test_protocol_profiles_require_maturity_and_opt_in(self) -> None:
        self.assertEqual(
            self.run_expression('graph["protocol_validate_selection"]("reaper.module-import.v1", false)'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('graph["protocol_validate_selection"]("reaper.pytyliki-ffi.v1", false)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('graph["protocol_validate_selection"]("reaper.pytyliki-ffi.v1", true)'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('graph["protocol_validate_selection"]("reaper.remote-network.v1", true)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('graph["protocol_validate_payload"]("reaper.system-runtime.v1", 1048577)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('graph["protocol_validate_payload"]("reaper.module-import.v1", -1)'),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
