from __future__ import annotations

import unittest
from unittest.mock import patch

from reaper import Interpreter, ReaperRuntimeError


class EmbeddedPytylikiRuntimeTests(unittest.TestCase):
    def test_native_embedded_builtins_share_pytiliki_profile_and_budget_api(self) -> None:
        output: list[str] = []
        profiles = [
            {"id": "cortex-m4-reference"},
            {"id": "riscv32imc-reference"},
            {"id": "avr-atmega328p"},
        ]
        budget = {
            "flash_used_bytes": 1408,
            "sram_used_bytes": 2752,
            "flash_fits": True,
            "sram_fits": True,
        }
        source = """
        make embedded := pytyliki_embedded_profiles("/absolute/path/libpytyliki_ffi.so")
        emit size(embedded)
        emit embedded[0]["id"]
        make parts := {
            "text_bytes": 1024,
            "rodata_bytes": 256,
            "data_bytes": 128,
            "bss_bytes": 512,
            "noinit_bytes": 64,
            "stack_reserve_bytes": 2048
        }
        make report := pytyliki_embedded_budget(
            "cortex-m4-reference",
            parts,
            "/absolute/path/libpytyliki_ffi.so"
        )
        emit report["flash_used_bytes"]
        emit report["sram_fits"]
        """
        with (
            patch("reaper.runtime.pytyliki_native.pytyliki_embedded_profiles", return_value=profiles),
            patch("reaper.runtime.pytyliki_native.pytyliki_embedded_budget", return_value=budget),
        ):
            Interpreter(output=output.append, allow_native_ffi=True).run(source)
        self.assertEqual(output, ["3", "cortex-m4-reference", "1408", "True"])

    def test_embedded_native_builtins_require_explicit_native_ffi_opt_in(self) -> None:
        source = 'emit size(pytyliki_embedded_profiles("/absolute/path/libpytyliki_ffi.so"))'
        with self.assertRaisesRegex(ReaperRuntimeError, "native FFI is disabled"):
            Interpreter(output=lambda _: None).run(source)

    def test_native_budget_builtin_requires_a_sections_map(self) -> None:
        source = (
            'emit pytyliki_embedded_budget("cortex-m4-reference", 12, '
            '"/absolute/path/libpytyliki_ffi.so")'
        )
        with self.assertRaisesRegex(ReaperRuntimeError, "sections map"):
            Interpreter(output=lambda _: None, allow_native_ffi=True).run(source)


if __name__ == "__main__":
    unittest.main()
