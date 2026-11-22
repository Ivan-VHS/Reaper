from __future__ import annotations

import ctypes
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper import Interpreter, native
from reaper.ffi import FfiError, PytylikiBridge


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeLibrary:
    def __init__(self, version=1):
        self.pytyliki_abi_version = FakeFunction(lambda: version)
        self.pytyliki_v1_norm_f64 = FakeFunction(self.norm)
        self.pytyliki_v1_dot_f64 = FakeFunction(self.dot)
        self.pytyliki_v1_distance_f64 = FakeFunction(self.distance)
        self.pytyliki_v1_orthogonal_f64 = FakeFunction(self.orthogonal)
        self.pytyliki_v1_embedded_profile_count = FakeFunction(self.embedded_count)
        self.pytyliki_v1_embedded_profile_at = FakeFunction(self.embedded_profile)
        self.pytyliki_v1_embedded_budget_evaluate = FakeFunction(self.embedded_budget)
        self.pytyliki_v1_plugin_count = FakeFunction(self.plugin_count)
        self.pytyliki_v1_plugin_at = FakeFunction(self.plugin_at)
        self.pytyliki_v1_plugin_find = FakeFunction(self.plugin_find)

    @staticmethod
    def plugin_count(output):
        output._obj.value = 2
        return 0

    @staticmethod
    def _write_plugin(index, output):
        records = (
            (b"operandu", b"Operandu", b"Data & logic", b"inspect_value",
             b"value.validation;schema.inspection;expression.metadata"),
            (b"dropaul", b"Dropaul", b"Actions & workflows", b"plan_workflow",
             b"workflow.graph;dependency.ordering;dry_run"),
        )
        item = output._obj
        (item.id, item.name, item.domain, item.service, item.capabilities) = records[index]
        return 0

    @classmethod
    def plugin_at(cls, index, output):
        if index >= 2:
            return -1
        return cls._write_plugin(index, output)

    @classmethod
    def plugin_find(cls, query, output):
        key = query.decode("utf-8").casefold()
        keys = ("operandu", "dropaul")
        names = ("operandu", "dropaul")
        display_names = ("Operandu", "Dropaul")
        for index, candidate in enumerate(keys):
            if key in {candidate, display_names[index].casefold()}:
                return cls._write_plugin(index, output)
        return -1

    @staticmethod
    def embedded_count(output):
        output._obj.value = 3
        return 0

    @staticmethod
    def embedded_profile(index, output):
        profiles = (
            (b"cortex-m4-reference", b"arm-cortex-m", b"arm-none-eabi-gcc",
             b"-mcpu=cortex-m4 -mthumb", 84_000_000, 0x08000000, 512 * 1024,
             0x20000000, 128 * 1024, 2048, 1),
            (b"riscv32imc-reference", b"riscv32", b"riscv64-unknown-elf-gcc",
             b"-march=rv32imc -mabi=ilp32", 50_000_000, 0x20000000, 256 * 1024,
             0x80000000, 64 * 1024, 2048, 1),
            (b"avr-atmega328p", b"avr", b"avr-gcc", b"-mmcu=atmega328p",
             16_000_000, 0, 32 * 1024, 0x800100, 2 * 1024, 256, 0),
        )
        if index >= len(profiles):
            return -1
        item = output._obj
        (item.id, item.architecture, item.compiler, item.compiler_flags,
         item.clock_hz, item.flash_base, item.flash_size_bytes, item.sram_base,
         item.sram_size_bytes, item.stack_reserve_bytes, item.is_reference_profile) = profiles[index]
        return 0

    @staticmethod
    def embedded_budget(profile_id, sections, output):
        if profile_id != b"cortex-m4-reference":
            return -1
        values = sections._obj
        result = output._obj
        result.flash_used_bytes = values.text_bytes + values.rodata_bytes + values.data_bytes
        result.sram_used_bytes = values.data_bytes + values.bss_bytes + values.noinit_bytes + values.stack_reserve_bytes
        result.flash_total_bytes = 512 * 1024
        result.sram_total_bytes = 128 * 1024
        result.flash_percent = result.flash_used_bytes * 100.0 / result.flash_total_bytes
        result.sram_percent = result.sram_used_bytes * 100.0 / result.sram_total_bytes
        result.flash_fits = int(result.flash_used_bytes <= result.flash_total_bytes)
        result.sram_fits = int(result.sram_used_bytes <= result.sram_total_bytes)
        return 0

    @staticmethod
    def norm(vector, count, output):
        values = [vector[index] for index in range(count)]
        output._obj.value = sum(value * value for value in values) ** 0.5
        return 0

    @staticmethod
    def dot(left, right, count, output):
        output._obj.value = sum(left[index] * right[index] for index in range(count))
        return 0

    @staticmethod
    def distance(left, right, count, output):
        output._obj.value = sum((left[index] - right[index]) ** 2 for index in range(count)) ** 0.5
        return 0

    @staticmethod
    def orthogonal(left, right, count, tolerance, output):
        a = [left[index] for index in range(count)]
        b = [right[index] for index in range(count)]
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        output._obj.value = int(na == 0 or nb == 0 or abs(dot / (na * nb)) <= tolerance)
        return 0


class NativeBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        native._load_library.cache_clear()

    def tearDown(self) -> None:
        native._load_library.cache_clear()

    def test_explicit_path_and_numeric_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()) as loader:
                self.assertEqual(native.pytyliki_norm([3, 4], str(path)), 5.0)
                self.assertEqual(native.pytyliki_dot([3, 4], [0, 2], str(path)), 8.0)
                self.assertEqual(native.pytyliki_distance([3, 4], [0, 0], str(path)), 5.0)
                self.assertTrue(native.pytyliki_orthogonal([1, 0], [0, 1], 1e-12, str(path)))
                self.assertEqual(loader.call_count, 1)

    def test_rejects_relative_path_missing_file_and_wrong_abi(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute"):
            native._load_library("pytyliki_ffi.dll")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with self.assertRaisesRegex(ValueError, "unsupported Pytyliki ABI"):
                with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary(version=2)):
                    native._load_library(str(path))

    def test_embedded_profile_and_budget_abi(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()):
                profiles = native.pytyliki_embedded_profiles(str(path))
                budget = native.pytyliki_embedded_budget(
                    "cortex-m4-reference",
                    {
                        "text_bytes": 1024, "rodata_bytes": 256, "data_bytes": 128,
                        "bss_bytes": 512, "noinit_bytes": 64, "stack_reserve_bytes": 2048,
                    },
                    str(path),
                )
        self.assertEqual(len(profiles), 3)
        self.assertEqual(profiles[0]["id"], "cortex-m4-reference")
        self.assertEqual(profiles[0]["flash"]["size"], 512 * 1024)
        self.assertTrue(profiles[0]["is_reference_profile"])
        self.assertEqual(budget["flash_used_bytes"], 1408)
        self.assertEqual(budget["sram_used_bytes"], 2752)
        self.assertTrue(budget["flash_fits"] and budget["sram_fits"])

    def test_embedded_budget_rejects_invalid_section_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing"):
            native.pytyliki_embedded_budget("cortex-m4-reference", {}, "/unused")
        with self.assertRaisesRegex(TypeError, "integer"):
            native.pytyliki_embedded_budget(
                "cortex-m4-reference",
                {
                    "text_bytes": True, "rodata_bytes": 0, "data_bytes": 0,
                    "bss_bytes": 0, "noinit_bytes": 0, "stack_reserve_bytes": 0,
                },
                "/unused",
            )

    def test_plugin_catalogue_and_name_lookup_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()):
                catalog = native.pytyliki_plugins(str(path))
                operand = native.pytyliki_plugin_info("Operandu", str(path))
                dropaul = native.pytyliki_plugin_info("dropaul", str(path))
                with self.assertRaisesRegex(KeyError, "unknown Pytyliki plugin"):
                    native.pytyliki_plugin_info("not-installed", str(path))
        self.assertEqual([item["id"] for item in catalog], ["operandu", "dropaul"])
        self.assertEqual(operand["service"], "inspect_value")
        self.assertIn("schema.inspection", operand["capabilities"])
        self.assertEqual(dropaul["name"], "Dropaul")

    def test_vectors_are_bounded_and_finite(self) -> None:
        with self.assertRaises(TypeError):
            native._vector([True])
        with self.assertRaises(ValueError):
            native._vector([float("nan")])
        with self.assertRaises(ValueError):
            native._vector([1.0] * 4097)


class PytylikiBridgeHandleTests(unittest.TestCase):
    def setUp(self) -> None:
        native._load_library.cache_clear()

    def tearDown(self) -> None:
        native._load_library.cache_clear()

    def test_typed_bridge_uses_public_abi_v1_and_closes_logically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()) as loader:
                bridge = PytylikiBridge(str(path))
                self.assertEqual(bridge.norm([3, 4]), 5.0)
                self.assertEqual(bridge.dot([3, 4], [0, 2]), 8.0)
                self.assertEqual(bridge.distance([3, 4], [0, 0]), 5.0)
                self.assertTrue(bridge.orthogonal([1, 0], [0, 1], 1e-12))
                self.assertEqual(loader.call_count, 1)
                bridge.close()
                with self.assertRaisesRegex(FfiError, "closed"):
                    bridge.norm([3, 4])

    def test_typed_bridge_rejects_relative_path_and_wrong_abi(self) -> None:
        with self.assertRaisesRegex(FfiError, "absolute"):
            PytylikiBridge("pytyliki_ffi.dll")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary(version=2)):
                with self.assertRaisesRegex(FfiError, "unsupported Pytyliki ABI"):
                    PytylikiBridge(str(path))

    def test_reaper_language_can_inspect_pytyliki_plugin_catalogue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            source = (
                f'let catalog = pytyliki_plugin_catalog("{path}")\n'
                f'let selected = pytyliki_plugin_info("Operandu", "{path}")\n'
                'emit size(catalog)\n'
                'emit selected.id\n'
                'emit selected.service\n'
                'emit contains(selected.capabilities, "schema.inspection")\n'
            )
            output: list[str] = []
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()):
                Interpreter(output=output.append, allow_native_ffi=True).run(source)
        self.assertEqual(output, ["2", "operandu", "inspect_value", "true"])

    def test_plugin_catalogue_builtins_keep_the_explicit_ffi_opt_in(self) -> None:
        source = 'emit size(pytyliki_plugin_catalog("/absolute/path/libpytyliki.so"))'
        with self.assertRaisesRegex(Exception, "native FFI is disabled"):
            Interpreter(output=lambda _line: None).run(source)

    def test_reaper_language_can_use_typed_bridge_builtins(self) -> None:
        source_template = (
            'make bridge := pytyliki_open("{library}")\n'
            'emit text(pytyliki_bridge_norm([3, 4], bridge))\n'
            'emit text(pytyliki_bridge_dot([3, 4], [0, 2], bridge))\n'
            'emit text(pytyliki_bridge_distance([3, 4], [0, 0], bridge))\n'
            'emit text(pytyliki_bridge_orthogonal([1, 0], [0, 1], 0.000000000001, bridge))\n'
            'ffi_close(bridge)\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            output: list[str] = []
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()):
                Interpreter(output=output.append, allow_native_ffi=True).run(
                    source_template.format(library=path)
                )
        self.assertEqual(output, ["5.0", "8.0", "5.0", "true"])


if __name__ == "__main__":
    unittest.main()
