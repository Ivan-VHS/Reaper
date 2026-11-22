from __future__ import annotations

import unittest

from reaper import Interpreter
from reaper.errors import ReaperRuntimeError


class MapLanguageTests(unittest.TestCase):
    def capture(self, source: str, engine: str = "treewalk", **limits: int) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, **limits).run(source, engine=engine)
        return output

    def test_map_literals_members_and_computed_keys(self) -> None:
        source = """
        make field := "score"
        make profile := { name: "Ada", [field]: 9, "active": true }
        emit profile.name
        emit profile[field]
        emit profile.active
        emit profile
        """
        expected = [
            "Ada",
            "9",
            "true",
            "{name: Ada, score: 9, active: true}",
        ]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)

    def test_nested_maps_and_map_indexing(self) -> None:
        source = """
        make config := { app: { name: "Reaper" }, version: 2 }
        emit config.app.name
        emit config["version"]
        """
        expected = ["Reaper", "2"]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)

    def test_optional_member_and_lazy_null_coalescing(self) -> None:
        source = """
        make user := { name: "Ada" }
        make absent := nothing
        emit absent?.nickname ?? "anonymous"
        emit nothing ?? "fallback"
        emit user.name ?? (1 / 0)
        emit "present" ?? (1 / 0)
        """
        expected = ["anonymous", "fallback", "Ada", "present"]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)

    def test_optional_access_only_suppresses_nothing_receiver(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "map has no key"):
            self.capture('make data := {name: "Ada"}\nemit data?.missing')
        with self.assertRaisesRegex(ReaperRuntimeError, "member access requires a map"):
            self.capture('emit "text"?.length')

    def test_map_access_errors_are_located(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, r"<memory>:2:"):
            self.capture('make user := {name: "Ada"}\nemit user.age')

    def test_map_building_obeys_collection_quota(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            self.capture("emit {a: 1, b: 2}", max_collection_items=1)

    def test_map_builtins(self) -> None:
        source = """
        make data := {a: 1, b: 2}
        emit keys(data)
        emit values(data)
        emit entries(data)
        emit get(data, "b")
        emit get(data, "missing", 7)
        emit has_key(data, "a")
        emit has_key(data, "missing")
        emit put(data, "c", 3)
        emit merge(data, {b: 8, c: 3})
        emit pick(data, ["b", "missing"])
        emit omit(data, "a")
        emit from_entries([["x", 4], ["y", 5]])
        """
        expected = [
            "[a, b]",
            "[1, 2]",
            "[[a, 1], [b, 2]]",
            "2",
            "7",
            "true",
            "false",
            "{a: 1, b: 2, c: 3}",
            "{a: 1, b: 8, c: 3}",
            "{b: 2}",
            "{b: 2}",
            "{x: 4, y: 5}",
        ]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)

    def test_map_higher_order_builtins(self) -> None:
        source = """
        craft double(key, value) { yield value * 2 }
        craft keep_even(key, value) { yield value % 2 == 0 }
        make data := {a: 1, b: 2, c: 3}
        emit map_values(data, double)
        emit filter_entries(data, keep_even)
        """
        expected = ["{a: 2, b: 4, c: 6}", "{b: 2}"]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)

    def test_sequence_toolbox(self) -> None:
        source = """
        craft parity(value) { yield value % 2 }
        craft add(left, right) { yield left + right }
        craft below_four(value) { yield value < 4 }
        craft join_numbers(left, right) { yield left * 10 + right }
        emit zip([1, 2], ["a", "b", "c"])
        emit enumerate(["x", "y"], 4)
        emit any([false, 0, true])
        emit all([true, 1, "yes"])
        emit compact([1, nothing, 2, nothing])
        emit group_by([1, 2, 3, 4], parity)
        emit count_by([1, 2, 3, 4], parity)
        emit scan([1, 2, 3], 0, add)
        emit take_while([1, 2, 3, 4, 1], below_four)
        emit drop_while([1, 2, 3, 4, 1], below_four)
        emit zip_with([1, 2], [3, 4], join_numbers)
        """
        expected = [
            "[[1, a], [2, b]]",
            "[[4, x], [5, y]]",
            "true",
            "true",
            "[1, 2]",
            "{1: [1, 3], 0: [2, 4]}",
            "{1: 2, 0: 2}",
            "[1, 3, 6]",
            "[1, 2, 3]",
            "[4, 1]",
            "[13, 24]",
        ]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)

    def test_invalid_map_and_callback_inputs_are_rejected(self) -> None:
        cases = (
            ("emit keys([1, 2])", "expected a map"),
            ("emit from_entries([[1]])", "key, value"),
            ("emit put({a: 1}, [], 2)", "hashable"),
            ("emit map_values({a: 1}, 7)", "Reaper function"),
        )
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ReaperRuntimeError, message):
                    self.capture(source)

    def test_existing_unary_power_precedence_is_preserved(self) -> None:
        source = "emit -2 ** 2"
        self.assertEqual(self.capture(source), ["4"])
        self.assertEqual(self.capture(source, engine="vm"), ["4"])

    def test_map_flow_is_vm_compatible(self) -> None:
        source = 'emit {name: "Reaper"} :: get("name")'
        expected = ["Reaper"]
        self.assertEqual(self.capture(source), expected)
        self.assertEqual(self.capture(source, engine="vm"), expected)


if __name__ == "__main__":
    unittest.main()
