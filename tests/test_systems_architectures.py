from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from reaper.systems_architectures import (
    describe_toolchains,
    load_matrix,
    main,
    select_architectures,
    validate_matrix,
)


class SystemsArchitectureMatrixTests(unittest.TestCase):
    def test_catalogue_has_14_ordered_targets(self):
        data = load_matrix()
        self.assertEqual(validate_matrix(data), 14)
        self.assertEqual([item["index"] for item in data["architectures"]], list(range(1, 15)))

    def test_windows_driver_target_families_are_explicit(self):
        data = load_matrix()
        decorations = {item["name"]: item["windows_inf_decoration"] for item in data["architectures"]}
        self.assertEqual(decorations["x86"], "NTx86")
        self.assertEqual(decorations["x86_64"], "NTamd64")
        self.assertEqual(decorations["aarch64"], "NTarm64")
        self.assertEqual(decorations["armv7-m"], None)

    def test_project_profiles_rank_relevant_targets(self):
        data = load_matrix()
        reaper = select_architectures(data, profile="reaper", which=lambda _: None)
        oplague = select_architectures(data, profile="oplague", which=lambda _: None)
        self.assertTrue(reaper)
        self.assertTrue(oplage)
        self.assertGreaterEqual(reaper[0]["profile_score"], reaper[-1]["profile_score"])
        self.assertIn("wasm32", {item["name"] for item in reaper})
        self.assertIn("x86_64", {item["name"] for item in oplague})
        self.assertNotIn("riscv64", {item["name"] for item in oplague})

    def test_toolchain_probe_is_injectable_and_path_only(self):
        data = load_matrix()
        target = next(item for item in data["architectures"] if item["name"] == "x86_64")
        state, found = describe_toolchains(target, which=lambda command: f"/mock/bin/{command}" if command == "clang" else None)
        self.assertEqual(state, "available")
        self.assertEqual(found, {"clang": "/mock/bin/clang"})
        available = select_architectures(data, available_only=True, which=lambda command: "/mock/bin/tool" if command == "avr-gcc" else None)
        self.assertEqual([item["name"] for item in available], ["avr"])

    def test_filter_and_bad_profile(self):
        data = load_matrix()
        embedded = select_architectures(data, tags={"bare-metal"}, which=lambda _: None)
        self.assertIn("riscv64", {item["name"] for item in embedded})
        with self.assertRaisesRegex(ValueError, "unknown project profile"):
            select_architectures(data, profile="not-a-project")
    
    def test_validation_rejects_duplicates_and_invalid_width(self):
        data = load_matrix()
        broken = json.loads(json.dumps(data))
        broken["architectures"][1]["id"] = broken["architectures"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate architecture id"):
            validate_matrix(broken)
        broken = json.loads(json.dumps(data))
        broken["architectures"][0]["word_bits"] = 24
        with self.assertRaisesRegex(ValueError, "word_bits"):
            validate_matrix(broken)

    def test_cli_and_external_matrix_path(self):
        output = StringIO()
        with redirect_stdout(output):
            result = main(["--profile", "oplague", "--json"])
        self.assertEqual(result, 0)
        self.assertIn("systems-architecture-matrix/v1", output.getvalue())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "matrix.json"
            path.write_text(json.dumps(load_matrix()), encoding="utf-8")
            with redirect_stdout(StringIO()) as sink:
                self.assertEqual(main(["--verify"], matrix_path=path), 0)
                self.assertIn("PASS (14 profiles)", sink.getvalue())


if __name__ == "__main__":
    unittest.main()
