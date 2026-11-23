from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter
from reaper.typecheck import check_source


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "examples" / "duck_pipeline.rpr"


class DuckPipelineTests(unittest.TestCase):
    def test_example_passes_static_analysis(self) -> None:
        source = PROGRAM.read_text(encoding="utf-8")
        result = check_source(source, str(PROGRAM))
        self.assertTrue(result.ok, [item.as_dict() for item in result.diagnostics])

    def test_example_normalizes_filters_and_reports_records(self) -> None:
        source = PROGRAM.read_text(encoding="utf-8")
        output: list[str] = []

        Interpreter(output=output.append).run(source, filename=str(PROGRAM))

        self.assertEqual(
            output,
            [
                "Valid count: 2",
                "Issue count: 2",
                "Active channels: [audio.main]",
                "Issues: [[EMPTY_NAME, channel name is empty, []], "
                "[OUT_OF_RANGE, level must be 0..100, [sys.temp, 140]]]",
            ],
        )

    def test_non_map_records_become_diagnostics(self) -> None:
        source = PROGRAM.read_text(encoding="utf-8")
        source = source.split('make raw_channels :=', 1)[0]
        source += '\\nmake results := ["not-a-map"] :: map(inspect_one)\\nemit results\\n'
        output: list[str] = []

        Interpreter(output=output.append).run(source, filename=str(PROGRAM))

        self.assertEqual(
            output,
            ["[[false, [INVALID_RECORD, channel record must be a map, []]]]"],
        )

    def test_map_access_and_conversion_builtins(self) -> None:
        output: list[str] = []
        interpreter = Interpreter(output=output.append)
        interpreter.globals.define(
            "channel",
            {"name": "  UI.Glass  ", "value": "0"},
        )

        interpreter.run(
            """
            emit has_key(channel, "value")
            emit has_key(channel, "level")
            emit get(channel, "name", "")
            emit get(channel, "missing", "fallback")
            emit to_int(get(channel, "value", "-1"), -1)
            emit to_int("not-a-number", -1)
            emit len(channel)
            """,
            filename="<duck-builtins-test>",
        )

        self.assertEqual(
            output,
            ["true", "false", "  UI.Glass  ", "fallback", "0", "-1", "2"],
        )

    def test_to_int_rejects_lossy_and_boolean_conversions(self) -> None:
        for expression in ("to_int(4.5)", "to_int(true)", 'to_int("4.5")'):
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(Exception, "to_int"):
                    Interpreter(output=lambda _line: None).run(
                        f"emit {expression}",
                        filename="<strict-integer-test>",
                    )


if __name__ == "__main__":
    unittest.main()
