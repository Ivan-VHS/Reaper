"""Explicit-path ctypes bridge to the Pytyliki C ABI v1.

Loading a native library executes trusted native code. No PATH search, implicit
name lookup, environment-variable discovery or bundled DLL probing is done.
"""
from __future__ import annotations

import ctypes
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

ABI_VERSION = 1
MAX_VECTOR_DIMENSION = 4096
_DOUBLE_POINTER = ctypes.POINTER(ctypes.c_double)


@lru_cache(maxsize=8)
def _load_library(explicit_path: str) -> ctypes.CDLL:
    path = Path(explicit_path).expanduser()
    if not path.is_absolute():
        raise ValueError("Pytyliki library path must be absolute and explicit")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"Pytyliki library does not exist: {path}") from error
    if not resolved.is_file():
        raise ValueError(f"Pytyliki library path is not a file: {resolved}")
    try:
        library = ctypes.CDLL(str(resolved))
    except OSError as error:
        raise ValueError(f"cannot load trusted Pytyliki library {resolved}: {error}") from error

    try:
        version = library.pytyliki_abi_version
        version.argtypes = []
        version.restype = ctypes.c_uint32
        actual_version = int(version())
    except (AttributeError, OSError) as error:
        raise ValueError("library does not expose the Pytyliki ABI version symbol") from error
    if actual_version != ABI_VERSION:
        raise ValueError(f"unsupported Pytyliki ABI version {actual_version}; expected {ABI_VERSION}")

    signatures = {
        "pytyliki_v1_dot_f64": ([_DOUBLE_POINTER, _DOUBLE_POINTER, ctypes.c_uint64, _DOUBLE_POINTER], ctypes.c_int32),
        "pytyliki_v1_norm_f64": ([_DOUBLE_POINTER, ctypes.c_uint64, _DOUBLE_POINTER], ctypes.c_int32),
        "pytyliki_v1_distance_f64": ([_DOUBLE_POINTER, _DOUBLE_POINTER, ctypes.c_uint64, _DOUBLE_POINTER], ctypes.c_int32),
        "pytyliki_v1_orthogonal_f64": ([_DOUBLE_POINTER, _DOUBLE_POINTER, ctypes.c_uint64, ctypes.c_double, ctypes.POINTER(ctypes.c_int32)], ctypes.c_int32),
    }
    for symbol, (arguments, result_type) in signatures.items():
        try:
            function = getattr(library, symbol)
        except AttributeError as error:
            raise ValueError(f"Pytyliki ABI v1 symbol is missing: {symbol}") from error
        function.argtypes = arguments
        function.restype = result_type
    return library


def _vector(values: Any, label: str = "vector") -> list[float]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{label} must be a list")
    if not 1 <= len(values) <= MAX_VECTOR_DIMENSION:
        raise ValueError(f"{label} must contain 1..{MAX_VECTOR_DIMENSION} values")
    result: list[float] = []
    for index, raw in enumerate(values):
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise TypeError(f"{label}[{index}] must be a real number")
        try:
            value = float(raw)
        except OverflowError as error:
            raise ValueError(f"{label}[{index}] is outside the float64 range") from error
        if not math.isfinite(value):
            raise ValueError(f"{label}[{index}] must be finite")
        result.append(value)
    return result


def _array(values: list[float]) -> Any:
    return (ctypes.c_double * len(values))(*values)


def _status(status: int, operation: str) -> None:
    if status != 0:
        raise ValueError(f"Pytyliki ABI v1 {operation} failed with status {status}")


def pytyliki_norm(values: Any, library_path: str) -> float:
    vector = _vector(values)
    library = _load_library(library_path)
    output = ctypes.c_double()
    status = library.pytyliki_v1_norm_f64(_array(vector), len(vector), ctypes.byref(output))
    _status(int(status), "norm")
    if not math.isfinite(output.value):
        raise ValueError("Pytyliki ABI returned a non-finite norm")
    return float(output.value)


def pytyliki_dot(left: Any, right: Any, library_path: str) -> float:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    library = _load_library(library_path)
    output = ctypes.c_double()
    status = library.pytyliki_v1_dot_f64(_array(a), _array(b), len(a), ctypes.byref(output))
    _status(int(status), "dot product")
    if not math.isfinite(output.value):
        raise ValueError("Pytyliki ABI returned a non-finite dot product")
    return float(output.value)


def pytyliki_distance(left: Any, right: Any, library_path: str) -> float:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    library = _load_library(library_path)
    output = ctypes.c_double()
    status = library.pytyliki_v1_distance_f64(_array(a), _array(b), len(a), ctypes.byref(output))
    _status(int(status), "distance")
    if not math.isfinite(output.value):
        raise ValueError("Pytyliki ABI returned a non-finite distance")
    return float(output.value)


def pytyliki_orthogonal(
    left: Any, right: Any, tolerance: float, library_path: str
) -> bool:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise TypeError("tolerance must be a real number")
    tolerance_value = float(tolerance)
    if not math.isfinite(tolerance_value) or not 0.0 <= tolerance_value <= 1.0:
        raise ValueError("tolerance must be finite and between 0 and 1")
    library = _load_library(library_path)
    output = ctypes.c_int32()
    status = library.pytyliki_v1_orthogonal_f64(
        _array(a), _array(b), len(a), tolerance_value, ctypes.byref(output)
    )
    _status(int(status), "orthogonality")
    if output.value not in (0, 1):
        raise ValueError("Pytyliki ABI returned an invalid orthogonality flag")
    return bool(output.value)


class _EmbeddedTargetV1(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_char * 32),
        ("architecture", ctypes.c_char * 32),
        ("abi", ctypes.c_char * 32),
        ("compiler", ctypes.c_char * 48),
        ("description", ctypes.c_char * 128),
        ("word_bits", ctypes.c_uint32),
        ("capabilities", ctypes.c_uint32),
    ]


class _EmbeddedSourceReportV1(ctypes.Structure):
    _fields_ = [
        ("source_bytes", ctypes.c_uint64),
        ("line_count", ctypes.c_uint64),
        ("include_count", ctypes.c_uint64),
        ("heap_calls", ctypes.c_uint64),
        ("blocking_calls", ctypes.c_uint64),
        ("register_markers", ctypes.c_uint64),
        ("host_io_calls", ctypes.c_uint64),
        ("warnings", ctypes.c_uint32),
    ]


_EMBEDDED_WARNING_BITS = (
    (1 << 0, "dynamic-allocation"),
    (1 << 1, "blocking-delay"),
    (1 << 2, "register-oriented-code"),
    (1 << 3, "host-io"),
)


def _decode_abi_text(value: bytes) -> str:
    return value.split(b"\0", 1)[0].decode("utf-8", errors="replace")


def pytyliki_embedded_targets(library_path: str) -> list[dict[str, Any]]:
    """Read the optional Embedded C target API from an explicitly named ABI v1 library."""
    library = _load_library(library_path)
    try:
        count_fn = library.pytyliki_v1_embedded_target_count
        target_fn = library.pytyliki_v1_embedded_target_at
    except AttributeError as error:
        raise ValueError("Pytyliki ABI v1 library does not expose the Embedded C target API") from error
    count_fn.argtypes = []
    count_fn.restype = ctypes.c_uint64
    target_fn.argtypes = [ctypes.c_uint64, ctypes.POINTER(_EmbeddedTargetV1)]
    target_fn.restype = ctypes.c_int32
    count = int(count_fn())
    if not 0 <= count <= 128:
        raise ValueError(f"Pytyliki returned an invalid Embedded C target count: {count}")
    results: list[dict[str, Any]] = []
    for index in range(count):
        target = _EmbeddedTargetV1()
        status = int(target_fn(index, ctypes.byref(target)))
        _status(status, f"embedded target {index}")
        results.append({
            "id": _decode_abi_text(target.id),
            "architecture": _decode_abi_text(target.architecture),
            "abi": _decode_abi_text(target.abi),
            "compiler": _decode_abi_text(target.compiler),
            "description": _decode_abi_text(target.description),
            "word_bits": int(target.word_bits),
            "capabilities": int(target.capabilities),
        })
    return results


def pytyliki_embedded_inspect(source: str, library_path: str) -> dict[str, Any]:
    """Run Pytyliki's bounded lexical Embedded C scanner through its explicit C ABI."""
    if not isinstance(source, str):
        raise TypeError("Embedded C source must be text")
    payload = source.encode("utf-8")
    if len(payload) > 1024 * 1024:
        raise ValueError("Embedded C source exceeds the 1048576-byte limit")
    library = _load_library(library_path)
    try:
        inspect_fn = library.pytyliki_v1_embedded_inspect_source
    except AttributeError as error:
        raise ValueError("Pytyliki ABI v1 library does not expose Embedded C source inspection") from error
    inspect_fn.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(_EmbeddedSourceReportV1)]
    inspect_fn.restype = ctypes.c_int32
    report = _EmbeddedSourceReportV1()
    status = int(inspect_fn(ctypes.c_char_p(payload), len(payload), ctypes.byref(report)))
    _status(status, "embedded source inspection")
    warnings = [name for bit, name in _EMBEDDED_WARNING_BITS if report.warnings & bit]
    return {
        "source_bytes": int(report.source_bytes),
        "line_count": int(report.line_count),
        "include_count": int(report.include_count),
        "heap_calls": int(report.heap_calls),
        "blocking_calls": int(report.blocking_calls),
        "register_markers": int(report.register_markers),
        "host_io_calls": int(report.host_io_calls),
        "warnings": warnings,
        "executed": False,
    }
