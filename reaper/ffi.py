"""Opt-in C ABI bridge and the Pytyliki memory/core ABI adapter."""
from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

from .errors import ReaperRuntimeError


ABI_TYPES: dict[str, Any] = {
    "void": None,
    "i8": ctypes.c_int8, "u8": ctypes.c_uint8,
    "i16": ctypes.c_int16, "u16": ctypes.c_uint16,
    "i32": ctypes.c_int32, "u32": ctypes.c_uint32,
    "i64": ctypes.c_int64, "u64": ctypes.c_uint64,
    "f32": ctypes.c_float, "f64": ctypes.c_double,
    "bool": ctypes.c_bool, "size_t": ctypes.c_size_t,
    "cstr": ctypes.c_char_p,
}


class FfiError(ReaperRuntimeError):
    pass


class NativeFunction:
    __reaper_native__ = True

    def __init__(self, library: "CAbiLibrary", symbol: str, result_type: str, argument_types: list[str]) -> None:
        self.library = library
        self.symbol = symbol
        self.result_type = result_type
        self.argument_types = argument_types
        try:
            self.function = getattr(library.handle, symbol)
        except AttributeError as error:
            raise FfiError(f"native symbol not found: {symbol}") from error
        self.function.restype = ABI_TYPES[result_type]
        self.function.argtypes = [ABI_TYPES[item] for item in argument_types]

    def __call__(self, *arguments: Any) -> Any:
        if self.library.closed:
            raise FfiError("native library handle is closed")
        if len(arguments) != len(self.argument_types):
            raise FfiError(f"{self.symbol} expects {len(self.argument_types)} argument(s)")
        converted = []
        for value, kind in zip(arguments, self.argument_types):
            if kind == "cstr":
                if not isinstance(value, (str, bytes)):
                    raise FfiError("cstr arguments must be text")
                converted.append(value.encode("utf-8") if isinstance(value, str) else value)
            else:
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

    def bind(self, symbol: str, result_type: str, argument_types: str = "") -> NativeFunction:
        if self.closed:
            raise FfiError("native library handle is closed")
        result_type = result_type.strip().lower()
        if result_type not in ABI_TYPES:
            raise FfiError(f"unsupported C ABI return type: {result_type}")
        args = [part.strip().lower() for part in argument_types.split(",") if part.strip()]
        if any(part not in ABI_TYPES or part == "void" for part in args):
            raise FfiError("unsupported C ABI argument type")
        if not symbol or not symbol.isidentifier():
            raise FfiError("native symbol must be a C identifier")
        return NativeFunction(self, symbol, result_type, args)

    def close(self) -> None:
        # ctypes does not expose a portable dlclose/FreeLibrary contract.
        # Closing invalidates Reaper bindings; the OS unloads at process exit.
        self.closed = True


class _PlCpuInfo(ctypes.Structure):
    _fields_ = [
        ("vendor", ctypes.c_char * 32),
        ("model", ctypes.c_char * 96),
        ("logical_cpus", ctypes.c_uint),
        ("family", ctypes.c_uint),
        ("model_id", ctypes.c_uint),
    ]


class _PlBenchmark(ctypes.Structure):
    _fields_ = [
        ("iterations", ctypes.c_uint64),
        ("elapsed_ms", ctypes.c_double),
        ("score", ctypes.c_double),
    ]


class _PlAnalysis(ctypes.Structure):
    _fields_ = [
        ("files_scanned", ctypes.c_uint),
        ("findings", ctypes.c_uint),
        ("read_errors", ctypes.c_uint),
    ]


def _decode(value: bytes) -> str:
    return value.split(b"\0", 1)[0].decode("utf-8", errors="replace")


class PytylikiBridge:
    """Typed adapter for Pytyliki's pl_* C ABI; no symbol guessing."""
    def __init__(self, path: str) -> None:
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            raise FfiError(f"Pytyliki native library does not exist: {target}")
        try:
            self.handle = ctypes.CDLL(str(target))
        except OSError as error:
            raise FfiError(f"cannot load Pytyliki library {target}: {error}") from error
        self.path = str(target)
        self.closed = False
        self._cpu: _PlCpuInfo | None = None
        self._bench: _PlBenchmark | None = None
        self._analysis: _PlAnalysis | None = None
        self._configure()

    def _ensure_open(self) -> None:
        if self.closed:
            raise FfiError("Pytyliki native library handle is closed")

    def close(self) -> None:
        # Keep the ctypes handle alive until process teardown; logical close
        # prevents new calls without relying on platform-specific dlclose.
        self.closed = True

    def _configure(self) -> None:
        try:
            self.handle.pl_cpu_profile.argtypes = [ctypes.POINTER(_PlCpuInfo)]
        self.handle.pl_cpu_profile.restype = ctypes.c_int
        self.handle.pl_run_benchmark.argtypes = [ctypes.c_uint64, ctypes.POINTER(_PlBenchmark)]
        self.handle.pl_run_benchmark.restype = ctypes.c_int
        self.handle.pl_analyze_file.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(_PlAnalysis), ctypes.c_char_p, ctypes.c_size_t,
        ]
        self.handle.pl_analyze_file.restype = ctypes.c_int
        self.handle.pl_write_json.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(_PlCpuInfo),
            ctypes.POINTER(_PlBenchmark), ctypes.POINTER(_PlAnalysis),
        ]
            self.handle.pl_write_json.restype = ctypes.c_int
        except AttributeError as error:
            raise FfiError(f"Pytyliki library is missing an expected pl_* symbol: {error}") from error

    @staticmethod
    def _check(status: int, operation: str) -> None:
        if status != 0:
            raise FfiError(f"Pytyliki {operation} failed with status {status}")

    def cpu_profile(self) -> dict[str, Any]:
        self._ensure_open()
        value = _PlCpuInfo()
        self._check(self.handle.pl_cpu_profile(ctypes.byref(value)), "pl_cpu_profile")
        self._cpu = value
        return {
            "vendor": _decode(value.vendor), "model": _decode(value.model),
            "logical_cpus": int(value.logical_cpus), "family": int(value.family),
            "model_id": int(value.model_id),
        }

    def benchmark(self, iterations: int) -> dict[str, Any]:
        self._ensure_open()
        if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 1:
            raise FfiError("benchmark iterations must be a positive integer")
        value = _PlBenchmark()
        self._check(self.handle.pl_run_benchmark(iterations, ctypes.byref(value)), "pl_run_benchmark")
        self._bench = value
        return {
            "iterations": int(value.iterations),
            "elapsed_ms": float(value.elapsed_ms),
            "score": float(value.score),
        }

    def analyze_file(self, path: str) -> dict[str, Any]:
        self._ensure_open()
        value = _PlAnalysis()
        details = ctypes.create_string_buffer(16_384)
        self._check(
            self.handle.pl_analyze_file(
                str(Path(path).resolve()).encode("utf-8"),
                ctypes.byref(value), details, ctypes.sizeof(details),
            ),
            "pl_analyze_file",
        )
        self._analysis = value
        return {
            "files_scanned": int(value.files_scanned),
            "findings": int(value.findings),
            "read_errors": int(value.read_errors),
            "details": _decode(details.value),
        }

    def write_json(self, path: str) -> None:
        self._ensure_open()
        if self._cpu is None or self._bench is None or self._analysis is None:
            raise FfiError("call cpu_profile(), benchmark(), and analyze_file() before write_json()")
        self._check(
            self.handle.pl_write_json(
                str(Path(path).resolve()).encode("utf-8"),
                ctypes.byref(self._cpu), ctypes.byref(self._bench), ctypes.byref(self._analysis),
            ),
            "pl_write_json",
        )
