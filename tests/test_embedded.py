from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper import embedded, native
from reaper.cli import main
from reaper.runtime import Interpreter


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeEmbeddedLibrary:
    def __init__(self):
        self.pytyliki_abi_version = FakeFunction(lambda: 1)
        self.pytyliki_v1_norm_f64 = FakeFunction(lambda *_: 0)
        self.pytyliki_v1_dot_f64 = FakeFunction(lambda *_: 0)
        self.pytyliki_v1_distance_f64 = FakeFunction(lambda *_: 0)
        self.pytyliki_v1_orthogonal_f64 = FakeFunction(lambda *_: 0)
        self.pytyliki_v1_embedded_target_count = FakeFunction(lambda: 1)
        self.pytyliki_v1_embedded_target_at = FakeFunction(self.target_at)
        self.pytyliki_v1_embedded_inspect_source = FakeFunction(self.inspect)

    @staticmethod
    def target_at(index, output):
        if index != 0:
            return -1
        value = output._obj
        value.id = b"native-c11"
        value.architecture = b"host-native"
        value.abi = b"host C ABI"
        value.compiler = b"cc"
        value.description = b"Host C11 test profile"
        value.word_bits = 0
        value.capabilities = 0
        return 0

    @staticmethod
    def inspect(source, length, output):
        value = output._obj
        value.source_bytes = length
        value.line_count = 1
        value.include_count = 1
        value.heap_calls = 0
        value.blocking_calls = 0
        value.register_markers = 0
        value.host_io_calls = 0
        value.warnings = 0
        return 0


class EmbeddedProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        native._load_library.cache_clear()

    def tearDown(self) -> None:
        native._load_library.cache_clear()

    def test_catalog_has_target_profiles_and_metadata(self) -> None:
        profiles = embedded.embedded_targets()
        self.assertGreaterEqual(len(profiles), 7)
        self.assertEqual(embedded.embedded_profile("arm-cortex-m0")["word_bits"], 32)
        self.assertEqual(embedded.embedded_profile("avr-atmega328p")["compiler"], "avr-gcc")

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown Embedded C"):
            embedded.embedded_profile("covert-target")

    def test_toolchain_probe_only_resolves_path(self) -> None:
        with patch("reaper.embedded.shutil.which", return_value="/tools/arm-none-eabi-gcc"):
            result = embedded.embedded_toolchain("arm-cortex-m0")
        self.assertTrue(result["available"])
        self.assertEqual(result["executable"], "/tools/arm-none-eabi-gcc")
        self.assertIn("PATH lookup only", result["probe"])

    def test_inspection_is_bounded_and_reports_advisory_patterns(self) -> None:
        source = '#include <stdint.h>\nvolatile int *GPIO;\nvoid f(void) { malloc(4); HAL_Delay(1); printf("x"); }\n'
        report = embedded.embedded_inspect(source)
        self.assertEqual(report["include_count"], 1)
        self.assertEqual(report["heap_calls"], 1)
        self.assertEqual(report["blocking_calls"], 1)
        self.assertGreaterEqual(report["register_markers"], 2)
        self.assertEqual(set(report["warnings"]), {
            "dynamic-allocation", "blocking-delay", "register-oriented-code", "host-io"
        })
        self.assertFalse(report["executed"])
        with self.assertRaisesRegex(ValueError, "exceeds"):
            embedded.embedded_inspect("x" * (embedded.MAX_SOURCE_BYTES + 1))

    def test_build_plan_is_argv_only_and_never_executes(self) -> None:
        with patch("reaper.embedded.shutil.which", return_value="/tools/avr-gcc"):
            plan = embedded.embedded_build_plan("avr-atmega328p", "main.c", "main.elf")
        self.assertTrue(plan["compiler_available"])
        self.assertFalse(plan["shell"])
        self.assertFalse(plan["executed"])
        self.assertIn("-mmcu=atmega328p", plan["command"])
        self.assertIn("main.c", plan["command"])

    def test_native_pytiliki_embedded_abi_extension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            fake = FakeEmbeddedLibrary()
            with patch("reaper.native.ctypes.CDLL", return_value=fake):
                targets = native.pytyliki_embedded_targets(str(path))
                report = native.pytyliki_embedded_inspect("#include <stdint.h>", str(path))
        self.assertEqual(targets[0]["id"], "native-c11")
        self.assertEqual(report["include_count"], 1)
        self.assertFalse(report["executed"])

    def test_runtime_builtins_are_available_to_reaper_programs(self) -> None:
        output: list[str] = []
        source = (
            'emit size(embedded_targets())\n'
            'emit embedded_profile("arm-cortex-m0")["compiler"]\n'
            'emit embedded_inspect("#include <stdint.h>")["include_count"]\n'
        )
        Interpreter(output=output.append).run(source)
        self.assertEqual(output, ["7", "arm-none-eabi-gcc", "1"])

    def test_cli_catalog_emits_json(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--embedded-targets"])
        self.assertEqual(code, 0)
        self.assertIn('"arm-cortex-m0"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
