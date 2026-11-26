from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksFiftySixToSixtyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_56_60.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as workspace\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_sixty_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('workspace["foundation_validate_catalog_60"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(workspace["foundation_all_frameworks_60"]())'),
            ["60"],
        )
        self.assertEqual(
            self.run_expression('workspace["foundation_all_frameworks_60"]()[59][1]'),
            ["Workspace"],
        )

    def test_grid_axes_coordinates_and_complete_cells(self) -> None:
        grid = '["coverage", [["row", "runtime", 2], ["column", "platform", 2]], ["runtime", "compiler"], ["hosted", "native"]]'
        cells = '[["runtime", "hosted", "yes"], ["runtime", "native", "yes"], ["compiler", "hosted", "partial"], ["compiler", "native", "partial"]]'
        self.assertEqual(
            self.run_expression(f'workspace["grid_validate_descriptor"]({grid})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'workspace["grid_validate_cells"]({grid}, {cells})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'workspace["grid_validate_coordinate"]({grid}, ["runtime", "native"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'workspace["grid_validate_cells"]({grid}, {cells[:-1]})'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('workspace["grid_validate_axis"](["row", "runtime", 1.5])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('workspace["grid_validate_descriptor"](["bad", [["row"], ["column"]], ["r"], ["c"]])'),
            ["false"],
        )

        self.assertEqual(
            self.run_expression(
                'workspace["grid_validate_descriptor"](["coverage", [["row", "runtime", 3], ["column", "platform", 2]], ["runtime", "compiler"], ["hosted", "native"]])'
            ),
            ["false"],
        )


    def test_contour_ports_match_interface_and_direction(self) -> None:
        self.assertEqual(
            self.run_expression(
                'workspace["contour_validate_port"](["source-out", "output", "token-stream.v1", "1"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["contour_validate_connection"](["source-out", "output", "token-stream.v1", "1"], ["parser-in", "input", "token-stream.v1", "1"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["contour_validate_connection"](["source-out", "output", "token-stream.v1", "1"], ["parser-in", "input", "syntax-tree.v1", "1"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["contour_validate_descriptor"](["parser-boundary", "parser", [["input", "input", "token-stream.v1", "1"], ["output", "output", "syntax-tree.v1", "1"]], ["no ambient filesystem access"]])'
            ),
            ["true"],
        )

    def test_perimeter_defaults_to_deny_and_validates_rule_sets(self) -> None:
        self.assertEqual(
            self.run_expression('workspace["perimeter_validate_policy"](workspace["perimeter_default_policy"]())'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["perimeter_decision"](workspace["perimeter_default_policy"](), "application", "trusted-host", "egress", "capability-grant")'
            ),
            ["deny"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["perimeter_decision"](workspace["perimeter_default_policy"](), "runtime", "trusted-host", "egress", "explicit-host-dispatch")'
            ),
            ["allow"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["perimeter_decision"]([], "untrusted-input", "application", "ingress", "validated-data-only")'
            ),
            ["deny"],
        )

    def test_working_environment_rejects_unreleased_profiles_and_secrets(self) -> None:
        self.assertEqual(
            self.run_expression(
                'workspace["working_environment_validate_profile"](["developer-host", "hosted-reference", "local", "network-disabled-by-default", "implemented"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["working_environment_validate_profile"](["embedded-cross", "freestanding", "cross-toolchain", "hardware-access-disabled", "planned"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('workspace["working_environment_validate_variables"]([["LANG", "uk"], ["BUILD_MODE", "debug"]])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('workspace["working_environment_validate_variables"]([["API_TOKEN", "secret-value"]])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('workspace["working_environment_validate_variables"]([["SECRET_PATH", "x"]])'),
            ["false"],
        )

    def test_workspace_roots_membership_and_mutation_state(self) -> None:
        workspace = '["reaper", "projects/reaper", "projects/reaper/src", "projects/reaper/build", "clean", ["modules/main.rpr"]]'
        self.assertEqual(
            self.run_expression(f'workspace["workspace_validate_descriptor"]({workspace})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'workspace["workspace_validate_membership"]({workspace}, "projects/reaper/src/main.rpr")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'workspace["workspace_validate_membership"]({workspace}, "projects/other/main.rpr")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'workspace["workspace_validate_descriptor"](["reaper", "projects/reaper", "projects/other/src", "projects/reaper/build", "clean", ["modules/main.rpr"]])'
            ),
            ["false"],
        )
        read_only = '["reaper", "projects/reaper", "projects/reaper/src", "projects/reaper/build", "read-only", []]'
        self.assertEqual(
            self.run_expression(f'workspace["workspace_mutation_allowed"]({read_only})'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(f'workspace["workspace_mutation_allowed"]({workspace})'),
            ["true"],
        )
        invalid = '["reaper", "projects/reaper", "projects/other/src", "projects/reaper/build", "clean", ["modules/main.rpr"]]'
        self.assertEqual(
            self.run_expression(f'workspace["workspace_mutation_allowed"]({invalid})'),
            ["false"],
        )



if __name__ == "__main__":
    unittest.main()
