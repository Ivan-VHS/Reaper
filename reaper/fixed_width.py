"""Fixed-width integer ranges shared by the Reaper frontends and runtimes."""

from __future__ import annotations

FIXED_INTEGER_RANGES: dict[str, tuple[int, int]] = {
    "i8": (-(1 << 7), (1 << 7) - 1),
    "u8": (0, (1 << 8) - 1),
    "i16": (-(1 << 15), (1 << 15) - 1),
    "u16": (0, (1 << 16) - 1),
    "i32": (-(1 << 31), (1 << 31) - 1),
    "u32": (0, (1 << 32) - 1),
    "i64": (-(1 << 63), (1 << 63) - 1),
    "u64": (0, (1 << 64) - 1),
}


def is_fixed_integer_type(type_name: object) -> bool:
    return isinstance(type_name, str) and type_name in FIXED_INTEGER_RANGES


def fixed_integer_bounds(type_name: str) -> tuple[int, int]:
    try:
        return FIXED_INTEGER_RANGES[type_name]
    except KeyError as error:
        raise ValueError(f"unsupported fixed-width integer type: {type_name}") from error


def fixed_integer_fits(value: object, type_name: str) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    minimum, maximum = fixed_integer_bounds(type_name)
    return minimum <= value <= maximum


def require_fixed_integer(value: object, type_name: str) -> int:
    if not fixed_integer_fits(value, type_name):
        minimum, maximum = fixed_integer_bounds(type_name)
        raise ValueError(f"value must be an integer in the {type_name} range {minimum}..{maximum}")
    return int(value)
