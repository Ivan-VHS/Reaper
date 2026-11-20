from __future__ import annotations

import contextlib
import io
import unittest

from reaper.reference_ecosystems import (
    load_registry,
    main,
    resolve_ecosystem,
    select_ecosystems,
    validate_registry,
)


class ReferenceEcosystemTests(unittest.TestCase):
    def test_registry_contains_the_exact_66_positions(self):
        data = load_registry()
        self.assertEqual(validate_registry(data), 66)
        self.assertEqual([item["index"] for item in data["languages"]], list(range(1, 67)))
        self.assertEqual(data["languages"][0]["name"], "x86 / x86-64 Assembly")
        self.assertEqual(data["languages"][-1]["name"], "Forth-83 / CamelForth")

    def test_names_and_aliases_resolve_without_reordering(self):
        data = load_registry()
        self.assertEqual(resolve_ecosystem(data, "RISC-V")["index"], 3)
        self.assertEqual(resolve_ecosystem(data, "CUDA")["index"], 50)
        self.assertEqual(resolve_ecosystem(data, "CamelForth")["index"], 66)
        self.assertIsNone(resolve_ecosystem(data, "not-a-language"))

    def test_hdl_and_gpu_profiles_are_separate(self):
        data = load_registry()
        hdl = select_ecosystems(data, category="hdl")
        gpu = select_ecosystems(data, category="gpu-compute")
        self.assertEqual(len(hdl), 10)
        self.assertEqual(hdl[0]["name"], "Verilog")
        self.assertIn("CUDA C++", {item["name"] for item in gpu})
        self.assertNotIn("Verilog", {item["name"] for item in gpu})

    def test_reaper_profile_ranks_native_and_safety_references(self):
        results = select_ecosystems(load_registry(), profile="reaper")
        self.assertTrue(results)
        self.assertGreaterEqual(results[0]["profile_score"], results[-1]["profile_score"])
        names = {item["name"] for item in results}
        self.assertIn("Rust", names)
        self.assertIn("LLVM IR", names)

    def test_toolchain_probe_is_injectable_and_never_invokes_tools(self):
        data = load_registry()
        which = lambda command: f"/mock/bin/{command}" if command in {"nvcc", "rustc"} else None
        results = select_ecosystems(data, profile="gpu", available_only=True, which=which)
        self.assertTrue(results)
        found = {item["name"] for item in results}
        self.assertIn("CUDA C++", found)
        self.assertTrue(all(item["toolchain_state"] == "available" for item in results))

    def test_entries_without_known_toolchain_candidates_are_not_probed(self):
        data = load_registry()
        item = resolve_ecosystem(data, "FALSE")
        self.assertEqual(item["toolchains"], [])
        selected = select_ecosystems(data, which=lambda _command: None)
        false_entry = next(entry for entry in selected if entry["name"] == "FALSE")
        self.assertEqual(false_entry["toolchain_state"], "not-probed")

    def test_registry_rejects_missing_positions(self):
        data = load_registry()
        broken = dict(data)
        broken["languages"] = data["languages"][:-1]
        with self.assertRaisesRegex(ValueError, "exactly 66"):
            validate_registry(broken)

    def test_cli_verify_and_unknown_lookup(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["verify"]), 0)
        self.assertIn("PASS (66 entries)", output.getvalue())
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(main(["show", "unknown-ecosystem"]), 2)
        self.assertIn("unknown ecosystem", error.getvalue())


if __name__ == "__main__":
    unittest.main()
