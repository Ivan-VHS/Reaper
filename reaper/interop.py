"""Narrow C ABI declarations and explicit foreign-object lifetime wrappers.

Header parsing intentionally handles simple scalar prototypes only. It does not
run a preprocessor or infer layouts for structs, unions, macros or variadic calls.
"""
from __future__ import annotations

import ctypes
import re
from dataclasses import dataclass
from typing import Any, Protocol

from .security import CapabilityAuthority, CapabilityToken


_C_TYPES: dict[str, Any] = {
    "void": None,
    "int": ctypes.c_int,
    "int32_t": ctypes.c_int32,
    "int64_t": ctypes.c_int64,
    "size_t": ctypes.c_size_t,
    "float": ctypes.c_float,
    "double": ctypes.c_double,
    "char*": ctypes.c_char_p,
    "const char*": ctypes.c_char_p,
    "void*": ctypes.c_void_p,
}


@dataclass(frozen=True, slots=True)
class CFunctionSignature:
    name: str
    return_type: str
    argument_types: tuple[str, ...]


_PROTOTYPE = re.compile(
    r"(?m)^\s*(?P<return>void|int32_t|int64_t|size_t|int|float|double|const\s+char\s*\*|char\s*\*|void\s*\*)"
    r"\s*(?P<name>[A-Za-z_]\w*)\s*\((?P<args>[^;{}]*)\)\s*;"
)


def _normalize_c_type(raw: str) -> str:
    value = re.sub(r"\b(const|volatile|restrict)\b", "", raw)
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace(" *", "*").replace("* ", "*")
    if value not in _C_TYPES:
        raise ValueError(f"unsupported C ABI type: {raw.strip()}")
    return value


def _argument_type(declaration: str) -> str:
    text = declaration.strip()
    if not text or text == "void":
        return "void"
    text = re.sub(r"\s+[A-Za-z_]\w*$", "", text)
    return _normalize_c_type(text)


def parse_c_header(header: str) -> tuple[CFunctionSignature, ...]:
    """Read plain function prototypes from a deliberately limited C header subset."""
    cleaned = re.sub(r"/\*.*?\*/|//[^\n]*", "", header, flags=re.S)
    signatures: list[CFunctionSignature] = []
    for match in _PROTOTYPE.finditer(cleaned):
        result = _normalize_c_type(match.group("return"))
        arguments_text = match.group("args").strip()
        if arguments_text in {"", "void"}:
            arguments: tuple[str, ...] = ()
        else:
            if "..." in arguments_text:
                raise ValueError("variadic C functions are not supported")
            arguments = tuple(_argument_type(item) for item in arguments_text.split(","))
            if "void" in arguments:
                raise ValueError("'void' may only appear as the sole argument marker")
        signatures.append(CFunctionSignature(match.group("name"), result, arguments))
    return tuple(signatures)


class NativeLibrary:
    """Explicit ctypes loader; callers must supply a valid native.load capability."""

    def __init__(self, library: Any, path: str) -> None:
        self._library = library
        self.path = path

    @classmethod
    def load(
        cls, path: str, authority: CapabilityAuthority, token: CapabilityToken
    ) -> "NativeLibrary":
        if not authority.verify(token, "native.load", path):
            raise PermissionError("a matching native.load capability is required")
        return cls(ctypes.CDLL(path), path)

    def bind(self, signature: CFunctionSignature) -> Any:
        if signature.return_type not in _C_TYPES or any(
            item not in _C_TYPES or item == "void" for item in signature.argument_types
        ):
            raise ValueError("C function signature contains an unsupported ABI type")
        function = getattr(self._library, signature.name)
        function.argtypes = [_C_TYPES[item] for item in signature.argument_types]
        function.restype = _C_TYPES[signature.return_type]
        return function


class ForeignAdapter(Protocol):
    def import_value(self, value: Any) -> Any: ...
    def export_value(self, value: Any) -> Any: ...


class AdapterRegistry:
    """Named adapter registry; only adapters explicitly registered by the host work."""

    def __init__(self) -> None:
        self._adapters: dict[str, ForeignAdapter] = {}

    def register(self, name: str, adapter: ForeignAdapter) -> None:
        if not name or name in self._adapters:
            raise ValueError("adapter name must be non-empty and unique")
        self._adapters[name] = adapter

    def convert(self, value: Any, source: str, target: str) -> Any:
        if source not in self._adapters or target not in self._adapters:
            raise LookupError("source and target adapters must both be registered")
        host_value = self._adapters[source].export_value(value)
        return self._adapters[target].import_value(host_value)


class PythonAdapter:
    def import_value(self, value: Any) -> Any:
        return value

    def export_value(self, value: Any) -> Any:
        return value


class ForeignHandle:
    """A revocable handle with one explicit release callback."""

    def __init__(self, value: Any, owner: str, release: Any = None) -> None:
        if not owner:
            raise ValueError("foreign handle owner must be non-empty")
        self._value = value
        self.owner = owner
        self._release = release
        self._closed = False

    @property
    def value(self) -> Any:
        if self._closed:
            raise RuntimeError("foreign handle has been released")
        return self._value

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        value, self._value = self._value, None
        if self._release is not None:
            self._release(value)

    def __enter__(self) -> "ForeignHandle":
        if self._closed:
            raise RuntimeError("foreign handle has been released")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()
