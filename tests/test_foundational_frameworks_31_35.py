from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksThirtyOneToThirtyFiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_31_35.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as host\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_thirty_five_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('host["foundation_validate_catalog_35"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(host["foundation_all_frameworks_35"]())'),
            ["35"],
        )
        self.assertEqual(
            self.run_expression('host["foundation_all_frameworks_35"]()[34][1]'),
            ["Host"],
        )

    def test_layer_contracts_and_chain_continuity(self) -> None:
        self.assertEqual(
            self.run_expression(
                'host["layer_validate_contract"](["frontend-boundary", "parser", "semantic-analysis", "syntax-tree.v1", "implemented"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'host["layer_validate_chain"]([["parser", "semantic-analysis"], ["semantic-analysis", "canonical-ir"], ["canonical-ir", "execution-engine"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'host["layer_validate_chain"]([["parser", "canonical-ir"], ["semantic-analysis", "execution-engine"]])'
            ),
            ["false"],
        )

    def test_middleware_has_known_phases_and_unique_order_positions(self) -> None:
        self.assertEqual(
            self.run_expression(
                'host["middleware_validate_pipeline"]([["audit", "before-execute", 10, "abort"], ["report", "after-execute", 20, "skip"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'host["middleware_validate_pipeline"]([["audit", "before-execute", 10, "abort"], ["report", "before-execute", 10, "skip"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'host["middleware_validate_pipeline"]([["audit", "unknown-phase", 10, "abort"]])'
            ),
            ["false"],
        )

    def test_integration_envelopes_match_direction_version_and_size(self) -> None:
        self.assertEqual(
            self.run_expression(
                'host["integration_validate_envelope"](["oplage.device-snapshot.v1", 1, 0, "consumes", 4096])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'host["integration_validate_envelope"](["oplage.device-snapshot.v1", 1, 0, "provides", 4096])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'host["integration_validate_envelope"](["not-applicable.v1", 1, 0, "both", 10])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'host["integration_validate_envelope"](["oplage.device-snapshot.v1", 1, 0, "consumes", 1048577])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('host["integration_validate_opt_in"]("pytyliki.c-abi.v1", false)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('host["integration_validate_opt_in"]("pytyliki.c-abi.v1", true)'),
            ["true"],
        )

    def test_container_profiles_reject_planned_network_container(self) -> None:
        self.assertEqual(
            self.run_expression('host["container_validate_selection"]("reference-bounded")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('host["container_validate_selection"]("explicit-network")'),
            ["false"],
        )

    def test_host_requires_known_capabilities_and_grants_subset(self) -> None:
        self.assertEqual(
            self.run_expression(
                'host["host_validate_descriptor"](["reaper-host", 1, "canonical-vm", ["FS_READ"], 65536])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'host["host_validate_descriptor"](["reaper-host", 2, "canonical-vm", ["FS_READ"], 65536])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'host["host_validate_descriptor"](["reaper-host", 1, "canonical-vm", ["UNKNOWN"], 65536])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'host["host_validate_grant_policy"](["FS_READ", "CLOCK"], ["FS_READ"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'host["host_validate_grant_policy"](["FS_READ"], ["FS_READ", "NETWORK"])'
            ),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
