from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.embedded import (
    EmbeddedError, PROFILES, RegisterBank, SimRegister, TelemetryDecoder,
    encode_telemetry_frame, get_profile, init_project, inspect_project,
    linker_script, load_svd, memory_budget, parse_diagnostics, parse_map_file,
    parse_size_output, profile_from_dict,
)


class EmbeddedProfileTests(unittest.TestCase):
    def test_reference_profiles_are_explicit_and_well_formed(self) -> None:
        self.assertEqual(set(PROFILES), {
            "cortex-m4-reference", "riscv32imc-reference", "avr-atmega328p"
        })
        for profile in PROFILES.values():
            self.assertGreater(profile.flash.size, 0)
            self.assertGreater(profile.sram.size, 0)
            self.assertLessEqual(profile.stack_bytes, profile.sram.size)
            self.assertTrue(profile.compiler)

    def test_overlapping_memory_regions_are_rejected(self) -> None:
        raw = get_profile("cortex-m4-reference").to_dict()
        raw["sram"]["base"] = raw["flash"]["base"] + 64
        with self.assertRaisesRegex(EmbeddedError, "overlap"):
            profile_from_dict(raw)

    def test_invalid_address_range_is_rejected(self) -> None:
        raw = get_profile("cortex-m4-reference").to_dict()
        raw["flash"]["base"] = 0xFFFFFFF0
        with self.assertRaises(EmbeddedError):
            profile_from_dict(raw)

    def test_linker_script_contains_declared_regions(self) -> None:
        script = linker_script(get_profile("cortex-m4-reference"))
        self.assertIn("ENTRY(main)", script)
        self.assertIn("ORIGIN = 0x08000000", script)
        self.assertIn("LENGTH = 131072", script)


class EmbeddedProjectTests(unittest.TestCase):
    def test_init_and_inspect_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = init_project(Path(temporary) / "board")
            self.assertTrue((project / "embedded.json").is_file())
            self.assertTrue((project / "linker.ld").is_file())
            self.assertTrue((project / "src" / "main.c").is_file())
            report = inspect_project(project)
            self.assertEqual(report["profile"]["id"], "cortex-m4-reference")
            self.assertEqual(report["sources"], ["src/main.c"])

    def test_init_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = init_project(Path(temporary) / "board")
            with self.assertRaisesRegex(EmbeddedError, "refusing to overwrite"):
                init_project(project)

    def test_custom_profile_round_trip(self) -> None:
        raw = get_profile("riscv32imc-reference").to_dict()
        restored = profile_from_dict(json.loads(json.dumps(raw)))
        self.assertEqual(restored.id, "riscv32imc-reference")
        self.assertEqual(restored.flags, ("-march=rv32imc", "-mabi=ilp32"))


class MemoryBudgetTests(unittest.TestCase):
    def test_flash_and_sram_budgets_include_data_and_stack(self) -> None:
        profile = get_profile("cortex-m4-reference")
        report = memory_budget(profile, {
            ".text": 1000, ".rodata": 200, ".data": 100,
            ".bss": 300, ".noinit": 50,
        })
        self.assertEqual(report["flash_used"], 1300)
        self.assertEqual(report["sram_static_used"], 450)
        self.assertEqual(report["sram_used_with_stack"], 450 + profile.stack_bytes)
        self.assertTrue(report["flash_ok"])
        self.assertTrue(report["sram_ok"])

    def test_overflow_is_reported_without_wrapping(self) -> None:
        profile = get_profile("avr-atmega328p")
        report = memory_budget(profile, {".text": profile.flash.size + 1})
        self.assertFalse(report["flash_ok"])
        self.assertTrue(report["flash_percent"] > 100)


class ToolchainDiagnosticsTests(unittest.TestCase):
    def test_gcc_diagnostics_are_clickable_records(self) -> None:
        diagnostics = parse_diagnostics(
            "src/main.c:17:4: error: expected ';' before token\n"
            "src/startup.S:9: warning: unused label\n"
        )
        self.assertEqual(diagnostics[0]["line"], 17)
        self.assertEqual(diagnostics[0]["column"], 4)
        self.assertEqual(diagnostics[0]["severity"], "error")
        self.assertIsNone(diagnostics[1]["column"])

    def test_size_output_sections(self) -> None:
        sections = parse_size_output(
            "section size addr\n.text 100 0x8000000\n.data 12 0x20000000\n"
        )
        self.assertEqual(sections, {".text": 100, ".data": 12})

    def test_linker_map_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "firmware.map"
            path.write_text(
                ".text 0x0000000008000000 0x00000120\n"
                ".bss 0x0000000020000000 0x00000030\n",
                encoding="utf-8",
            )
            self.assertEqual(parse_map_file(path), {".text": 0x120, ".bss": 0x30})


class SimulatedHardwareTests(unittest.TestCase):
    def test_register_writes_respect_access_and_masks(self) -> None:
        bank = RegisterBank()
        bank.add(SimRegister("GPIOA.ODR", 0x40020014, 0, 0xFFFF, "read-write"))
        bank.add(SimRegister("GPIOA.IDR", 0x40020010, 3, 0, "read-only"))
        self.assertEqual(bank.write("GPIOA.ODR", 5), 5)
        self.assertEqual(bank.read("GPIOA.IDR"), 3)
        with self.assertRaisesRegex(EmbeddedError, "reserved"):
            bank.write("GPIOA.ODR", 0x10000)
        with self.assertRaisesRegex(EmbeddedError, "read-only"):
            bank.write("GPIOA.IDR", 1)

    def test_svd_import_reads_peripheral_registers(self) -> None:
        xml = """<device><peripherals><peripheral><name>GPIOA</name>
        <baseAddress>0x40020000</baseAddress><registers>
        <register><name>ODR</name><addressOffset>0x14</addressOffset>
        <resetValue>0x0</resetValue><access>read-write</access></register>
        <register><name>IDR</name><addressOffset>0x10</addressOffset>
        <resetValue>0x2</resetValue><access>read-only</access></register>
        </registers></peripheral></peripherals></device>"""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "device.svd"
            path.write_text(xml, encoding="utf-8")
            bank = load_svd(path)
        self.assertEqual(bank.read("GPIOA.IDR"), 2)
        self.assertEqual(bank.snapshot()["GPIOA.ODR"]["address"], 0x40020014)


class TelemetryTests(unittest.TestCase):
    def test_incremental_frame_decode(self) -> None:
        frame = encode_telemetry_frame(7, b"hello")
        decoder = TelemetryDecoder()
        self.assertEqual(decoder.feed(frame[:3]), [])
        self.assertEqual(decoder.feed(frame[3:]), [(7, b"hello")])

    def test_bad_crc_is_discarded_and_next_frame_recovers(self) -> None:
        bad = bytearray(encode_telemetry_frame(1, b"x"))
        bad[-1] ^= 0xFF
        good = encode_telemetry_frame(2, b"ok")
        decoder = TelemetryDecoder()
        self.assertEqual(decoder.feed(bytes(bad) + good), [(2, b"ok")])

    def test_frame_payload_limit(self) -> None:
        with self.assertRaises(EmbeddedError):
            encode_telemetry_frame(1, b"x" * 4097)
        with self.assertRaises(EmbeddedError):
            TelemetryDecoder(max_payload=4097)


if __name__ == "__main__":
    unittest.main()
