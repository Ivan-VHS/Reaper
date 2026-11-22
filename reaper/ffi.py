"""Opt-in C ABI bridge and the Pytyliki memory/core ABI adapter."""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

from .errors import ReaperRuntimeError


ABI_TYPES: dict[str, Any] = {
    "void": None,
    "i8": ctypes.c_int8,
    "u8": ctypes.c_uint8,
    "i16": ctypes.c_int16,
    "u16": ctypes.c_uint16,
    "i32": ctypes.c_int32,
    "u32": ctypes.c_uint32,
    "i64": ctypes.c_int64,
    "u64": ctypes.c_uint64,
    "f32": ctypes.c_float,
    "f64": ctypes.c_double,
    "bool": ctypes.c_bool,
    "size_t": ctypes.c_size_t,
    "cstr": ctypes.c_char_p,
}


class FfiError(ReaperRuntimeError):
    """Raised when a native binding cannot be loaded or called safely."""


class NativeFunction:
    __reaper_native__ = True

    def __init__(
        self,
        library: "CAbiLibrary",
        symbol: str,
        result_type: str,
        argument_types: list[str],
    ) -> None:
        self.library = library
        self.symbol = symbol
        self.result_type = result_type
        self.argument_types = argument_types

        try:
            self.function = getattr(library.handle, symbol)
        except AttributeError as error:
            raise FfiError(f"native symbol not found: {symbol}") from error

        self.function.restype = ABI_TYPES[result_type]
        self.function.argtypes = [
            ABI_TYPES[argument_type]
            for argument_type in argument_types
        ]

    def __call__(self, *arguments: Any) -> Any:
        if self.library.closed:
            raise FfiError("native library handle is closed")

        if len(arguments) != len(self.argument_types):
            expected = len(self.argument_types)
            raise FfiError(f"{self.symbol} expects {expected} argument(s)")

        converted = []
        for value, kind in zip(arguments, self.argument_types):
            if kind == "cstr":
                if not isinstance(value, (str, bytes)):
                    raise FfiError("cstr arguments must be text")

                if isinstance(value, str):
                    value = value.encode("utf-8")

            converted.append(value)

        try:
            result = self.function(*converted)
        except (TypeError, ValueError, OSError) as error:
            raise FfiError(f"native call {self.symbol} failed: {error}") from error

        if self.result_type == "cstr" and result is not None:
            return result.decode("utf-8", errors="replace")

        return result


class CAbiLibrary:
    def __init__(self, path: str) -> None:
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            raise FfiError(f"native library does not exist: {target}")

        try:
            self.handle = ctypes.CDLL(str(target))
        except OSError as error:
            raise FfiError(f"cannot load native library {target}: {error}") from error

        self.path = str(target)
        self.closed = False

    def bind(
        self,
        symbol: str,
        result_type: str,
        argument_types: str = "",
    ) -> NativeFunction:
        if self.closed:
            raise FfiError("native library handle is closed")

        result_type = result_type.strip().lower()
        if result_type not in ABI_TYPES:
            raise FfiError(f"unsupported C ABI return type: {result_type}")

        arguments = [
            part.strip().lower()
            for part in argument_types.split(",")
            if part.strip()
        ]
        if any(
            argument not in ABI_TYPES or argument == "void"
            for argument in arguments
        ):
            raise FfiError("unsupported C ABI argument type")

        if not symbol or not symbol.isidentifier():
            raise FfiError("native symbol must be a C identifier")

        return NativeFunction(self, symbol, result_type, arguments)

    def close(self) -> None:
        # ctypes has no portable dlclose/FreeLibrary contract.
        # Closing invalidates Reaper bindings; the OS unloads at process exit.
        self.closed = True


class PytylikiBridge:
    """Typed adapter for the current Pytyliki C ABI v1 numerical contract.

    The native module owns ABI signatures and finite/bounded vector checks.
    This handle only adds lifecycle semantics for Reaper programs.
    """

    def __init__(self, path: str) -> None:
        target = Path(path).expanduser()
        if not target.is_absolute():
            raise FfiError("Pytyliki library path must be absolute and explicit")

        try:
            resolved = target.resolve(strict=True)
        except OSError as error:
            raise FfiError(
                f"Pytyliki native library does not exist: {target}"
            ) from error

        if not resolved.is_file():
            raise FfiError(f"Pytyliki native library path is not a file: {resolved}")

        try:
            from .native import _load_library

            _load_library(str(resolved))
        except (OSError, TypeError, ValueError) as error:
            raise FfiError(
                f"cannot validate Pytyliki C ABI v1 library: {error}"
            ) from error

        self.path = str(resolved)
        self.closed = False

    def _ensure_open(self) -> None:
        if self.closed:
            raise FfiError("Pytyliki library handle is closed")

    def norm(self, values: Any) -> float:
        self._ensure_open()
        from .native import pytyliki_norm

        try:
            return pytyliki_norm(values, self.path)
        except (TypeError, ValueError, OSError) as error:
            raise FfiError(f"Pytyliki norm failed: {error}") from error

    def dot(self, left: Any, right: Any) -> float:
        self._ensure_open()
        from .native import pytyliki_dot

        try:
            return pytyliki_dot(left, right, self.path)
        except (TypeError, ValueError, OSError) as error:
            raise FfiError(f"Pytyliki dot product failed: {error}") from error

    def distance(self, left: Any, right: Any) -> float:
        self._ensure_open()
        from .native import pytyliki_distance

        try:
            return pytyliki_distance(left, right, self.path)
        except (TypeError, ValueError, OSError) as error:
            raise FfiError(f"Pytyliki distance failed: {error}") from error

    def orthogonal(
        self,
        left: Any,
        right: Any,
        tolerance: float,
    ) -> bool:
        self._ensure_open()
        from .native import pytyliki_orthogonal

        try:
            return pytyliki_orthogonal(left, right, tolerance, self.path)
        except (TypeError, ValueError, OSError) as error:
            raise FfiError(
                f"Pytyliki orthogonality check failed: {error}"
            ) from error

    def close(self) -> None:
        # ctypes has no portable cross-platform unload contract. Logical close
        # rejects future calls; the OS releases the retained library handle.
        self.closed = True
