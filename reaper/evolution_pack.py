"""Catalytic language pack: bounded functional, result, snapshot and data helpers."""
from __future__ import annotations

import math
import statistics
from typing import Any, Callable

from .errors import ReaperRuntimeError
from .lexer import Token

BUILTIN_NAMES = frozenset({
    "ok", "err", "is_ok", "is_err", "unwrap", "unwrap_or", "result_map",
    "result_bind", "try_call", "recover", "some", "is_some", "is_none",
    "some_value", "coalesce", "snapshot", "clone", "reflash", "rebind",
    "zip", "enumerate", "all_of", "any_of", "find", "find_index", "count_by",
    "take_while", "drop_while", "scan", "group_by", "partition_by", "window",
    "transpose", "interleave", "compact", "pluck", "keys", "values", "entries",
    "merge", "get_or", "has_key", "put", "remove_key", "slice", "flat_map",
    "clamp", "lerp", "sign", "is_even", "is_odd", "gcd", "lcm", "mean",
    "median", "variance", "stdev", "sum_by", "min_by", "max_by", "words",
    "lines", "char_at", "pad_left", "pad_right", "repeat_text", "count_text",
    "slice_text",
})


def install_evolution_builtins(interpreter: Any, register: Callable[..., None]) -> None:
    """Register bounded additions in an existing Interpreter instance."""
    limit, text_limit = interpreter.max_collection_items, interpreter.max_text_length
    token = Token("BUILTIN", "evolution_pack", 1, 1)

    def seq(value: Any) -> Any:
        if not isinstance(value, (list, tuple, str, range)):
            raise TypeError("expected a list, text, or range")
        if len(value) > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        return value

    def bounded(value: list[Any]) -> list[Any]:
        if len(value) > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        return value

    def call(fn: Any, *args: Any) -> Any:
        return interpreter._call(fn, list(args), token)

    def truth(fn: Any, value: Any) -> bool:
        return interpreter._truthy(call(fn, value))

    def num(value: Any, label: str = "value") -> int | float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{label} must be a number")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{label} must be finite")
        return value

    def whole(value: Any, label: str = "value") -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{label} must be a whole number")
        return value

    def txt(value: Any, label: str = "value") -> str:
        if not isinstance(value, str):
            raise TypeError(f"{label} must be text")
        return value

    def tagged(value: Any, name: str) -> bool:
        return isinstance(value, dict) and value.get("tag") == name

    def ok(value: Any) -> dict[str, Any]:
        return {"tag": "ok", "value": value}

    def err(message: Any) -> dict[str, Any]:
        return {"tag": "err", "error": interpreter._display(message)}

    def unwrap(value: Any) -> Any:
        if tagged(value, "ok"):
            return value["value"]
        if tagged(value, "err"):
            raise ReaperRuntimeError(str(value.get("error", "cannot unwrap an error result")))
        raise TypeError("unwrap() expects an ok() or err() result")

    def unwrap_or(value: Any, fallback: Any) -> Any:
        if tagged(value, "ok"):
            return value["value"]
        if tagged(value, "err"):
            return fallback
        raise TypeError("unwrap_or() expects an ok() or err() result")

    def result_map(value: Any, fn: Any) -> Any:
        if tagged(value, "err"):
            return value
        if not tagged(value, "ok"):
            raise TypeError("result_map() expects an ok() or err() result")
        return ok(call(fn, value["value"]))

    def result_bind(value: Any, fn: Any) -> Any:
        if tagged(value, "err"):
            return value
        if not tagged(value, "ok"):
            raise TypeError("result_bind() expects an ok() or err() result")
        result = call(fn, value["value"])
        if not (tagged(result, "ok") or tagged(result, "err")):
            raise TypeError("result_bind() callback must return ok() or err()")
        return result

    def try_call(fn: Any, *args: Any) -> dict[str, Any]:
        try:
            return ok(call(fn, *args))
        except (ReaperRuntimeError, TypeError, ValueError, OverflowError) as failure:
            return err(str(failure))

    def recover(value: Any, fallback: Any) -> Any:
        if tagged(value, "ok"):
            return value["value"]
        if tagged(value, "err"):
            return fallback
        raise TypeError("recover() expects an ok() or err() result")

    def snapshot(value: Any, depth: int = 0) -> Any:
        if depth > 128:
            raise ValueError("snapshot nesting limit exceeded")
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            if len(value) > limit:
                raise ValueError(f"collection item limit ({limit}) exceeded")
            return [snapshot(item, depth + 1) for item in value]
        if isinstance(value, dict):
            if len(value) > limit:
                raise ValueError(f"collection item limit ({limit}) exceeded")
            return {key: snapshot(item, depth + 1) for key, item in value.items()}
        raise TypeError("snapshot() supports only scalar, list, and map values")

    def reflash(value: Any, *functions: Any) -> Any:
        if len(functions) > 256:
            raise ValueError("reflash() accepts at most 256 transformations")
        for fn in functions:
            value = call(fn, value)
        return value

    def map_of(*arguments: Any) -> dict[Any, Any]:
        if len(arguments) % 2:
            raise ValueError("map_of() expects alternating key/value arguments")
        if len(arguments) // 2 > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        result = {}
        for index in range(0, len(arguments), 2):
            try:
                result[arguments[index]] = arguments[index + 1]
            except TypeError as failure:
                raise TypeError("map_of() keys must be hashable") from failure
        return result

    def map_from_entries(values: Any) -> dict[Any, Any]:
        result = {}
        for entry in seq(values):
            pair = seq(entry)
            if len(pair) != 2:
                raise ValueError("map_from_entries() expects [key, value] pairs")
            try:
                result[pair[0]] = pair[1]
            except TypeError as failure:
                raise TypeError("map_from_entries() keys must be hashable") from failure
        if len(result) > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        return result

    def rebind(source: Any, updates: Any) -> dict[Any, Any]:
        if not isinstance(source, dict) or not isinstance(updates, dict):
            raise TypeError("rebind() expects two maps")
        if len(source) + len(updates) > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        return {**source, **updates}

    def zip_values(*sequences: Any) -> list[list[Any]]:
        if len(sequences) < 2:
            raise ValueError("zip() expects at least two sequences")
        return bounded([list(row) for row in zip(*(seq(v) for v in sequences))])

    def enumerate_values(values: Any, start: Any = 0) -> list[list[Any]]:
        start = whole(start, "start")
        return bounded([[start + i, v] for i, v in enumerate(seq(values))])

    def all_of(values: Any, fn: Any = None) -> bool:
        return all(interpreter._truthy(v) if fn is None else truth(fn, v) for v in seq(values))

    def any_of(values: Any, fn: Any = None) -> bool:
        return any(interpreter._truthy(v) if fn is None else truth(fn, v) for v in seq(values))

    def find(values: Any, fn: Any) -> Any:
        return next((v for v in seq(values) if truth(fn, v)), None)

    def find_index(values: Any, fn: Any) -> int:
        return next((i for i, v in enumerate(seq(values)) if truth(fn, v)), -1)

    def count_by(values: Any, fn: Any) -> int:
        return sum(1 for v in seq(values) if truth(fn, v))

    def take_while(values: Any, fn: Any) -> list[Any]:
        result = []
        for value in seq(values):
            if not truth(fn, value):
                break
            result.append(value)
        return bounded(result)

    def drop_while(values: Any, fn: Any) -> list[Any]:
        source = seq(values)
        index = 0
        while index < len(source) and truth(fn, source[index]):
            index += 1
        return bounded(list(source[index:]))

    def scan(values: Any, initial: Any, fn: Any) -> list[Any]:
        result, accumulator = [], initial
        for value in seq(values):
            accumulator = call(fn, accumulator, value)
            result.append(accumulator)
        return bounded(result)

    def group_by(values: Any, fn: Any) -> dict[Any, list[Any]]:
        groups: dict[Any, list[Any]] = {}
        for value in seq(values):
            key = call(fn, value)
            try:
                groups.setdefault(key, []).append(value)
            except TypeError as failure:
                raise TypeError("group_by() callback must return a hashable key") from failure
            if len(groups) > limit:
                raise ValueError(f"collection item limit ({limit}) exceeded")
        return groups

    def partition_by(values: Any, fn: Any) -> list[list[Any]]:
        yes, no = [], []
        for value in seq(values):
            (yes if truth(fn, value) else no).append(value)
        return [bounded(yes), bounded(no)]

    def window(values: Any, width: Any) -> list[list[Any]]:
        source, width = seq(values), whole(width, "window width")
        if width < 1:
            raise ValueError("window width must be positive")
        return bounded([list(source[i:i + width]) for i in range(max(0, len(source) - width + 1))])

    def transpose(values: Any) -> list[list[Any]]:
        rows = [seq(row) for row in seq(values)]
        if not rows:
            return []
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("transpose() requires rows of equal length")
        return bounded([bounded([row[col] for row in rows]) for col in range(width)])

    def interleave(*sequences: Any) -> list[Any]:
        if len(sequences) < 2:
            raise ValueError("interleave() expects at least two sequences")
        normalized, result = [seq(v) for v in sequences], []
        for index in range(max((len(v) for v in normalized), default=0)):
            for values in normalized:
                if index < len(values):
                    result.append(values[index])
                    if len(result) > limit:
                        raise ValueError(f"collection item limit ({limit}) exceeded")
        return result

    def compact(values: Any) -> list[Any]:
        return bounded([v for v in seq(values) if v is not None])

    def pluck(values: Any, key: Any, fallback: Any = None) -> list[Any]:
        result = []
        for value in seq(values):
            if not isinstance(value, dict):
                raise TypeError("pluck() expects a sequence of maps")
            result.append(value.get(key, fallback))
        return bounded(result)

    def map_values(value: Any, mode: str) -> list[Any]:
        if not isinstance(value, dict):
            raise TypeError(f"{mode}() expects a map")
        result = list(value.keys()) if mode == "keys" else list(value.values())
        return bounded(result)

    def entries(value: Any) -> list[list[Any]]:
        if not isinstance(value, dict):
            raise TypeError("entries() expects a map")
        return bounded([[k, v] for k, v in value.items()])

    def merge(*maps: Any) -> dict[Any, Any]:
        if len(maps) < 2:
            raise ValueError("merge() expects at least two maps")
        result: dict[Any, Any] = {}
        for value in maps:
            if not isinstance(value, dict):
                raise TypeError("merge() expects only maps")
            result.update(value)
        if len(result) > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        return result

    def get_or(value: Any, key: Any, fallback: Any) -> Any:
        if not isinstance(value, dict):
            raise TypeError("get_or() expects a map")
        return value.get(key, fallback)

    def has_key(value: Any, key: Any) -> bool:
        if not isinstance(value, dict):
            raise TypeError("has_key() expects a map")
        return key in value

    def put(value: Any, key: Any, item: Any) -> dict[Any, Any]:
        if not isinstance(value, dict):
            raise TypeError("put() expects a map")
        result = dict(value)
        result[key] = item
        if len(result) > limit:
            raise ValueError(f"collection item limit ({limit}) exceeded")
        return result

    def remove_key(value: Any, key: Any) -> dict[Any, Any]:
        if not isinstance(value, dict):
            raise TypeError("remove_key() expects a map")
        result = dict(value)
        result.pop(key, None)
        return result

    def slice_values(value: Any, start: Any, end: Any = None) -> Any:
        source, start = seq(value), whole(start, "slice start")
        if end is not None:
            end = whole(end, "slice end")
        result = source[start:end]
        if isinstance(result, str):
            if len(result) > text_limit:
                raise ValueError(f"text length limit ({text_limit}) exceeded")
            return result
        return bounded(list(result))

    def flat_map(values: Any, fn: Any) -> list[Any]:
        result = []
        for value in seq(values):
            result.extend(seq(call(fn, value)))
            if len(result) > limit:
                raise ValueError(f"collection item limit ({limit}) exceeded")
        return result

    def clamp(value: Any, lower: Any, upper: Any) -> int | float:
        value, lower, upper = num(value), num(lower, "lower bound"), num(upper, "upper bound")
        if lower > upper:
            raise ValueError("clamp() lower bound cannot exceed upper bound")
        return min(max(value, lower), upper)

    def lerp(start: Any, end: Any, amount: Any) -> int | float:
        result = num(start, "start") + (num(end, "end") - num(start, "start")) * num(amount, "amount")
        if isinstance(result, float) and not math.isfinite(result):
            raise ValueError("lerp() result must be finite")
        return result

    def sign(value: Any) -> int:
        value = num(value)
        return 1 if value > 0 else (-1 if value < 0 else 0)

    def even(value: Any) -> bool:
        return whole(value) % 2 == 0

    def odd(value: Any) -> bool:
        return whole(value) % 2 != 0

    def gcd(left: Any, right: Any) -> int:
        return math.gcd(whole(left), whole(right))

    def lcm(left: Any, right: Any) -> int:
        return math.lcm(whole(left), whole(right))

    def numeric_values(values: Any) -> list[int | float]:
        source = list(seq(values))
        if not source:
            raise ValueError("numeric aggregate expects a non-empty sequence")
        return [num(value, "sequence item") for value in source]

    def mean(values: Any) -> float:
        return statistics.fmean(numeric_values(values))

    def median(values: Any) -> int | float:
        return statistics.median(numeric_values(values))

    def variance(values: Any) -> float:
        return statistics.pvariance(numeric_values(values))

    def stdev(values: Any) -> float:
        return statistics.pstdev(numeric_values(values))

    def sum_by(values: Any, fn: Any) -> int | float:
        return sum(num(call(fn, value), "callback result") for value in seq(values))

    def extreme_by(values: Any, fn: Any, highest: bool = False) -> Any:
        source = list(seq(values))
        if not source:
            raise ValueError("min_by()/max_by() expects a non-empty sequence")
        return (max if highest else min)(source, key=lambda value: call(fn, value))

    def words(value: Any) -> list[str]:
        return bounded(txt(value).split())

    def lines(value: Any) -> list[str]:
        return bounded(txt(value).splitlines())

    def char_at(value: Any, index: Any) -> str:
        try:
            return txt(value)[whole(index, "index")]
        except IndexError as failure:
            raise ValueError("char_at() index is out of range") from failure

    def pad(value: Any, width: Any, fill: Any = " ", left: bool = True) -> str:
        value, fill, width = txt(value), txt(fill, "fill"), whole(width, "width")
        if width < 0:
            raise ValueError("padding width cannot be negative")
        if len(fill) != 1:
            raise ValueError("padding fill must be exactly one character")
        result = value.rjust(width, fill) if left else value.ljust(width, fill)
        if len(result) > text_limit:
            raise ValueError(f"text length limit ({text_limit}) exceeded")
        return result

    def repeat_text(value: Any, count: Any) -> str:
        value, count = txt(value), whole(count, "repeat count")
        if count < 0:
            raise ValueError("repeat count cannot be negative")
        if len(value) * count > text_limit:
            raise ValueError(f"text length limit ({text_limit}) exceeded")
        return value * count

    def count_text(value: Any, needle: Any) -> int:
        return txt(value).count(txt(needle, "needle"))

    def slice_text(value: Any, start: Any, end: Any = None) -> str:
        return slice_values(txt(value), start, end)

    additions = [
        ("ok", ok, 1, 1), ("err", err, 1, 1),
        ("is_ok", lambda v: tagged(v, "ok"), 1, 1), ("is_err", lambda v: tagged(v, "err"), 1, 1),
        ("unwrap", unwrap, 1, 1), ("unwrap_or", unwrap_or, 2, 2),
        ("result_map", result_map, 2, 2), ("result_bind", result_bind, 2, 2),
        ("try_call", try_call, 1, 9), ("recover", recover, 2, 2),
        ("some", lambda v: {"tag": "some", "value": v}, 1, 1),
        ("is_some", lambda v: tagged(v, "some"), 1, 1), ("is_none", lambda v: v is None, 1, 1),
        ("some_value", lambda v: v["value"] if tagged(v, "some") else (_raise("some_value() expects some(value)")), 1, 1),
        ("coalesce", lambda v, fallback: fallback if v is None else v, 2, 2),
        ("snapshot", snapshot, 1, 1), ("clone", snapshot, 1, 1), ("reflash", reflash, 1, 257),
        ("rebind", rebind, 2, 2), ("map_of", map_of, 0, 64),
        ("map_from_entries", map_from_entries, 1, 1), ("zip", zip_values, 2, 16), ("enumerate", enumerate_values, 1, 2),
        ("all_of", all_of, 1, 2), ("any_of", any_of, 1, 2), ("find", find, 2, 2),
        ("find_index", find_index, 2, 2), ("count_by", count_by, 2, 2),
        ("take_while", take_while, 2, 2), ("drop_while", drop_while, 2, 2),
        ("scan", scan, 3, 3), ("group_by", group_by, 2, 2), ("partition_by", partition_by, 2, 2),
        ("window", window, 2, 2), ("transpose", transpose, 1, 1), ("interleave", interleave, 2, 16),
        ("compact", compact, 1, 1), ("pluck", pluck, 2, 3),
        ("keys", lambda v: map_values(v, "keys"), 1, 1), ("values", lambda v: map_values(v, "values"), 1, 1),
        ("entries", entries, 1, 1), ("merge", merge, 2, 16), ("get_or", get_or, 3, 3),
        ("has_key", has_key, 2, 2), ("put", put, 3, 3), ("remove_key", remove_key, 2, 2),
        ("slice", slice_values, 2, 3), ("flat_map", flat_map, 2, 2),
        ("clamp", clamp, 3, 3), ("lerp", lerp, 3, 3), ("sign", sign, 1, 1),
        ("is_even", even, 1, 1), ("is_odd", odd, 1, 1), ("gcd", gcd, 2, 2), ("lcm", lcm, 2, 2),
        ("mean", mean, 1, 1), ("median", median, 1, 1), ("variance", variance, 1, 1), ("stdev", stdev, 1, 1),
        ("sum_by", sum_by, 2, 2), ("min_by", lambda v, fn: extreme_by(v, fn), 2, 2),
        ("max_by", lambda v, fn: extreme_by(v, fn, True), 2, 2),
        ("words", words, 1, 1), ("lines", lines, 1, 1), ("char_at", char_at, 2, 2),
        ("pad_left", lambda v, w, *f: pad(v, w, f[0] if f else " ", True), 2, 3),
        ("pad_right", lambda v, w, *f: pad(v, w, f[0] if f else " ", False), 2, 3),
        ("repeat_text", repeat_text, 2, 2), ("count_text", count_text, 2, 2), ("slice_text", slice_text, 2, 3),
    ]
    for name, callback, minimum, maximum in additions:
        register(name, callback, minimum, maximum)


def _raise(message: str) -> Any:
    raise ReaperRuntimeError(message)
