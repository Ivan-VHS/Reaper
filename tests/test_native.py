from __future__ import annotations

import ctypes
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper import native


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

    def test_vectors_are_bounded_and_finite(self) -> None:
        with self.assertRaises(TypeError):
            native._vector([True])
        with self.assertRaises(ValueError):
            native._vector([float("nan")])
        with self.assertRaises(ValueError):
            native._vector([1.0] * 4097)


if __name__ == "__main__":
    unittest.main()
