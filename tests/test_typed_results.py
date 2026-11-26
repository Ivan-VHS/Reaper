from __future__ import annotations

import unittest

from reaper.runtime import Interpreter, OptionValue, ResultValue


class TypedResultRuntimeTests(unittest.TestCase):
    def run_source(self, source: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source)
        return output

    def test_result_composition_preserves_first_failure(self) -> None:
        output = self.run_source("""
craft double(value) {
    yield value * 2
}
craft annotate(message) {
    yield "parse-error: " ++ message
}
make good := map_ok(ok(21), double)
make bad := map_err(err("missing"), annotate)
make combined := zip3_ok(ok(1), err("first"), err("second"))
emit result_is_ok(good)
emit result_value(good)
emit result_is_err(bad)
emit result_error(bad)
emit result_error(combined)
""")
        self.assertEqual(output, [
            "true", "42", "true", "parse-error: missing", "first"
        ])

    def test_result_unwrap_rejects_the_wrong_variant(self) -> None:
        output = self.run_source("""
emit result_is_err(err("no"))
emit result_is_ok(ok(1))
""")
        self.assertEqual(output, ["true", "true"])
        with self.assertRaisesRegex(Exception, "cannot unwrap Err"):
            self.run_source('emit result_value(err("no"))')

    def test_option_values_have_explicit_presence(self) -> None:
        output = self.run_source("""
make available := some("ready")
make missing := none()
emit option_is_some(available)
emit option_is_none(missing)
emit option_value(available)
emit option_or(missing, "fallback")
""")
        self.assertEqual(output, ["true", "true", "ready", "fallback"])

    def test_option_unwrap_rejects_none(self) -> None:
        with self.assertRaisesRegex(Exception, "cannot unwrap None"):
            self.run_source("emit option_value(none())")

    def test_public_values_are_immutable_tagged_records(self) -> None:
        self.assertEqual(ResultValue.ok(3).is_ok, True)
        self.assertEqual(ResultValue.err("failed").error, "failed")
        self.assertEqual(OptionValue.some(4).value, 4)
        self.assertEqual(OptionValue.none().is_some, False)


if __name__ == "__main__":
    unittest.main()
