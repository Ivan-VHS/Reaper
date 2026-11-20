from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile

from reaper.interop import (
    EXPECTED_GROUP_COUNTS,
    inspect_toolchains,
    load_matrix,
    main,
    select_entries,
    validate_matrix,
)


class InteroperabilityCatalogueTests(unittest.TestCase):
    def test_catalogue_contains_all_forty_requested_ecosystems(self):
        data = load_matrix()
        self.assertEqual(validate_matrix(data), 40)
        counts = {group: 0 for group in EXPECTED_GROUP_COUNTS}
        names = set()
        for item in data["entries"]:
            counts[item["group"]] += 1
            names.add(item["name"])
        self.assertEqual(counts, EXPECTED_GROUP_COUNTS)
        self.assertTrue({"x86", "ARM", "RISC-V", "MIPS", "AVR", "6502", "Z80"} <= names)
        self.assertTrue({"C", "C++", "Rust", "Zig", "D", "Nim", "Ada", "Modula-2", "Oberon"} <= names)
        self.assertTrue({"Verilog", "SystemVerilog", "VHDL", "Chisel", "Bluespec"} <= names)
        self.assertTrue({"WebAssembly", "LLVM IR", "JVM", "Dalvik", "LuaJIT", "Forth", "PostScript", "BCPL", "BLISS"} <= names)
        self.assertTrue({"Brainfuck", "FALSE", "Befunge", "Malbolge", "Piet", "Whitespace", "GLSL", "HLSL", "SPIR-V", "PTX"} <= names)

    def test_group_filter_and_injected_path_lookup(self):
        data = load_matrix()
        isa = select_entries(
            data,
            group="isa",
            which=lambda command: f"/mock/bin/{command}" if command == "avr-gcc" else None,
        )
        self.assertEqual(len(isa), 7)
        avr = next(item for item in isa if item["name"] == "AVR")
        self.assertEqual(avr["toolchain_state"], "available")
        self.assertEqual(avr["toolchains_found"], {"avr-gcc": "/mock/bin/avr-gcc"})

    def test_empty_command_list_is_metadata_only_not_available(self):
        data = load_matrix()
        bliss = next(item for item in data["entries"] if item["name"] == "BLISS")
        self.assertEqual(inspect_toolchains(bliss, which=lambda _: None)["toolchain_state"], "metadata-only")
        self.assertEqual(select_entries(data, available_only=True, which=lambda _: None), [])

    def test_validator_rejects_duplicate_ids_and_wrong_distribution(self):
        data = json.loads(json.dumps(load_matrix()))
        data["entries"][1]["id"] = data["entries"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate entry id"):
            validate_matrix(data)
        data = json.loads(json.dumps(load_matrix()))
        data["entries"].pop()
        with self.assertRaisesRegex(ValueError, "exactly 40"):
            validate_matrix(data)

    def test_verify_cli(self):
        output = StringIO()
        with redirect_stdout(output):
            result = main(["verify"])
        self.assertEqual(result, 0)
        self.assertIn("PASS (40 entries)", output.getvalue())

    def test_external_matrix_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "interop.json"
            path.write_text(json.dumps(load_matrix()), encoding="utf-8")
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(main(["list", "--group", "hdl", "--json"], matrix_path=path), 0)
            report = json.loads(output.getvalue())
            self.assertEqual(len(report["results"]), 5)


if __name__ == "__main__":
    unittest.main()
