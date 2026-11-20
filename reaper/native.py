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
