"""Tree-walk runtime for Reaper's first stable language slice."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from .errors import ExecutionLimitError, ReaperRuntimeError
from .lexer import Token
from .parser import Node, parse


@dataclass(slots=True)
class Binding:
    value: Any
    mutable: bool


class Environment:
    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self.values: dict[str, Binding] = {}

    def define(self, name: str, value: Any, mutable: bool = False) -> None:
        if name in self.values:
            raise ReaperRuntimeError(f"'{name}' is already defined in this scope")
        self.values[name] = Binding(value, mutable)

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name].value
        if self.parent is not None:
            return self.parent.get(name)
        raise ReaperRuntimeError(f"unknown name '{name}'")

    def change(self, name: str, value: Any) -> None:
        if name in self.values:
            binding = self.values[name]
            if not binding.mutable:
                raise ReaperRuntimeError(f"'{name}' was declared with 'make' and cannot be changed; use 'vary'")
            binding.value = value
            return
        if self.parent is not None:
            self.parent.change(name, value)
            return
        raise ReaperRuntimeError(f"unknown name '{name}'")


@dataclass(slots=True)
class UserFunction:
    name: str
    parameters: list[str]
    body: Node
    closure: Environment


@dataclass(slots=True)
class Builtin:
    name: str
    callback: Callable[..., Any]
    minimum: int
    maximum: int | None


class _ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class Interpreter:
    def __init__(
        self,
        output: Callable[[str], None] = print,
        max_steps: int = 1_000_000,
        max_call_depth: int = 256,
        max_collection_items: int = 100_000,
        max_text_length: int = 1_000_000,
    ) -> None:
        if (
            max_steps < 1
            or max_call_depth < 1
            or max_collection_items < 1
            or max_text_length < 1
        ):
            raise ValueError("execution limits must be positive")
        self.output = output
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth
        self.max_collection_items = max_collection_items
        self.max_text_length = max_text_length
        self.steps = 0
        self.call_depth = 0
        self.filename = "<memory>"
        self.globals = Environment()
        self._install_builtins()

    def run(self, source: str, filename: str = "<memory>") -> Any:
        self.filename = filename
        tree = parse(source, filename)
        try:
            return self._execute_block(tree, self.globals, create_scope=False)
        except _ReturnSignal as signal:
            raise ReaperRuntimeError(f"{filename}: yield can only be used inside a craft function") from signal

    def _tick(self, token: Token) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            raise ExecutionLimitError(
                f"{self.filename}:{token.line}:{token.column}: execution stopped after "
                f"{self.max_steps} steps; increase --steps only for programs you trust"
            )

    def _check_collection_size(self, values: Any, token: Token) -> Any:
        try:
            size = len(values)
        except (OverflowError, TypeError) as error:
            raise self._error(token, "collection size cannot be represented") from error
        if size > self.max_collection_items:
            raise self._error(
                token,
                f"collection item limit ({self.max_collection_items}) exceeded",
            )
        return values

    def _execute_block(self, block: Node, environment: Environment, create_scope: bool = True) -> Any:
        scope = Environment(environment) if create_scope else environment
        result = None
        for statement in block.children or []:
            result = self._execute(statement, scope)
        return result

    def _execute(self, node: Node, environment: Environment) -> Any:
        self._tick(node.token)
        children = node.children or []
        if node.kind == "declare":
            name, mutable = node.value
            environment.define(name, self._evaluate(children[0], environment), mutable)
        elif node.kind == "change":
            environment.change(node.value, self._evaluate(children[0], environment))
        elif node.kind == "emit":
            self.output(self._display(self._evaluate(children[0], environment)))
        elif node.kind == "yield":
            value = self._evaluate(children[0], environment) if children else None
            raise _ReturnSignal(value)
        elif node.kind == "function":
            name, parameters = node.value
            environment.define(name, UserFunction(name, parameters, children[0], environment))
        elif node.kind == "when":
            if self._truthy(self._evaluate(children[0], environment)):
                return self._execute_block(children[1], environment)
            if len(children) == 3:
                return self._execute_block(children[2], environment)
        elif node.kind == "each":
            values = self._evaluate(children[0], environment)
            if not isinstance(values, (list, tuple, str, range)):
                raise self._error(node.token, "'each' needs a list, text, or range")
            self._check_collection_size(values, node.token)
            result = None
            for value in values:
                self._tick(node.token)
                scope = Environment(environment)
                scope.define(node.value, value)
                result = self._execute_block(children[1], scope)
            return result
        elif node.kind == "while":
            result = None
            while self._truthy(self._evaluate(children[0], environment)):
                self._tick(node.token)
                result = self._execute_block(children[1], environment)
            return result
        elif node.kind == "expression":
            return self._evaluate(children[0], environment)
        elif node.kind == "block":
            return self._execute_block(node, environment)
        else:
            raise self._error(node.token, f"unknown statement kind '{node.kind}'")
        return None

    def _evaluate(self, node: Node, environment: Environment) -> Any:
        self._tick(node.token)
        children = node.children or []
        if node.kind == "literal":
            return node.value
        if node.kind == "name":
            return environment.get(node.value)
        if node.kind == "list":
            if len(children) > self.max_collection_items:
                raise self._error(
                    node.token,
                    f"collection item limit ({self.max_collection_items}) exceeded",
                )
            return [self._evaluate(item, environment) for item in children]
        if node.kind == "index":
            collection = self._evaluate(children[0], environment)
            index = self._evaluate(children[1], environment)
            try:
                if isinstance(collection, dict):
                    return collection[index]
                if isinstance(index, bool) or not isinstance(index, int):
                    raise TypeError("sequence indexes must be whole numbers")
                return collection[index]
            except (IndexError, KeyError, TypeError) as error:
                raise self._error(node.token, f"cannot read this index: {error}") from error
        if node.kind == "unary":
            value = self._evaluate(children[0], environment)
            if node.value == "NOT":
                return not self._truthy(value)
            if node.value == "-" and self._is_number(value):
                return -value
            raise self._error(node.token, "unary '-' expects a number")
        if node.kind == "call":
            callee = self._evaluate(children[0], environment)
            arguments = [self._evaluate(arg, environment) for arg in children[1:]]
            return self._call(callee, arguments, node.token)
        if node.kind == "binary":
            operator = node.value
            left = self._evaluate(children[0], environment)
            if operator == "AND":
                return self._evaluate(children[1], environment) if self._truthy(left) else left
            if operator == "OR":
                return left if self._truthy(left) else self._evaluate(children[1], environment)
            if operator == "~>":
                right = children[1]
                if right.kind == "call":
                    callee = self._evaluate(right.children[0], environment)
                    arguments = [self._evaluate(arg, environment) for arg in right.children[1:]]
                else:
                    callee, arguments = self._evaluate(right, environment), []
                return self._call(callee, [left, *arguments], node.token)
            right = self._evaluate(children[1], environment)
            return self._binary(operator, left, right, node.token)
        raise self._error(node.token, f"unknown expression kind '{node.kind}'")

    def _binary(self, operator: str, left: Any, right: Any, token: Token) -> Any:
        if operator == "==":
            return self._equal(left, right)
        if operator == "!=":
            return not self._equal(left, right)
        if operator == "++":
            if isinstance(left, str) and isinstance(right, str):
                if len(left) + len(right) > self.max_text_length:
                    raise self._error(
                        token,
                        f"text length limit ({self.max_text_length}) exceeded",
                    )
                return left + right
            if isinstance(left, (list, tuple, range)) and isinstance(right, (list, tuple, range)):
                total = len(left) + len(right)
                if total > self.max_collection_items:
                    raise self._error(
                        token,
                        f"collection item limit ({self.max_collection_items}) exceeded",
                    )
                return [*left, *right]
            raise self._error(token, "'++' joins text values or sequences of items")
        if operator in {"<", "<=", ">", ">="}:
            compatible = (
                self._is_number(left) and self._is_number(right)
            ) or (type(left) is str and type(right) is str)
            if not compatible:
                raise self._error(token, f"'{operator}' needs two numbers or two text values")
            return {
                "<": left < right, "<=": left <= right,
                ">": left > right, ">=": left >= right,
            }[operator]
        if operator in {"+", "-", "*", "/", "//", "%", "**"}:
            if not (self._is_number(left) and self._is_number(right)):
                raise self._error(token, f"'{operator}' needs two numbers")
            if operator in {"/", "//", "%"} and right == 0:
                raise self._error(token, "division by zero")
            try:
                result = {
                    "+": lambda: left + right,
                    "-": lambda: left - right,
                    "*": lambda: left * right,
                    "/": lambda: left / right,
                    "//": lambda: left // right,
                    "%": lambda: left % right,
                    "**": lambda: left ** right,
                }[operator]()
            except (ArithmeticError, ValueError, TypeError) as error:
                raise self._error(token, f"numeric operation failed: {error}") from error
            if not isinstance(result, (int, float)) or isinstance(result, bool):
                raise self._error(token, "numeric operations must produce real numbers")
            if isinstance(result, float) and not math.isfinite(result):
                raise self._error(token, "numeric result is not finite")
            return result
        raise self._error(token, f"unknown operator '{operator}'")

    def _call(self, callee: Any, arguments: list[Any], token: Token) -> Any:
        if isinstance(callee, Builtin):
            valid = len(arguments) >= callee.minimum and (
                callee.maximum is None or len(arguments) <= callee.maximum
            )
            if not valid:
                expected = (
                    str(callee.minimum) if callee.minimum == callee.maximum
                    else f"at least {callee.minimum}" if callee.maximum is None
                    else f"{callee.minimum}..{callee.maximum}"
                )
                raise self._error(token, f"{callee.name}() expects {expected} arguments, got {len(arguments)}")
            try:
                return callee.callback(*arguments)
            except ReaperRuntimeError:
                raise
            except (TypeError, ValueError, OverflowError) as error:
                raise self._error(token, f"{callee.name}(): {error}") from error
        if isinstance(callee, UserFunction):
            if len(arguments) != len(callee.parameters):
                raise self._error(
                    token, f"{callee.name}() expects {len(callee.parameters)} arguments, got {len(arguments)}"
                )
            if self.call_depth >= self.max_call_depth:
                raise self._error(token, f"call-depth limit ({self.max_call_depth}) exceeded")
            local = Environment(callee.closure)
            for name, value in zip(callee.parameters, arguments):
                local.define(name, value)
            self.call_depth += 1
            try:
                try:
                    self._execute_block(callee.body, local, create_scope=False)
                except _ReturnSignal as signal:
                    return signal.value
                return None
            finally:
                self.call_depth -= 1
        raise self._error(token, "this value cannot be called")

    def _install_builtins(self) -> None:
        def register(name: str, callback: Callable[..., Any], minimum: int, maximum: int | None = None) -> None:
            self.globals.define(name, Builtin(name, callback, minimum, maximum))

        def sequence(value: Any) -> Any:
            if not isinstance(value, (list, tuple, str, range)):
                raise TypeError("expected a list, text, or range")
            try:
                size = len(value)
            except OverflowError as error:
                raise ValueError("collection length exceeds interpreter limits") from error
            if size > self.max_collection_items:
                raise ValueError(
                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            return value

        def push(values: Any, item: Any) -> list[Any]:
            values = sequence(values)
            if len(values) >= self.max_collection_items:
                raise ValueError(
                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            return [*values, item]

        def concat(*values: Any) -> Any:
            if not values:
                return ""
            if all(isinstance(value, str) for value in values):
                total = sum(len(value) for value in values)
                if total > self.max_text_length:
                    raise ValueError(f"text length limit ({self.max_text_length}) exceeded")
                return "".join(values)
            if all(isinstance(value, (list, tuple, range)) for value in values):
                checked = [sequence(value) for value in values]
                total = sum(len(value) for value in checked)
                if total > self.max_collection_items:
                    raise ValueError(f"collection item limit ({self.max_collection_items}) exceeded")
                return [item for value in checked for item in value]
            raise TypeError("concat() expects only text values or only sequences")

        def join(separator: str, values: Any) -> str:
            if not isinstance(separator, str):
                raise TypeError("join() separator must be text")
            values = sequence(values)
            if not isinstance(values, (list, tuple, range)) or any(not isinstance(item, str) for item in values):
                raise TypeError("join() expects a sequence containing only text values")
            result = separator.join(values)
            if len(result) > self.max_text_length:
                raise ValueError(f"text length limit ({self.max_text_length}) exceeded")
            return result

        def extend(values: Any, additions: Any) -> list[Any]:
            values = sequence(values)
            additions = sequence(additions)
            total = len(values) + len(additions)
            if total > self.max_collection_items:
                raise ValueError(f"collection item limit ({self.max_collection_items}) exceeded")
            return [*values, *additions]

        def bounded_range(*arguments: int) -> range:
            return sequence(self._range(*arguments))

        def bounded_size(value: Any) -> int:
            if not isinstance(value, (str, list, tuple, dict, range)):
                raise TypeError("expected text, list, map, or range")
            try:
                size = len(value)
            except OverflowError as error:
                raise ValueError("collection length exceeds interpreter limits") from error
            if size > self.max_collection_items:
                raise ValueError(
                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            return size

        def callback(value: Any) -> None:
            if not isinstance(value, (UserFunction, Builtin)):
                raise TypeError("expected a Reaper function")

        register("size", bounded_size, 1, 1)
        register("text", self._display, 1, 1)
        register("number", self._to_number, 1, 1)
        register("kind", self._kind, 1, 1)
        register("range", bounded_range, 1, 3)
        register("push", push, 2, 2)
        register("concat", concat, 0, None)
        register("join", join, 2, 2)
        register("extend", extend, 2, 2)
        register("first", lambda values: _first(sequence(values)), 1, 1)
        register("rest", lambda values: sequence(values)[1:], 1, 1)
        register("sum", lambda values: _sum(sequence(values)), 1, 1)
        register("sorted", lambda values: sorted(sequence(values)), 1, 1)
        register("map", lambda values, fn: self._map(sequence(values), callback, fn), 2, 2)
        register("keep", lambda values, fn: self._keep(sequence(values), callback, fn), 2, 2)
        register("fold", lambda values, initial, fn: self._fold(sequence(values), initial, callback, fn), 3, 3)
        register("say", lambda *values: self.output(" ".join(self._display(v) for v in values)), 1, None)
        register("ask", lambda prompt: input(self._display(prompt)), 1, 1)
        register("assert", self._assert, 1, 2)

    def _map(self, values: Any, validator: Callable[[Any], None], function: Any) -> list[Any]:
        validator(function)
        return [self._call(function, [item], Token("BUILTIN", "map", 1, 1)) for item in values]

    def _keep(self, values: Any, validator: Callable[[Any], None], function: Any) -> list[Any]:
        validator(function)
        return [
            item for item in values
            if self._truthy(self._call(function, [item], Token("BUILTIN", "keep", 1, 1)))
        ]

    def _fold(self, values: Any, initial: Any, validator: Callable[[Any], None], function: Any) -> Any:
        validator(function)
        result = initial
        for item in values:
            result = self._call(function, [result, item], Token("BUILTIN", "fold", 1, 1))
        return result

    @staticmethod
    def _range(*arguments: int) -> range:
        if any(isinstance(value, bool) or not isinstance(value, int) for value in arguments):
            raise TypeError("range() arguments must be whole numbers")
        if len(arguments) == 1:
            return range(arguments[0])
        if len(arguments) == 2:
            return range(arguments[0], arguments[1])
        if arguments[2] == 0:
            raise ValueError("range() step cannot be zero")
        return range(*arguments)

    @staticmethod
    def _to_number(value: Any) -> int | float:
        if isinstance(value, bool):
            raise TypeError("booleans are not numbers")
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            parsed = float(value) if "." in value else int(value)
            if isinstance(parsed, float) and not math.isfinite(parsed):
                raise ValueError("number must be finite")
            return parsed
        raise TypeError("cannot convert this value to a number")

    @staticmethod
    def _kind(value: Any) -> str:
        if value is None:
            return "nothing"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "text"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "map"
        if isinstance(value, (UserFunction, Builtin)):
            return "craft"
        return "unknown"

    def _assert(self, condition: Any, message: Any = "assertion failed") -> None:
        if not self._truthy(condition):
            raise ReaperRuntimeError(self._display(message))

    @staticmethod
    def _truthy(value: Any) -> bool:
        return bool(value)

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _equal(self, left: Any, right: Any) -> bool:
        if type(left) is not type(right):
            return False
        if isinstance(left, list):
            return len(left) == len(right) and all(self._equal(a, b) for a, b in zip(left, right))
        if isinstance(left, dict):
            return left.keys() == right.keys() and all(self._equal(left[key], right[key]) for key in left)
        return left == right

    def _display(self, value: Any) -> str:
        if value is None:
            return "nothing"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, list):
            return "[" + ", ".join(self._display(item) for item in value) + "]"
        if isinstance(value, str):
            return value
        if isinstance(value, range):
            return f"range({value.start}, {value.stop}, {value.step})"
        return str(value)

    def _error(self, token: Token, message: str) -> ReaperRuntimeError:
        return ReaperRuntimeError(f"{self.filename}:{token.line}:{token.column}: {message}")


def _raise_type(message: str) -> Any:
    raise TypeError(message)


def _first(values: Any) -> Any:
    if not values:
        raise ValueError("first() cannot read an empty sequence")
    return values[0]


def _sum(values: Any) -> int | float:
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise TypeError("sum() expects only numbers")
    return sum(values)


def run(
    source: str,
    filename: str = "<memory>",
    output: Callable[[str], None] = print,
    max_steps: int = 1_000_000,
    max_collection_items: int = 100_000,
    max_text_length: int = 1_000_000,
) -> Any:
    return Interpreter(
        output=output,
        max_steps=max_steps,
        max_collection_items=max_collection_items,
        max_text_length=max_text_length,
    ).run(source, filename)
