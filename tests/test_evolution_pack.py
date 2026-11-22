import unittest

from reaper.runtime import Interpreter


class EvolutionLanguagePackTests(unittest.TestCase):
    def capture(self, source: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source)
        return output

    def test_result_and_option_constructions(self):
        self.assertEqual(self.capture(
            'craft double(x) { yield x * 2 }\n'
            'make success := ok(21)\n'
            'emit unwrap(result_map(success, double))\n'
            'emit unwrap_or(err("offline"), 7)\n'
            'emit some_value(some("ready"))\n'
            'emit coalesce(nothing, "fallback")'
        ), ["42", "7", "ready", "fallback"])

    def test_functional_collection_constructions(self):
        self.assertEqual(self.capture(
            'craft even(x) { yield x % 2 == 0 }\n'
            'craft add(a, b) { yield a + b }\n'
            'craft pair(x) { yield [x, x] }\n'
            'emit zip([1, 2], ["a", "b"])\n'
            'emit enumerate(["x", "y"], 4)\n'
            'emit find([1, 3, 4, 6], even)\n'
            'emit take_while([2, 4, 5, 6], even)\n'
            'emit scan([1, 2, 3], 0, add)\n'
            'emit flat_map([1, 2], pair)'
        ), ["[[1, a], [2, b]]", "[[4, x], [5, y]]", "4", "[2, 4]", "[1, 3, 6]", "[1, 1, 2, 2]"])

    def test_snapshot_and_reflash(self):
        self.assertEqual(self.capture(
            'craft double(x) { yield x * 2 }\n'
            'craft increment(x) { yield x + 1 }\n'
            'make state := snapshot([1, [2, 3]])\n'
            'emit state\n'
            'emit reflash(3, double, increment)'
        ), ["[1, [2, 3]]", "7"])

    def test_numeric_and_text_extensions(self):
        self.assertEqual(self.capture(
            'emit clamp(12, 0, 10)\n'
            'emit lerp(10, 20, 0.25)\n'
            'emit gcd(42, 30)\n'
            'emit mean([2, 4, 6])\n'
            'emit median([9, 1, 4])\n'
            'emit words("reaper has flow")\n'
            'emit pad_left("7", 3, "0")\n'
            'emit repeat_text("ab", 3)\n'
            'emit count_text("banana", "an")\n'
            'emit slice_text("reaper", 1, 4)'
        ), ["10", "12.5", "6", "4.0", "4", "[reaper, has, flow]", "007", "ababab", "2", "eap"])

    def test_try_call_captures_runtime_error(self):
        self.assertEqual(self.capture(
            'craft divide(a, b) { yield a / b }\n'
            'make outcome := try_call(divide, 4, 0)\n'
            'emit is_err(outcome)\n'
            'emit recover(outcome, "recovered")'
        ), ["true", "recovered"])

    def test_map_constructors_and_copy_on_write_updates(self):
        self.assertEqual(self.capture(
            'make source := map_of("a", 1, "b", 2)\n'
            'make changed := put(source, "c", 3)\n'
            'emit keys(changed)\n'
            'emit get_or(changed, "missing", 9)\n'
            'emit remove_key(changed, "a")\n'
            'emit rebind(source, map_of("b", 20, "d", 4))'
        ), ["[a, b, c]", "9", "{\'b\': 2, \'c\': 3}", "{\'a\': 1, \'b\': 20, \'d\': 4}"])

    def test_flow_coalescing_and_membership_operators(self):
        self.assertEqual(self.capture(
            'emit [1, 2, 3] |> size()\n'
            'emit 2 in [1, 2, 3]\n'
            'emit "a" in "reaper"\n'
            'emit 9 ?? missing_name\n'
            'emit nothing ?? "fallback"'
        ), ["3", "true", "true", "9", "fallback"])

    def test_collection_bounds_are_enforced(self):
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(Exception, "collection item limit"):
            interpreter.run("emit interleave([1, 2], [3, 4])")


if __name__ == "__main__":
    unittest.main()
