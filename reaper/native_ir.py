"""Versioned typed IR and runtime-call registry for native Reaper backends."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


NATIVE_IR_VERSION = 1


class NativeType(str, Enum):
    I64 = "i64"
    BOOL = "bool"
    STRING = "string"
    ARRAY = "array<i64>"
    MAP = "map<string,i64>"
    UNIT = "unit"


class Ownership(str, Enum):
    SCALAR = "scalar"
    BORROWED = "borrowed"
    OWNED = "owned"


class Effect(str, Enum):
    PURE = "pure"
    ALLOCATE = "allocate"
    MUTATE = "mutate"
    IO = "io"


@dataclass(frozen=True, slots=True)
class RuntimeCall:
    call_id: str
    arguments: tuple[NativeType, ...]
    result: NativeType
    c_symbol: str
    effect: Effect
    argument_ownership: tuple[Ownership, ...]
    result_ownership: Ownership


_RUNTIME_CALLS = (
    RuntimeCall("i64.add", (NativeType.I64, NativeType.I64), NativeType.I64, "rpr_add", Effect.PURE, (Ownership.SCALAR, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("i64.sub", (NativeType.I64, NativeType.I64), NativeType.I64, "rpr_sub", Effect.PURE, (Ownership.SCALAR, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("i64.mul", (NativeType.I64, NativeType.I64), NativeType.I64, "rpr_mul", Effect.PURE, (Ownership.SCALAR, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("i64.floor_div", (NativeType.I64, NativeType.I64), NativeType.I64, "rpr_floor_div", Effect.PURE, (Ownership.SCALAR, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("i64.mod", (NativeType.I64, NativeType.I64), NativeType.I64, "rpr_mod", Effect.PURE, (Ownership.SCALAR, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("i64.pow", (NativeType.I64, NativeType.I64), NativeType.I64, "rpr_pow", Effect.PURE, (Ownership.SCALAR, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("string.concat", (NativeType.STRING, NativeType.STRING), NativeType.STRING, "rpr_string_concat", Effect.ALLOCATE, (Ownership.BORROWED, Ownership.BORROWED), Ownership.OWNED),
    RuntimeCall("string.length", (NativeType.STRING,), NativeType.I64, "rpr_string_length", Effect.PURE, (Ownership.BORROWED,), Ownership.SCALAR),
    RuntimeCall("array.new", (), NativeType.ARRAY, "rpr_array_from", Effect.ALLOCATE, (), Ownership.OWNED),
    RuntimeCall("array.retain", (NativeType.ARRAY,), NativeType.ARRAY, "rpr_array_retain", Effect.MUTATE, (Ownership.BORROWED,), Ownership.OWNED),
    RuntimeCall("array.release", (NativeType.ARRAY,), NativeType.UNIT, "rpr_array_release", Effect.MUTATE, (Ownership.OWNED,), Ownership.SCALAR),
    RuntimeCall("array.get", (NativeType.ARRAY, NativeType.I64), NativeType.I64, "rpr_array_get_owned", Effect.MUTATE, (Ownership.OWNED, Ownership.SCALAR), Ownership.SCALAR),
    RuntimeCall("array.length", (NativeType.ARRAY,), NativeType.I64, "rpr_array_length_owned", Effect.MUTATE, (Ownership.OWNED,), Ownership.SCALAR),
    RuntimeCall("array.push", (NativeType.ARRAY, NativeType.I64), NativeType.ARRAY, "rpr_array_push_owned", Effect.MUTATE, (Ownership.OWNED, Ownership.SCALAR), Ownership.OWNED),
    RuntimeCall("map.new", (), NativeType.MAP, "rpr_map_from", Effect.ALLOCATE, (), Ownership.OWNED),
    RuntimeCall("map.retain", (NativeType.MAP,), NativeType.MAP, "rpr_map_retain", Effect.MUTATE, (Ownership.BORROWED,), Ownership.OWNED),
    RuntimeCall("map.release", (NativeType.MAP,), NativeType.UNIT, "rpr_map_release", Effect.MUTATE, (Ownership.OWNED,), Ownership.SCALAR),
    RuntimeCall("map.get", (NativeType.MAP, NativeType.STRING), NativeType.I64, "rpr_map_get_owned", Effect.MUTATE, (Ownership.OWNED, Ownership.BORROWED), Ownership.SCALAR),
    RuntimeCall("map.put", (NativeType.MAP, NativeType.STRING, NativeType.I64), NativeType.MAP, "rpr_map_put_owned", Effect.MUTATE, (Ownership.OWNED, Ownership.BORROWED, Ownership.SCALAR), Ownership.OWNED),
    RuntimeCall("map.has", (NativeType.MAP, NativeType.STRING), NativeType.BOOL, "rpr_map_has_owned", Effect.MUTATE, (Ownership.OWNED, Ownership.BORROWED), Ownership.SCALAR),
    RuntimeCall("map.length", (NativeType.MAP,), NativeType.I64, "rpr_map_length_owned", Effect.MUTATE, (Ownership.OWNED,), Ownership.SCALAR),
)

RUNTIME_CALLS: dict[str, RuntimeCall] = {call.call_id: call for call in _RUNTIME_CALLS}


class NativeIRVerificationError(ValueError):
    pass


def runtime_call(call_id: str) -> RuntimeCall:
    try:
        return RUNTIME_CALLS[call_id]
    except KeyError as error:
        raise NativeIRVerificationError(f"unknown runtime-call ID: {call_id}") from error


@dataclass(frozen=True, slots=True)
class NativeIRValue:
    value_id: int
    operation: str
    result_type: NativeType
    operands: tuple[int, ...] = ()
    symbol: str | None = None
    runtime_call: str | None = None
    ownership: Ownership = Ownership.SCALAR
    source_line: int = 1
    source_column: int = 1


@dataclass(frozen=True, slots=True)
class NativeIRModule:
    values: tuple[NativeIRValue, ...]
    source_name: str = "<memory>"
    version: int = NATIVE_IR_VERSION


def verify_native_ir(module: NativeIRModule) -> None:
    """Verify SSA-style IDs, operand order, type contracts and runtime calls."""
    if not isinstance(module, NativeIRModule):
        raise NativeIRVerificationError("expected a NativeIRModule")
    if module.version != NATIVE_IR_VERSION:
        raise NativeIRVerificationError("unsupported native IR version")
    if not isinstance(module.source_name, str) or not module.source_name:
        raise NativeIRVerificationError("native IR source name must not be empty")
    if not isinstance(module.values, tuple):
        raise NativeIRVerificationError("native IR values must be an immutable tuple")

    for index, value in enumerate(module.values):
        where = f"{module.source_name}: native IR value {index}"
        if not isinstance(value, NativeIRValue):
            raise NativeIRVerificationError(f"{where}: expected a NativeIRValue")
        if type(value.value_id) is not int or value.value_id != index:
            raise NativeIRVerificationError(f"{where}: SSA value ID must match its position")
        if not isinstance(value.operation, str) or not value.operation:
            raise NativeIRVerificationError(f"{where}: operation must be named")
        if not isinstance(value.result_type, NativeType):
            raise NativeIRVerificationError(f"{where}: invalid result type")
        if not isinstance(value.operands, tuple):
            raise NativeIRVerificationError(f"{where}: operands must be a tuple")
        if not all(type(operand) is int and 0 <= operand < index for operand in value.operands):
            raise NativeIRVerificationError(f"{where}: operands must reference earlier SSA values")
        if type(value.source_line) is not int or value.source_line < 1:
            raise NativeIRVerificationError(f"{where}: invalid source line")
        if type(value.source_column) is not int or value.source_column < 1:
            raise NativeIRVerificationError(f"{where}: invalid source column")

        if value.operation in {"CONST", "LOAD"}:
            if value.operands:
                raise NativeIRVerificationError(f"{where}: {value.operation} cannot have operands")
        elif value.operation == "UNARY":
            if len(value.operands) != 1:
                raise NativeIRVerificationError(f"{where}: unary operation needs one operand")
        elif value.operation == "BINARY":
            if len(value.operands) != 2:
                raise NativeIRVerificationError(f"{where}: binary operation needs two operands")
        elif value.operation == "CALL":
            if not value.symbol:
                raise NativeIRVerificationError(f"{where}: call must name a function")
        elif value.operation == "ARRAY_LITERAL":
            if value.result_type != NativeType.ARRAY:
                raise NativeIRVerificationError(f"{where}: array literal must produce array type")
            if any(module.values[operand].result_type != NativeType.I64 for operand in value.operands):
                raise NativeIRVerificationError(f"{where}: first native array slice contains only i64 values")
        elif value.operation == "MAP_LITERAL":
            if value.result_type != NativeType.MAP:
                raise NativeIRVerificationError(f"{where}: map literal must produce map type")
            if len(value.operands) % 2:
                raise NativeIRVerificationError(f"{where}: map literal requires key/value operand pairs")
            for offset in range(0, len(value.operands), 2):
                key_type = module.values[value.operands[offset]].result_type
                item_type = module.values[value.operands[offset + 1]].result_type
                if key_type != NativeType.STRING:
                    raise NativeIRVerificationError(f"{where}: native map keys must be strings")
                if item_type != NativeType.I64:
                    raise NativeIRVerificationError(f"{where}: native map values must be i64")
        elif value.operation == "INDEX":
            if len(value.operands) != 2:
                raise NativeIRVerificationError(f"{where}: index operation needs collection and key")
        else:
            raise NativeIRVerificationError(f"{where}: unsupported operation {value.operation!r}")

        if value.runtime_call is not None:
            descriptor = runtime_call(value.runtime_call)
            actual_types = tuple(module.values[operand].result_type for operand in value.operands)
            if actual_types != descriptor.arguments:
                raise NativeIRVerificationError(f"{where}: runtime-call argument types do not match {value.runtime_call}")
            if value.result_type != descriptor.result:
                raise NativeIRVerificationError(f"{where}: runtime-call result type does not match {value.runtime_call}")
            if value.ownership != descriptor.result_ownership:
                raise NativeIRVerificationError(f"{where}: result ownership does not match {value.runtime_call}")
        elif value.result_type in {NativeType.ARRAY, NativeType.MAP} and value.ownership != Ownership.OWNED:
            raise NativeIRVerificationError(f"{where}: heap collection results must be owned")


def serialize_native_ir(module: NativeIRModule) -> dict[str, object]:
    verify_native_ir(module)
    return {
        "version": module.version,
        "source": module.source_name,
        "values": [
            {
                "id": value.value_id,
                "op": value.operation,
                "type": value.result_type.value,
                "operands": list(value.operands),
                "symbol": value.symbol,
                "runtime_call": value.runtime_call,
                "ownership": value.ownership.value,
                "line": value.source_line,
                "column": value.source_column,
            }
            for value in module.values
        ],
    }


def optimize_native_ir(module: NativeIRModule) -> NativeIRModule:
    """Run checked constant folding while preserving IDs and source mapping."""
    verify_native_ir(module)
    constants: dict[int, int] = {}
    rewritten: list[NativeIRValue] = []
    for value in module.values:
        if value.operation == "CONST" and value.result_type == NativeType.I64 and value.symbol is not None:
            try:
                constants[value.value_id] = int(value.symbol)
            except ValueError:
                pass
        if value.runtime_call in {"i64.add", "i64.sub", "i64.mul"} and len(value.operands) == 2:
            left = constants.get(value.operands[0])
            right = constants.get(value.operands[1])
            if left is not None and right is not None:
                result = {
                    "i64.add": lambda: left + right,
                    "i64.sub": lambda: left - right,
                    "i64.mul": lambda: left * right,
                }[value.runtime_call]()
                if -(1 << 63) <= result <= (1 << 63) - 1:
                    rewritten.append(NativeIRValue(
                        value.value_id, "CONST", NativeType.I64,
                        symbol=str(result), source_line=value.source_line,
                        source_column=value.source_column,
                    ))
                    constants[value.value_id] = result
                    continue
        rewritten.append(value)
    result = NativeIRModule(tuple(rewritten), module.source_name, module.version)
    verify_native_ir(result)
    return result


@dataclass(frozen=True, slots=True)
class RegisterAllocation:
    registers: tuple[tuple[int, int], ...]
    spills: tuple[int, ...]
    register_count: int


def allocate_registers(module: NativeIRModule, register_limit: int = 6) -> RegisterAllocation:
    """Assign SSA values to abstract registers with a linear-scan allocator."""
    verify_native_ir(module)
    if type(register_limit) is not int or register_limit < 1:
        raise ValueError("register_limit must be a positive integer")
    last_use = {value.value_id: value.value_id for value in module.values}
    for value in module.values:
        for operand in value.operands:
            last_use[operand] = max(last_use[operand], value.value_id)
    active: list[tuple[int, int, int]] = []
    assignments: dict[int, int] = {}
    spills: list[int] = []
    for value in module.values:
        active = [entry for entry in active if entry[0] >= value.value_id]
        used = {entry[1] for entry in active}
        free = [register for register in range(register_limit) if register not in used]
        if not free:
            spills.append(value.value_id)
            continue
        register = free[0]
        assignments[value.value_id] = register
        active.append((last_use[value.value_id], register, value.value_id))
        active.sort()
    return RegisterAllocation(tuple(sorted(assignments.items())), tuple(spills), register_limit)


@dataclass(frozen=True, slots=True)
class DropAction:
    value_id: int
    runtime_call: str
    source_line: int
    source_column: int


def ownership_drop_plan(module: NativeIRModule) -> tuple[DropAction, ...]:
    """Return deterministic release actions for owned aggregate values."""
    verify_native_ir(module)
    last_use = {value.value_id: value.value_id for value in module.values}
    for value in module.values:
        for operand in value.operands:
            last_use[operand] = max(last_use[operand], value.value_id)
    actions: list[DropAction] = []
    for value in module.values:
        if value.ownership == Ownership.OWNED and value.result_type in {NativeType.ARRAY, NativeType.MAP}:
            release = "array.release" if value.result_type == NativeType.ARRAY else "map.release"
            actions.append(DropAction(value.value_id, release, value.source_line, value.source_column))
    return tuple(sorted(actions, key=lambda item: (last_use[item.value_id], -item.value_id)))
