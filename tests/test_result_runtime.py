from __future__ import annotations

import unittest

from reaper import Interpreter, ReaperRuntimeError
from reaper.memory import MemoryManager
from reaper.result import (
    RequestContext,
    ResultContractError,
    ResultValue,
    context_get,
    context_to_map,
    context_with,
    err,
    is_err,
    is_ok,
    ok,
    request_context,
    result_and_then,
    result_context,
    result_error,
    result_map,
    result_or,
    result_recover,
    result_value,
)
from reaper.typecheck import check_source


class RequestContextTests(unittest.TestCase):
    def test_context_is_explicit_and_copies_metadata(self):
        metadata = {"service": "gateway"}
        context = request_context("req-42", "trace-9", "parent-3", metadata)
        metadata["service"] = "changed"

        self.assertEqual(context_get(context, "request_id"), "req-42")
        self.assertEqual(context_get(context, "trace_id"), "trace-9")
        self.assertEqual(context_get(context, "parent_id"), "parent-3")
        self.assertEqual(context_get(context, "service"), "gateway")

    def test_context_with_returns_a_new_context(self):
        original = request_context("req-1", metadata={"region": "eu"})
        updated = context_with(original, "attempt", 2)

        self.assertIsNot(original, updated)
        self.assertIsNone(context_get(original, "attempt"))
        self.assertEqual(context_get(updated, "attempt"), 2)
        self.assertEqual(context_to_map(updated)["metadata"]["region"], "eu")

    def test_missing_optional_context_is_a_safe_empty_result(self):
        self.assertIsNone(context_get(None, "request_id"))
        self.assertEqual(context_to_map(None), {})

    def test_invalid_context_data_is_rejected(self):
        with self.assertRaisesRegex(ResultContractError, "request_id"):
            request_context("")
        with self.assertRaisesRegex(ResultContractError, "metadata"):
            request_context("req-1", metadata=[1, 2])
        with self.assertRaisesRegex(ResultContractError, "JSON-compatible"):
            request_context("req-1", metadata={"not_finite": float("nan")})


class ResultValueTests(unittest.TestCase):
    def test_success_and_error_have_distinct_shapes(self):
        success = ok({"answer": 42})
        failure = err("APP-E001", "upstream unavailable", {"retryable": True})

        self.assertTrue(is_ok(success))
        self.assertFalse(is_err(success))
        self.assertTrue(is_err(failure))
        self.assertFalse(is_ok(failure))
        self.assertEqual(result_value(success), {"answer": 42})
        self.assertEqual(
            result_error(failure),
            {
                "code": "APP-E001",
                "message": "upstream unavailable",
                "details": {"retryable": True},
            },
        )
        with self.assertRaisesRegex(ReaperRuntimeError, "APP-E001"):
            result_value(failure)

    def test_error_details_are_defensively_copied(self):
        details = {"attempt": 1}
        failure = err("APP-E002", "request failed", details)
        details["attempt"] = 99
        exposed = result_error(failure)
        exposed["details"]["attempt"] = 7

        self.assertEqual(result_error(failure)["details"]["attempt"], 1)

    def test_error_contract_rejects_bad_codes_messages_and_details(self):
        with self.assertRaisesRegex(ResultContractError, "error code"):
            err("bad code", "no")
        with self.assertRaisesRegex(ResultContractError, "error message"):
            err("APP-E001", "  ")
        with self.assertRaisesRegex(ResultContractError, "details"):
            err("APP-E001", "bad", ["not", "a", "map"])

    def test_map_preserves_failure_and_context(self):
        context = request_context("req-map")
        failure = err("APP-E003", "stop", context=context)
        called = []

        result = result_map(failure, lambda value: called.append(value), lambda fn, args: fn(*args))

        self.assertIs(result, failure)
        self.assertEqual(called, [])
        self.assertIs(result_context(result), context)

    def test_map_transforms_success(self):
        context = request_context("req-map-ok")
        result = result_map(ok(4, context), lambda value: value * 3, lambda fn, args: fn(*args))
        self.assertEqual(result_value(result), 12)
        self.assertIs(result_context(result), context)

    def test_and_then_requires_a_result_and_inherits_context(self):
        context = request_context("req-flat-map")
        result = result_and_then(
            ok(5, context),
            lambda value: ok(value + 1),
            lambda fn, args: fn(*args),
        )
        self.assertEqual(result_value(result), 6)
        self.assertIs(result_context(result), context)

        with self.assertRaisesRegex(TypeError, "Result value"):
            result_and_then(ok(1), lambda value: value + 1, lambda fn, args: fn(*args))

    def test_recover_receives_structured_error_and_inherits_context(self):
        context = request_context("req-recover")
        failure = err("APP-E004", "temporary", {"attempt": 2}, context)
        recovered = result_recover(
            failure,
            lambda error: ok(error["details"]["attempt"]),
            lambda fn, args: fn(*args),
        )
        self.assertEqual(result_value(recovered), 2)
        self.assertIs(result_context(recovered), context)

    def test_recover_does_not_run_on_success(self):
        result = ok(9)
        recovered = result_recover(
            result,
            lambda _error: self.fail("recovery callback must not run"),
            lambda fn, args: fn(*args),
        )
        self.assertIs(recovered, result)

    def test_fallback_returns_payload_without_throwing(self):
        self.assertEqual(result_or(ok(3), 0), 3)
        self.assertEqual(result_or(err("APP-E005", "missing"), 0), 0)

    def test_success_has_no_error_payload(self):
        self.assertIsNone(result_error(ok(7)))

    def test_runtime_heap_tracks_payloads_inside_results(self):
        heap = MemoryManager(max_heap_bytes=4096)
        result = heap.track(ok({"items": [1, 2, 3]}))
        self.assertGreaterEqual(heap.stats()["objects"], 2)
        self.assertEqual(heap.collect([result]), 0)
        self.assertGreaterEqual(heap.stats()["objects"], 2)
        self.assertEqual(heap.collect([]), 2)


class ResultLanguageTests(unittest.TestCase):
    SOURCE = '''
craft increment(value) {
    yield value + 1
}

craft validate(value) {
    when value > 10 {
        yield err("APP-E010", "value is too large")
    } otherwise {
        yield ok(value)
    }
}

craft fallback(error) {
    yield ok(0)
}

make context := request_context("req-42", "trace-42", nothing, resource_stats())
make initial := ok(5, context)
make mapped := initial :: result_map(increment)
make completed := mapped :: result_and_then(validate)
make failed := err("APP-E020", "network unavailable", resource_stats(), context)
make recovered := failed :: result_recover(fallback)
make context_details := context_to_map(context_with(context, "attempt", 1))

emit is_ok(completed)
emit result_value(completed)
emit is_err(failed)
emit result_value(recovered)
emit context_get(result_context(completed), "request_id")
emit context_details["metadata"]["attempt"]
'''

    def test_result_pipeline_and_context_run_in_treewalk_and_vm(self):
        outputs = []
        for engine in ("treewalk", "vm"):
            output = []
            Interpreter(output=output.append).run(self.SOURCE, engine=engine)
            outputs.append(output)

        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(
            outputs[0],
            ["true", "7", "true", "0", "req-42", "1"],
        )

    def test_result_value_propagates_a_structured_failure_as_runtime_error(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "APP-E404: not found"):
            Interpreter(output=lambda _line: None).run(
                'make failure := err("APP-E404", "not found")\n'
                'emit result_value(failure)'
            )

    def test_static_checker_infers_result_payload_and_context_types(self):
        checked = check_source('''
craft increment(value) { yield value + 1 }
craft validate(value) { yield ok(value) }
craft recover(error) { yield ok(0) }
make context := request_context("req-1")
make first := ok(1, context)
make mapped := first :: result_map(increment)
make chained := mapped :: result_and_then(validate)
make recovered := chained :: result_recover(recover)
make payload := result_value(mapped)
make fallback := result_or(mapped, 0)
make context_map := context_to_map(context_with(context, "attempt", 1))
make status := is_ok(recovered)
''')
        self.assertTrue(checked.ok, checked.as_dict())

    def test_static_checker_rejects_non_result_input(self):
        checked = check_source("result_value(42)")
        self.assertFalse(checked.ok)
        self.assertEqual(checked.diagnostics[0].code, "RPR-T0011")

    def test_static_checker_rejects_context_type_mismatch(self):
        checked = check_source('context_with(42, "attempt", 1)')
        self.assertFalse(checked.ok)
        self.assertEqual(checked.diagnostics[0].code, "RPR-T0012")

    def test_static_checker_rejects_flat_map_callback_with_plain_value(self):
        checked = check_source('''
craft increment(value) { yield value + 1 }
make result := ok(2) :: result_and_then(increment)
''')
        self.assertFalse(checked.ok)
        self.assertEqual(checked.diagnostics[0].code, "RPR-T0010")


if __name__ == "__main__":
    unittest.main()
