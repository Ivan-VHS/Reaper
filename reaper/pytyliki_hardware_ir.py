"""Strict importer and pure lowering adapter for Pytyliki Hardware IR v1.

Pytyliki owns hardware-domain semantics. Reaper owns CanonicalIR and execution.
The imported typed metadata remains attached as a sidecar because the existing
stack CanonicalIR cannot encode physical dimensions, register layouts or effects.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

from .ir import CanonicalIR, IRInstruction, verify
from .lexer import Token

SCHEMA = "reaper.typed-hardware-ir.v1"
TYPE_SYSTEM = "pytyliki.dimension-vector.v1"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 65_536
MAX_TYPES = 64
MAX_VALUES = 512
MAX_SYMBOLS = 192
MAX_EXPONENT = 16
MMIO_READ = 1 << 2
MMIO_WRITE = 1 << 3

WIDTHS = {"i64": 64, "u32": 32, "u64": 64, "f64": 64,
          "bool": 0, "unit": 0, "quantity": 0}
NUMERIC = {"i64", "u32", "u64", "f64", "quantity"}
OPERATIONS = {"const.f64", "input", "add", "sub", "mul", "div",
              "neg", "mmio.read", "mmio.write"}


class PytylikiHardwareIRError(ValueError):
    """Invalid, unsupported or unsafe Pytyliki Hardware IR."""


@dataclass(frozen=True, slots=True)
class HardwareSpan:
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class HardwareType:
    id: int
    kind: str
    width: int
    dimensions: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class HardwareValue:
    id: int
    op: str
    type_id: int
    lhs: int | None
    rhs: int | None
    symbol: int | None
    immediate: float
    effect: str
    span: HardwareSpan


@dataclass(frozen=True, slots=True)
class HardwareSymbol:
    name: str
    kind: str
    type_id: int
    access: str
    value: int | None
    span: HardwareSpan


@dataclass(frozen=True, slots=True)
class HardwareModule:
    schema: str
    module: str
    source_name: str
    target: str
    source_bytes: int
    allowed_effects: int
    inferred_effects: int
    types: tuple[HardwareType, ...]
    values: tuple[HardwareValue, ...]
    symbols: tuple[HardwareSymbol, ...]
    result_value: int | None

    @property
    def is_pure(self) -> bool:
        return self.inferred_effects == 0


@dataclass(frozen=True, slots=True)
class ReaperHardwareLowering:
    hardware: HardwareModule
    canonical_ir: CanonicalIR


def _integer(value: Any, label: str, low: int, high: int) -> int:
    if type(value) is not int or value < low or value > high:
        raise PytylikiHardwareIRError(f"{label}: expected integer in [{low}, {high}]")
    return value


def _text(value: Any, label: str, limit: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > limit or "\0" in value:
        raise PytylikiHardwareIRError(f"{label}: expected bounded non-empty text")
    return value


def _object(value: Any, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise PytylikiHardwareIRError(f"{label}: object fields do not match the v1 contract")
    return value


def _payload(value: Mapping[str, Any] | str | bytes | bytearray) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        raw = value.encode("utf-8") if isinstance(value, str) else bytes(value)
        if len(raw) > MAX_JSON_BYTES:
            raise PytylikiHardwareIRError("JSON payload exceeds the 2 MiB limit")
        try:
            decoded = raw.decode("utf-8", errors="strict")
            result = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PytylikiHardwareIRError("payload is not valid UTF-8 JSON") from exc
        if not isinstance(result, Mapping):
            raise PytylikiHardwareIRError("JSON root must be an object")
        return result
    raise PytylikiHardwareIRError("payload must be an object, UTF-8 JSON or bytes")


def _span(raw: Any, source_bytes: int, label: str) -> HardwareSpan:
    item = _object(raw, {"start", "end", "line", "column"}, label)
    start = _integer(item["start"], f"{label}.start", 0, source_bytes)
    end = _integer(item["end"], f"{label}.end", start, source_bytes)
    line = _integer(item["line"], f"{label}.line", 1, 2**31 - 1)
    column = _integer(item["column"], f"{label}.column", 1, 2**31 - 1)
    return HardwareSpan(start, end, line, column)


def _same_type(left: HardwareType, right: HardwareType) -> bool:
    return (left.kind, left.width, left.dimensions) == (right.kind, right.width, right.dimensions)


def _product_type(left: HardwareType, right: HardwareType, divide: bool) -> tuple[str, int, tuple[int, ...]]:
    if left.kind not in NUMERIC or right.kind not in NUMERIC:
        raise PytylikiHardwareIRError("mul/div operands must be numeric")
    if left.kind == "quantity" or right.kind == "quantity":
        if left.kind != "quantity" and any(left.dimensions):
            raise PytylikiHardwareIRError("scalar left operand carries dimensions")
        if right.kind != "quantity" and any(right.dimensions):
            raise PytylikiHardwareIRError("scalar right operand carries dimensions")
        sign = -1 if divide else 1
        dimensions = tuple(a + sign * b for a, b in zip(left.dimensions, right.dimensions, strict=True))
        if any(abs(part) > MAX_EXPONENT for part in dimensions):
            raise PytylikiHardwareIRError("dimension exponent exceeds the v1 limit")
        return "quantity", 0, dimensions
    if left.kind != right.kind or left.width != right.width:
        raise PytylikiHardwareIRError("mul/div scalar types must match exactly")
    return left.kind, left.width, left.dimensions


def import_hardware_ir(payload: Mapping[str, Any] | str | bytes | bytearray) -> HardwareModule:
    root = _object(_payload(payload), {
        "schema", "producer", "module", "source_name", "target", "source_bytes",
        "type_system", "result_value", "effects", "types", "values", "symbols",
    }, "root")
    if root["schema"] != SCHEMA or root["producer"] != "pytyliki":
        raise PytylikiHardwareIRError("unsupported schema or producer")
    if root["type_system"] != TYPE_SYSTEM:
        raise PytylikiHardwareIRError("unsupported type-system identity")

    module_name = _text(root["module"], "module", 47)
    source_name = _text(root["source_name"], "source_name", 47)
    target = _text(root["target"], "target", 32)
    if target not in {"host", "sim", "riscv64", "x86_64"}:
        raise PytylikiHardwareIRError(f"unsupported target {target!r}")
    source_bytes = _integer(root["source_bytes"], "source_bytes", 0, MAX_SOURCE_BYTES)

    effect_obj = _object(root["effects"], {"allowed", "inferred"}, "effects")
    allowed = _integer(effect_obj["allowed"], "effects.allowed", 0, 0xFF)
    inferred = _integer(effect_obj["inferred"], "effects.inferred", 0, 0xFF)
    if inferred & ~allowed:
        raise PytylikiHardwareIRError("inferred effects exceed the declared allowlist")

    raw_types = root["types"]
    if not isinstance(raw_types, list) or len(raw_types) > MAX_TYPES:
        raise PytylikiHardwareIRError("types: invalid table size")
    types: list[HardwareType] = []
    for index, raw in enumerate(raw_types):
        item = _object(raw, {"id", "kind", "width", "dimensions"}, f"types[{index}]")
        if _integer(item["id"], "type id", 0, MAX_TYPES - 1) != index:
            raise PytylikiHardwareIRError("type IDs must be contiguous and ordered")
        kind = _text(item["kind"], "type kind", 16)
        if kind not in WIDTHS or _integer(item["width"], "type width", 0, 64) != WIDTHS[kind]:
            raise PytylikiHardwareIRError("unknown type or inconsistent bit width")
        dims = item["dimensions"]
        if not isinstance(dims, list) or len(dims) != 8:
            raise PytylikiHardwareIRError("quantity dimensions must have exactly eight axes")
        dimensions = tuple(_integer(part, "dimension exponent", -MAX_EXPONENT, MAX_EXPONENT) for part in dims)
        if kind != "quantity" and any(dimensions):
            raise PytylikiHardwareIRError("only quantity types may carry physical dimensions")
        types.append(HardwareType(index, kind, WIDTHS[kind], dimensions))

    raw_symbols = root["symbols"]
    if not isinstance(raw_symbols, list) or len(raw_symbols) > MAX_SYMBOLS:
        raise PytylikiHardwareIRError("symbols: invalid table size")
    symbols: list[HardwareSymbol] = []
    symbol_index: dict[str, int] = {}
    for index, raw in enumerate(raw_symbols):
        item = _object(raw, {"name", "kind", "type", "access", "value", "span"}, f"symbols[{index}]")
        name = _text(item["name"], f"symbols[{index}].name", 47)
        if name in symbol_index:
            raise PytylikiHardwareIRError(f"duplicate symbol {name!r}")
        kind = _text(item["kind"], "symbol kind", 16)
        access = _text(item["access"], "register access", 16)
        if kind not in {"input", "derive", "register", "operation"}:
            raise PytylikiHardwareIRError("unknown symbol kind")
        if access not in {"none", "read_only", "write_only", "read_write"}:
            raise PytylikiHardwareIRError("unknown register access class")
        type_id = _integer(item["type"], "symbol type", 0, len(types) - 1)
        value = item["value"]
        if kind == "register":
            if value is not None or access == "none" or types[type_id].kind not in {"i64", "u32", "u64"}:
                raise PytylikiHardwareIRError("register requires fixed-width integer type and access class")
        else:
            if value is None or access != "none":
                raise PytylikiHardwareIRError("value symbol requires a binding and access=none")
            value = _integer(value, "symbol value", 0, MAX_VALUES - 1)
        symbol_index[name] = index
        symbols.append(HardwareSymbol(name, kind, type_id, access, value,
                                      _span(item["span"], source_bytes, f"symbols[{index}].span")))

    raw_values = root["values"]
    if not isinstance(raw_values, list) or len(raw_values) > MAX_VALUES:
        raise PytylikiHardwareIRError("values: invalid table size")
    values: list[HardwareValue] = []
    seen_effects = 0
    for index, raw in enumerate(raw_values):
        item = _object(raw, {"id", "op", "type", "lhs", "rhs", "symbol", "immediate", "effect", "span"}, f"values[{index}]")
        if _integer(item["id"], "value id", 0, MAX_VALUES - 1) != index:
            raise PytylikiHardwareIRError("value IDs must be contiguous and topologically ordered")
        op = _text(item["op"], "operation", 24)
        if op not in OPERATIONS:
            raise PytylikiHardwareIRError(f"unknown HIR operation {op!r}")
        type_id = _integer(item["type"], "result type", 0, len(types) - 1)

        def value_ref(field: str, bound: int, *, prior: bool) -> int | None:
            raw_ref = item[field]
            if raw_ref is None:
                return None
            ref = _integer(raw_ref, field, 0, bound)
            if prior and ref >= index:
                raise PytylikiHardwareIRError(f"{field} must reference an earlier HIR value")
            return ref

        lhs = value_ref("lhs", index - 1, prior=True) if index else None
        rhs = value_ref("rhs", index - 1, prior=True) if index else None
        if index == 0 and (item["lhs"] is not None or item["rhs"] is not None):
            raise PytylikiHardwareIRError("first HIR value cannot have operands")
        sym = value_ref("symbol", len(symbols) - 1, prior=False) if symbols else None
        if not symbols and item["symbol"] is not None:
            raise PytylikiHardwareIRError("HIR symbol reference has no symbol table")
        immediate = item["immediate"]
        if isinstance(immediate, bool) or not isinstance(immediate, (int, float)):
            raise PytylikiHardwareIRError("HIR immediate must be numeric")
        try:
            immediate = float(immediate)
        except (OverflowError, ValueError) as exc:
            raise PytylikiHardwareIRError("HIR immediate must be finite") from exc
        if not math.isfinite(immediate):
            raise PytylikiHardwareIRError("HIR immediate must be finite")
        effect = _text(item["effect"], "value effect", 24)
        source_span = _span(item["span"], source_bytes, f"values[{index}].span")
        result_type = types[type_id]

        if op == "const.f64":
            if lhs is not None or rhs is not None or sym is not None or effect != "pure" or result_type.kind not in NUMERIC:
                raise PytylikiHardwareIRError("malformed numeric constant")
        elif op == "input":
            if lhs is None or rhs is not None or sym is None or effect != "pure":
                raise PytylikiHardwareIRError("malformed input-reference node")
            symbol = symbols[sym]
            if symbol.kind not in {"input", "derive"} or symbol.value != lhs or symbol.type_id != type_id:
                raise PytylikiHardwareIRError("input-reference node does not match its input symbol")
            if not _same_type(result_type, types[values[lhs].type_id]):
                raise PytylikiHardwareIRError("input-reference node changes type")
        elif op in {"add", "sub"}:
            if lhs is None or rhs is None or sym is not None or effect != "pure":
                raise PytylikiHardwareIRError("malformed add/sub node")
            if not _same_type(result_type, types[values[lhs].type_id]) or not _same_type(result_type, types[values[rhs].type_id]):
                raise PytylikiHardwareIRError("add/sub requires identical operand and result types")
        elif op in {"mul", "div"}:
            if lhs is None or rhs is None or sym is not None or effect != "pure":
                raise PytylikiHardwareIRError("malformed mul/div node")
            expected = _product_type(types[values[lhs].type_id], types[values[rhs].type_id], op == "div")
            if expected != (result_type.kind, result_type.width, result_type.dimensions):
                raise PytylikiHardwareIRError("mul/div result does not match dimension algebra")
        elif op == "neg":
            if lhs is None or rhs is not None or sym is not None or effect != "pure":
                raise PytylikiHardwareIRError("malformed negation")
            if not _same_type(result_type, types[values[lhs].type_id]):
                raise PytylikiHardwareIRError("negation changes operand type")
        elif op == "mmio.read":
            if lhs is not None or rhs is not None or sym is None or effect != "mmio.read":
                raise PytylikiHardwareIRError("malformed MMIO read")
            register = symbols[sym]
            if register.kind != "register" or register.access == "write_only" or register.type_id != type_id:
                raise PytylikiHardwareIRError("MMIO read violates register descriptor")
            seen_effects |= MMIO_READ
        elif op == "mmio.write":
            if lhs is None or rhs is not None or sym is None or effect != "mmio.write":
                raise PytylikiHardwareIRError("malformed MMIO write")
            register = symbols[sym]
            if register.kind != "register" or register.access == "read_only":
                raise PytylikiHardwareIRError("MMIO write violates register access")
            if result_type.kind != "unit" or not _same_type(types[values[lhs].type_id], types[register.type_id]):
                raise PytylikiHardwareIRError("MMIO write value or unit result type is invalid")
            seen_effects |= MMIO_WRITE
        values.append(HardwareValue(index, op, type_id, lhs, rhs, sym, immediate, effect, source_span))

    for symbol in symbols:
        if symbol.kind != "register":
            if symbol.value is None or symbol.value >= len(values):
                raise PytylikiHardwareIRError(f"symbol {symbol.name!r} references an unknown value")
            if symbol.type_id != values[symbol.value].type_id:
                raise PytylikiHardwareIRError(f"symbol {symbol.name!r} type does not match its value")

    for symbol in symbols:
        if symbol.kind == "operation":
            if symbol.value is None:
                raise PytylikiHardwareIRError("operation symbol has no HIR value")
            value = values[symbol.value]
            if value.op not in {"mmio.read", "mmio.write"} or value.symbol is None:
                raise PytylikiHardwareIRError("operation symbol must refer to an effectful hardware value")
            register = symbols[value.symbol]
            if register.kind != "register":
                raise PytylikiHardwareIRError("operation HIR must reference a register symbol")
            if value.op == "mmio.read":
                expected_type = register.type_id
            else:
                expected_type = next((i for i, item in enumerate(types) if item.kind == "unit"), None)
            if expected_type is None or symbol.type_id != expected_type or value.type_id != expected_type:
                raise PytylikiHardwareIRError("operation symbol type does not match its MMIO result")

    if seen_effects != inferred:
        raise PytylikiHardwareIRError("effect summary does not match HIR operations")
    if inferred & ~allowed:
        raise PytylikiHardwareIRError("inferred effects exceed the allowlist")
    result_value = root["result_value"]
    if result_value is not None:
        result_value = _integer(result_value, "result_value", 0, len(values) - 1)
    return HardwareModule(SCHEMA, module_name, source_name, target, source_bytes,
                          allowed, inferred, tuple(types), tuple(values), tuple(symbols), result_value)


def _token(kind: str, value: str, span: HardwareSpan) -> Token:
    return Token(kind, value, span.line, span.column)


def lower_pure(module: HardwareModule, *, emit_result: bool = False) -> ReaperHardwareLowering:
    """Lower only the pure f64/quantity subset; preserve hardware metadata separately."""
    if not isinstance(module, HardwareModule):
        raise PytylikiHardwareIRError("expected an imported HardwareModule")
    if not module.is_pure:
        raise PytylikiHardwareIRError("effectful hardware IR cannot enter Reaper's pure VM path")
    if module.target != "host":
        raise PytylikiHardwareIRError("pure CanonicalIR lowering requires the explicit host target")
    if any(item.kind not in {"f64", "quantity"} for item in module.types):
        raise PytylikiHardwareIRError("fixed-width integer and non-numeric types have no matching overflow/width semantics in Reaper CanonicalIR")

    symbol_by_id = {index: item for index, item in enumerate(module.symbols)}
    instructions: list[IRInstruction] = []
    visiting: set[int] = set()
    emitted: set[int] = set()

    def emit_value(index: int) -> None:
        if index in emitted:
            return
        if index in visiting or index < 0 or index >= len(module.values):
            raise PytylikiHardwareIRError("lowering found a cyclic or invalid HIR value")
        value = module.values[index]
        token = _token("NUMBER", repr(value.immediate), value.span)
        visiting.add(index)
        if value.op == "const.f64":
            instructions.append(IRInstruction("CONST", value.immediate, token))
        elif value.op == "input":
            if value.symbol is None:
                raise PytylikiHardwareIRError("input value has no symbol binding")
            symbol = symbol_by_id[value.symbol]
            instructions.append(IRInstruction("LOAD", symbol.name, _token("IDENT", symbol.name, value.span)))
        elif value.op in {"add", "sub", "mul", "div"}:
            assert value.lhs is not None and value.rhs is not None
            emit_value(value.lhs)
            emit_value(value.rhs)
            operator = {"add": "+", "sub": "-", "mul": "*", "div": "/"}[value.op]
            instructions.append(IRInstruction("BINARY", operator, token))
        elif value.op == "neg":
            assert value.lhs is not None
            emit_value(value.lhs)
            instructions.append(IRInstruction("UNARY", "-", token))
        else:
            raise PytylikiHardwareIRError(f"{value.op!r} has no pure CanonicalIR lowering")
        visiting.remove(index)
        emitted.add(index)

    for symbol in module.symbols:
        if symbol.kind == "register":
            continue
        assert symbol.value is not None
        emit_value(symbol.value)
        instructions.append(IRInstruction("DEFINE", (symbol.name, False), _token("MAKE", "make", symbol.span)))

    if emit_result and module.result_value is not None:
        result_symbol = next((item for item in module.symbols
                              if item.kind != "register" and item.value == module.result_value), None)
        if result_symbol is not None:
            instructions.append(IRInstruction("LOAD", result_symbol.name,
                                              _token("IDENT", result_symbol.name, result_symbol.span)))
        else:
            emit_value(module.result_value)
        instructions.append(IRInstruction("EMIT", None,
                                          _token("EMIT", "emit", module.values[module.result_value].span)))

    canonical = CanonicalIR(tuple(instructions), module.source_name)
    verify(canonical)
    return ReaperHardwareLowering(module, canonical)
