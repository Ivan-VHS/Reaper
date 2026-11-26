from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksSixteenToTwentyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_16_20.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as runtime\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_twenty_unique_foundations(self) -> None:
        self.assertEqual(
            self.run_expression('runtime["foundation_validate_catalog_20"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(runtime["foundation_all_frameworks_20"]())'),
            ["20"],
        )
        self.assertEqual(
            self.run_expression('runtime["foundation_all_frameworks_20"]()[19][1]'),
            ["Library"],
        )

    def test_runtime_lifecycle_is_ordered_and_terminal(self) -> None:
        self.assertEqual(
            self.run_expression(
                'runtime["runtime_validate_lifecycle"](["created", "initialized", "ready", "running", "draining", "stopped"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["runtime_validate_lifecycle"](["created", "ready", "stopped"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["runtime_validate_lifecycle"](["created", "initialized", "ready", "running", "stopped"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["runtime_validate_lifecycle"](["created", "failed", "ready"])'
            ),
            ["false"],
        )

    def test_execution_context_checks_engine_platform_and_quotas(self) -> None:
        self.assertEqual(
            self.run_expression('runtime["execution_validate_context"](runtime["execution_default_context"]())'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["execution_validate_context"](["native-object", "hosted-reference", 1000, 32, 4096, 8192])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["execution_validate_context"](["treewalk", "unknown-platform", 1000, 32, 4096, 8192])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["execution_validate_context"](["treewalk", "hosted-reference", 1000, 0, 4096, 8192])'
            ),
            ["false"],
        )

    def test_engine_selection_and_routes_are_maturity_aware(self) -> None:
        self.assertEqual(
            self.run_expression(
                'runtime["engine_validate_selection"](["canonical-vm", "canonical-ir", "runtime-value"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["engine_validate_selection"](["native-object", "typed-ir", "target-object"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["engine_validate_route"](["source", "lexer", "parser", "semantic-analysis", "canonical-ir", "canonical-vm", "runtime-value"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["engine_validate_route"](["source", "parser", "native-object"])'
            ),
            ["false"],
        )

    def test_kernel_adapter_and_request_match_host_capability(self) -> None:
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_adapter"]([1, "duck-host", "trusted-host", ["FS_READ", "CLOCK"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_adapter"]([2, "duck-host", "trusted-host", ["FS_READ"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_adapter"]([1.5, "duck-host", "trusted-host", ["FS_READ"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_adapter"]([1, "sim-host", "simulator", ["UNKNOWN"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_request"](["filesystem.read", "FS_READ", 4096])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_request"](["filesystem.read", "FS_WRITE", 4096])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["kernel_validate_request"](["filesystem.read", "FS_READ", 1048577])'
            ),
            ["false"],
        )

    def test_library_contracts_and_dependencies_are_versioned(self) -> None:
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_descriptor"](["reaper.modules", 1, 0, "import"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_descriptor"](["reaper.modules", 2, 0, "import"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_descriptor"](["reaper.ffi", 1, 0, "inspect"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_descriptor"](["reaper.ffi", 1, 0, "import"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_dependencies"]([["reaper.modules", 1, 0], ["reaper.resources", 1, 0]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_dependencies"]([["reaper.modules", 1, 0], ["reaper.modules", 1, 0]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'runtime["library_validate_dependencies"]([["unknown.module", 1, 0]])'
            ),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
