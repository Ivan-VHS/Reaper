"""Typed front-end IR for Reaper.

This is a portable compiler front end, not a machine-code backend. It preserves
source locations and emits deterministic JSON suitable for later backends.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .parser import Node, parse


@dataclass(frozen=True, slots=True)
class TypeDiagnostic:
    code: str
    message: str
    line: int
    column: int

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message,
                "line": self.line, "column": self.column}


@dataclass(frozen=True, slots=True)
class _Binding:
    type_name: str
    mutable: bool


@dataclass(frozen=True, slots=True)
class IRNode:
    """Immutable, source-mapped intermediate representation node."""

    opcode: str
    value: Any
    type_name: str
    line: int
    column: int
    children: tuple["IRNode", ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "opcode": self.opcode,
            "value": _json_value(self.value),
            "type": self.type_name,
            "source": {"line": self.line, "column": self.column},
            "children": [child.as_dict() for child in self.children],
        }


@dataclass(frozen=True, slots=True)
class CompilationUnit:
    format_version: int
    source_digest: str
    root: IRNode
    diagnostics: tuple[TypeDiagnostic, ...]

    @property
    def ir_digest(self) -> str:
        encoded = json.dumps(self.root.as_dict(), sort_keys=True,
                             ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {
            "format": "quarry-ir",
            "format_version": self.format_version,
            "source_digest": self.source_digest,
            "ir_digest": self.ir_digest,
            "diagnostics": [item.as_dict() for item in self.diagnostics],
            "root": self.root.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class OptimizationStats:
    nodes_before: int
    nodes_after: int
    folded_expressions: int


class StaticTypeError(ValueError):
    def __init__(self, diagnostics: tuple[TypeDiagnostic, ...]) -> None:
        self.diagnostics = diagnostics
        summary = "; ".join(f"{item.line}:{item.column}: {item.message}" for item in diagnostics)
        super().__init__(summary or "static type check failed")


_BUILTINS: dict[str, tuple[int, int | None, str]] = {
    "size": (1, 1, "Number"),
    "text": (1, 1, "Text"),
    "number": (1, 1, "Number"),
    "kind": (1, 1, "Text"),
    "range": (1, 3, "Range"),
    "push": (2, 2, "List[Any]"),
    "first": (1, 1, "Any"),
    "rest": (1, 1, "List[Any]"),
    "sum": (1, 1, "Number"),
    "sorted": (1, 1, "List[Any]"),
    "map": (2, 2, "List[Any]"),
    "keep": (2, 2, "List[Any]"),
    "fold": (3, 3, "Any"),
    "say": (1, None, "Nothing"),
    "ask": (1, 1, "Text"),
    "assert": (1, 2, "Nothing"),
}

_VALID_OPCODES = {
    "program", "declare", "change", "emit", "yield", "function", "when",
    "each", "while", "expression", "block", "literal", "name", "list",
    "index", "unary", "call", "binary",
}


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


class TypeChecker:
    """Conservative static checker for the currently implemented language slice.

    Function parameters start as Any because 0.1 has no type-annotation syntax.
    A later assignment of incompatible known types is rejected in strict mode.
    Runtime semantics remain unchanged unless callers explicitly run this pass.
    """

    def __init__(self) -> None:
        self.scopes: list[dict[str, _Binding]] = [{}]
        self.functions: dict[str, tuple[int, str]] = {}
        self.diagnostics: list[TypeDiagnostic] = []
        self.node_types: dict[int, str] = {}
        self.return_types: list[list[str]] = []

    def check(self, tree: Node) -> tuple[TypeDiagnostic, ...]:
        self._check_block(tree, create_scope=False)
        return tuple(self.diagnostics)

    def _error(self, node: Node, code: str, message: str) -> None:
        self.diagnostics.append(TypeDiagnostic(
            code, message, node.token.line, node.token.column
        ))

    def _lookup(self, name: str) -> _Binding | None:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    @staticmethod
    def _unify(left: str, right: str) -> str:
        if left == right:
            return left
        if left == "Any" or right == "Any":
            return "Any"
        if {left, right} <= {"Integer", "Number"}:
            return "Number"
        if left.startswith("List[") and right.startswith("List["):
            return "List[Any]"
        return "Any"

    def _check_block(self, block: Node, create_scope: bool = True) -> None:
        if create_scope:
            self.scopes.append({})
        for statement in block.children or []:
            if statement.kind == "function":
                name, parameters = statement.value
                self.scopes[-1].setdefault(name, _Binding("Function", False))
                self.functions.setdefault(name, (len(parameters), "Any"))
        for statement in block.children or []:
            self._statement(statement)
        if create_scope:
            self.scopes.pop()

    def _statement(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "declare":
            name, mutable = node.value
            value_type = self._infer(children[0])
            if name in self.scopes[-1]:
                self._error(node, "duplicate-binding", f"'{name}' is already defined in this scope")
            else:
                self.scopes[-1][name] = _Binding(value_type, mutable)
        elif node.kind == "change":
            binding = self._lookup(node.value)
            value_type = self._infer(children[0])
            if binding is None:
                self._error(node, "unknown-name", f"unknown name '{node.value}'")
            elif not binding.mutable:
                self._error(node, "immutable-binding", f"'{node.value}' is immutable; declare it with 'vary'")
            elif binding.type_name != "Any" and value_type != "Any" and self._unify(binding.type_name, value_type) == "Any":
                self._error(node, "assignment-type", f"cannot assign {value_type} to {binding.type_name} binding '{node.value}'")
        elif node.kind == "function":
            name, parameters = node.value
            self.functions.setdefault(name, (len(parameters), "Any"))
            self.scopes.append({parameter: _Binding("Any", False) for parameter in parameters})
            returns: list[str] = []
            self.return_types.append(returns)
            self._check_block(children[0], create_scope=False)
            self.return_types.pop()
            return_type = "Nothing"
            for item in returns:
                return_type = item if return_type == "Nothing" else self._unify(return_type, item)
            self.functions[name] = (len(parameters), return_type if returns else "Nothing")
            self.scopes.pop()
        elif node.kind == "yield":
            if not self.return_types:
                self._error(node, "yield-outside-function", "'yield' is only valid inside a function")
            value_type = self._infer(children[0]) if children else "Nothing"
            if self.return_types:
                self.return_types[-1].append(value_type)
        elif node.kind == "emit":
            self._infer(children[0])
        elif node.kind == "when":
            self._infer(children[0])
            self._check_block(children[1])
            if len(children) == 3:
                self._check_block(children[2])
        elif node.kind == "each":
            iterable_type = self._infer(children[0])
            if not (iterable_type == "Any" or iterable_type == "Range"
                    or iterable_type == "Text" or iterable_type.startswith("List[")):
                self._error(node, "not-iterable", f"'each' cannot iterate over {iterable_type}")
            element_type = "Text" if iterable_type == "Text" else (
                iterable_type[5:-1] if iterable_type.startswith("List[") else "Any"
            )
            self.scopes.append({node.value: _Binding(element_type, False)})
            self._check_block(children[1], create_scope=False)
            self.scopes.pop()
        elif node.kind == "while":
            self._infer(children[0])
            self._check_block(children[1])
        elif node.kind == "block":
            self._check_block(node)
        elif node.kind == "expression":
            self._infer(children[0])

    def _infer(self, node: Node) -> str:
        children = node.children or []
        if node.kind == "literal":
            value = node.value
            result = ("Nothing" if value is None else "Boolean" if isinstance(value, bool)
                      else "Integer" if isinstance(value, int) else "Number"
                      if isinstance(value, float) else "Text" if isinstance(value, str) else "Any")
        elif node.kind == "name":
            binding = self._lookup(node.value)
            if binding is not None:
                result = binding.type_name
            elif node.value in _BUILTINS or node.value in self.functions:
                result = "Function"
            else:
                self._error(node, "unknown-name", f"unknown name '{node.value}'")
                result = "Any"
        elif node.kind == "list":
            element_type = "Nothing"
            for item in children:
                item_type = self._infer(item)
                element_type = item_type if element_type == "Nothing" else self._unify(element_type, item_type)
            result = f"List[{element_type if element_type != 'Nothing' else 'Any'}]"
        elif node.kind == "index":
            collection_type = self._infer(children[0])
            index_type = self._infer(children[1])
            if index_type not in {"Any", "Integer"}:
                self._error(node, "index-type", "sequence indexes must be whole numbers")
            if collection_type.startswith("List["):
                result = collection_type[5:-1]
            elif collection_type == "Text":
                result = "Text"
            elif collection_type == "Any":
                result = "Any"
            else:
                self._error(node, "not-indexable", f"{collection_type} cannot be indexed")
                result = "Any"
        elif node.kind == "unary":
            operand = self._infer(children[0])
            if node.value == "-" and operand not in {"Any", "Integer", "Number"}:
                self._error(node, "unary-type", "unary '-' expects a number")
            result = "Boolean" if node.value == "NOT" else "Number"
        elif node.kind == "call":
            result = self._call_type(node)
        elif node.kind == "binary":
            operator = node.value
            if operator == "~>":
                if children[1].kind == "call":
                    result = self._call_type(children[1], piped_type=self._infer(children[0]))
                else:
                    self._infer(children[0])
                    self._infer(children[1])
                    result = "Any"
            else:
                left = self._infer(children[0])
                right = self._infer(children[1])
                if operator in {"+", "-", "*", "/", "//", "%", "**"}:
                    for operand in (left, right):
                        if operand not in {"Any", "Integer", "Number"}:
                            self._error(node, "numeric-operands", f"'{operator}' expects numeric operands, got {operand}")
                    result = "Number" if operator == "/" or "Number" in {left, right} else "Integer"
                elif operator == "++":
                    if left not in {"Any", "Text"} or right not in {"Any", "Text"}:
                        self._error(node, "text-operands", "'++' joins text values only")
                    result = "Text"
                elif operator in {"<", "<=", ">", ">="}:
                    compatible = (
                        left == "Any" or right == "Any"
                        or (left in {"Integer", "Number"} and right in {"Integer", "Number"})
                        or (left == right == "Text")
                    )
                    if not compatible:
                        self._error(node, "comparison-operands", "comparison needs two numbers or two text values")
                    result = "Boolean"
                elif operator in {"==", "!="}:
                    result = "Boolean"
                else:
                    result = "Any"
        else:
            result = "Any"
        self.node_types[id(node)] = result
        return result

    def _call_type(self, node: Node, piped_type: str | None = None) -> str:
        children = node.children or []
        callee = children[0]
        name = callee.value if callee.kind == "name" else None
        argument_types = ([piped_type] if piped_type is not None else [])
        argument_types.extend(self._infer(item) for item in children[1:])
        if name in _BUILTINS:
            minimum, maximum, result = _BUILTINS[name]
            count = len(argument_types)
            if count < minimum or (maximum is not None and count > maximum):
                expected = str(minimum) if minimum == maximum else (
                    f"at least {minimum}" if maximum is None else f"{minimum}..{maximum}"
                )
                self._error(node, "call-arity", f"{name}() expects {expected} arguments, got {count}")
            if name == "sum" and argument_types and argument_types[0] not in {"Any", "List[Any]", "List[Integer]", "List[Number]"}:
                self._error(node, "builtin-argument", "sum() expects a list of numbers")
            if name == "number" and argument_types and argument_types[0] == "Boolean":
                self._error(node, "builtin-argument", "number() does not convert booleans")
            return result
        if name in self.functions:
            arity, result = self.functions[name]
            if len(argument_types) != arity:
                self._error(node, "call-arity", f"{name}() expects {arity} arguments, got {len(argument_types)}")
            return result
        callee_type = self._infer(callee)
        if callee_type != "Any" and callee_type != "Function":
            self._error(node, "not-callable", f"{callee_type} is not callable")
        return "Any"


def _lower(node: Node, inferred: dict[int, str]) -> IRNode:
    token = node.token
    return IRNode(
        opcode=node.kind,
        value=_json_value(node.value),
        type_name=inferred.get(id(node), "Any"),
        line=token.line,
        column=token.column,
        children=tuple(_lower(child, inferred) for child in (node.children or [])),
    )


def verify_ir(root: IRNode) -> None:
    """Validate structural invariants before another tool consumes the IR."""
    if root.opcode != "program":
        raise ValueError("IR root must be a program node")

    def visit(node: IRNode) -> None:
        if node.opcode not in _VALID_OPCODES:
            raise ValueError(f"unknown IR opcode: {node.opcode}")
        if not node.type_name or node.line < 1 or node.column < 1:
            raise ValueError("IR nodes require a type and positive source coordinates")
        for child in node.children:
            visit(child)

    visit(root)


def compile_source(source: str, filename: str = "<memory>", *, strict: bool = False) -> CompilationUnit:
    """Parse, type-check and lower source into a deterministic portable IR."""
    tree = parse(source, filename)
    checker = TypeChecker()
    diagnostics = checker.check(tree)
    if strict and diagnostics:
        raise StaticTypeError(diagnostics)
    root = _lower(tree, checker.node_types)
    verify_ir(root)
    return CompilationUnit(
        format_version=1,
        source_digest=hashlib.sha256(source.encode("utf-8")).hexdigest(),
        root=root,
        diagnostics=diagnostics,
    )


def _node_count(node: IRNode) -> int:
    return 1 + sum(_node_count(child) for child in node.children)


def optimize_ir(root: IRNode, *, max_text_length: int = 1_000_000) -> tuple[IRNode, OptimizationStats]:
    """Apply deterministic, side-effect-free constant folding to literal expressions."""
    if max_text_length < 1:
        raise ValueError("max_text_length must be positive")
    before = _node_count(root)
    folded = 0

    def visit(node: IRNode) -> IRNode:
        nonlocal folded
        children = tuple(visit(child) for child in node.children)
        current = IRNode(node.opcode, node.value, node.type_name, node.line,
                         node.column, children)
        if current.opcode != "binary" or len(children) != 2:
            return current
        left, right = children
        if left.opcode != "literal" or right.opcode != "literal":
            return current
        a, b, op = left.value, right.value, current.value
        value: Any
        try:
            if op in {"+", "-", "*", "/", "//", "%", "**"}:
                if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                    return current
                if op in {"/", "//", "%"} and b == 0:
                    return current
                if op == "**" and (abs(b) > 100 or abs(a) > 1_000_000):
                    return current
                value = {"+": lambda: a + b, "-": lambda: a - b,
                         "*": lambda: a * b, "/": lambda: a / b,
                         "//": lambda: a // b, "%": lambda: a % b,
                         "**": lambda: a ** b}[op]()
            elif op == "++" and isinstance(a, str) and isinstance(b, str):
                if len(a) + len(b) > max_text_length:
                    return current
                value = a + b
            elif op == "==" :
                value = type(a) is type(b) and a == b
            elif op == "!=":
                value = not (type(a) is type(b) and a == b)
            elif op in {"<", "<=", ">", ">="} and (
                (isinstance(a, (int, float)) and not isinstance(a, bool)
                 and isinstance(b, (int, float)) and not isinstance(b, bool))
                or (type(a) is str and type(b) is str)
            ):
                value = {"<": lambda: a < b, "<=": lambda: a <= b,
                         ">": lambda: a > b, ">=": lambda: a >= b}[op]()
            else:
                return current
            if isinstance(value, float) and not math.isfinite(value):
                return current
        except (ArithmeticError, OverflowError, ValueError):
            return current
        folded += 1
        return IRNode("literal", value, current.type_name, current.line,
                      current.column, ())
    optimized = visit(root)
    verify_ir(optimized)
    return optimized, OptimizationStats(before, _node_count(optimized), folded)


def optimize(unit: CompilationUnit, *, max_text_length: int = 1_000_000) -> tuple[CompilationUnit, OptimizationStats]:
    root, stats = optimize_ir(unit.root, max_text_length=max_text_length)
    return CompilationUnit(unit.format_version, unit.source_digest,
                           root, unit.diagnostics), stats
