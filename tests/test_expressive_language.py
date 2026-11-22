from __future__ import annotations

import unittest

from reaper import Interpreter, ReaperRuntimeError


class ExpressiveLanguageTests(unittest.TestCase):
    def run_source(self, source: str, engine: str = "treewalk", **limits: int) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, **limits).run(source, engine=engine)
        return output

    def assert_both_engines(self, source: str, expected: list[str]) -> None:
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.run_source(source, engine), expected)

    def test_match_literal_binding_variant_and_guard(self) -> None:
        source = """
        craft classify(result) {
            match result {
                case Ok(value) if value > 10 { yield "large=" ++ text(value) }
                case Ok(value) { yield "small=" ++ text(value) }
                case Err(message) { yield "error=" ++ message }
                case _ { yield "unknown" }
            }
        }
        emit classify(Ok(42))
        emit classify(Ok(3))
        emit classify(Err("offline"))
        """
        self.assert_both_engines(source, ["large=42", "small=3", "error=offline"])

    def test_match_list_and_map_destructuring(self) -> None:
        source = """
        match [7, 9] {
            case [first, second] { emit first + second }
            case _ { emit 0 }
        }
        match {profile: {avatar: "bird"}} {
            case {profile: {avatar: image}} { emit image }
            case _ { emit "missing" }
        }
        """
        self.assert_both_engines(source, ["16", "bird"])

    def test_let_else_returns_from_function_when_pattern_fails(self) -> None:
        source = """
        craft head_or_default(values) {
            let [head, tail] := values else { yield "empty" }
            yield head
        }
        emit head_or_default([5, 6])
        emit head_or_default([])
        """
        self.assert_both_engines(source, ["5", "empty"])

    def test_ternary_and_null_coalescing_are_lazy_and_null_specific(self) -> None:
        source = """
        vary calls := 0
        craft fallback() {
            change calls := calls + 1
            yield "fallback"
        }
        emit true ? "yes" : "no"
        emit false ? "bad" : "chosen"
        emit 0 ?? 9
        emit nothing ?? fallback()
        emit calls
        """
        self.assert_both_engines(source, ["yes", "chosen", "0", "fallback", "1"])

    def test_null_coalescing_assignment_is_mutable_and_lazy(self) -> None:
        source = """
        vary value := nothing
        value ??= 12
        value ??= 99
        make stable := 4
        stable ??= 5
        emit value
        emit stable
        """
        self.assert_both_engines(source, ["12", "4"])

    def test_optional_chaining_and_map_values(self) -> None:
        source = """
        make user := {profile: {avatar: "duck"}, labels: ["a", "b"]}
        make absent := nothing
        emit user?.profile?.avatar
        emit user?.labels?.length
        emit absent?.profile?.avatar ?? "no-avatar"
        emit user?.labels?.[9] ?? "out-of-range"
        """
        self.assert_both_engines(source, ["duck", "2", "no-avatar", "out-of-range"])

    def test_membership_exclusive_and_inclusive_ranges(self) -> None:
        source = """
        emit 3 in 1..5
        emit 5 in 1..5
        emit 5 in 1..=5
        emit 2 in 4..=1
        emit [1, 2, 3] :: map(number) :: sum()
        """
        self.assert_both_engines(source, ["true", "false", "true", "true", "6"])

    def test_list_comprehension_with_filter(self) -> None:
        source = """
        emit [item * 3 for item in 1..7 if item % 2 == 0]
        emit [text(item) ++ "!" for item in ["a", "b"]]
        """
        self.assert_both_engines(source, ["[6, 12, 18]", "[a!, b!]"])

    def test_zip_and_enumerate(self) -> None:
        source = """
        emit zip([1, 2, 3], ["a", "b"])
        emit enumerate(["x", "y"], 4)
        """
        self.assert_both_engines(source, ["[[1, a], [2, b]]", "[[4, x], [5, y]]"])

    def test_compose_pipe_partial_and_curry(self) -> None:
        source = """
        craft double(x) { yield x * 2 }
        craft increment(x) { yield x + 1 }
        craft add(a, b) { yield a + b }
        emit compose(double, increment)(3)
        emit pipe_fn(double, increment)(3)
        emit partial(add, 4)(5)
        emit curry(add, 2)(4)(5)
        """
        self.assert_both_engines(source, ["8", "7", "9", "9"])

    def test_bounded_memoize_and_ttl_cache(self) -> None:
        source = """
        vary calls := 0
        craft counted(x) {
            change calls := calls + 1
            yield x * 10
        }
        make cached := memoize(counted, 4)
        emit cached(2)
        emit cached(2)
        emit calls
        make short_cache := memo_ttl(counted, 60000, 4)
        emit short_cache(3)
        emit short_cache(3)
        emit calls
        """
        self.assert_both_engines(source, ["20", "20", "1", "30", "30", "2"])

    def test_transducer_pipeline_runs_without_intermediate_collections(self) -> None:
        source = """
        craft even(x) { yield x % 2 == 0 }
        craft double(x) { yield x * 2 }
        emit transduce(1..10, filtering(even), mapping(double), taking(3))
        """
        self.assert_both_engines(source, ["[4, 8, 12]"])

    def test_result_option_helpers_and_guard_invariants(self) -> None:
        source = """
        craft recover(message) { yield "recovered:" ++ message }
        emit is_ok(Ok(5))
        emit unwrap(Ok(5))
        emit is_err(Err("disk"))
        emit or_else(Err("disk"), recover)
        emit unwrap(Some("value"))
        emit invariant_guard(2 + 2 == 4, "math invariant")
        """
        self.assert_both_engines(source, ["true", "5", "true", "recovered:disk", "value", "true"])

    def test_failed_invariant_reports_language_error(self) -> None:
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine), self.assertRaisesRegex(ReaperRuntimeError, "invariant"):
                self.run_source('emit invariant_guard(false, "invariant failed")', engine)

    def test_comprehension_and_transducer_obey_collection_limits(self) -> None:
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine), self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
                self.run_source("emit [x for x in 0..5]", engine, max_collection_items=3)

    def test_let_else_requires_diverging_fallback(self) -> None:
        source = """
        craft invalid(values) {
            let [one, two] := values else { emit "invalid" }
            yield one
        }
        emit invalid([])
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine), self.assertRaisesRegex(ReaperRuntimeError, "must leave"):
                self.run_source(source, engine)


if __name__ == "__main__":
    unittest.main()
