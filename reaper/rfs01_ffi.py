"""Explicit-path adapter for the optional Pytyliki RFS-01 C ABI extension."""

from __future__ import annotations

import ctypes
import math
from pathlib import Path
from typing import Any, Mapping

from .ffi import FfiError
from .native import _load_library


_LAYER = {
    "Basement": 1,
    "Corridor": 2,
    "Gate": 3,
    "Skyline": 4,
    "Horizon": 5,
}
_CHANNEL = {"Wire": 1, "Rail": 2, "Beat": 3, "Current": 4, "Bridge": 5}
_ABI_VERSION = 1


class _NodeV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("id", ctypes.c_char * 64),
        ("layer", ctypes.c_uint32),
        ("pressure", ctypes.c_double),
        ("load_limit", ctypes.c_double),
        ("integrity", ctypes.c_double),
        ("noise_db", ctypes.c_double),
        ("core_seed", ctypes.c_char * 128),
        ("active", ctypes.c_int32),
    ]


class _LinkV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("id", ctypes.c_char * 64),
        ("origin", ctypes.c_char * 64),
        ("target", ctypes.c_char * 64),
        ("channel", ctypes.c_uint32),
        ("blocked", ctypes.c_int32),
        ("weight", ctypes.c_double),
    ]


class _SignalV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("sequence", ctypes.c_uint64),
        ("origin", ctypes.c_char * 64),
        ("payload", ctypes.c_char * 4096),
        ("trusted", ctypes.c_int32),
        ("manufactured", ctypes.c_int32),
    ]


def _text(value: Any, label: str, capacity: int, allow_empty: bool = False) -> bytes:
    if not isinstance(value, str):
        raise FfiError(f"{label} must be text")
    encoded = value.encode("utf-8")
    if b"\0" in encoded or len(encoded) >= capacity or (not allow_empty and not encoded):
        raise FfiError(f"{label} must fit in {capacity - 1} UTF-8 bytes and contain no NUL")
    return encoded


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FfiError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise FfiError(f"{label} must be a finite number")
    return result


def _node(value: Mapping[str, Any]) -> _NodeV1:
    if not isinstance(value, Mapping):
        raise FfiError("RFS-01 node must be a mapping")
    try:
        layer = _LAYER[value["layer"]]
        active = value["active"]
        if not isinstance(active, bool):
            raise FfiError("node.active must be boolean")
        result = _NodeV1()
        result.struct_size = ctypes.sizeof(_NodeV1)
        result.abi_version = _ABI_VERSION
        result.id = _text(value["id"], "node.id", 64)
        result.layer = layer
        result.pressure = _number(value["pressure"], "node.pressure")
        result.load_limit = _number(value["load_limit"], "node.load_limit")
        result.integrity = _number(value["integrity"], "node.integrity")
        result.noise_db = _number(value["noise_db"], "node.noise_db")
        result.core_seed = _text(value["core_seed"], "node.core_seed", 128)
        result.active = int(active)
        return result
    except KeyError as error:
        raise FfiError(f"RFS-01 node is missing field {error.args[0]!r}") from error


def _link(value: Mapping[str, Any]) -> _LinkV1:
    if not isinstance(value, Mapping):
        raise FfiError("RFS-01 link must be a mapping")
    try:
        channel = _CHANNEL[value["channel"]]
        blocked = value["blocked"]
        if not isinstance(blocked, bool):
            raise FfiError("link.blocked must be boolean")
        result = _LinkV1()
        result.struct_size = ctypes.sizeof(_LinkV1)
        result.abi_version = _ABI_VERSION
        result.id = _text(value["id"], "link.id", 64)
        result.origin = _text(value["origin"], "link.origin", 64)
        result.target = _text(value["target"], "link.target", 64)
        result.channel = channel
        result.blocked = int(blocked)
        result.weight = _number(value["weight"], "link.weight")
        return result
    except KeyError as error:
        raise FfiError(f"RFS-01 link has a missing or unsupported field {error.args[0]!r}") from error


def _signal(value: Mapping[str, Any]) -> _SignalV1:
    if not isinstance(value, Mapping):
        raise FfiError("RFS-01 signal must be a mapping")
    try:
        trusted = value["trusted"]
        manufactured = value["manufactured"]
        if not isinstance(trusted, bool) or not isinstance(manufactured, bool):
            raise FfiError("signal trust flags must be boolean")
        sequence = value["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence < (1 << 64):
            raise FfiError("signal.sequence must be an unsigned 64-bit integer")
        result = _SignalV1()
        result.struct_size = ctypes.sizeof(_SignalV1)
        result.abi_version = _ABI_VERSION
        result.sequence = sequence
        result.origin = _text(value["origin"], "signal.origin", 64)
        result.payload = _text(value["payload"], "signal.payload", 4096, allow_empty=True)
        result.trusted = int(trusted)
        result.manufactured = int(manufactured)
        return result
    except KeyError as error:
        raise FfiError(f"RFS-01 signal is missing field {error.args[0]!r}") from error


def _decode(value: bytes) -> str:
    return value.split(b"\0", 1)[0].decode("utf-8", errors="strict")


def _node_dict(value: _NodeV1) -> dict[str, Any]:
    layer = next(name for name, number in _LAYER.items() if number == value.layer)
    return {
        "id": _decode(value.id),
        "layer": layer,
        "pressure": float(value.pressure),
        "load_limit": float(value.load_limit),
        "integrity": float(value.integrity),
        "noise_db": float(value.noise_db),
        "core_seed": _decode(value.core_seed),
        "active": bool(value.active),
    }


class PytylikiRFS01Bridge:
    """Opt-in bridge to Pytyliki's read-only RFS-01 C11 record/planning API.

    Loading native code is explicit. This bridge never searches PATH, loads a
    library by name, or mutates process, kernel, or hardware state.
    """

    def __init__(self, library_path: str) -> None:
        path = Path(library_path).expanduser()
        if not path.is_absolute():
            raise FfiError("Pytyliki RFS-01 library path must be absolute and explicit")
        try:
            self.path = str(path.resolve(strict=True))
            self.library = _load_library(self.path)
        except (OSError, TypeError, ValueError) as error:
            raise FfiError(f"cannot load trusted Pytyliki library: {error}") from error
        self.closed = False
        try:
            version = self.library.pytyliki_rfs01_abi_version
        except AttributeError as error:
            raise FfiError("Pytyliki library does not expose the RFS-01 ABI extension") from error
        version.argtypes = []
        version.restype = ctypes.c_uint32
        actual = int(version())
        if actual != _ABI_VERSION:
            raise FfiError(f"unsupported Pytyliki RFS-01 ABI version {actual}; expected {_ABI_VERSION}")

        signatures = {
            "pytyliki_rfs01_validate_node_v1": ([ctypes.POINTER(_NodeV1)], ctypes.c_int32),
            "pytyliki_rfs01_validate_link_v1": ([ctypes.POINTER(_LinkV1)], ctypes.c_int32),
            "pytyliki_rfs01_validate_signal_v1": ([ctypes.POINTER(_SignalV1)], ctypes.c_int32),
            "pytyliki_rfs01_signal_is_clean_v1": ([ctypes.POINTER(_SignalV1)], ctypes.c_int32),
            "pytyliki_rfs01_pressure_reserve_v1": ([ctypes.POINTER(_NodeV1), ctypes.POINTER(ctypes.c_double)], ctypes.c_int32),
            "pytyliki_rfs01_plan_pressure_forward_v1": ([ctypes.POINTER(_NodeV1), ctypes.POINTER(_NodeV1), ctypes.POINTER(_LinkV1), ctypes.POINTER(_NodeV1)], ctypes.c_int32),
            "pytyliki_rfs01_plan_signal_forward_v1": ([ctypes.POINTER(_NodeV1), ctypes.POINTER(_NodeV1), ctypes.POINTER(_LinkV1), ctypes.POINTER(_SignalV1), ctypes.POINTER(_NodeV1)], ctypes.c_int32),
            "pytyliki_rfs01_root_restore_v1": ([ctypes.POINTER(_NodeV1), ctypes.POINTER(_NodeV1)], ctypes.c_int32),
            "pytyliki_rfs01_core_restore_v1": ([ctypes.POINTER(_NodeV1), ctypes.POINTER(_NodeV1), ctypes.POINTER(_NodeV1)], ctypes.c_int32),
        }
        try:
            for name, (arguments, result_type) in signatures.items():
                function = getattr(self.library, name)
                function.argtypes = arguments
                function.restype = result_type
        except AttributeError as error:
            raise FfiError(f"Pytyliki RFS-01 symbol is missing: {error}") from error

    def _ensure_open(self) -> None:
        if self.closed:
            raise FfiError("Pytyliki RFS-01 bridge is closed")

    @staticmethod
    def _status(status: int, operation: str) -> None:
        messages = {
            -1: "invalid argument or record",
            -2: "unsupported ABI version",
            -3: "target load limit would be exceeded",
            -4: "link is blocked or does not match the route",
            -5: "signal is untrusted, manufactured, or from another origin",
        }
        if status != 0:
            raise FfiError(f"Pytyliki RFS-01 {operation}: {messages.get(status, f'ABI status {status}')}")

    def validate_node(self, record: Mapping[str, Any]) -> None:
        self._ensure_open()
        item = _node(record)
        self._status(int(self.library.pytyliki_rfs01_validate_node_v1(ctypes.byref(item))), "validate node")

    def validate_link(self, record: Mapping[str, Any]) -> None:
        self._ensure_open()
        item = _link(record)
        self._status(int(self.library.pytyliki_rfs01_validate_link_v1(ctypes.byref(item))), "validate link")

    def validate_signal(self, record: Mapping[str, Any]) -> None:
        self._ensure_open()
        item = _signal(record)
        self._status(int(self.library.pytyliki_rfs01_validate_signal_v1(ctypes.byref(item))), "validate signal")

    def signal_is_clean(self, record: Mapping[str, Any]) -> bool:
        self._ensure_open()
        item = _signal(record)
        status = int(self.library.pytyliki_rfs01_signal_is_clean_v1(ctypes.byref(item)))
        if status < 0:
            self._status(status, "check signal provenance")
        return bool(status)

    def reserve(self, record: Mapping[str, Any]) -> float:
        self._ensure_open()
        item = _node(record)
        output = ctypes.c_double()
        status = self.library.pytyliki_rfs01_pressure_reserve_v1(ctypes.byref(item), ctypes.byref(output))
        self._status(int(status), "compute reserve")
        if not math.isfinite(output.value):
            raise FfiError("Pytyliki RFS-01 returned a non-finite reserve")
        return float(output.value)

    def plan_pressure_forward(
        self, source: Mapping[str, Any], target: Mapping[str, Any], link: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._ensure_open()
        source_item, target_item, link_item = _node(source), _node(target), _link(link)
        output = _NodeV1()
        status = self.library.pytyliki_rfs01_plan_pressure_forward_v1(
            ctypes.byref(source_item), ctypes.byref(target_item), ctypes.byref(link_item), ctypes.byref(output)
        )
        self._status(int(status), "plan pressure flow")
        return _node_dict(output)

    def plan_signal_forward(
        self, source: Mapping[str, Any], target: Mapping[str, Any],
        link: Mapping[str, Any], signal: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._ensure_open()
        source_item, target_item, link_item, signal_item = _node(source), _node(target), _link(link), _signal(signal)
        output = _NodeV1()
        status = self.library.pytyliki_rfs01_plan_signal_forward_v1(
            ctypes.byref(source_item), ctypes.byref(target_item), ctypes.byref(link_item),
            ctypes.byref(signal_item), ctypes.byref(output)
        )
        self._status(int(status), "plan signal flow")
        return _node_dict(output)

    def restore_root(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        self._ensure_open()
        root = _node(snapshot)
        output = _NodeV1()
        status = self.library.pytyliki_rfs01_root_restore_v1(ctypes.byref(root), ctypes.byref(output))
        self._status(int(status), "restore root")
        return _node_dict(output)

    def restore_core(
        self, current: Mapping[str, Any], snapshot: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._ensure_open()
        current_item, root_item = _node(current), _node(snapshot)
        output = _NodeV1()
        status = self.library.pytyliki_rfs01_core_restore_v1(
            ctypes.byref(current_item), ctypes.byref(root_item), ctypes.byref(output)
        )
        self._status(int(status), "restore core")
        return _node_dict(output)

    def close(self) -> None:
        # ctypes does not expose a portable dlclose/FreeLibrary contract.
        self.closed = True

    def __enter__(self) -> "PytylikiRFS01Bridge":
        self._ensure_open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
