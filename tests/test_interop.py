from __future__ import annotations

import unittest

from reaper.interop import (
    AdapterRegistry, CFunctionSignature, ForeignHandle, PythonAdapter, parse_c_header,
)


class InteropTests(unittest.TestCase):
    def test_parses_supported_scalar_c_prototypes(self) -> None:
        header = """
        /* tiny public API */
        int32_t add_values(int32_t left, int32_t right);
        const char *version(void);
        double scale(double value, float factor);
        """
        signatures = parse_c_header(header)
        self.assertEqual(
            signatures,
            (
                CFunctionSignature("add_values", "int32_t", ("int32_t", "int32_t")),
                CFunctionSignature("version", "const char*", ()),
                CFunctionSignature("scale", "double", ("double", "float")),
            ),
        )

    def test_rejects_variadic_declarations(self) -> None:
        with self.assertRaisesRegex(ValueError, "variadic"):
            parse_c_header("int log_message(const char *format, ...);")

    def test_adapter_registry_requires_both_sides(self) -> None:
        registry = AdapterRegistry()
        registry.register("python", PythonAdapter())
        self.assertEqual(registry.convert([1, 2], "python", "python"), [1, 2])
        with self.assertRaises(LookupError):
            registry.convert(1, "python", "javascript")

    def test_foreign_handle_releases_once_and_blocks_use_after_release(self) -> None:
        released: list[object] = []
        handle = ForeignHandle("native-object", "test", released.append)
        self.assertEqual(handle.value, "native-object")
        handle.close()
        handle.close()
        self.assertEqual(released, ["native-object"])
        with self.assertRaises(RuntimeError):
            _ = handle.value


if __name__ == "__main__":
    unittest.main()
