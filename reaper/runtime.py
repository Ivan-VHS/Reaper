"""Tree-walk runtime for Reaper's first stable language slice."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from .errors import ExecutionLimitError, ReaperRuntimeError
from .lexer import Token
from .parser import Node, parse
from .impact import catalog as impact_catalog, find_profile as impact_profile, rank_profiles as impact_rank, search_profiles as impact_search
from . import metric_space
from .glyphs import GLYPHS
from .memory import MemoryArena, MemoryBuffer, MemoryFrame, MemoryPool, MemoryView, apply_memory_glyph


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
            if operator == "|>":
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
            raise self._error(token, "'++' joins text values; convert other values with text()")
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
            if not isinstance(value, (list, tuple, str, range, MemoryBuffer, MemoryView)):
                raise TypeError("expected a list, text, range, memory buffer, or view")
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

        def bounded_range(*arguments: int) -> range:
            return sequence(self._range(*arguments))

        def bounded_size(value: Any) -> int:
            if not isinstance(value, (str, list, tuple, dict, range, MemoryBuffer, MemoryView)):
                raise TypeError("expected text, list, map, range, memory buffer, or view")
            try:
                size = len(value)
            except OverflowError as error:
                raise ValueError("collection length exceeds interpreter limits") from error
            if size > self.max_collection_items:
                raise ValueError(                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            return size

        def callback(value: Any) -> None:
            if not isinstance(value, (UserFunction, Builtin)):
                raise TypeError("expected a Reaper function")

        def memory_payload(value: Any) -> bytes:
            if isinstance(value, str):
                return value.encode("utf-8")
            if isinstance(value, (bytes, bytearray)):
                return bytes(value)
            if isinstance(value, list) and all(
                isinstance(item, int) and not isinstance(item, bool) and 0 <= item <= 255
                for item in value
            ):
                return bytes(value)
            raise TypeError("payload must be text, bytes, or a list of byte values")

        def memory_write(target: Any, offset: int, value: Any) -> int:
            payload = memory_payload(value)
            if isinstance(target, MemoryView):
                if target.readonly or target.buffer.readonly:
                    raise ValueError("view is read-only")
                offset = self._whole_memory_integer(offset, "offset")
                if offset + len(payload) > len(target):
                    raise ValueError("write exceeds view bounds")
                return target.buffer.write(target.start + offset, payload)
            if not isinstance(target, MemoryBuffer):
                raise TypeError("expected a Reaper memory buffer or view")
            return target.write(offset, payload)

        def memory_read(target: Any, offset: int = 0, length: int | None = None) -> Any:
            if isinstance(target, MemoryView):
                if offset != 0 or length is not None:
                    raise ValueError("offset and length are not accepted with a view")
                return target.read()
            if not isinstance(target, MemoryBuffer):
                raise TypeError("expected a Reaper memory buffer or view")
            return target.read(offset, length)

        register("size", bounded_size, 1, 1)
        register("text", self._display, 1, 1)
        register("number", self._to_number, 1, 1)
        register("kind", self._kind, 1, 1)
        register("range", bounded_range, 1, 3)
        register("push", push, 2, 2)
        register("first", lambda values: _first(sequence(values)), 1, 1)
        register("rest", lambda values: sequence(values)[1:], 1, 1)
        register("sum", lambda values: _sum(sequence(values)), 1, 1)
        register("sorted", lambda values, *options: self._sorted(sequence(values), callback, *options), 1, 3)
        register("sort_by", lambda values, fn, *direction: self._sort_by(sequence(values), callback, fn, direction[0] if direction else "asc"), 2, 3)
        register("map", lambda values, fn: self._map(sequence(values), callback, fn), 2, 2)
        register("keep", lambda values, fn: self._keep(sequence(values), callback, fn), 2, 2)
        register("filter", lambda values, fn: self._keep(sequence(values), callback, fn), 2, 2)
        register("fold", lambda values, initial, fn: self._fold(sequence(values), initial, callback, fn), 3, 3)
        register("reduce", lambda values, initial, fn: self._fold(sequence(values), initial, callback, fn), 3, 3)
        register("chunk", lambda values, width: self._chunk(sequence(values), width), 2, 2)
        register("take", lambda values, count: self._take(sequence(values), count), 2, 2)
        register("drop", lambda values, count: self._drop(sequence(values), count), 2, 2)
        register("flatten", lambda values: self._flatten(sequence(values)), 1, 1)
        register("reverse", lambda values: values[::-1] if isinstance(values, str) else list(reversed(sequence(values))), 1, 1)
        register("unique", lambda values: self._unique(sequence(values)), 1, 1)
        register("split", self._split_text, 2, 2)
        register("join", self._join_text, 2, 2)
        register("trim", lambda value: self._require_text(value).strip(), 1, 1)
        register("lower", lambda value: self._require_text(value).lower(), 1, 1)
        register("upper", lambda value: self._require_text(value).upper(), 1, 1)
        register("replace", self._replace_text, 3, 4)
        register("contains", self._contains, 2, 2)
        register("starts_with", self._starts_with, 2, 2)
        register("ends_with", self._ends_with, 2, 2)
        register("say", lambda *values: self.output(" ".join(self._display(v) for v in values)), 1, None)
        register("ask", lambda prompt: input(self._display(prompt)), 1, 1)
        register("assert", self._assert, 1, 2)
        register("memory_write", memory_write, 3, 3)
        register("memory_read", memory_read, 1, 3)
        register("memory_capacity", lambda buffer: buffer.capacity if isinstance(buffer, MemoryBuffer) else _raise_type("expected a memory buffer"), 1, 1)
        for spec in GLYPHS:
            internal_name = f"\\0glyph:{spec.token}"
            if spec.implemented:
                action = lambda *values, operation=spec.operation: apply_memory_glyph(operation, *values)
            else:
                action = lambda *values, glyph=spec.token: _raise_type(
                    f"glyph {glyph!r} is reserved; no runtime operation is assigned yet"
                )
            self.globals.define(
                internal_name,
                Builtin(f"glyph {spec.token}", action, 0, None),
            )
        register("impact_catalog", impact_catalog, 0, 0)
        register("impact_profile", impact_profile, 1, 1)
        register("impact_search", impact_search, 1, 1)
        register("impact_rank", lambda profiles, dimension: impact_rank(sequence(profiles), dimension), 2, 2)
        register("metric_dot", lambda left, right: metric_space.dot(sequence(left), sequence(right)), 2, 2)
        register("vector_norm", lambda values, *kind: metric_space.vector_norm(sequence(values), kind[0] if kind else "l2"), 1, 2)
        register("vector_normalize", lambda values: metric_space.normalize(sequence(values)), 1, 1)
        register("normalize_vector", lambda values: metric_space.normalize(sequence(values)), 1, 1)
        register("manhattan_distance", lambda left, right: metric_space.manhattan_distance(sequence(left), sequence(right)), 2, 2)
        register("chebyshev_distance", lambda left, right: metric_space.chebyshev_distance(sequence(left), sequence(right)), 2, 2)
        register("squared_euclidean_distance", lambda left, right: metric_space.squared_euclidean_distance(sequence(left), sequence(right)), 2, 2)
        register("cosine_similarity", lambda left, right: metric_space.cosine_similarity(sequence(left), sequence(right)), 2, 2)
        register("angle_between", lambda left, right: metric_space.angle_between(sequence(left), sequence(right)), 2, 2)
        register("vector_projection", lambda vector, onto: metric_space.project(vector, onto), 2, 2)
        register("vector_centroid", lambda vectors: metric_space.centroid(sequence(vectors)), 1, 1)
        register("euclidean_distance", lambda left, right: metric_space.euclidean_distance(sequence(left), sequence(right)), 2, 2)
        register("is_orthogonal", lambda left, right, *tol: metric_space.is_orthogonal(
            sequence(left), sequence(right), tol[0] if tol else 1e-12
        ), 2, 3)
        register("quadratic_form", lambda values, matrix: metric_space.quadratic_form(
            sequence(values), sequence(matrix)
        ), 2, 2)
        register("law_of_cosines", metric_space.law_of_cosines, 3, 3)
        register("de_gua_area", metric_space.de_gua_area, 3, 3)
        register("parseval_energy", lambda values: metric_space.parseval_energy(sequence(values)), 1, 1)
        register("unit_circle_residual", metric_space.unit_circle_residual, 1, 1)
        register("spherical_hypotenuse", metric_space.spherical_hypotenuse, 2, 2)
        register("hyperbolic_hypotenuse", metric_space.hyperbolic_hypotenuse, 2, 2)
        register("minkowski_interval", lambda ct, spatial: metric_space.minkowski_interval(
            ct, sequence(spatial)
        ), 2, 2)
        register("combine_variances", lambda values: metric_space.combine_uncorrelated_variances(
            sequence(values)
        ), 1, 1)
        register("reciprocal_altitude", metric_space.reciprocal_altitude, 2, 2)

    @staticmethod
    def _require_text(value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError("expected text")
        return value

    def _sorted(self, values: Any, validator: Callable[[Any], None], *options: Any) -> list[Any]:
        key_function = None
        direction = "asc"
        if len(options) == 1:
            if isinstance(options[0], str):
                direction = options[0]
            else:
                key_function = options[0]
        elif len(options) == 2:
            key_function, direction = options
        if direction not in ("asc", "desc"):
            raise ValueError("sort direction must be 'asc' or 'desc'")
        if key_function is not None:
            validator(key_function)
            key = lambda item: self._call(key_function, [item], Token("BUILTIN", "sorted", 1, 1))
        else:
            key = None
        return sorted(values, key=key, reverse=direction == "desc")

    def _sort_by(self, values: Any, validator: Callable[[Any], None], function: Any, direction: Any) -> list[Any]:
        return self._sorted(values, validator, function, direction)

    def _chunk(self, values: Any, width: Any) -> list[Any]:
        if isinstance(width, bool) or not isinstance(width, int) or width < 1:
            raise ValueError("chunk width must be a positive whole number")
        result = [values[index:index + width] for index in range(0, len(values), width)]
        if len(result) > self.max_collection_items:
            raise ValueError(f"collection item limit ({self.max_collection_items}) exceeded")
        return result

    @staticmethod
    def _slice_count(count: Any, name: str) -> int:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{name} count must be a non-negative whole number")
        return count

    def _take(self, values: Any, count: Any) -> Any:
        return values[:self._slice_count(count, "take")]

    def _drop(self, values: Any, count: Any) -> Any:
        return values[self._slice_count(count, "drop"):]

    def _flatten(self, values: Any) -> list[Any]:
        result: list[Any] = []
        for item in values:
            if not isinstance(item, (list, tuple)):
                raise TypeError("flatten() expects a list of lists")
            if len(result) + len(item) > self.max_collection_items:
                raise ValueError(f"collection item limit ({self.max_collection_items}) exceeded")
            result.extend(item)
        return result

    def _unique(self, values: Any) -> list[Any]:
        result: list[Any] = []
        seen: set[Any] = set()
        for item in values:
            try:
                marker = (type(item), item)
                if marker in seen:
                    continue
                seen.add(marker)
            except TypeError:
                if any(self._equal(item, previous) for previous in result):
                    continue
            result.append(item)
        return result

    def _split_text(self, value: Any, separator: Any) -> list[str]:
        value = self._require_text(value)
        separator = self._require_text(separator)
        if not separator:
            raise ValueError("split separator cannot be empty")
        result = value.split(separator)
        if len(result) > self.max_collection_items:
            raise ValueError(f"collection item limit ({self.max_collection_items}) exceeded")
        return result

    def _join_text(self, values: Any, separator: Any) -> str:
        if not isinstance(values, (list, tuple)):
            raise TypeError("join() expects a list of text values")
        separator = self._require_text(separator)
        if any(not isinstance(item, str) for item in values):
            raise TypeError("join() expects a list of text values")
        result = separator.join(values)
        if len(result) > self.max_text_length:
            raise ValueError(f"text length limit ({self.max_text_length}) exceeded")
        return result

    def _replace_text(self, value: Any, old: Any, new: Any, *count: Any) -> str:
        value, old, new = (self._require_text(item) for item in (value, old, new))
        if count and (isinstance(count[0], bool) or not isinstance(count[0], int) or count[0] < 0):
            raise ValueError("replace count must be a non-negative whole number")
        result = value.replace(old, new, count[0] if count else -1)
        if len(result) > self.max_text_length:
            raise ValueError(f"text length limit ({self.max_text_length}) exceeded")
        return result

    def _contains(self, container: Any, needle: Any) -> bool:
        if isinstance(container, str):
            if not isinstance(needle, str):
                raise TypeError("text membership expects text")
            return needle in container
        if isinstance(container, (list, tuple, range)):
            return any(self._equal(item, needle) for item in container)
        raise TypeError("contains() expects text or a sequence")

    def _starts_with(self, value: Any, prefix: Any) -> bool:
        return self._require_text(value).startswith(self._require_text(prefix))

    def _ends_with(self, value: Any, suffix: Any) -> bool:
        return self._require_text(value).endswith(self._require_text(suffix))

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
        if isinstance(value, MemoryBuffer):
            return "memory_buffer"
        if isinstance(value, MemoryView):
            return "memory_view"
        if isinstance(value, MemoryArena):
            return "memory_arena"
        if isinstance(value, MemoryFrame):
            return "memory_frame"
        if isinstance(value, MemoryPool):
            return "memory_pool"
        if isinstance(value, bytes):
            return "bytes"
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

    @staticmethod
    def _whole_memory_integer(value: Any, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label} must be a non-negative whole number")
        return value

    def _display(self, value: Any) -> str:
        if isinstance(value, MemoryBuffer):
            return f"memory_buffer(length={value.length}, capacity={value.capacity}, alignment={value.alignment})"
        if isinstance(value, MemoryView):
            return f"memory_view(length={len(value)}, step={value.step}, readonly={str(value.readonly).lower()})"
        if isinstance(value, MemoryArena):
            return f"memory_arena(used={value.used}, limit={value.limit}, closed={str(value.closed).lower()})"
        if isinstance(value, MemoryFrame):
            return f"memory_frame(closed={str(value.closed).lower()})"
        if isinstance(value, MemoryPool):
            return f"memory_pool(slot_size={value.slot_size}, capacity={value.capacity})"
        if isinstance(value, bytes):
            return value.hex()
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