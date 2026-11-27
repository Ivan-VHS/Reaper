"""Tree-walk runtime for Reaper's first stable language slice."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from .errors import ExecutionLimitError, ReaperRuntimeError
from .governance import ConsentAuthority
from .lexer import Token
from .parser import Node, parse
from .impact import catalog as impact_catalog, find_profile as impact_profile, rank_profiles as impact_rank, search_profiles as impact_search
from . import arithmetic, metric_space, native as pytyliki_native
from pathlib import Path

from .debugger import RuntimeDebugger
from .ffi import CAbiLibrary, NativeFunction, PytylikiBridge
from .memory import HeapLimitError, MemoryManager, RegionError
from .modules import ModuleError, ModuleLoader
from .resources import ResourceError, ResourceHandle, ResourceManager
from .token_catalog import token_catalog, token_info, token_is_reserved


@dataclass(slots=True)
class Binding:
    value: Any
    mutable: bool


class Environment:
    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self.values: dict[str, Binding] = {}
        self.exports: set[str] = set()

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
        allow_native_ffi: bool = False,
        max_heap_bytes: int = 64 * 1024 * 1024,
        max_open_resources: int = 64,
        debugger: RuntimeDebugger | None = None,
        consent_authority: ConsentAuthority | None = None,
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
        self.allow_native_ffi = allow_native_ffi
        self.memory = MemoryManager(max_heap_bytes=max_heap_bytes)
        self.resources = ResourceManager(max_open=max_open_resources)
        self.module_loader = ModuleLoader(self)
        self.debugger = debugger
        self.consent_authority = consent_authority
        self.call_stack: list[str] = []
        self._active_vm: Any = None
        self._current_environment: Environment | None = None
        self._ffi_libraries: list[Any] = []
        self._install_builtins()

    def _memory_roots(self) -> list[Any]:
        roots: list[Any] = [self.globals, self.module_loader.cache]
        if self._current_environment is not None:
            roots.append(self._current_environment)
        return roots

    def run(self, source: str, filename: str = "<memory>", engine: str = "treewalk") -> Any:
        if engine not in {"treewalk", "vm"}:
            raise ValueError("engine must be 'treewalk' or 'vm'")
        self.filename = filename
        tree = parse(source, filename)
        root = self.module_loader.begin_root(filename)
        try:
            if engine == "vm":
                from .ir import lower
                from .vm import VirtualMachine, assemble
                program = assemble(lower(tree, filename))
                machine = VirtualMachine(self, program)
                self._active_vm = machine
                try:
                    return machine.run()
                finally:
                    self._active_vm = None
            return self._execute_block(tree, self.globals, create_scope=False)
        except _ReturnSignal as signal:
            raise ReaperRuntimeError(f"{filename}: yield can only be used inside a craft function") from signal
        finally:
            self.resources.close_all()
            for library in reversed(self._ffi_libraries):
                library.close()
            self._ffi_libraries.clear()
            self.module_loader.end_root(root)
            self._current_environment = None
            self.memory.collect(self._memory_roots())

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
        self._current_environment = environment
        if self.debugger is not None:
            self.debugger.before_statement(node.token, environment, self.call_stack, self.filename)
        self._tick(node.token)
        children = node.children or []
        if node.kind == "import":
            specifier, alias = node.value
            exports = self.module_loader.load(specifier, self.filename)
            if alias:
                environment.define(alias, exports)
            else:
                for symbol, value in exports.items():
                    environment.define(symbol, value)
        elif node.kind == "export":
            if children:
                declaration = children[0]
                self._execute(declaration, environment)
                if declaration.kind == "declare":
                    name = declaration.value[0]
                else:
                    name = declaration.value[0]
            else:
                name = node.value
            if name not in environment.values:
                raise self._error(node.token, f"cannot export undefined local name '{name}'")
            environment.exports.add(name)
        elif node.kind == "declare":
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
        self._current_environment = environment
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
            return self.memory.track([self._evaluate(item, environment) for item in children])
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
            if operator == "::":
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
                return self.memory.track(callee.callback(*arguments))
            except ReaperRuntimeError:
                raise
            except (TypeError, ValueError, OverflowError) as error:
                raise self._error(token, f"{callee.name}(): {error}") from error
        if isinstance(callee, NativeFunction):
            try:
                return self.memory.track(callee(*arguments))
            except (TypeError, ValueError, OSError, RuntimeError) as error:
                raise self._error(token, f"native call {callee.symbol} failed: {error}") from error
        if getattr(callee, "__reaper_bytecode__", False):
            if self._active_vm is None:
                raise self._error(token, "bytecode function called outside the virtual machine")
            return self.memory.track(self._active_vm.call_function(callee, arguments, token))
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
            self.call_stack.append(callee.name)
            try:
                try:
                    return self.memory.track(self._execute_block(callee.body, local, create_scope=False))
                except _ReturnSignal as signal:
                    return self.memory.track(signal.value)
            finally:
                self.call_stack.pop()
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
                raise ValueError(                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            return size

        def integer(value: Any, label: str) -> int:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{label} must be a whole number")
            return value

        def euclidean_divmod(dividend: Any, divisor: Any) -> list[int]:
            dividend = integer(dividend, "dividend")
            divisor = integer(divisor, "divisor")
            if divisor == 0:
                raise ValueError("division by zero")
            quotient, remainder = divmod(dividend, abs(divisor))
            if divisor < 0:
                quotient = -quotient
            return [quotient, remainder]

        def partition(values: Any, count: Any) -> list[Any]:
            values = sequence(values)
            count = integer(count, "partition count")
            if count < 1:
                raise ValueError("partition count must be positive")
            if count > self.max_collection_items:
                raise ValueError(
                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            total = len(values)
            base, extra = divmod(total, count)
            result: list[Any] = []
            offset = 0
            for index in range(count):
                width = base + (1 if index < extra else 0)
                piece = values[offset:offset + width]
                result.append(piece if isinstance(values, str) else list(piece))
                offset += width
            return result

        def distribute(total: Any, count: Any) -> list[int]:
            total = integer(total, "total")
            count = integer(count, "distribution count")
            if count < 1:
                raise ValueError("distribution count must be positive")
            if count > self.max_collection_items:
                raise ValueError(
                    f"collection item limit ({self.max_collection_items}) exceeded"
                )
            quotient, remainder = euclidean_divmod(total, count)
            return [
                quotient + (1 if index < remainder else 0)
                for index in range(count)
            ]

        def proportional_split(total: Any, weights: Any) -> list[int]:
            total = integer(total, "total")
            if total < 0:
                raise ValueError("proportional total cannot be negative")
            weights = sequence(weights)
            if isinstance(weights, str) or not weights:
                raise TypeError("weights must be a non-empty list of whole numbers")
            normalized = [integer(weight, "weight") for weight in weights]
            if any(weight < 0 for weight in normalized):
                raise ValueError("weights must be non-negative")
            weight_sum = sum(normalized)
            if weight_sum == 0:
                raise ValueError("at least one weight must be positive")
            products = [total * weight for weight in normalized]
            allocations = [product // weight_sum for product in products]
            remainders = [product % weight_sum for product in products]
            undistributed = total - sum(allocations)
            priority = sorted(
                range(len(normalized)),
                key=lambda index: (-remainders[index], index),
            )
            for index in priority[:undistributed]:
                allocations[index] += 1
            return allocations

        def callback(value: Any) -> None:
            if not isinstance(value, (UserFunction, Builtin, NativeFunction)) and not getattr(value, "__reaper_bytecode__", False):
                raise TypeError("expected a Reaper function")

        def iterate(seed: Any, steps: Any, function: Any) -> list[Any]:
            callback(function)
            if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
                raise ValueError("iterate steps must be a non-negative whole number")
            if steps + 1 > self.max_collection_items:
                raise ValueError(f"collection item limit ({self.max_collection_items}) exceeded")
            token = Token("BUILTIN", "iterate", 1, 1)
            history = [seed]
            value = seed
            for _ in range(steps):
                self._tick(token)
                value = self._call(function, [value], token)
                history.append(value)
            return history

        register("divmod_euclidean", euclidean_divmod, 2, 2)
        register("euclidean_divmod", euclidean_divmod, 2, 2)
        register("quotient", lambda dividend, divisor: euclidean_divmod(dividend, divisor)[0], 2, 2)
        register("remainder", lambda dividend, divisor: euclidean_divmod(dividend, divisor)[1], 2, 2)
        register("is_divisible", lambda dividend, divisor: euclidean_divmod(dividend, divisor)[1] == 0, 2, 2)
        register("partition", partition, 2, 2)
        register("distribute", distribute, 2, 2)
        register("proportional_split", proportional_split, 2, 2)
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
        register("token_catalog", lambda *group: token_catalog(group[0] if group else None), 0, 1)
        register("token_info", token_info, 1, 1)
        register("token_is_reserved", token_is_reserved, 1, 1)

        def consent_check(token: Any, subject: Any, purpose: Any, scope: Any) -> bool:
            if self.consent_authority is None:
                raise ReaperRuntimeError(
                    "consent_check requires a host-injected ConsentAuthority"
                )
            if not all(isinstance(value, str) for value in (subject, purpose, scope)):
                raise TypeError("consent_check subject, purpose and scope must be text")
            return self.consent_authority.verify(
                token, subject=subject, purpose=purpose, scope=scope
            )

        def consent_revoke(token: Any) -> bool:
            if self.consent_authority is None:
                raise ReaperRuntimeError(
                    "consent_revoke requires a host-injected ConsentAuthority"
                )
            return self.consent_authority.revoke(token)

        register("consent_check", consent_check, 4, 4)
        register("consent_revoke", consent_revoke, 1, 1)

        def script_directory() -> Path:
            if self.filename.startswith("<") and self.filename.endswith(">"):
                return Path.cwd()
            return Path(self.filename).resolve().parent

        def open_file(path: Any, mode: Any = "r") -> ResourceHandle:
            if not isinstance(path, str) or not isinstance(mode, str):
                raise TypeError("file_open expects text path and mode")
            return self.resources.open_text(path, mode, script_directory())

        def with_file(path: Any, mode: Any, function: Any) -> Any:
            callback(function)
            handle = open_file(path, mode)
            try:
                return self._call(function, [handle], Token("BUILTIN", "with_file", 1, 1))
            finally:
                self.resources.close(handle)

        def ffi_open(path: Any) -> CAbiLibrary:
            if not self.allow_native_ffi:
                raise ValueError("native FFI is disabled; run with --allow-native-ffi")
            if not isinstance(path, str):
                raise TypeError("ffi_open expects a native library path")
            library = CAbiLibrary(path)
            self._ffi_libraries.append(library)
            return library

        def ffi_bind(library: Any, symbol: Any, result_type: Any, argument_types: Any = "") -> NativeFunction:
            if not isinstance(library, CAbiLibrary):
                raise TypeError("ffi_bind expects a library returned by ffi_open")
            if not all(isinstance(value, str) for value in (symbol, result_type, argument_types)):
                raise TypeError("ffi_bind symbol and type signatures must be text")
            return library.bind(symbol, result_type, argument_types)

        def pytyliki_open(path: Any) -> PytylikiBridge:
            if not self.allow_native_ffi:
                raise ValueError("native FFI is disabled; run with --allow-native-ffi")
            if not isinstance(path, str):
                raise TypeError("pytyliki_open expects a native library path")
            bridge = PytylikiBridge(path)
            self._ffi_libraries.append(bridge)
            return bridge

        def ffi_close(library: Any) -> None:
            if not isinstance(library, (CAbiLibrary, PytylikiBridge)):
                raise TypeError("ffi_close expects a handle returned by ffi_open or pytyliki_open")
            library.close()

        register("file_open", open_file, 1, 2)
        register("file_read", self.resources.read, 1, 1)
        register("file_write", self.resources.write, 2, 2)
        register("file_close", self.resources.close, 1, 1)
        register("with_file", with_file, 3, 3)
        register("resource_stats", self.resources.stats, 0, 0)
        register("heap_stats", self.memory.stats, 0, 0)
        register("heap_collect", lambda: self.memory.collect(self._memory_roots()), 0, 0)
        register("region_begin", self.memory.begin_region, 0, 0)
        register("region_end", lambda token: self.memory.end_region(token, self._memory_roots()), 1, 1)
        register("ffi_open", ffi_open, 1, 1)
        register("ffi_bind", ffi_bind, 3, 4)
        register("ffi_close", ffi_close, 1, 1)
        register("pytyliki_open", pytyliki_open, 1, 1)
        register(
            "pytyliki_bridge_norm",
            lambda values, bridge: self._require_pytyliki(bridge).norm(values),
            2, 2,
        )
        register(
            "pytyliki_bridge_dot",
            lambda left, right, bridge: self._require_pytyliki(bridge).dot(left, right),
            3, 3,
        )
        register(
            "pytyliki_bridge_distance",
            lambda left, right, bridge: self._require_pytyliki(bridge).distance(left, right),
            3, 3,
        )
        register(
            "pytyliki_bridge_orthogonal",
            lambda left, right, tolerance, bridge: self._require_pytyliki(bridge).orthogonal(
                left, right, tolerance
            ),
            4, 4,
        )

        def pytyliki_embedded_profiles(path: Any) -> list[dict[str, Any]]:
            if not self.allow_native_ffi:
                raise ValueError("native FFI is disabled; run with --allow-native-ffi")
            if not isinstance(path, str):
                raise TypeError("pytyliki_embedded_profiles expects an explicit library path")
            return pytyliki_native.pytyliki_embedded_profiles(path)

        def pytyliki_embedded_budget(
            profile_id: Any, text_bytes: Any, rodata_bytes: Any, data_bytes: Any,
            bss_bytes: Any, noinit_bytes: Any, stack_reserve_bytes: Any, path: Any
        ) -> dict[str, Any]:
            if not self.allow_native_ffi:
                raise ValueError("native FFI is disabled; run with --allow-native-ffi")
            if not isinstance(profile_id, str) or not isinstance(path, str):
                raise TypeError("pytyliki_embedded_budget expects a profile id and an explicit library path")
            sections = {
                "text_bytes": text_bytes,
                "rodata_bytes": rodata_bytes,
                "data_bytes": data_bytes,
                "bss_bytes": bss_bytes,
                "noinit_bytes": noinit_bytes,
                "stack_reserve_bytes": stack_reserve_bytes,
            }
            return pytyliki_native.pytyliki_embedded_budget(profile_id, sections, path)

        register("pytyliki_embedded_profiles", pytyliki_embedded_profiles, 1, 1)
        register("pytyliki_embedded_budget", pytyliki_embedded_budget, 8, 8)

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

        # Bounded arithmetic and sequence-composition primitives.
        register("multiply", arithmetic.multiply, 2, 2)
        register("product", lambda values: arithmetic.product(sequence(values)), 1, 1)
        register("compute", arithmetic.compute, 2, 3)
        register("calculate", arithmetic.compute, 2, 3)
        register("scale_values", lambda values, factor: arithmetic.scale(sequence(values), factor), 2, 2)
        register("amplify", arithmetic.amplify, 2, 2)
        register("compound", lambda left, right: arithmetic.compound(sequence(left), sequence(right)), 2, 2)
        register("expand", lambda values, count: arithmetic.expand(sequence(values), count), 2, 2)
        register("accumulate", lambda values: arithmetic.accumulate(sequence(values)), 1, 1)
        register("iterate", iterate, 3, 3)
        register("cross_multiply", lambda left, right: arithmetic.cross_multiply(sequence(left), sequence(right)), 2, 2)
        register("exponentiate", arithmetic.exponentiate, 2, 2)
        register("factorize", arithmetic.factor, 1, 1)
        register("combine", lambda left, right: arithmetic.combine(sequence(left), sequence(right)), 2, 2)
        register("fuse", lambda left, right: arithmetic.fuse(sequence(left), sequence(right)), 2, 2)
        register("aggregate", lambda values: arithmetic.aggregate(sequence(values)), 1, 1)
        register("pair", arithmetic.pair, 2, 2)
        register("couple", lambda left, right: arithmetic.couple(sequence(left), sequence(right)), 2, 2)
        register("convolve", lambda signal, kernel: arithmetic.convolve(sequence(signal), sequence(kernel)), 2, 2)
        register("cartesianize", lambda left, right: arithmetic.cartesianize(sequence(left), sequence(right)), 2, 2)
        from .federation import read_json, write_json, oplage_metrics, compare_oplage_snapshots
        from .gpu_telemetry import normalize_oplage_gpu_snapshot, load_oplage_gpu_snapshot
        from .ventusample import ventusample_metrics, compare_ventusample_packs
        from .native import pytyliki_norm, pytyliki_dot, pytyliki_distance, pytyliki_orthogonal
        register("read_json", read_json, 1, 1)
        register("write_json", write_json, 2, 2)
        register("oplage_metrics", oplage_metrics, 1, 1)
        register("oplage_compare", compare_oplage_snapshots, 2, 3)
        register("oplage_gpu_normalize", normalize_oplage_gpu_snapshot, 1, 1)
        register("oplage_gpu_load", load_oplage_gpu_snapshot, 1, 1)
        register("ventusample_metrics", ventusample_metrics, 1, 1)
        register("ventusample_compare", compare_ventusample_packs, 2, 2)
        register("pytyliki_norm", pytyliki_norm, 2, 2)
        register("pytyliki_dot", pytyliki_dot, 3, 3)
        register("pytyliki_distance", pytyliki_distance, 3, 3)
        register("pytyliki_orthogonal", pytyliki_orthogonal, 4, 4)

    @staticmethod
    def _require_pytyliki(value: Any) -> PytylikiBridge:
        if not isinstance(value, PytylikiBridge):
            raise TypeError("expected a Pytyliki bridge returned by pytyliki_open")
        return value

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
        if isinstance(value, (UserFunction, Builtin, NativeFunction)) or getattr(value, "__reaper_bytecode__", False):
            return "craft"
        if isinstance(value, ResourceHandle):
            return "resource"
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