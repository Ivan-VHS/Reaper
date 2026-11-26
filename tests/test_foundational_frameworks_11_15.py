from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksElevenToFifteenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_11_15.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as systems\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_fifteen_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('systems["foundation_validate_catalog_15"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(systems["foundation_all_frameworks_15"]())'),
            ["15"],
        )
        self.assertEqual(
            self.run_expression('systems["foundation_all_frameworks_15"]()[14][1]'),
            ["Shell"],
        )

    def test_structure_schema_and_fixed_width_values(self) -> None:
        schema = '["gpio.pin.v1", 1, [["pin", "u8", "immutable"], ["enabled", "bool", "mutable"]]]'
        self.assertEqual(
            self.run_expression(f'systems["structure_validate_schema"]({schema})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'systems["structure_validate_instance"]({schema}, [13, true])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'systems["structure_validate_instance"]({schema}, [256, true])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(f'systems["structure_validate_instance"]({schema}, [-1, true])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(f'systems["structure_validate_instance"]({schema}, [13.5, true])'),
            ["false"],
        )
        bad_schema = '["gpio.pin.v1", 1, [["pin", "u8", "immutable"], ["pin", "bool", "mutable"]]]'
        self.assertEqual(
            self.run_expression(f'systems["structure_validate_schema"]({bad_schema})'),
            ["false"],
        )

    def test_construction_plan_requires_dependency_first_order(self) -> None:
        self.assertEqual(
            self.run_expression(
                'systems["construction_validate_plan"](["app", [["compile", []], ["test", ["compile"]]]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["construction_validate_plan"](["app", [["test", ["compile"]], ["compile", []]]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["construction_validate_plan"](["app", [["compile", []], ["compile", []]]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["construction_build_order"](["app", [["compile", []], ["test", ["compile"]]]])'
            ),
            ["[compile, test]"],
        )

    def test_ecosystem_inventory_and_links(self) -> None:
        self.assertEqual(
            self.run_expression('systems["ecosystem_validate_peers"](systems["ecosystem_peers"]())'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('systems["ecosystem_find_peer"]("oplague")[0]'),
            ["oplague"],
        )
        self.assertEqual(
            self.run_expression('systems["ecosystem_validate_link"](["oplague", "reaper", "oplage.device-snapshot.v1", "json-file", "implemented"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('systems["ecosystem_validate_link"](["reaper", "unknown", "unknown.v1", "network"])'),
            ["false"],
        )

    def test_extension_manifest_and_lifecycle_are_fail_closed(self) -> None:
        manifest = '["sample.extension", 1, ["reaper.host-service.v1", 1, 0, "both"], ["FS_READ"], "sample.start"]'
        self.assertEqual(
            self.run_expression(f'systems["extension_validate_manifest"]({manifest})'),
            ["true"],
        )
        denied = '["sample.extension", 1, ["reaper.host-service.v1", 2, 0, "both"], ["FS_READ"], "sample.start"]'
        self.assertEqual(
            self.run_expression(f'systems["extension_validate_manifest"]({denied})'),
            ["false"],
        )
        unknown_capability = '["sample.extension", 1, ["reaper.host-service.v1", 1, 0, "both"], ["ROOT_ACCESS"], "sample.start"]'
        self.assertEqual(
            self.run_expression(f'systems["extension_validate_manifest"]({unknown_capability})'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('systems["extension_validate_transition"]("enabled", "disabled")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('systems["extension_validate_transition"]("declared", "enabled")'),
            ["false"],
        )

    def test_shell_context_requests_and_lifecycle(self) -> None:
        self.assertEqual(
            self.run_expression(
                'systems["shell_validate_context"](["reaper-host", "session-1", "main.rpr", ["FS_READ"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["shell_validate_context"](["reaper-host", "session-1", "main.rpr", ["ROOT_ACCESS"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["shell_validate_request"](["notify", "FS_READ", 1024])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["shell_validate_request"](["notify", "FS_READ", 65537])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["shell_validate_lifecycle"](systems["shell_lifecycle"]())'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'systems["shell_validate_lifecycle"](["start", "bootstrap", "run"])'
            ),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
