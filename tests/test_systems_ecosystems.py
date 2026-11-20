from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from reaper.cli import main as reaper_cli_main
from reaper.systems_ecosystems import (
    CATEGORIES,
    describe_toolchains,
    load_matrix,
    main,
    select_ecosystems,
    validate_matrix,
)


class SystemsEcosystemMatrixTests(unittest.TestCase):
    def test_catalogue_covers_all_40_requested_positions(self):
        data = load_matrix()
        self.assertEqual(validate_matrix(data), 40)
        self.assertEqual([item["index"] for item in data["entries"]], list(range(1, 41)))
        names = {item["name"] for item in data["entries"]}
        false_entry = next(item for item in data["entries"] if item["id"] == "esoteric-false")
        self.assertEqual(false_entry["commands"], [])
        self.assertTrue({
            "x86", "ARM", "RISC-V", "MIPS", "AVR", "6502", "Z80",
            "C", "C++", "Rust", "Zig", "D", "Nim", "Ada", "Modula-2", "Oberon",
            "Verilog", "SystemVerilog", "VHDL", "Chisel", "Bluespec",
            "WebAssembly", "LLVM IR", "JVM", "Dalvik", "LuaJIT", "Forth",
            "PostScript", "BCPL", "BLISS", "Brainfuck", "FALSE", "Befunge",
            "Malbolge", "Piet", "Whitespace", "GLSL", "HLSL", "SPIR-V", "PTX",
        }.issubset(names))

    def test_category_counts_and_profiles_are_complete(self):
        data = load_matrix()
        counts = {
            category: sum(item["category"] == category for item in data["entries"])
            for category in CATEGORIES
        }
        self.assertEqual(counts, {
            "isa": 7, "system-language": 9, "hdl": 5,
            "vm-bytecode": 9, "specialized": 10,
        })
        for profile in ("reaper", "pytyliki", "oplague"):
            self.assertTrue(select_ecosystems(data, profile=profile, which=lambda _: None))

    def test_toolchain_probe_is_injectable_and_never_executes_tools(self):
        data = load_matrix()
        riscv = next(item for item in data["entries"] if item["id"] == "isa-riscv")
        state, found = describe_toolchains(
            riscv,
            which=lambda command: "/mock/bin/riscv64-unknown-elf-gcc"
            if command == "riscv64-unknown-elf-gcc" else None,
        )
        self.assertEqual(state, "available")
        self.assertEqual(found, {"riscv64-unknown-elf-gcc": "/mock/bin/riscv64-unknown-elf-gcc"})
        available = select_ecosystems(
            data,
            available_only=True,
            which=lambda command: "/mock/bin/tool" if command == "spirv-val" else None,
        )
        self.assertEqual([item["name"] for item in available], ["SPIR-V"])
        self.assertEqual(available[0]["support_boundary"], "toolchain-discovery-only")

    def test_exact_target_lookup_and_category_filter(self):
        data = load_matrix()
        target = select_ecosystems(data, target="llvm ir", which=lambda _: None)
        self.assertEqual([item["id"] for item in target], ["vm-llvm-ir"])
        hdl = select_ecosystems(data, category="hdl", which=lambda _: None)
        self.assertEqual([item["name"] for item in hdl], [
            "Verilog", "SystemVerilog", "VHDL", "Chisel", "Bluespec",
        ])
        with self.assertRaisesRegex(ValueError, "unknown project profile"):
            select_ecosystems(data, profile="not-a-project")

    def test_validation_rejects_duplicate_ids_and_unknown_categories(self):
        data = load_matrix()
        broken = json.loads(json.dumps(data))
        broken["entries"][1]["id"] = broken["entries"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate ecosystem id"):
            validate_matrix(broken)
        broken = json.loads(json.dumps(data))
        broken["entries"][0]["category"] = "magic"
        with self.assertRaisesRegex(ValueError, "unknown category"):
            validate_matrix(broken)

    def test_cli_verify_and_json_output(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--verify"]), 0)
        self.assertIn("PASS (40 entries; isa=7", output.getvalue())
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--target", "PTX", "--json"]), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["results"][0]["id"], "gpu-ptx")
        self.assertEqual(payload["results"][0]["support_boundary"], "toolchain-discovery-only")

    def test_cli_rejects_unknown_target(self):
        error = StringIO()
        with redirect_stderr(error):
            self.assertEqual(main(["--target", "not-a-target"]), 1)
        self.assertIn("unknown or unavailable target", error.getvalue())

    def test_top_level_reaper_cli_exposes_the_registry(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(reaper_cli_main(["--systems-ecosystems"]), 0)
        self.assertIn("Systems ecosystem matrix: 40 result(s)", output.getvalue())
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                reaper_cli_main(["--ecosystem", "RISC-V", "--ecosystems-json"]), 0
            )
        self.assertEqual(json.loads(output.getvalue())["results"][0]["name"], "RISC-V")
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                reaper_cli_main(["--ecosystem-category", "hdl"]), 0
            )
        self.assertIn("Bluespec", output.getvalue())

    def test_external_matrix_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ecosystems.json"
            path.write_text(json.dumps(load_matrix()), encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--verify"], matrix_path=path), 0)
            self.assertIn("PASS (40 entries", output.getvalue())


if __name__ == "__main__":
    unittest.main()
