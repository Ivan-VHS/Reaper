"""Canonical stack IR lowering for the Reaper AST."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from .parser import Node
from .source import SourceSpan, span_to_data


@dataclass(frozen=True, slots=True)
class IRInstruction:
    op: str
    argument: Any
    token: Any
    span: SourceSpan | None = field(default=None)
    origin_span: SourceSpan | None = field(default=None)
    expanded_from: tuple[SourceSpan, ...] = field(default=())


@dataclass(frozen=True, slots=True)
class IRFunction:
    name: str
    parameters: tuple[str, ...]
    code: tuple[IRInstruction, ...]
    span: SourceSpan | None = field(default=None)


@dataclass(frozen=True, slots=True)
class CanonicalIR:
    code: tuple[IRInstruction, ...]
    source_name: str = "<memory>"
    schema_version: int = 1

    def as_dict(self) -> dict[str, Any]:
        """Return a deterministic, versioned IR projection with its source map."""
        verify(self)
        return {
            "schema": "reaper.canonical-ir/v1",
            "version": self.schema_version,
            "source_name": self.source_name,
            "code": [_instruction_data(item, index) for index, item in enumerate(self.code)],
            "source_map": _source_map(self.code),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize the IR and source map without timestamps or host-dependent data."""
        return json.dumps(
            self.as_dict(), ensure_ascii=False, sort_keys=True,
            indent=indent, allow_nan=False,
            separators=None if indent is not None else (",", ":"),
        )


class IRVerificationError(ValueError):
    pass


class _Lowerer:
    def __init__(self) -> None:
        self.code: list[IRInstruction] = []

    def emit(self, op: str, argument: Any, token: Any) -> int:
        span = getattr(token, "span", None)
        self.code.append(IRInstruction(
            op, argument, token, span=span, origin_span=span,
        ))
        return len(self.code) - 1

    def patch(self, index: int, argument: Any) -> None:
        old = self.code[index]
        self.code[index] = IRInstruction(
            old.op, argument, old.token, old.span, old.origin_span, old.expanded_from,
        )

    def statements(self, nodes: list[Node] | None) -> None:
        for node in nodes or []:
            self.statement(node)

    def scoped_block(self, block: Node) -> None:
        self.emit("ENTER_SCOPE", None, block.token)
        self.statements(block.children)
        self.emit("EXIT_SCOPE", None, block.token)

    def statement(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "declare":
            self.expression(children[0])
            self.emit("DEFINE", node.value, node.token)
        elif node.kind == "change":
            self.expression(children[0])
            self.emit("ASSIGN", node.value, node.token)
        elif node.kind == "emit":
            self.expression(children[0])
            self.emit("EMIT", None, node.token)
        elif node.kind == "yield":
            if children:
                self.expression(children[0])
            else:
                self.emit("CONST", None, node.token)
            self.emit("RETURN", None, node.token)
        elif node.kind == "function":
            name, parameters = node.value
            nested = _Lowerer()
            nested.statements(children[0].children)
            nested.emit("CONST", None, node.token)
            nested.emit("RETURN", None, node.token)
            function = IRFunction(
                name, tuple(parameters), tuple(nested.code),
                span=getattr(node.token, "span", None),
            )
            self.emit("MAKE_FUNCTION", function, node.token)
            self.emit("DEFINE", (name, False), node.token)
        elif node.kind == "when":
            self.expression(children[0])
            no_jump = self.emit("JUMP_IF_FALSE", None, node.token)
            self.scoped_block(children[1])
            if len(children) == 3:
                end_jump = self.emit("JUMP", None, node.token)
                self.patch(no_jump, len(self.code))
                self.scoped_block(children[2])
                self.patch(end_jump, len(self.code))
            else:
                self.patch(no_jump, len(self.code))
        elif node.kind == "each":
            self.expression(children[0])
            self.emit("ITER_INIT", node.value, node.token)
            loop_start = len(self.code)
            next_index = self.emit("ITER_NEXT", (node.value, None), node.token)
            self.statements(children[1].children)
            self.emit("EXIT_SCOPE", None, node.token)
            self.emit("JUMP", loop_start, node.token)
            self.patch(next_index, (node.value, len(self.code)))
            self.emit("ITER_END", None, node.token)
        elif node.kind == "while":
            loop_start = len(self.code)
            self.expression(children[0])
            exit_jump = self.emit("JUMP_IF_FALSE", None, node.token)
            self.scoped_block(children[1])
            self.emit("JUMP", loop_start, node.token)
            self.patch(exit_jump, len(self.code))
        elif node.kind == "expression":
            self.expression(children[0])
            self.emit("POP", None, node.token)
        elif node.kind == "block":
            self.scoped_block(node)
        elif node.kind == "import":
            self.emit("IMPORT", node.value, node.token)
        elif node.kind == "export":
            if children:
                child = children[0]
                self.statement(child)
                if child.kind == "declare":
                    name = child.value[0]
                elif child.kind == "function":
                    name = child.value[0]
                else:
                    raise IRVerificationError("only declarations and functions can be exported inline")
            else:
                name = node.value
            self.emit("EXPORT", name, node.token)
        else:
            raise IRVerificationError(f"cannot lower statement kind: {node.kind}")

    def expression(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "literal":
            self.emit("CONST", node.value, node.token)
        elif node.kind == "name":
            self.emit("LOAD", node.value, node.token)
        elif node.kind == "list":
            for item in children:
                self.expression(item)
            self.emit("BUILD_LIST", len(children), node.token)
        elif node.kind == "index":
            self.expression(children[0])
            self.expression(children[1])
            self.emit("INDEX", None, node.token)
        elif node.kind == "unary":
            self.expression(children[0])
            self.emit("UNARY", node.value, node.token)
        elif node.kind == "call":
            self.expression(children[0])
            for argument in children[1:]:
                self.expression(argument)
            self.emit("CALL", len(children) - 1, node.token)
        elif node.kind == "binary":
            operator = node.value
            if operator == "AND":
                self.expression(children[0])
                index = self.emit("AND_JUMP", None, node.token)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "OR":
                self.expression(children[0])
                index = self.emit("OR_JUMP", None, node.token)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "::":
                self.expression(children[0])
                right = children[1]
                if right.kind == "call":
                    self.expression(right.children[0])
                    for argument in right.children[1:]:
                        self.expression(argument)
                    self.emit("PIPE_CALL", len(right.children) - 1, node.token)
                else:
                    self.expression(right)
                    self.emit("PIPE_CALL", 0, node.token)
            else:
                self.expression(children[0])
                self.expression(children[1])
                self.emit("BINARY", operator, node.token)
        else:
            raise IRVerificationError(f"cannot lower expression kind: {node.kind}")



def _argument_data(value: Any) -> Any:
    """Convert IR operands to JSON data without repr()-based unstable fallbacks."""
    if isinstance(value, IRFunction):
        return {
            "kind": "function",
            "name": value.name,
            "parameters": list(value.parameters),
            "span": span_to_data(value.span),
            "code": [_instruction_data(item, index) for index, item in enumerate(value.code)],
        }
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise IRVerificationError("IR cannot serialize a non-finite floating-point operand")
        return value
    if isinstance(value, tuple):
        return [_argument_data(item) for item in value]
    if isinstance(value, list):
        return [_argument_data(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise IRVerificationError("IR JSON object keys must be strings")
        return {key: _argument_data(item) for key, item in value.items()}
    raise IRVerificationError(f"IR operand is not JSON-serializable: {type(value).__name__}")


def _instruction_data(instruction: IRInstruction, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "op": instruction.op,
        "argument": _argument_data(instruction.argument),
        "span": span_to_data(instruction.span),
        "origin_span": span_to_data(instruction.origin_span),
        "expanded_from": [item.to_dict() for item in instruction.expanded_from],
    }


def _source_map(code: tuple[IRInstruction, ...]) -> list[dict[str, Any]]:
    entries = []
    for index, instruction in enumerate(code):
        if instruction.span is None and instruction.origin_span is None and not instruction.expanded_from:
            continue
        entries.append({
            "instruction": index,
            "span": span_to_data(instruction.span),
            "origin_span": span_to_data(instruction.origin_span),
            "expanded_from": [item.to_dict() for item in instruction.expanded_from],
        })
    return entries


_ALLOWED = {
    "CONST", "LOAD", "DEFINE", "ASSIGN", "EMIT", "RETURN", "MAKE_FUNCTION",
    "JUMP_IF_FALSE", "JUMP", "ENTER_SCOPE", "EXIT_SCOPE", "ITER_INIT",
    "ITER_NEXT", "ITER_END", "POP", "BUILD_LIST", "INDEX", "UNARY",
    "CALL", "PIPE_CALL", "BINARY", "AND_JUMP", "OR_JUMP", "IMPORT", "EXPORT",
}


def lower(tree: Node, source_name: str = "<memory>") -> CanonicalIR:
    compiler = _Lowerer()
    compiler.statements(tree.children)
    module = CanonicalIR(tuple(compiler.code), source_name)
    verify(module)
    return module


def verify(module: CanonicalIR) -> None:
    """Validate IR structure and operands before a VM can consume the module."""
    if not isinstance(module, CanonicalIR):
        raise IRVerificationError("expected a CanonicalIR module")
    if not isinstance(module.code, tuple):
        raise IRVerificationError("module code must be an immutable instruction tuple")
    if not isinstance(module.source_name, str) or not module.source_name:
        raise IRVerificationError("module source_name must be non-empty text")
    if type(module.schema_version) is not int or module.schema_version != 1:
        raise IRVerificationError("unsupported canonical IR schema version")

    def validate_span(span: Any, where: str) -> None:
        if span is not None and not isinstance(span, SourceSpan):
            raise IRVerificationError(f"{where}: source coordinates must use SourceSpan")

    binary_operators = {
        "==", "!=", "<", "<=", ">", ">=", "++",
        "+", "-", "*", "/", "//", "%", "**",
    }

    def require_name(value: Any, label: str) -> None:
        if not isinstance(value, str) or not value:
            raise IRVerificationError(f"{label}: expected a non-empty name")

    def check(code: tuple[IRInstruction, ...], label: str) -> None:
        if not isinstance(code, tuple):
            raise IRVerificationError(f"{label}: instruction code must be a tuple")

        for index, instruction in enumerate(code):
            where = f"{label}: instruction {index}"
            if not isinstance(instruction, IRInstruction):
                raise IRVerificationError(f"{where}: expected an IRInstruction")
            if not isinstance(instruction.op, str) or instruction.op not in _ALLOWED:
                raise IRVerificationError(f"{where}: unknown IR operation: {instruction.op!r}")

            validate_span(instruction.span, where)
            validate_span(instruction.origin_span, where)
            if not isinstance(instruction.expanded_from, tuple):
                raise IRVerificationError(f"{where}: expanded_from must be an immutable span tuple")
            for provenance in instruction.expanded_from:
                validate_span(provenance, where)
            token_span = getattr(instruction.token, "span", None)
            if token_span is not None and instruction.span != token_span:
                raise IRVerificationError(f"{where}: instruction span differs from its source token")

            op = instruction.op
            argument = instruction.argument

            if op in {"JUMP", "JUMP_IF_FALSE", "AND_JUMP", "OR_JUMP"}:
                if type(argument) is not int or argument < 0 or argument > len(code):
                    raise IRVerificationError(f"{where}: invalid jump target")

            elif op in {"CALL", "PIPE_CALL", "BUILD_LIST"}:
                if type(argument) is not int or argument < 0:
                    raise IRVerificationError(f"{where}: argument count must be a non-negative integer")

            elif op == "DEFINE":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: DEFINE requires (name, mutable)")
                require_name(argument[0], where)
                if type(argument[1]) is not bool:
                    raise IRVerificationError(f"{where}: DEFINE mutable flag must be boolean")

            elif op in {"LOAD", "ASSIGN", "EXPORT", "ITER_INIT"}:
                require_name(argument, where)

            elif op == "ITER_NEXT":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: ITER_NEXT requires (name, target)")
                require_name(argument[0], where)
                target = argument[1]
                if type(target) is not int or target < 0 or target > len(code):
                    raise IRVerificationError(f"{where}: invalid iterator exit target")

            elif op == "MAKE_FUNCTION":
                function = argument
                if not isinstance(function, IRFunction):
                    raise IRVerificationError(f"{where}: MAKE_FUNCTION requires an IRFunction")
                validate_span(function.span, where)
                require_name(function.name, where)
                if not isinstance(function.parameters, tuple):
                    raise IRVerificationError(f"{where}: function parameters must be a tuple")
                for parameter in function.parameters:
                    require_name(parameter, where)
                if len(set(function.parameters)) != len(function.parameters):
                    raise IRVerificationError(f"{where}: function parameter names must be unique")
                check(function.code, function.name)

            elif op == "IMPORT":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: IMPORT requires (specifier, alias)")
                require_name(argument[0], where)
                if argument[1] is not None:
                    require_name(argument[1], where)

            elif op == "UNARY":
                if not isinstance(argument, str) or argument not in {"NOT", "-"}:
                    raise IRVerificationError(f"{where}: unsupported unary operator {argument!r}")

            elif op == "BINARY":
                if not isinstance(argument, str) or argument not in binary_operators:
                    raise IRVerificationError(f"{where}: unsupported binary operator {argument!r}")

    check(module.code, module.source_name)
