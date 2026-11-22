"""Kora standard library: 66 utility functions, standard-library-only."""

from __future__ import annotations

import asyncio
import heapq
import builtins as _builtins
import json as _json
import math
import os
import random
import re
import sys as _sys
import tempfile
import textwrap
import threading
import time as _time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping


class KoraError(ValueError):
    """Raised when a Kora operation receives invalid input."""


@dataclass(frozen=True)
class Ok:
    value: object


@dataclass(frozen=True)
class Err:
    error: Exception


# ZDORO (11): numerical helpers.


def clamp(x, min, max):
    if min > max:
        raise KoraError("min must not exceed max")
    return _builtins.max(min, _builtins.min(max, x))


def lerp(a, b, t):
    return a + (b - a) * t


def map_range(x, in_min, in_max, out_min, out_max):
    if in_min == in_max:
        raise KoraError("input range must not have zero width")
    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)


def round_to(x, decimals):
    return round(x, decimals)


def approx_eq(a, b, eps):
    if eps < 0:
        raise KoraError("eps must be non-negative")
    return math.isclose(a, b, rel_tol=0, abs_tol=eps)


def sign(x):
    return (x > 0) - (x < 0)


def gcd(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise KoraError("integer arguments required")
    return math.gcd(a, b)


def lcm(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise KoraError("integer arguments required")
    return math.lcm(a, b)


def is_prime(n):
    if not isinstance(n, int) or isinstance(n, bool):
        raise KoraError("integer required")
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2

    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2

    return True


def rand_int(lo, hi):
    if lo > hi:
        raise KoraError("min must not exceed max")
    return random.randint(lo, hi)


def rand_normal(mean, std):
    if std < 0:
        raise KoraError("std must be non-negative")
    return random.gauss(mean, std)


# DILLY (11): text helpers.


def slugify(text):
    normalized = unicodedata.normalize("NFKD", _builtins.str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def pad_both(text, length, fill=" "):
    text = _builtins.str(text)
    fill = _builtins.str(fill)

    if not fill:
        raise KoraError("fill must not be empty")

    missing = _builtins.max(0, length - len(text))
    left = missing // 2
    right = missing - left

    left_fill = (fill * ((left + len(fill) - 1) // len(fill)))[:left]
    right_fill = (fill * ((right + len(fill) - 1) // len(fill)))[:right]
    return left_fill + text + right_fill


def truncate(text, max_len, suffix="..."):
    text = _builtins.str(text)

    if max_len < 0:
        raise KoraError("max_len must be non-negative")
    if len(text) <= max_len:
        return text
    if len(suffix) >= max_len:
        return suffix[:max_len]

    return text[:max_len - len(suffix)] + suffix


def between(text, left, right):
    text = _builtins.str(text)
    start = text.find(left)
    if start < 0:
        return ""

    start += len(left)
    end = text.find(right, start)
    return "" if end < 0 else text[start:end]


def count_sub(text, sub):
    if not sub:
        raise KoraError("sub must not be empty")
    return _builtins.str(text).count(_builtins.str(sub))


def words(text):
    pattern = r"[^\W_]+(?:['’][^\W_]+)?"
    return re.findall(pattern, _builtins.str(text), re.UNICODE)


def to_camel(text):
    parts = re.findall(r"[A-Za-z0-9]+", _builtins.str(text))
    if not parts:
        return ""

    return parts[0].lower() + "".join(
        part[:1].upper() + part[1:]
        for part in parts[1:]
    )


def to_snake(text):
    text = _builtins.str(text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", text)
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()


def levenshtein(a, b):
    a = _builtins.str(a)
    b = _builtins.str(b)

    if len(a) < len(b):
        a, b = b, a

    previous_row = list(range(len(b) + 1))
    for row_index, char_a in enumerate(a, 1):
        current_row = [row_index]

        for column_index, char_b in enumerate(b, 1):
            insert_cost = current_row[-1] + 1
            delete_cost = previous_row[column_index] + 1
            replace_cost = previous_row[column_index - 1] + (char_a != char_b)
            current_row.append(min(insert_cost, delete_cost, replace_cost))

        previous_row = current_row

    return previous_row[-1]


def template(tpl, vars_map):
    pattern = r"\{\{\s*([^{}]+?)\s*\}\}"

    def replace(match):
        key = match.group(1).strip()
        return _builtins.str(vars_map.get(key, match.group(0)))

    return re.sub(pattern, replace, _builtins.str(tpl))


def wrap(text, width):
    if width < 1:
        raise KoraError("width must be positive")

    lines = textwrap.wrap(
        _builtins.str(text),
        width,
        break_long_words=False,
    )
    return "\n".join(lines)


# BAPLAP (11): collection helpers.


def chunk(list, size):
    if size < 1:
        raise KoraError("size must be positive")
    return [list[i:i + size] for i in range(0, len(list), size)]


def window(list, size):
    if size < 1:
        raise KoraError("size must be positive")

    last_start = _builtins.max(0, len(list) - size + 1)
    return [list[i:i + size] for i in range(last_start)]


def compact(list):
    return [item for item in list if item is not None and item != ""]


def dedup_by(list, key_fn):
    seen = _builtins.set()
    result = []

    for item in list:
        key = key_fn(item)
        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


def group_by(list, key_fn):
    groups = defaultdict(_builtins.list)
    for item in list:
        groups[key_fn(item)].append(item)
    return dict(groups)


def partition(list, pred_fn):
    matching = []
    remaining = []

    for item in list:
        target = matching if pred_fn(item) else remaining
        target.append(item)

    return matching, remaining


def zip_with(a, b, fn):
    return [fn(left, right) for left, right in zip(a, b)]


def flatten_depth(list, depth):
    if depth < 0:
        raise KoraError("depth must be non-negative")

    result = _builtins.list(list)
    for _ in range(depth):
        result = [
            item
            for value in result
            for item in (
                value
                if isinstance(value, (_builtins.list, tuple))
                else [value]
            )
        ]

    return result


def sample(list, k):
    if k < 0 or k > len(list):
        raise KoraError("k outside list bounds")
    return random.sample(_builtins.list(list), k)


def rotate(list, shift):
    items = _builtins.list(list)
    if not items:
        return items

    offset = shift % len(items)
    if not offset:
        return items

    return items[-offset:] + items[:-offset]


def binary_search(sorted_list, target):
    low = 0
    high = len(sorted_list)

    while low < high:
        middle = (low + high) // 2
        if sorted_list[middle] < target:
            low = middle + 1
        else:
            high = middle

    if low < len(sorted_list) and sorted_list[low] == target:
        return low
    return -1


# KALI (11): mapping and heap helpers.


def get_path(obj, path, default_val=None):
    current = obj

    for key in _builtins.str(path).split("."):
        if isinstance(current, Mapping) and key in current:
            current = current[key]
        elif (
            isinstance(current, (list, tuple))
            and key.isdigit()
            and int(key) < len(current)
        ):
            current = current[int(key)]
        else:
            return default_val

    return current


def set_path(obj, path, value):
    result = dict(obj)
    current = result
    parts = _builtins.str(path).split(".")

    for key in parts[:-1]:
        child = current.get(key, {})
        child = dict(child) if isinstance(child, dict) else {}
        current[key] = child
        current = child

    current[parts[-1]] = value
    return result


def pick(obj, keys):
    return {key: obj[key] for key in keys if key in obj}


def omit(obj, keys):
    omitted = _builtins.set(keys)
    return {
        key: value
        for key, value in obj.items()
        if key not in omitted
    }


def deep_merge(base, override):
    result = dict(base)

    for key, value in override.items():
        current = result.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            result[key] = deep_merge(current, value)
        else:
            result[key] = value

    return result


def invert(obj):
    result = {}

    for key, value in obj.items():
        if value in result:
            raise KoraError(f"duplicate value: {value!r}")
        result[value] = key

    return result


def filter_entries(obj, pred_fn):
    return {
        key: value
        for key, value in obj.items()
        if pred_fn(key, value)
    }


def set_union(a, b):
    return _builtins.set(a) | _builtins.set(b)


def set_intersect(a, b):
    return _builtins.set(a) & _builtins.set(b)


def set_diff(a, b):
    return _builtins.set(a) - _builtins.set(b)


def heap_push_pop(heap_ref, item, cmp_fn=None):
    if cmp_fn is None:
        return heapq.heappushpop(heap_ref, item)

    heap_ref.append(item)
    index = len(heap_ref) - 1

    while index:
        parent = (index - 1) // 2
        if cmp_fn(heap_ref[index], heap_ref[parent]) >= 0:
            break

        heap_ref[index], heap_ref[parent] = heap_ref[parent], heap_ref[index]
        index = parent

    root = heap_ref[0]
    last_item = heap_ref.pop()

    if heap_ref:
        heap_ref[0] = last_item
        index = 0

        while True:
            left = 2 * index + 1
            right = left + 1
            smallest = index

            if left < len(heap_ref) and cmp_fn(heap_ref[left], heap_ref[smallest]) < 0:
                smallest = left
            if right < len(heap_ref) and cmp_fn(heap_ref[right], heap_ref[smallest]) < 0:
                smallest = right
            if smallest == index:
                break

            heap_ref[index], heap_ref[smallest] = heap_ref[smallest], heap_ref[index]
            index = smallest

    return root


# PYEMONT (11): composition, error handling and asynchronous helpers.


def pipe(value, fns):
    for function in fns:
        value = function(value)
    return value


def compose(fns):
    functions = list(fns)

    def apply(value):
        for function in reversed(functions):
            value = function(value)
        return value

    return apply


def memoize(fn, ttl_ms):
    cache = {}
    lock = threading.RLock()

    def call(*a, **kw):
        key = (a, tuple(sorted(kw.items())))
        now = _time.monotonic() * 1000

        with lock:
            cached = cache.get(key)
            if cached is not None and (
                ttl_ms is None or now - cached[0] < ttl_ms
            ):
                return cached[1]

        value = fn(*a, **kw)

        with lock:
            cache[key] = (now, value)

        return value

    call.cache_clear = cache.clear
    return call


def once(fn):
    lock = threading.Lock()
    state = {}

    def call(*a, **kw):
        with lock:
            if "value" not in state:
                state["value"] = fn(*a, **kw)
            return state["value"]

    return call


def debounce(fn, wait_ms):
    lock = threading.Lock()
    state = {"timer": None}

    def call(*a, **kw):
        def run():
            fn(*a, **kw)

        with lock:
            if state["timer"]:
                state["timer"].cancel()

            timer = threading.Timer(max(0, wait_ms) / 1000, run)
            timer.daemon = True
            state["timer"] = timer
            timer.start()

    def cancel():
        timer = state["timer"]
        if timer is not None:
            timer.cancel()

    call.cancel = cancel
    return call


def throttle(fn, interval_ms):
    lock = threading.Lock()
    state = {"last": -float("inf")}

    def call(*a, **kw):
        now = _time.monotonic() * 1000

        with lock:
            if now - state["last"] < interval_ms:
                return None
            state["last"] = now

        return fn(*a, **kw)

    return call


def try_run(fn, *a, **kw):
    try:
        return Ok(fn(*a, **kw))
    except Exception as error:
        return Err(error)


def retry(fn, attempts, backoff_ms, *a, **kw):
    if attempts < 1:
        raise KoraError("attempts must be >= 1")

    for attempt in range(attempts):
        try:
            return fn(*a, **kw)
        except Exception:
            if attempt == attempts - 1:
                raise
            delay = max(0, backoff_ms) * 2**attempt / 1000
            _time.sleep(delay)


def ensure(cond, message):
    if not cond:
        raise KoraError(_builtins.str(message))
    return cond


async def all_settled(tasks):
    async def settle(task):
        try:
            return {"status": "fulfilled", "value": await task}
        except Exception as error:
            return {"status": "rejected", "reason": error}

    return await asyncio.gather(*(settle(task) for task in tasks))


async def race_timeout(task, timeout_ms):
    timeout = max(0, timeout_ms) / 1000
    return await asyncio.wait_for(task, timeout)


# LIUR (6): filesystem, process and reflection helpers.


def read_text(path, encoding="utf-8"):
    return Path(path).read_text(encoding=encoding)


def write_atomic(path, content):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix="." + target.name + ".",
        dir=target.parent,
    )

    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
            newline="",
        ) as stream:
            stream.write(_builtins.str(content))
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, target)
    except BaseException:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise

    return _builtins.str(target)


class DirectoryWatcher:
    def __init__(self, path, on_event, interval=0.25):
        self.path = Path(path)
        self.callback = on_event
        self.interval = interval
        self.stopped = threading.Event()

        if not self.path.is_dir():
            raise KoraError(f"directory not found: {path}")

        self.snapshot = self.scan()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def scan(self):
        return {
            path.name: (path.stat().st_mtime_ns, path.stat().st_size)
            for path in self.path.iterdir()
        }

    def run(self):
        while not self.stopped.wait(self.interval):
            try:
                current_snapshot = self.scan()

                for name in current_snapshot.keys() - self.snapshot.keys():
                    self.callback({
                        "event": "created",
                        "path": _builtins.str(self.path / name),
                    })

                for name in self.snapshot.keys() - current_snapshot.keys():
                    self.callback({
                        "event": "deleted",
                        "path": _builtins.str(self.path / name),
                    })

                for name in current_snapshot.keys() & self.snapshot.keys():
                    if current_snapshot[name] != self.snapshot[name]:
                        self.callback({
                            "event": "modified",
                            "path": _builtins.str(self.path / name),
                        })

                self.snapshot = current_snapshot
            except Exception as error:
                self.callback({"event": "error", "error": error})

    def close(self):
        self.stopped.set()
        self.thread.join(timeout=_builtins.max(1, self.interval * 4))


def watch_dir(path, on_event):
    return DirectoryWatcher(path, on_event)


def env_get(name, default_val=None):
    return os.environ.get(name, default_val)


def args():
    return list(_sys.argv[1:])


def type_of(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, _builtins.str):
        return "string"
    if isinstance(value, _builtins.list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if callable(value):
        return "function"
    return type(value).__name__


# SRETUO (5): JSON, clocks and async timing.


def parse_safe(raw_str):
    try:
        return Ok(_json.loads(raw_str))
    except (ValueError, TypeError) as error:
        return Err(error)


def stringify_pretty(value, indent=2):
    return _json.dumps(
        value,
        ensure_ascii=False,
        indent=indent,
        allow_nan=False,
    )


def now_ms():
    return int(_time.time() * 1000)


def format_iso(ms, tz="UTC"):
    from zoneinfo import ZoneInfo

    target_timezone = (
        timezone.utc
        if tz in ("UTC", "Z")
        else ZoneInfo(tz)
    )
    return datetime.fromtimestamp(ms / 1000, tz=target_timezone).isoformat()


async def sleep(ms):
    await asyncio.sleep(max(0, ms) / 1000)


num = SimpleNamespace(
    clamp=clamp,
    lerp=lerp,
    map_range=map_range,
    round_to=round_to,
    approx_eq=approx_eq,
    sign=sign,
    gcd=gcd,
    lcm=lcm,
    is_prime=is_prime,
    rand_int=rand_int,
    rand_normal=rand_normal,
)

str = SimpleNamespace(
    slugify=slugify,
    pad_both=pad_both,
    truncate=truncate,
    between=between,
    count_sub=count_sub,
    words=words,
    to_camel=to_camel,
    to_snake=to_snake,
    levenshtein=levenshtein,
    template=template,
    wrap=wrap,
)

arr = SimpleNamespace(
    chunk=chunk,
    window=window,
    compact=compact,
    dedup_by=dedup_by,
    group_by=group_by,
    partition=partition,
    zip_with=zip_with,
    flatten_depth=flatten_depth,
    sample=sample,
    rotate=rotate,
    binary_search=binary_search,
)

map = SimpleNamespace(
    get_path=get_path,
    set_path=set_path,
    pick=pick,
    omit=omit,
    deep_merge=deep_merge,
    invert=invert,
    filter_entries=filter_entries,
)

set = SimpleNamespace(
    union=set_union,
    intersect=set_intersect,
    diff=set_diff,
)
heap = SimpleNamespace(push_pop=heap_push_pop)

fn = SimpleNamespace(
    pipe=pipe,
    compose=compose,
    memoize=memoize,
    once=once,
    debounce=debounce,
    throttle=throttle,
)

err = SimpleNamespace(
    try_run=try_run,
    retry=retry,
    ensure=ensure,
)
async_ = SimpleNamespace(
    all_settled=all_settled,
    race_timeout=race_timeout,
)

io = SimpleNamespace(
    read_text=read_text,
    write_atomic=write_atomic,
    watch_dir=watch_dir,
)

json = SimpleNamespace(
    parse_safe=parse_safe,
    stringify_pretty=stringify_pretty,
)

time = SimpleNamespace(
    now_ms=now_ms,
    format_iso=format_iso,
    sleep=sleep,
)

sys = SimpleNamespace(
    env_get=env_get,
    args=args,
)
meta = SimpleNamespace(type_of=type_of)

API = {
    "num": num,
    "str": str,
    "arr": arr,
    "map": map,
    "set": set,
    "heap": heap,
    "fn": fn,
    "err": err,
    "async": async_,
    "io": io,
    "json": json,
    "time": time,
    "sys": sys,
    "meta": meta,
}


def call(module, function, *args, **kwargs):
    try:
        namespace = API[module]
        operation = getattr(namespace, function)
    except (KeyError, AttributeError) as error:
        raise KoraError(f"unknown Kora function: {module}.{function}") from error

    return operation(*args, **kwargs)


FUNCTION_COUNT = 66
