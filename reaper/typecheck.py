"""Conservative static type analysis for the existing Reaper language.

The checker infers types from the current .rpr grammar. It does not add syntax
or change runtime semantics; unknown values remain Any so modules and explicit
FFI boundaries can be checked without pretending to know their host contracts.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ReaperError
from .parser import Node, parse


ANY = "Any"
NOTHING = "Nothing"
NUMERIC = {"Int", "Float", "Number", "i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64", "isize", "usize"}

BUILTIN_ARITY: dict[str, tuple[int, int | None]] = {
    "divmod_euclidean": (2, 2), "euclidean_divmod": (2, 2),
    "quotient": (2, 2), "remainder": (2, 2), "is_divisible": (2, 2),
    "partition": (2, 2), "distribute": (2, 2), "proportional_split": (2, 2),
    "size": (1, 1), "text": (1, 1), "number": (1, 1), "kind": (1, 1),
    "range": (1, 3), "push": (2, 2), "first": (1, 1), "rest": (1, 1),
    "sum": (1, 1), "sorted": (1, 3), "sort_by": (2, 3),
    "map": (2, 2), "keep": (2, 2), "filter": (2, 2), "fold": (3, 3),
    "reduce": (3, 3), "chunk": (2, 2), "take": (2, 2), "drop": (2, 2),
    "flatten": (1, 1), "reverse": (1, 1), "unique": (1, 1),
    "split": (2, 2), "join": (2, 2), "trim": (1, 1), "lower": (1, 1),
    "upper": (1, 1), "replace": (3, 4), "contains": (2, 2),
    "starts_with": (2, 2), "ends_with": (2, 2), "say": (1, None),
    "ask": (1, 1), "assert": (1, 2), "token_catalog": (0, 1),
    "token_info": (1, 1), "token_is_reserved": (1, 1),
    "consent_check": (4, 4), "consent_revoke": (1, 1),
    "file_open": (1, 2), "file_read": (1, 1), "file_write": (2, 2),
    "file_close": (1, 1), "with_file": (3, 3), "resource_stats": (0, 0),
    "heap_stats": (0, 0), "heap_collect": (0, 0), "region_begin": (0, 0),
    "region_end": (1, 1), "ffi_open": (1, 1), "ffi_bind": (3, 4),
    "ffi_close": (1, 1), "pytyliki_open": (1, 1),
    "ok": (1, 1), "err": (1, 1), "some": (1, 1), "none": (0, 0),
    "result_is_ok": (1, 1), "result_is_err": (1, 1),
    "result_value": (1, 1), "result_error": (1, 1),
    "option_is_some": (1, 1), "option_is_none": (1, 1),
    "option_value": (1, 1), "option_or": (2, 2),
    "map_ok": (2, 2), "map_err": (2, 2), "zip_ok": (2, 2), "zip3_ok": (3, 3),
}

BUILTIN_RETURN: dict[str, str] = {
    "divmod_euclidean": "List[Int]", "euclidean_divmod": "List[Int]",
    "quotient": "Int", "remainder": "Int", "is_divisible": "Bool",
    "partition": "List[Any]", "distribute": "List[Int]",
    "proportional_split": "List[Int]", "size": "Int", "text": "Text",
    "number": "Number", "kind": "Text", "range": "List[Int]",
    "push": "List[Any]", "first": ANY, "rest": "List[Any]", "sum": "Number",
    "sorted": "List[Any]", "sort_by": "List[Any]", "map": "List[Any]",
    "keep": "List[Any]", "filter": "List[Any]", "fold": ANY, "reduce": ANY,
    "chunk": "List[Any]", "take": "List[Any]", "drop": "List[Any]",
    "flatten": "List[Any]", "reverse": ANY, "unique": "List[Any]",
    "split": "List[Text]", "join": "Text", "trim": "Text", "lower": "Text",
    "upper": "Text", "replace": "Text", "contains": "Bool",
    "starts_with": "Bool", "ends_with": "Bool", "say": "Nothing",
    "ask": "Text", "assert": "Nothing", "token_catalog": "List[Any]",
    "token_info": "Any", "token_is_reserved": "Bool", "consent_check": "Bool",
    "consent_revoke": "Bool", "file_open": "Resource", "file_read": "Text",
    "file_write": "Nothing", "file_close": "Nothing", "with_file": ANY,
    "resource_stats": "Map", "heap_stats": "Map", "heap_collect": "Int",
    "region_begin": "Region", "region_end": "Nothing", "ffi_open": "Library",
    "ffi_bind": "Function", "ffi_close": "Nothing", "pytyliki_open": "Bridge",
    "result_is_ok": "Bool", "result_is_err": "Bool",
    "option_is_some": "Bool", "option_is_none": "Bool",
}


SUPPORTED_EFFECTS = frozenset({
    "console", "filesystem", "network", "clock", "native",
    "process", "device", "unsafe", "allocate", "synchronize",
})
SUPPORTED_TRAITS = frozenset({"Numeric", "Copy", "Clone", "Eq", "Ord", "Display"})
BUILTIN_EFFECTS: dict[str, str] = {
    "say": "console", "ask": "console",
    "file_open": "filesystem", "file_read": "filesystem",
    "file_write": "filesystem", "file_close": "filesystem", "with_file": "filesystem",
    "ffi_open": "native", "ffi_bind": "native", "ffi_close": "native",
    "pytyliki_open": "native",
    "heap_collect": "allocate", "region_begin": "allocate", "region_end": "allocate",
    "consent_check": "unsafe", "consent_revoke": "unsafe",
}


@dataclass(frozen=True, slots=True)
class TypeDiagnostic:
    code: str
    message: str
    line: int
    column: int
    severity: str = "error"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
        }


@dataclass(slots=True)
class Binding:
    type_name: str
    mutable: bool


@dataclass(slots=True)
class FunctionInfo:
    arity: int
    return_type: str = ANY
    parameter_types: tuple[str | None, ...] = ()
    type_parameters: tuple[str, ...] = ()
    trait_bounds: dict[str, tuple[str, ...]] = field(default_factory=dict)
    declared_return_type: str | None = None
    effects: frozenset[str] | None = None


@dataclass(frozen=True, slots=True)
class TypeCheckResult:
    filename: str
    diagnostics: tuple[TypeDiagnostic, ...]

    @property
    def ok(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "file": self.filename,
            "diagnostics": [item.as_dict() for item in self.diagnostics],
            "summary": {
                "errors": sum(item.severity == "error" for item in self.diagnostics),
                "warnings": sum(item.severity == "warning" for item in self.diagnostics),
            },
        }


class TypeChecker:
    """Infer a conservative type model without rejecting unknown host values."""

    def __init__(self, filename: str = "<memory>") -> None:
        self.filename = filename
        self.scopes: list[dict[str, Binding]] = [{}]
        self.functions: dict[str, FunctionInfo] = {}
        self.diagnostics: list[TypeDiagnostic] = []
        self.return_types: list[list[str]] = []
        self.function_stack: list[FunctionInfo] = []

    def check(self, tree: Node) -> TypeCheckResult:
        self._collect_functions(tree)
        for statement in tree.children or []:
            if statement.kind == "function":
                self._check_function(statement)
        self._visit_block_contents(tree)
        return TypeCheckResult(self.filename, tuple(self.diagnostics))

    def _collect_functions(self, node: Node) -> None:
        for child in node.children or []:
            if child.kind == "function":
                name, parameters = child.value
                metadata = child.metadata or {}
                parameter_types = tuple(metadata.get("parameter_types", ()))
                if parameter_types and len(parameter_types) != len(parameters):
                    self._report(child, "RPR-T0016", "function parameter type metadata does not match its arity")
                effects_value = metadata.get("effects")
                effects = None if effects_value is None else frozenset(effects_value)
                self.functions[name] = FunctionInfo(
                    arity=len(parameters),
                    return_type=metadata.get("return_type") or ANY,
                    parameter_types=parameter_types,
                    type_parameters=tuple(metadata.get("type_parameters", ())),
                    trait_bounds=dict(metadata.get("trait_bounds", {})),
                    declared_return_type=metadata.get("return_type"),
                    effects=effects,
                )
                for effect in effects or ():
                    if effect not in SUPPORTED_EFFECTS:
                        self._report(child, "RPR-EFF0001", f"unknown effect '{effect}'")
                for declared_type in [*(parameter_types or ()), metadata.get("return_type")]:
                    if declared_type is not None:
                        self._validate_type_expression(declared_type, child)

    def _validate_type_expression(self, type_name: str, node: Node) -> None:
        parts = self._generic_parts(type_name)
        if parts is None:
            return
        name, arguments = parts
        expected = {"Option": 1, "Result": 2, "List": 1, "Map": 2, "Stream": 1}
        if name in expected and len(arguments) != expected[name]:
            self._report(node, "RPR-T0017", f"{name} expects {expected[name]} generic type argument(s), got {len(arguments)}")
        for argument in arguments:
            self._validate_type_expression(argument, node)

    def _check_function(self, node: Node) -> None:
        name, parameters = node.value
        info = self.functions[name]
        previous_scope = self.scopes
        self.scopes = [{}]
        for index, parameter in enumerate(parameters):
            parameter_type = info.parameter_types[index] if index < len(info.parameter_types) else None
            self.scopes[-1][parameter] = Binding(parameter_type or ANY, False)
        self.function_stack.append(info)
        self.return_types.append([])
        self._visit_block_contents(node.children[0])
        returned = self.return_types.pop()
        inferred = self._unify_all(returned) if returned else NOTHING
        if info.declared_return_type is not None:
            for actual in returned:
                if not self._assignable(info.declared_return_type, actual):
                    self._report(
                        node, "RPR-T0013",
                        f"function '{name}' declares {info.declared_return_type} but returns {actual}",
                    )
            info.return_type = info.declared_return_type
        else:
            info.return_type = inferred
        self.function_stack.pop()
        self.scopes = previous_scope

    def _visit_block_contents(self, block: Node) -> None:
        for statement in block.children or []:
            self._statement(statement)

    def _statement(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "function":
            return
        if node.kind == "declare":
            name, mutable = node.value
            value_type = self._expression(children[0])
            self.scopes[-1][name] = Binding(value_type, mutable)
            return
        if node.kind == "change":
            actual = self._expression(children[0])
            binding = self._find_binding(node.value)
            if binding is None:
                return
            if not binding.mutable:
                self._report(node, "RPR-T0002", f"'{node.value}' is immutable and cannot be reassigned")
            elif not self._assignable(binding.type_name, actual):
                self._report(
                    node, "RPR-T0001",
                    f"cannot assign {actual} to '{node.value}' declared as {binding.type_name}",
                )
            return
        if node.kind in {"emit", "expression"}:
            if children:
                self._expression(children[0])
            return
        if node.kind == "yield":
            value_type = self._expression(children[0]) if children else NOTHING
            if self.return_types:
                self.return_types[-1].append(value_type)
            return
        if node.kind == "export":
            if children:
                self._statement(children[0])
            return
        if node.kind == "import":
            return
        if node.kind == "when":
            self._expression(children[0])
            self._nested_block(children[1])
            if len(children) == 3:
                self._nested_block(children[2])
            return
        if node.kind == "each":
            iterable_type = self._expression(children[0])
            element_type = self._element_type(iterable_type, node)
            self.scopes.append({node.value: Binding(element_type, False)})
            self._visit_block_contents(children[1])
            self.scopes.pop()
            return
        if node.kind == "while":
            self._expression(children[0])
            self._nested_block(children[1])
            return
        if node.kind == "block":
            self._nested_block(node)
            return

    def _nested_block(self, node: Node) -> None:
        self.scopes.append({})
        self._visit_block_contents(node)
        self.scopes.pop()

    def _expression(self, node: Node) -> str:
        children = node.children or []
        if node.kind == "literal":
            if node.value is None:
                return NOTHING
            if isinstance(node.value, bool):
                return "Bool"
            if isinstance(node.value, int):
                return "Int"
            if isinstance(node.value, float):
                return "Float"
            if isinstance(node.value, str):
                return "Text"
            return ANY
        if node.kind == "name":
            binding = self._find_binding(node.value)
            return binding.type_name if binding else ANY
        if node.kind == "list":
            return f"List[{self._unify_all([self._expression(item) for item in children])}]"
        if node.kind == "index":
            collection_type = self._expression(children[0])
            index_type = self._expression(children[1])
            if collection_type.startswith("List[") or collection_type == "Text":
                if index_type not in {"Int", ANY}:
                    self._report(node, "RPR-T0003", f"sequence index must be Int, not {index_type}")
            elif collection_type not in {"Map", ANY}:
                self._report(
                    node,
                    "RPR-T0008",
                    f"cannot index a value of type {collection_type}",
                )
                return ANY
            return self._element_type(collection_type, node)
        if node.kind == "unary":
            operand = self._expression(children[0])
            if node.value == "-" and operand not in NUMERIC | {ANY, "Number"}:
                self._report(node, "RPR-T0004", f"unary '-' requires a number, not {operand}")
                return ANY
            return "Bool" if node.value == "NOT" else operand
        if node.kind == "call":
            return self._call(node)
        if node.kind == "binary":
            operator = node.value
            left = self._expression(children[0])
            if operator in {"AND", "OR"}:
                right = self._expression(children[1])
                return self._unify(left, right)
            if operator == "::":
                return self._flow_type(children[0], children[1], left)
            right = self._expression(children[1])
            if operator in {"+", "-", "*", "/", "//", "%", "**"}:
                if not self._numeric(left) or not self._numeric(right):
                    self._report(node, "RPR-T0004", f"operator '{operator}' requires numeric operands, got {left} and {right}")
                    return ANY
                if ANY in {left, right}:
                    return "Number"
                return "Float" if "Float" in {left, right} or operator == "/" else "Int"
            if operator == "++":
                if left not in {"Text", ANY} or right not in {"Text", ANY}:
                    self._report(node, "RPR-T0005", f"operator '++' requires Text operands, got {left} and {right}")
                return "Text"
            if operator in {"<", "<=", ">", ">="}:
                compatible = (self._numeric(left) and self._numeric(right)) or (left == right == "Text") or ANY in {left, right}
                if not compatible:
                    self._report(node, "RPR-T0006", f"operator '{operator}' cannot compare {left} with {right}")
                return "Bool"
            if operator in {"==", "!="}:
                return "Bool"
        return ANY

    def _call(self, node: Node) -> str:
        children = node.children or []
        callee = children[0]
        arguments = children[1:]
        argument_types = [self._expression(argument) for argument in arguments]
        if callee.kind != "name":
            self._expression(callee)
            return ANY
        name = callee.value
        if name in BUILTIN_ARITY:
            minimum, maximum = BUILTIN_ARITY[name]
            if len(arguments) < minimum or (maximum is not None and len(arguments) > maximum):
                expected = str(minimum) if minimum == maximum else (
                    f"at least {minimum}" if maximum is None else f"{minimum}..{maximum}"
                )
                self._report(node, "RPR-T0007", f"{name}() expects {expected} arguments, got {len(arguments)}")
            self._check_builtin_arguments(node, name, argument_types)
            self._check_builtin_effect(node, name)

            if name == "ok":
                return f"Result<{argument_types[0] if argument_types else ANY}, Any>"
            if name == "err":
                return f"Result<Any, {argument_types[0] if argument_types else ANY}>"
            if name == "some":
                return f"Option<{argument_types[0] if argument_types else ANY}>"
            if name == "none":
                return "Option[Any]"
            if name in {"result_is_ok", "result_is_err", "option_is_some", "option_is_none"}:
                return "Bool"
            if name in {"result_value", "result_error", "option_value"} and argument_types:
                parts = self._generic_parts(argument_types[0])
                if name == "result_value":
                    return parts[1][0] if parts and parts[0] == "Result" and len(parts[1]) == 2 else ANY
                if name == "result_error":
                    return parts[1][1] if parts and parts[0] == "Result" and len(parts[1]) == 2 else ANY
                return parts[1][0] if parts and parts[0] == "Option" and len(parts[1]) == 1 else ANY
            if name == "option_or" and len(argument_types) == 2:
                parts = self._generic_parts(argument_types[0])
                value_type = parts[1][0] if parts and parts[0] == "Option" else ANY
                return self._unify(value_type, argument_types[1])
            if name == "map_ok" and len(argument_types) == 2:
                parts = self._generic_parts(argument_types[0])
                success = self._callback_return(arguments[1])
                if parts and parts[0] == "Result" and len(parts[1]) == 2:
                    return f"Result<{success}, {parts[1][1]}>"
                return "Result[Any, Any]"
            if name == "map_err" and len(argument_types) == 2:
                parts = self._generic_parts(argument_types[0])
                mapped = self._callback_return(arguments[1])
                if parts and parts[0] == "Result" and len(parts[1]) == 2:
                    return f"Result<{parts[1][0]}, {mapped}>"
                return "Result[Any, Any]"
            if name == "zip_ok" and len(argument_types) == 2:
                left = self._generic_parts(argument_types[0])
                right = self._generic_parts(argument_types[1])
                if left and right and left[0] == right[0] == "Result":
                    return "Result<List[Any], Any>"
                return "Result<List[Any]>, Any>"
            if name == "zip3_ok":
                return "Result<List[Any], Any>"
            if name == "push" and argument_types:
                item_type = argument_types[1] if len(argument_types) > 1 else ANY
                element_type = self._element_type(argument_types[0], node)
                return f"List[{self._unify(element_type, item_type)}]"
            if name == "map" and len(arguments) > 1:
                return f"List[{self._callback_return(arguments[1])}]"
            if name in {"keep", "filter"} and argument_types:
                return argument_types[0]
            if name in {"sorted", "sort_by", "rest", "take", "drop", "unique", "partition"} and argument_types:
                return argument_types[0] if argument_types[0].startswith("List[") else "List[Any]"
            if name == "first" and argument_types:
                return self._element_type(argument_types[0], node)
            if name == "reverse" and argument_types:
                return argument_types[0] if argument_types[0] == "Text" or argument_types[0].startswith("List[") else "List[Any]"
            if name == "flatten" and argument_types:
                nested_type = self._element_type(argument_types[0], node)
                return nested_type if nested_type.startswith("List[") else "List[Any]"
            if name == "chunk":
                return "List[Any]"
            if name in {"map", "keep", "filter", "sorted", "sort_by", "push", "rest", "take", "drop", "chunk", "unique", "flatten", "partition", "distribute", "proportional_split", "range", "divmod_euclidean", "euclidean_divmod", "split"}:
                if name == "range" or name in {"distribute", "proportional_split", "divmod_euclidean", "euclidean_divmod"}:
                    return "List[Int]"
                if name == "split":
                    return "List[Text]"
                return "List[Any]"
            return BUILTIN_RETURN.get(name, ANY)

        function = self.functions.get(name)
        if function is not None:
            if len(arguments) != function.arity:
                self._report(node, "RPR-T0007", f"{name}() expects {function.arity} arguments, got {len(arguments)}")
            if self.function_stack:
                caller_effects = self.function_stack[-1].effects
                if caller_effects is not None:
                    if function.effects is None:
                        self._report(node, "RPR-EFF0003", f"call to '{name}' has no declared effect contract")
                    else:
                        missing = function.effects - caller_effects
                        if missing:
                            self._report(node, "RPR-EFF0002", f"call to '{name}' requires undeclared effects: {', '.join(sorted(missing))}")

            bindings: dict[str, str] = {}
            type_parameters = set(function.type_parameters)
            for index, actual in enumerate(argument_types):
                if index >= len(function.parameter_types):
                    break
                expected = function.parameter_types[index]
                if expected is None:
                    continue
                if not self._bind_type_variables(expected, actual, type_parameters, bindings):
                    self._report(node, "RPR-T0014", f"argument {index + 1} to '{name}' expects {self._substitute_type(expected, bindings)}, got {actual}")
            for parameter, traits in function.trait_bounds.items():
                actual = bindings.get(parameter)
                if actual is None:
                    continue
                for trait in traits:
                    if not self._supports_trait(actual, trait):
                        self._report(node, "RPR-T0015", f"type {actual} does not satisfy trait bound {trait} for {parameter}")
            return self._substitute_type(function.return_type, bindings)
        return ANY

    def _check_builtin_effect(self, node: Node, name: str) -> None:
        if not self.function_stack:
            return
        allowed = self.function_stack[-1].effects
        required = BUILTIN_EFFECTS.get(name)
        if allowed is not None and required is not None and required not in allowed:
            self._report(node, "RPR-EFF0002", f"call to '{name}' requires effect '{required}'")

    def _callback_return(self, node: Node) -> str:
        if node.kind == "name" and node.value in self.functions:
            return self.functions[node.value].return_type
        return ANY

    def _generic_parts(self, type_name: str) -> tuple[str, list[str]] | None:
        opening = type_name.find("<")
        if opening <= 0 or not type_name.endswith(">"):
            return None
        head = type_name[:opening]
        body = type_name[opening + 1:-1]
        parts: list[str] = []
        depth = 0
        start = 0
        for index, char in enumerate(body):
            if char == "<":
                depth += 1
            elif char == ">":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(body[start:index].strip())
                start = index + 1
        parts.append(body[start:].strip())
        return head, parts

    def _bind_type_variables(
        self, expected: str, actual: str, type_parameters: set[str], bindings: dict[str, str]
    ) -> bool:
        if expected in type_parameters:
            previous = bindings.get(expected)
            if previous is None:
                bindings[expected] = actual
                return True
            return self._assignable(previous, actual) and self._assignable(actual, previous)
        expected_parts = self._generic_parts(expected)
        actual_parts = self._generic_parts(actual)
        if expected_parts and actual_parts and expected_parts[0] == actual_parts[0] and len(expected_parts[1]) == len(actual_parts[1]):
            return all(
                self._bind_type_variables(left, right, type_parameters, bindings)
                for left, right in zip(expected_parts[1], actual_parts[1])
            )
        return self._assignable(expected, actual)

    def _substitute_type(self, type_name: str, bindings: dict[str, str]) -> str:
        parts = self._generic_parts(type_name)
        if parts:
            return parts[0] + "<" + ", ".join(self._substitute_type(item, bindings) for item in parts[1]) + ">"
        return bindings.get(type_name, type_name)

    def _supports_trait(self, type_name: str, trait: str) -> bool:
        if trait not in SUPPORTED_TRAITS:
            return False
        if trait == "Numeric":
            return self._numeric(type_name)
        primitive = {"Int", "Float", "Number", "Bool", "Text", "i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64"}
        if trait in {"Copy", "Clone", "Eq", "Ord", "Display"}:
            return type_name in primitive
        return False

    def _flow_type(self, left_node: Node, right_node: Node, left_type: str) -> str:
        if right_node.kind != "call":
            return ANY
        children = right_node.children or []
        callee = children[0]
        extra_nodes = children[1:]
        extra_types = [self._expression(item) for item in extra_nodes]
        if callee.kind != "name":
            return ANY
        name = callee.value
        if name in BUILTIN_ARITY:
            minimum, maximum = BUILTIN_ARITY[name]
            supplied = 1 + len(extra_nodes)
            if supplied < minimum or (maximum is not None and supplied > maximum):
                expected = str(minimum) if minimum == maximum else (
                    f"at least {minimum}" if maximum is None else f"{minimum}..{maximum}"
                )
                self._report(right_node, "RPR-T0007", f"{name}() expects {expected} arguments, got {supplied}")
            self._check_builtin_arguments(right_node, name, [left_type, *extra_types])
            if name == "map":
                callback = extra_nodes[0] if extra_nodes else None
                if callback is not None and callback.kind == "name" and callback.value in self.functions:
                    return f"List[{self.functions[callback.value].return_type}]"
                return "List[Any]"
            if name in {"keep", "filter", "sorted", "sort_by", "take", "drop", "unique", "rest"}:
                return left_type
            if name == "sum":
                return "Number"
            if name in {"size", "length"}:
                return "Int"
            if name in {"text", "join", "trim", "lower", "upper"}:
                return "Text"
            if name == "reverse":
                return left_type
            if name in BUILTIN_RETURN:
                return BUILTIN_RETURN[name]
        function = self.functions.get(name)
        if function is not None:
            supplied = 1 + len(extra_nodes)
            if supplied != function.arity:
                self._report(right_node, "RPR-T0007", f"{name}() expects {function.arity} arguments, got {supplied}")
            return function.return_type
        return ANY

    def _check_builtin_arguments(self, node: Node, name: str, types: list[str]) -> None:
        if not types:
            return
        sequence_builtins = {
            "size", "first", "rest", "sum", "sorted", "sort_by", "map", "keep",
            "filter", "fold", "reduce", "chunk", "take", "drop", "flatten",
            "reverse", "unique", "join", "contains",
        }
        if name in sequence_builtins:
            sequence_type = types[0]
            if sequence_type != ANY and not (
                sequence_type.startswith("List[") or sequence_type in {"Text", "Map"}
            ):
                self._report(node, "RPR-T0008", f"{name}() expects a collection or Text, got {sequence_type}")
        if name in {"quotient", "remainder", "is_divisible", "divmod_euclidean", "euclidean_divmod"}:
            for value_type in types[:2]:
                if value_type not in {"Int", ANY}:
                    self._report(node, "RPR-T0009", f"{name}() expects Int arguments, got {value_type}")

    def _element_type(self, type_name: str, node: Node | None = None) -> str:
        if type_name.startswith("List[") and type_name.endswith("]"):
            return type_name[5:-1]
        if type_name == "Text":
            return "Text"
        if type_name in {ANY, "Map"}:
            return ANY
        if node is not None:
            self._report(node, "RPR-T0008", f"cannot iterate or index a value of type {type_name}")
        return ANY

    def _find_binding(self, name: str) -> Binding | None:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def _numeric(self, type_name: str) -> bool:
        if type_name in NUMERIC | {"Number", ANY}:
            return True
        for function in reversed(self.function_stack):
            if type_name in function.type_parameters:
                return "Numeric" in function.trait_bounds.get(type_name, ())
        return False

    def _assignable(self, expected: str, actual: str) -> bool:
        if expected == ANY or actual == ANY or expected == actual:
            return True
        if expected == "Float" and actual == "Int":
            return True
        if expected == "Number" and actual in NUMERIC:
            return True
        if expected.startswith("&") or actual.startswith("&"):
            return expected == actual or expected == ANY
        if expected.startswith("List[") and actual.startswith("List["):
            return expected == "List[Any]" or expected == actual
        expected_parts = self._generic_parts(expected)
        actual_parts = self._generic_parts(actual)
        if expected_parts and actual_parts and expected_parts[0] == actual_parts[0] and len(expected_parts[1]) == len(actual_parts[1]):
            return all(self._assignable(left, right) or left == "Any" for left, right in zip(expected_parts[1], actual_parts[1]))
        return False

    def _unify_all(self, types: list[str]) -> str:
        if not types:
            return ANY
        result = types[0]
        for item in types[1:]:
            result = self._unify(result, item)
        return result

    def _unify(self, left: str, right: str) -> str:
        if left == right:
            return left
        if left == ANY or right == ANY:
            return ANY
        if left in NUMERIC and right in NUMERIC:
            return "Float"
        if left == "Number" and right in NUMERIC | {"Number"}:
            return "Number"
        if right == "Number" and left in NUMERIC | {"Number"}:
            return "Number"
        if left == NOTHING:
            return f"Optional[{right}]"
        if right == NOTHING:
            return f"Optional[{left}]"
        return f"Union[{left},{right}]"

    def _report(self, node: Node, code: str, message: str) -> None:
        self.diagnostics.append(TypeDiagnostic(code, message, node.token.line, node.token.column))


def check_source(source: str, filename: str = "<memory>") -> TypeCheckResult:
    tree = parse(source, filename)
    return TypeChecker(filename).check(tree)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run conservative static type analysis on a Reaper .rpr source file.")
    parser.add_argument("source", type=Path, help="Reaper source file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable diagnostics")
    args = parser.parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8")
        result = check_source(source, str(args.source))
    except (OSError, UnicodeError, ReaperError, ValueError) as error:
        payload = {"ok": False, "file": str(args.source), "error": str(error)}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"reaper typecheck: {error}")
        return 2
    if args.json:
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    else:
        for diagnostic in result.diagnostics:
            print(f"{args.source}:{diagnostic.line}:{diagnostic.column}: {diagnostic.severity} {diagnostic.code}: {diagnostic.message}")
        errors = result.as_dict()["summary"]["errors"]
        warnings = result.as_dict()["summary"]["warnings"]
        print(f"Reaper typecheck: {'PASS' if result.ok else 'FAIL'} ({errors} error(s), {warnings} warning(s))")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
