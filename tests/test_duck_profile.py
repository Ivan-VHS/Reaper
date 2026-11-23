from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter, ReaperRuntimeError
from reaper.typecheck import check_source


class DuckProfileRuntimeTests(unittest.TestCase):
    def interpreter(self, **options):
        return Interpreter(output=lambda _line: None, **options)

    def test_inspection_reports_only_safe_shape_metadata(self):
        runtime = self.interpreter()
        runtime.globals.define(
            "settings",
            {"host": "private.example", "port": 443, "enabled": True},
        )
        runtime.run(
            'make report := duck_inspect(settings)\n'
            'make structural := duck_supports(settings, "structural")'
        )

        self.assertEqual(
            runtime.globals.get("report"),
            {
                "kind": "map",
                "capabilities": ["indexable", "iterable", "keyed", "sized", "structural"],
                "size": 3,
                "fields": ["enabled", "host", "port"],
            },
        )
        self.assertTrue(runtime.globals.get("structural"))
        self.assertNotIn("private.example", str(runtime.globals.get("report")))

    def test_capabilities_are_kind_based_and_stable(self):
        runtime = self.interpreter()
        runtime.run(
            'make sequence := duck_capabilities([1, 2])\n'
            'make callable := duck_supports(range(3), "callable")\n'
            'make range_kind := kind(range(3))'
        )
        self.assertEqual(
            runtime.globals.get("sequence"),
            ["indexable", "iterable", "sized"],
        )
        self.assertFalse(runtime.globals.get("callable"))
        self.assertEqual(runtime.globals.get("range_kind"), "range")

    def test_map_membership_counts_present_nothing_as_present(self):
        runtime = self.interpreter()
        runtime.globals.define("settings", {"optional": None})
        runtime.run(
            'make present := duck_has(settings, "optional")\n'
            'make absent := duck_has(settings, "missing")'
        )
        self.assertTrue(runtime.globals.get("present"))
        self.assertFalse(runtime.globals.get("absent"))

    def test_probe_is_a_quiet_canary_and_preserves_requested_order(self):
        runtime = self.interpreter()
        runtime.globals.define("settings", {"host": "localhost"})
        runtime.run(
            'make report := duck_probe(settings, ["port", "host", "tls"])'
        )
        self.assertEqual(
            runtime.globals.get("report"),
            {"ok": False, "kind": "map", "missing": ["port", "tls"]},
        )

    def test_probe_returns_a_negative_result_for_non_maps(self):
        runtime = self.interpreter()
        runtime.run('make report := duck_probe(42, ["host"])')
        self.assertEqual(
            runtime.globals.get("report"),
            {"ok": False, "kind": "number", "missing": ["host"]},
        )

    def test_require_returns_the_original_map_unchanged(self):
        runtime = self.interpreter()
        settings = {"host": "localhost", "port": 8080}
        runtime.globals.define("settings", settings)
        runtime.run('make validated := settings :: duck_require(["host", "port"])')
        self.assertIs(runtime.globals.get("validated"), settings)

    def test_require_rejects_missing_fields(self):
        runtime = self.interpreter()
        runtime.globals.define("settings", {"host": "localhost"})
        with self.assertRaisesRegex(
            ReaperRuntimeError,
            "duck contract is missing required field",
        ):
            runtime.run('duck_require(settings, ["host", "port"])')

    def test_adapt_adds_only_missing_defaults_without_mutating_source(self):
        runtime = self.interpreter()
        source = {"host": "custom.example", "port": 9000}
        defaults = {"host": "default.example", "tls": False}
        runtime.globals.define("source", source)
        runtime.globals.define("defaults", defaults)
        runtime.run('make configured := duck_adapt(source, defaults)')

        self.assertEqual(
            runtime.globals.get("configured"),
            {"host": "custom.example", "port": 9000, "tls": False},
        )
        self.assertEqual(source, {"host": "custom.example", "port": 9000})
        self.assertEqual(defaults, {"host": "default.example", "tls": False})

    def test_adapt_enforces_the_collection_budget(self):
        runtime = self.interpreter(max_collection_items=2)
        runtime.globals.define("source", {"one": 1, "two": 2})
        runtime.globals.define("defaults", {"three": 3})
        with self.assertRaisesRegex(ReaperRuntimeError, "duck map item limit"):
            runtime.run("duck_adapt(source, defaults)")

    def test_duplicate_required_fields_are_checked_once_in_input_order(self):
        runtime = self.interpreter()
        runtime.globals.define("settings", {"host": "localhost"})
        runtime.run(
            'make report := duck_probe(settings, ["port", "host", "port"])'
        )
        self.assertEqual(
            runtime.globals.get("report"),
            {"ok": False, "kind": "map", "missing": ["port"]},
        )

    def test_probe_enforces_the_field_budget(self):
        runtime = self.interpreter(max_collection_items=2)
        with self.assertRaisesRegex(ReaperRuntimeError, "field limit"):
            runtime.run('duck_probe(42, ["one", "two", "three"])')

    def test_adapt_does_not_replace_explicit_nothing_with_a_default(self):
        runtime = self.interpreter()
        source = {"timeout": None}
        runtime.globals.define("source", source)
        runtime.globals.define("defaults", {"timeout": 30})
        runtime.run("make configured := duck_adapt(source, defaults)")
        self.assertIsNone(runtime.globals.get("configured")["timeout"])
        self.assertIsNone(source["timeout"])

    def test_adapt_rejects_non_text_map_keys(self):
        runtime = self.interpreter()
        runtime.globals.define("source", {1: "not a field name"})
        runtime.globals.define("defaults", {"enabled": True})
        with self.assertRaisesRegex(ReaperRuntimeError, "keys must be text"):
            runtime.run("duck_adapt(source, defaults)")

    def test_unknown_capabilities_fail_closed(self):
        runtime = self.interpreter()
        runtime.run('make supported := duck_supports([1], "future_magic")')
        self.assertFalse(runtime.globals.get("supported"))

    def test_duck_profile_has_treewalk_and_vm_parity(self):
        results = []
        for engine in ("treewalk", "vm"):
            runtime = self.interpreter()
            runtime.globals.define("source", {"enabled": True})
            runtime.globals.define("defaults", {"retries": 3})
            runtime.run(
                'make result := source :: duck_adapt(defaults)\n'
                'make report := duck_probe(result, ["enabled", "retries"])',
                engine=engine,
            )
            results.append(
                (runtime.globals.get("result"), runtime.globals.get("report"))
            )

        self.assertEqual(results[0], results[1])
        self.assertEqual(
            results[0][1],
            {"ok": True, "kind": "map", "missing": []},
        )


    def test_checked_in_example_typechecks_and_runs(self):
        example = Path(__file__).resolve().parents[1] / "examples" / "duck_profile.rpr"
        source = example.read_text(encoding="utf-8")
        checked = check_source(source, str(example))
        self.assertTrue(checked.ok, checked.as_dict())

        output: list[str] = []
        Interpreter(output=output.append).run(source, filename=str(example))
        self.assertTrue(any("resource contract: ready" in line for line in output))
        self.assertTrue(any("structural" in line for line in output))


class DuckProfileTypeCheckerTests(unittest.TestCase):
    def test_duck_builtins_have_known_types_and_arity(self):
        result = check_source(
            'make resources := resource_stats()\n'
            'make checked := resources :: duck_require(["open_files", "limit"])\n'
            'make report := duck_inspect(checked)\n'
            'make status := duck_supports(checked, "keyed")\n'
            'make probe := duck_probe(checked, "open_files")\n'
            'make adapted := duck_adapt(checked, heap_stats())\n'
            'make fields := duck_capabilities(adapted)\n'
            'make runtime := runtime_stats()'
        )
        self.assertTrue(result.ok, result.as_dict())

    def test_duck_contract_rejects_statically_known_non_map(self):
        result = check_source('duck_require([1, 2], "host")')
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0008")

    def test_duck_field_name_must_be_text(self):
        result = check_source("duck_has(resource_stats(), 7)")
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0005")

    def test_duck_adapt_requires_two_maps(self):
        result = check_source("duck_adapt(resource_stats(), [1, 2])")
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0008")


if __name__ == "__main__":
    unittest.main()
