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


class _EmbeddedProfileV1(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_char * 40),
        ("architecture", ctypes.c_char * 24),
        ("compiler", ctypes.c_char * 48),
        ("compiler_flags", ctypes.c_char * 96),
        ("clock_hz", ctypes.c_uint64),
        ("flash_base", ctypes.c_uint32),
        ("flash_size_bytes", ctypes.c_uint64),
        ("sram_base", ctypes.c_uint32),
        ("sram_size_bytes", ctypes.c_uint64),
        ("stack_reserve_bytes", ctypes.c_uint64),
        ("is_reference_profile", ctypes.c_int32),
    ]


class _EmbeddedSectionsV1(ctypes.Structure):
    _fields_ = [
        ("text_bytes", ctypes.c_uint64),
        ("rodata_bytes", ctypes.c_uint64),
        ("data_bytes", ctypes.c_uint64),
        ("bss_bytes", ctypes.c_uint64),
        ("noinit_bytes", ctypes.c_uint64),
        ("stack_reserve_bytes", ctypes.c_uint64),
    ]


class _EmbeddedBudgetV1(ctypes.Structure):
    _fields_ = [
        ("flash_used_bytes", ctypes.c_uint64),
        ("sram_used_bytes", ctypes.c_uint64),
        ("flash_total_bytes", ctypes.c_uint64),
        ("sram_total_bytes", ctypes.c_uint64),
        ("flash_percent", ctypes.c_double),
        ("sram_percent", ctypes.c_double),
        ("flash_fits", ctypes.c_int32),
        ("sram_fits", ctypes.c_int32),
    ]


_EMBEDDED_SECTION_FIELDS = (
    "text_bytes", "rodata_bytes", "data_bytes",
    "bss_bytes", "noinit_bytes", "stack_reserve_bytes",
)
_UINT64_MAX = (1 << 64) - 1


def _embedded_functions(library: ctypes.CDLL) -> tuple[Any, Any, Any]:
    try:
        count = library.pytyliki_v1_embedded_profile_count
        profile_at = library.pytyliki_v1_embedded_profile_at
        budget = library.pytyliki_v1_embedded_budget_evaluate
    except AttributeError as error:
        raise ValueError(
            "Pytyliki ABI v1 library does not expose the Embedded C profile/budget API"
        ) from error
    count.argtypes = [ctypes.POINTER(ctypes.c_uint64)]
    count.restype = ctypes.c_int32
    profile_at.argtypes = [ctypes.c_uint64, ctypes.POINTER(_EmbeddedProfileV1)]
    profile_at.restype = ctypes.c_int32
    budget.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(_EmbeddedSectionsV1),
        ctypes.POINTER(_EmbeddedBudgetV1),
    ]
    budget.restype = ctypes.c_int32
    return count, profile_at, budget


def _embedded_text(value: bytes) -> str:
    return value.decode("utf-8", errors="replace")


def pytyliki_embedded_profiles(library_path: str) -> list[dict[str, Any]]:
    """Read MCU profile metadata from an explicitly named Pytyliki ABI v1 library."""
    library = _load_library(library_path)
    count_fn, profile_at, _ = _embedded_functions(library)
    count = ctypes.c_uint64()
    _status(int(count_fn(ctypes.byref(count))), "embedded profile count")
    if count.value > 128:
        raise ValueError(f"Pytyliki returned an implausible Embedded C profile count: {count.value}")
    profiles: list[dict[str, Any]] = []
    for index in range(int(count.value)):
        value = _EmbeddedProfileV1()
        _status(int(profile_at(index, ctypes.byref(value))), f"embedded profile {index}")
        if value.is_reference_profile not in (0, 1):
            raise ValueError(f"Pytyliki returned an invalid reference-profile flag at index {index}")
        profiles.append({
            "id": _embedded_text(value.id),
            "architecture": _embedded_text(value.architecture),
            "compiler": _embedded_text(value.compiler),
            "compiler_flags": _embedded_text(value.compiler_flags),
            "clock_hz": int(value.clock_hz),
            "flash": {"base": int(value.flash_base), "size": int(value.flash_size_bytes)},
            "sram": {"base": int(value.sram_base), "size": int(value.sram_size_bytes)},
            "stack_bytes": int(value.stack_reserve_bytes),
            "is_reference_profile": bool(value.is_reference_profile),
        })
    return profiles


def pytyliki_embedded_budget(
    profile_id: str, sections: dict[str, Any], library_path: str
) -> dict[str, Any]:
    """Use Pytyliki's native overflow-checked FLASH/SRAM budget calculation."""
    if not isinstance(profile_id, str) or not profile_id or "\0" in profile_id:
        raise ValueError("profile_id must be non-empty text without NUL characters")
    if not isinstance(sections, dict):
        raise TypeError("sections must be a map")
    missing = [name for name in _EMBEDDED_SECTION_FIELDS if name not in sections]
    if missing:
        raise ValueError("sections is missing: " + ", ".join(missing))
    values: list[int] = []
    for name in _EMBEDDED_SECTION_FIELDS:
        value = sections[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"sections[{name!r}] must be an integer")
        if not 0 <= value <= _UINT64_MAX:
            raise ValueError(f"sections[{name!r}] must fit in uint64")
        values.append(value)

    library = _load_library(library_path)
    _, _, budget_fn = _embedded_functions(library)
    native_sections = _EmbeddedSectionsV1(*values)
    output = _EmbeddedBudgetV1()
    _status(
        int(budget_fn(
            profile_id.encode("utf-8"),
            ctypes.byref(native_sections),
            ctypes.byref(output),
        )),
        "embedded memory budget",
    )
    if output.flash_fits not in (0, 1) or output.sram_fits not in (0, 1):
        raise ValueError("Pytyliki returned invalid Embedded C budget flags")
    if not math.isfinite(output.flash_percent) or not math.isfinite(output.sram_percent):
        raise ValueError("Pytyliki returned non-finite Embedded C budget percentages")
    return {
        "profile_id": profile_id,
        "flash_used_bytes": int(output.flash_used_bytes),
        "sram_used_bytes": int(output.sram_used_bytes),
        "flash_total_bytes": int(output.flash_total_bytes),
        "sram_total_bytes": int(output.sram_total_bytes),
        "flash_percent": float(output.flash_percent),
        "sram_percent": float(output.sram_percent),
        "flash_fits": bool(output.flash_fits),
        "sram_fits": bool(output.sram_fits),
    }
