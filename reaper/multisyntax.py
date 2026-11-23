"""Multi-syntax execution frontends for Reaper.

The registry keeps Reaper's native language intact while adding bounded,
isolated frontends for a documented Python subset, data pipelines, Lisp,
Forth, Brainfuck and Befunge-93. Polyglot files execute named blocks in source
order. No frontend delegates learner code to Python exec/eval or a shell.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

MAX_SOURCE_CHARS = 1_000_000
MAX_COLLECTION_ITEMS = 100_000
MAX_POLYGLOT_BLOCKS = 128
POLYGLOT_HEADER = re.compile(r"^\s*%%\s+([a-z][a-z0-9_-]*)(?:\s+as\s+[A-Za-z_][A-Za-z0-9_]*)?\s*$", re.I)


class MultiSyntaxError(ValueError):
    """A syntax, validation or execution error from a registered frontend."""


@dataclass(frozen=True, slots=True)
class SyntaxSpec:
    name: str
    paradigm: str
    description: str
    status: str
    extensions: tuple[str, ...]


@dataclass(slots=True)
class _Budget:
    limit: int
    steps: int = 0

    def tick(self, amount: int = 1) -> None:
        self.steps += amount
        if self.steps > self.limit:
            raise MultiSyntaxError(f"execution step limit ({self.limit}) exceeded")


SPECS = (
    SyntaxSpec("reaper", "structured / flow-first", "Native Reaper syntax and runtime.", "native", (".rpr",)),
    SyntaxSpec("python", "imperative / dynamic", "A safe, documented Python-like subset; not CPython.", "implemented_subset", (".py",)),
    SyntaxSpec("pipeline", "functional / dataflow", "Left-to-right |> and -> data transformation chains.", "implemented_subset", (".pipe", ".ppl")),
    SyntaxSpec("lisp", "homoiconic / functional", "Small S-expression language with lexical closures and list primitives.", "implemented_subset", (".lisp", ".lsp", ".scm")),
    SyntaxSpec("forth", "concatenative / stack", "Bounded Forth-style data and return stacks with colon definitions.", "implemented_subset", (".forth", ".fs")),
    SyntaxSpec("brainfuck", "minimal / tape machine", "Eight-command Brainfuck with validated loops and bounded tape.", "implemented", (".bf", ".b")),
    SyntaxSpec("befunge93", "two-dimensional / self-modifying", "Bounded Befunge-93 grid, stack, directions and playfield writes.", "implemented_subset", (".bf93", ".befunge")),
)

ALIASES = {
    "native": "reaper", "rpr": "reaper", "py": "python",
    "pipe": "pipeline", "dataflow": "pipeline",
    "scheme": "lisp", "sexpr": "lisp", "s-expression": "lisp",
    "stack": "forth", "bf": "brainfuck", "brain-fuck": "brainfuck",
    "befunge": "befunge93", "befunge-93": "befunge93",
}


def list_syntaxes() -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "paradigm": item.paradigm,
            "description": item.description,
            "status": item.status,
            "extensions": list(item.extensions),
        }
        for item in SPECS
    ]


def normalize_syntax(name: str) -> str:
    value = str(name or "").strip().casefold()
    value = ALIASES.get(value, value)
    if value not in {item.name for item in SPECS}:
        raise MultiSyntaxError(f"unknown syntax {name!r}; available: {', '.join(item.name for item in SPECS)}")
    return value


def detect_syntax(filename: str | Path, explicit: str = "auto", source: str = "") -> str:
    if explicit.casefold() != "auto":
        return normalize_syntax(explicit)
                marker = re.match(r"\s*#!syntax\s+[a-z0-9_-]+\s*(?:\n|$)", source, re.I)
    if marker:
        return normalize_syntax(marker.group(1))
    suffix = Path(filename).suffix.casefold()
    for spec in SPECS:
        if suffix in spec.extensions:
            return spec.name
    return "reaper"


def _text(value: Any) -> str:
    if value is None:
        return "None"
    if value is True:
        return "True"
    if value is False:
        return "False"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_text(item) for item in value) + "]"
    return str(value)


class _ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class _BreakSignal(Exception):
    pass


class _ContinueSignal(Exception):
    pass


@dataclass(slots=True)
class _PythonFunction:
    interpreter: "_PythonSubset"
    node: ast.FunctionDef | ast.Lambda
    closure: list[dict[str, Any]]

    def __call__(self, *arguments: Any, **keywords: Any) -> Any:
        return self.interpreter.call_function(self, arguments, keywords)


class _PythonSubset:
    """Interpreter for a strict AST whitelist; never calls Python exec/eval."""

    _binary = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
    }
    _unary = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
    _compare = {
        ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
        ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.In: lambda left, right: left in right,
        ast.NotIn: lambda left, right: left not in right,
        ast.Is: operator.is_, ast.IsNot: operator.is_not,
    }
    _annotations = {"int", "float", "str", "bool", "list", "tuple", "dict", "set", "Any", "object"}

    def __init__(self, source: str, filename: str, output: Callable[[str], None], budget: _Budget):
        self.source = source
        self.filename = filename
        self.output = output
        self.budget = budget
        self.scopes: list[dict[str, Any]] = [{}]
        self.collection_limit = MAX_COLLECTION_ITEMS
        self._install_builtins()

    def _install_builtins(self) -> None:
        def emit(*values: Any, sep: str = " ", end: str = "\n") -> None:
            if len(values) > 128:
                raise MultiSyntaxError("print accepts at most 128 values")
            self.output(sep.join(_text(value) for value in values) + end)

        builtins: dict[str, Any] = {
            "print": emit, "len": len, "range": range, "sum": sum,
            "min": min, "max": max, "abs": abs, "round": round,
            "str": str, "int": int, "float": float, "bool": bool,
            "list": list, "tuple": tuple, "set": set, "dict": dict,
            "sorted": sorted, "reversed": reversed, "enumerate": enumerate,
            "zip": zip, "any": any, "all": all,
        }
        self.scopes[0].update(builtins)

    def lookup(self, name: str) -> Any:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise MultiSyntaxError(f"{self.filename}: unknown name {name!r}")

    def _store(self, name: str, value: Any) -> None:
        self.scopes[-1][name] = value

    def _bounded(self, value: Any) -> Any:
        if isinstance(value, (list, tuple, set, dict, range)) and len(value) > self.collection_limit:
            raise MultiSyntaxError("collection item limit exceeded")
        return value

    def evaluate(self, node: ast.AST) -> Any:
        self.budget.tick()
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (str, int, float, bool, type(None))):
                raise MultiSyntaxError("only string, numeric, boolean and None literals are supported")
            if isinstance(node.value, float) and not math.isfinite(node.value):
                raise MultiSyntaxError("non-finite numeric literals are not supported")
            return node.value
        if isinstance(node, ast.Name):
            return self.lookup(node.id)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values = [self.evaluate(item) for item in node.elts]
            self._bounded(values)
            if isinstance(node, ast.List): return values
            if isinstance(node, ast.Tuple): return tuple(values)
            return set(values)
        if isinstance(node, ast.Dict):
            if len(node.keys) > self.collection_limit:
                raise MultiSyntaxError("dictionary item limit exceeded")
            return {self.evaluate(key): self.evaluate(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.BinOp) and type(node.op) in self._binary:
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)) and abs(right) > 10_000:
                raise MultiSyntaxError("power exponent exceeds the safe limit")
            return self._bounded(self._binary[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._unary:
            return self._unary[type(node.op)](self.evaluate(node.operand))
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                value = self.evaluate(node.values[0])
                for child in node.values[1:]:
                    if not value: return value
                    value = self.evaluate(child)
                return value
            if isinstance(node.op, ast.Or):
                value = self.evaluate(node.values[0])
                for child in node.values[1:]:
                    if value: return value
                    value = self.evaluate(child)
                return value
        if isinstance(node, ast.Compare):
            left = self.evaluate(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                if type(operation) not in self._compare:
                    raise MultiSyntaxError("comparison operator is not supported")
                right = self.evaluate(comparator)
                if not self._compare[type(operation)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self.evaluate(node.body if self.evaluate(node.test) else node.orelse)
        if isinstance(node, ast.Subscript):
            return self.evaluate(node.value)[self.evaluate(node.slice)]
        if isinstance(node, ast.Slice):
            return slice(
                self.evaluate(node.lower) if node.lower else None,
                self.evaluate(node.upper) if node.upper else None,
                self.evaluate(node.step) if node.step else None,
            )
        if isinstance(node, ast.Call):
            function = self.evaluate(node.func)
            if not callable(function):
                raise MultiSyntaxError("attempted to call a non-callable value")
            if any(keyword.arg is None for keyword in node.keywords):
                raise MultiSyntaxError("argument unpacking is not supported")
            arguments = [self.evaluate(item) for item in node.args]
            keywords = {item.arg: self.evaluate(item.value) for item in node.keywords}
            try:
                return self._bounded(function(*arguments, **keywords))
            except MultiSyntaxError:
                raise
            except (TypeError, ValueError, ZeroDivisionError, OverflowError, KeyError, IndexError) as error:
                raise MultiSyntaxError(f"call failed: {error}") from error
        if isinstance(node, ast.Lambda):
            return _PythonFunction(self, node, list(self.scopes))
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                parts.append(value.value if isinstance(value, ast.Constant) else _text(self.evaluate(value.value)))
            return "".join(parts)
        if isinstance(node, ast.FormattedValue):
            return self.evaluate(node.value)
        raise MultiSyntaxError(f"Python subset does not support {type(node).__name__}")

    def _check_annotation(self, annotation: ast.AST | None) -> None:
        if annotation is None:
            return
        if isinstance(annotation, ast.Name) and annotation.id in self._annotations:
            return
        if isinstance(annotation, ast.Constant) and annotation.value == "Any":
            return
        if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
            if annotation.value.id in {"list", "tuple", "dict", "set"}:
                return
        raise MultiSyntaxError("only built-in boundary annotations (int/float/str/bool/list/dict/tuple/set/Any) are supported")

    def run(self) -> Any:
        if len(self.source) > MAX_SOURCE_CHARS:
            raise MultiSyntaxError("source exceeds the 1,000,000-character limit")
        try:
            tree = ast.parse(self.source, filename=self.filename, mode="exec")
        except SyntaxError as error:
            raise MultiSyntaxError(f"{self.filename}:{error.lineno}:{error.offset}: {error.msg}") from error
        except RecursionError as error:
            raise MultiSyntaxError("Python syntax nesting limit exceeded") from error
        return self.execute_block(tree.body)

    def call_function(self, function: _PythonFunction, arguments: tuple[Any, ...], keywords: dict[str, Any]) -> Any:
        node = function.node
        args = node.args
        if args.vararg or args.kwarg or args.kwonlyargs or args.posonlyargs:
            raise MultiSyntaxError("variadic, keyword-only and positional-only function parameters are not supported")
        parameters = [item.arg for item in args.args]
        defaults = [self.evaluate(item) for item in args.defaults]
        required = len(parameters) - len(defaults)
        if len(arguments) < required or len(arguments) > len(parameters):
            raise MultiSyntaxError(f"function expects {required}..{len(parameters)} arguments")
        if set(keywords) - set(parameters):
            raise MultiSyntaxError("unknown keyword argument")
        values = dict(zip(parameters, arguments))
        offset = len(parameters) - len(defaults)
        for parameter, default in zip(parameters[offset:], defaults):
            values.setdefault(parameter, default)
        values.update(keywords)
        for parameter in args.args:
            self._check_annotation(parameter.annotation)
        self._check_annotation(node.returns if isinstance(node, ast.FunctionDef) else None)
        previous = self.scopes
        self.scopes = [*function.closure, values]
        try:
            if isinstance(node, ast.Lambda):
                return self.evaluate(node.body)
            self.execute_block(node.body)
            return None
        except _ReturnSignal as signal:
            return signal.value
        finally:
            self.scopes = previous

    def _assign(self, target: ast.AST, value: Any) -> None:
        self.budget.tick()
        if isinstance(target, ast.Name):
            self._store(target.id, value)
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            try:
                values = list(value)
            except TypeError as error:
                raise MultiSyntaxError("cannot destructure a non-iterable value") from error
            if len(values) != len(target.elts):
                raise MultiSyntaxError("destructuring length mismatch")
            for child, item in zip(target.elts, values):
                self._assign(child, item)
            return
        if isinstance(target, ast.Subscript):
            container = self.evaluate(target.value)
            container[self.evaluate(target.slice)] = value
            return
        raise MultiSyntaxError(f"assignment to {type(target).__name__} is not supported")

    def _matches(self, pattern: ast.pattern, value: Any) -> tuple[bool, dict[str, Any]]:
        if isinstance(pattern, ast.MatchAs):
            if pattern.pattern is None:
                return True, {pattern.name: value} if pattern.name else {}
            matched, bindings = self._matches(pattern.pattern, value)
            if matched and pattern.name:
                bindings[pattern.name] = value
            return matched, bindings
        if isinstance(pattern, ast.MatchValue):
            return value == self.evaluate(pattern.value), {}
        if isinstance(pattern, ast.MatchSingleton):
            return value is pattern.value, {}
        if isinstance(pattern, ast.MatchSequence):
            if not isinstance(value, (list, tuple)) or len(value) != len(pattern.patterns):
                return False, {}
            bindings: dict[str, Any] = {}
            for item_pattern, item in zip(pattern.patterns, value):
                matched, found = self._matches(item_pattern, item)
                if not matched: return False, {}
                bindings.update(found)
            return True, bindings
        if isinstance(pattern, ast.MatchOr):
            for item in pattern.patterns:
                matched, bindings = self._matches(item, value)
                if matched: return True, bindings
            return False, {}
        raise MultiSyntaxError("only literal, wildcard, capture, sequence and OR match patterns are supported")

    def execute_block(self, statements: list[ast.stmt]) -> Any:
        result = None
        for statement in statements:
            result = self.execute_statement(statement)
        return result

    def execute_statement(self, node: ast.stmt) -> Any:
        self.budget.tick()
        if isinstance(node, ast.Expr):
            return self.evaluate(node.value)
        if isinstance(node, ast.Assign):
            value = self.evaluate(node.value)
            for target in node.targets: self._assign(target, value)
            return value
        if isinstance(node, ast.AnnAssign):
            self._check_annotation(node.annotation)
            if node.value is not None:
                value = self.evaluate(node.value)
                self._assign(node.target, value)
                return value
            return None
        if isinstance(node, ast.AugAssign):
            if not isinstance(node.target, ast.Name):
                raise MultiSyntaxError("augmented assignment currently requires a name")
            operation = self._binary.get(type(node.op))
            if operation is None: raise MultiSyntaxError("augmented operator is not supported")
            value = operation(self.lookup(node.target.id), self.evaluate(node.value))
            self._store(node.target.id, value)
            return value
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list:
                raise MultiSyntaxError("decorators are not enabled in the safe Python subset")
            self._check_annotation(node.returns)
            function = _PythonFunction(self, node, list(self.scopes))
            self._store(node.name, function)
            return function
        if isinstance(node, ast.Return):
            raise _ReturnSignal(self.evaluate(node.value) if node.value else None)
        if isinstance(node, ast.If):
            return self.execute_block(node.body if self.evaluate(node.test) else node.orelse)
        if isinstance(node, ast.While):
            result = None
            broke = False
            while self.evaluate(node.test):
                self.budget.tick()
                try:
                    result = self.execute_block(node.body)
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    broke = True
                    break
            if node.orelse and not broke:
                result = self.execute_block(node.orelse)
            return result
        if isinstance(node, ast.For):
            iterable = self.evaluate(node.iter)
            try:
                if len(iterable) > self.collection_limit:
                    raise MultiSyntaxError("for-loop iterable exceeds the collection limit")
            except TypeError:
                iterable = list(iterable)
                if len(iterable) > self.collection_limit:
                    raise MultiSyntaxError("for-loop iterable exceeds the collection limit")
            result = None
            broke = False
            for item in iterable:
                self.budget.tick()
                self._assign(node.target, item)
                try:
                    result = self.execute_block(node.body)
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    broke = True
                    break
            if node.orelse and not broke:
                result = self.execute_block(node.orelse)
            return result
        if isinstance(node, ast.Match):
            subject = self.evaluate(node.subject)
            for case in node.cases:
                matched, bindings = self._matches(case.pattern, subject)
                if matched:
                    self.scopes.append(bindings)
                    try:
                        if case.guard is None or self.evaluate(case.guard):
                            return self.execute_block(case.body)
                    finally:
                        self.scopes.pop()
            return None
        if isinstance(node, ast.Break):
            raise _BreakSignal()
        if isinstance(node, ast.Continue):
            raise _ContinueSignal()
        if isinstance(node, ast.Assert):
            if not self.evaluate(node.test):
                detail = self.evaluate(node.msg) if node.msg else "assertion failed"
                raise MultiSyntaxError(_text(detail))
            return None
        if isinstance(node, ast.Pass):
            return None
        raise MultiSyntaxError(f"Python subset does not support statement {type(node).__name__}")


def _split_pipeline(source: str) -> list[str]:
    stages: list[str] = []
    start = depth = 0
    quote = ""
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        if quote:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == quote: quote = ""
        elif char in {"'", '"'}:
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0: raise MultiSyntaxError("unbalanced delimiter in pipeline")
        elif depth == 0 and source[index:index + 2] in {"|>", "->"}:
            stages.append(source[start:index].strip())
            start = index + 2
            index += 1
        index += 1
    if quote or depth != 0:
        raise MultiSyntaxError("unterminated quote or unbalanced delimiter in pipeline")
    stages.append(source[start:].strip())
    if len(stages) < 2 or any(not item for item in stages):
        raise MultiSyntaxError("pipeline requires a value and at least one non-empty stage")
    return stages


def _run_pipeline(source: str, output: Callable[[str], None], budget: _Budget) -> Any:
    stages = _split_pipeline(source)
    evaluator = _PythonSubset("", "<pipeline>", output, budget)
    try:
        value = evaluator.evaluate(ast.parse(stages[0], mode="eval").body)
    except SyntaxError as error:
        raise MultiSyntaxError(f"invalid pipeline input expression: {error.msg}") from error
    for stage in stages[1:]:
        budget.tick()
        try:
            expression = ast.parse(stage, mode="eval").body
        except SyntaxError as error:
            raise MultiSyntaxError(f"invalid pipeline stage {stage!r}: {error.msg}") from error
        if isinstance(expression, ast.Name):
            name, arguments = expression.id, []
        elif isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name):
            name = expression.func.id
            arguments = [evaluator.evaluate(item) for item in expression.args]
            if expression.keywords:
                raise MultiSyntaxError("pipeline stages do not accept keyword arguments")
        else:
            raise MultiSyntaxError("pipeline stages must be a function name or a function call")
        if name == "upper": value = str(value).upper()
        elif name == "lower": value = str(value).lower()
        elif name == "trim": value = str(value).strip()
        elif name == "reverse": value = value[::-1]
        elif name == "sort": value = sorted(value)
        elif name == "unique": value = list(dict.fromkeys(value))
        elif name == "sum": value = sum(value)
        elif name == "count": value = len(value)
        elif name == "join": value = str(arguments[0] if arguments else "").join(_text(item) for item in value)
        elif name == "split": value = str(value).split(arguments[0] if arguments else None)
        elif name == "take": value = list(value)[:int(arguments[0])]
        elif name == "drop": value = list(value)[int(arguments[0]):]
        elif name in {"map", "filter"}:
            if len(arguments) != 1 or not callable(arguments[0]):
                raise MultiSyntaxError(f"{name} requires one lambda/function argument")
            value = list(map(arguments[0], value)) if name == "map" else list(filter(arguments[0], value))
        elif name == "add":
            if len(arguments) != 1: raise MultiSyntaxError("add requires one argument")
            value = value + arguments[0]
        elif name == "multiply":
            if len(arguments) != 1: raise MultiSyntaxError("multiply requires one argument")
            value = value * arguments[0]
        elif name == "emit":
            output(_text(value))
        else:
            raise MultiSyntaxError(f"unknown pipeline operation {name!r}")
        if isinstance(value, (list, tuple, dict, str)) and len(value) > MAX_COLLECTION_ITEMS:
            raise MultiSyntaxError("pipeline result exceeds the collection limit")
    return value


@dataclass(frozen=True, slots=True)
class _Symbol:
    value: str


@dataclass(slots=True)
class _LispFunction:
    parameters: list[str]
    body: list[Any]
    closure: dict[str, Any]


def _read_lisp(source: str) -> list[Any]:
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+', source)
    result: list[Any] = []
    stack: list[list[Any]] = []
    current = result
    for token in tokens:
        if token == "(":
            if len(stack) >= 256:
                raise MultiSyntaxError("Lisp nesting limit (256) exceeded")
            child: list[Any] = []
            current.append(child)
            stack.append(current)
            current = child
        elif token == ")":
            if not stack: raise MultiSyntaxError("unexpected ')' in Lisp source")
            current = stack.pop()
        elif token.startswith('"'):
            try: current.append(json.loads(token))
            except json.JSONDecodeError as error: raise MultiSyntaxError("invalid Lisp string literal") from error
        elif re.fullmatch(r"-?(?:\d+\.\d+|\d+)", token):
            current.append(float(token) if "." in token else int(token))
        elif token in {"#t", "true"}: current.append(True)
        elif token in {"#f", "false"}: current.append(False)
        elif token in {"nil", "null"}: current.append(None)
        else: current.append(_Symbol(token))
    if stack: raise MultiSyntaxError("unclosed '(' in Lisp source")
    return result


def _run_lisp(source: str, output: Callable[[str], None], budget: _Budget) -> Any:
    environment: dict[str, Any] = {}

    def display(value: Any) -> str:
        if isinstance(value, _Symbol): return value.value
        if isinstance(value, list): return "(" + " ".join(display(item) for item in value) + ")"
        if value is True: return "#t"
        if value is False: return "#f"
        if value is None: return "nil"
        return str(value)

    environment.update({
        "+": lambda *items: sum(items),
        "-": lambda first, *rest: -first if not rest else first - sum(rest),
        "*": lambda *items: math.prod(items),
        "/": lambda first, *rest: math.prod([first]) / math.prod(rest) if rest else 1 / first,
        "=": lambda left, right: left == right,
        "<": lambda left, right: left < right,
        "<=": lambda left, right: left <= right,
        ">": lambda left, right: left > right,
        ">=": lambda left, right: left >= right,
        "list": lambda *items: list(items),
        "car": lambda items: items[0] if items else None,
        "cdr": lambda items: items[1:] if items else [],
        "cons": lambda item, items: [item, *items],
        "length": len,
        "append": lambda left, right: [*left, *right],
        "not": lambda value: not value,
        "display": lambda value: output(display(value)),
        "newline": lambda: output(""),
        "map": lambda function, items: [function(item) for item in items],
        "filter": lambda function, items: [item for item in items if function(item)],
        "fold": lambda function, initial, items: _fold(function, initial, items),
    })

    def evaluate(expression: Any, scope: dict[str, Any]) -> Any:
        budget.tick()
        if isinstance(expression, _Symbol):
            if expression.value not in scope: raise MultiSyntaxError(f"unknown Lisp symbol {expression.value!r}")
            return scope[expression.value]
        if not isinstance(expression, list): return expression
        if not expression: return []
        head = expression[0]
        if isinstance(head, _Symbol):
            operation = head.value
            if operation == "quote":
                if len(expression) != 2: raise MultiSyntaxError("quote expects one expression")
                return expression[1]
            if operation == "if":
                if len(expression) not in {3, 4}: raise MultiSyntaxError("if expects 2 or 3 branches")
                condition = evaluate(expression[1], scope)
                return evaluate(expression[2] if condition else expression[3], scope) if condition or len(expression) == 4 else None
            if operation == "begin":
                result = None
                for item in expression[1:]: result = evaluate(item, scope)
                return result
            if operation == "define":
                if len(expression) < 3: raise MultiSyntaxError("define expects a name and value")
                target = expression[1]
                if isinstance(target, list) and target and isinstance(target[0], _Symbol):
                    name = target[0].value
                    function = _LispFunction([item.value for item in target[1:]], expression[2:], scope)
                    scope[name] = function
                    return function
                if not isinstance(target, _Symbol) or len(expression) != 3: raise MultiSyntaxError("invalid define form")
                scope[target.value] = evaluate(expression[2], scope)
                return scope[target.value]
            if operation == "lambda":
                if len(expression) < 3 or not isinstance(expression[1], list):
                    raise MultiSyntaxError("lambda expects a parameter list and body")
                if any(not isinstance(item, _Symbol) for item in expression[1]):
                    raise MultiSyntaxError("lambda parameter names must be symbols")
                return _LispFunction([item.value for item in expression[1]], expression[2:], scope)
            if operation == "let":
                if len(expression) < 3 or not isinstance(expression[1], list):
                    raise MultiSyntaxError("let expects bindings and a body")
                local = dict(scope)
                for pair in expression[1]:
                    if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], _Symbol):
                        raise MultiSyntaxError("invalid let binding")
                    local[pair[0].value] = evaluate(pair[1], local)
                result = None
                for item in expression[2:]: result = evaluate(item, local)
                return result
        function = evaluate(head, scope)
        arguments = [evaluate(item, scope) for item in expression[1:]]
        if isinstance(function, _LispFunction):
            if len(arguments) != len(function.parameters): raise MultiSyntaxError("Lisp function arity mismatch")
            local = dict(function.closure)
            local.update(zip(function.parameters, arguments))
            result = None
            for item in function.body: result = evaluate(item, local)
            return result
        if not callable(function): raise MultiSyntaxError("Lisp expression is not callable")
        try: return function(*arguments)
        except (TypeError, ValueError, ZeroDivisionError, IndexError) as error:
            raise MultiSyntaxError(f"Lisp call failed: {error}") from error

    parsed = _read_lisp(source)
    result = None
    for expression in parsed: result = evaluate(expression, environment)
    return result


def _fold(function: Callable[[Any, Any], Any], initial: Any, items: list[Any]) -> Any:
    value = initial
    for item in items: value = function(value, item)
    return value


def _run_forth(source: str, output: Callable[[str], None], budget: _Budget) -> list[Any]:
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[^\s]+', re.sub(r"\\[^\n]*", "", source))
    words: dict[str, list[str]] = {}
    data: list[Any] = []
    returns: list[Any] = []
    index = 0
    recursion = 0

    def pop() -> Any:
        if not data: raise MultiSyntaxError("Forth data stack underflow")
        return data.pop()

    def need(count: int) -> None:
        if len(data) < count: raise MultiSyntaxError(f"Forth word needs {count} stack item(s)")

    def execute(sequence: list[str]) -> None:
        nonlocal recursion
        position = 0
        while position < len(sequence):
            budget.tick()
            token = sequence[position]
            position += 1
            if token == ":":
                if position >= len(sequence): raise MultiSyntaxError("missing Forth word name after ':'")
                name = sequence[position].casefold()
                position += 1
                try: finish = sequence.index(";", position)
                except ValueError as error: raise MultiSyntaxError(f"Forth definition {name!r} is missing ';'") from error
                words[name] = sequence[position:finish]
                position = finish + 1
                continue
            if token.startswith('"'):
                try: data.append(json.loads(token))
                except json.JSONDecodeError as error: raise MultiSyntaxError("invalid Forth string literal") from error
            elif re.fullmatch(r"-?(?:\d+\.\d+|\d+)", token):
                data.append(float(token) if "." in token else int(token))
            else:
                name = token.casefold()
                if name in words:
                    recursion += 1
                    if recursion > 128: raise MultiSyntaxError("Forth word recursion limit exceeded")
                    try: execute(words[name])
                    finally: recursion -= 1
                elif name == "dup": need(1); data.append(data[-1])
                elif name == "drop": need(1); pop()
                elif name == "swap": need(2); data[-1], data[-2] = data[-2], data[-1]
                elif name == "over": need(2); data.append(data[-2])
                elif name == "rot": need(3); data[-3:] = [data[-2], data[-1], data[-3]]
                elif name == "nip": need(2); data.pop(-2)
                elif name == "tuck": need(2); data[-2:] = [data[-1], data[-2], data[-1]]
                elif name == "2dup": need(2); data.extend(data[-2:])
                elif name == "2drop": need(2); del data[-2:]
                elif name in {"+", "-", "*", "/", "mod", "=", "<", ">", "and", "or", "xor"}:
                    need(2); right, left = pop(), pop()
                    operations = {
                        "+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv,
                        "mod": operator.mod, "=": operator.eq, "<": operator.lt, ">": operator.gt,
                        "and": lambda a, b: bool(a) and bool(b), "or": lambda a, b: bool(a) or bool(b),
                        "xor": operator.xor,
                    }
                    data.append(operations[name](left, right))
                elif name == "negate": need(1); data.append(-pop())
                elif name == "abs": need(1); data.append(abs(pop()))
                elif name == "1+": need(1); data.append(pop() + 1)
                elif name == "1-": need(1); data.append(pop() - 1)
                elif name == "emit": need(1); output(chr(int(pop()) & 255))
                elif name == ".": need(1); output(_text(pop()) + " ")
                elif name == ".s": output("<" + " ".join(_text(item) for item in data) + ">")
                elif name == "cr": output("")
                elif name == ">r": need(1); returns.append(pop())
                elif name == "r>":
                    if not returns: raise MultiSyntaxError("Forth return stack underflow")
                    data.append(returns.pop())
                elif name == "r@":
                    if not returns: raise MultiSyntaxError("Forth return stack underflow")
                    data.append(returns[-1])
                elif name == "depth": data.append(len(data))
                elif name == "clear": data.clear()
                else: raise MultiSyntaxError(f"unknown Forth word {token!r}")
            if len(data) > MAX_COLLECTION_ITEMS: raise MultiSyntaxError("Forth data stack limit exceeded")

    execute(tokens)
    return data


def analyze_brainfuck(source: str) -> dict[str, Any]:
    commands = [(index, char) for index, char in enumerate(source) if char in "><+-.,[]"]
    pairs: dict[int, int] = {}
    stack: list[int] = []
    for position, (source_index, command) in enumerate(commands):
        if command == "[": stack.append(position)
        elif command == "]":
            if not stack: raise MultiSyntaxError(f"unmatched ']' at source offset {source_index}")
            opening = stack.pop()
            pairs[opening] = position
            pairs[position] = opening
    if stack:
        offset = commands[stack[-1]][0]
        raise MultiSyntaxError(f"unmatched '[' at source offset {offset}")

    pointer_prefix = [0]
    for _source_index, command in commands:
        delta = 1 if command == ">" else -1 if command == "<" else 0
        pointer_prefix.append(pointer_prefix[-1] + delta)
    warnings: list[dict[str, Any]] = []
    for opening, closing in sorted((a, b) for a, b in pairs.items() if a < b):
        displacement = pointer_prefix[closing] - pointer_prefix[opening + 1]
        if displacement:
            warnings.append({
                "code": "BF-W001",
                "opening_offset": commands[opening][0],
                "closing_offset": commands[closing][0],
                "textual_pointer_delta": displacement,
                "message": "loop body has a non-zero textual pointer displacement; verify the loop's pointer invariant",
            })
    return {
        "schema": "reaper.brainfuck-analysis.v1",
        "command_count": len(commands),
        "loop_count": sum(1 for _source_index, command in commands if command == "["),
        "loop_pairs": len(pairs) // 2,
        "pointer_balance_warnings": warnings,
        "validated": True,
    }


def _run_brainfuck(
    source: str,
    output: Callable[[str], None],
    budget: _Budget,
    input_text: str,
    tape_size: int,
    cell_bits: int,
    eof_mode: str,
) -> dict[str, Any]:
    if not 1 <= tape_size <= 1_000_000: raise MultiSyntaxError("Brainfuck tape size must be 1..1000000")
    if cell_bits not in {8, 16, 32}: raise MultiSyntaxError("Brainfuck cell width must be 8, 16 or 32 bits")
    if eof_mode not in {"zero", "keep", "max"}: raise MultiSyntaxError("Brainfuck EOF mode must be zero, keep or max")
    analysis = analyze_brainfuck(source)
    commands = [char for char in source if char in "><+-.,[]"]
    jump: dict[int, int] = {}
    stack: list[int] = []
    for index, command in enumerate(commands):
        if command == "[": stack.append(index)
        elif command == "]":
            opening = stack.pop()
            jump[opening] = index
            jump[index] = opening
    tape = [0] * tape_size
    pointer = 0
    instruction = 0
    if len(input_text) > MAX_SOURCE_CHARS:
        raise MultiSyntaxError("input text exceeds the 1,000,000-character limit")
    input_bytes = input_text.encode("utf-8")
    input_pointer = 0
    output_bytes = bytearray()
    mask = (1 << cell_bits) - 1
    while instruction < len(commands):
        budget.tick()
        command = commands[instruction]
        if command == ">":
            pointer += 1
            if pointer >= tape_size: raise MultiSyntaxError("Brainfuck pointer moved beyond the right edge of the tape")
        elif command == "<":
            pointer -= 1
            if pointer < 0: raise MultiSyntaxError("Brainfuck pointer moved left of tape cell zero")
        elif command == "+": tape[pointer] = (tape[pointer] + 1) & mask
        elif command == "-": tape[pointer] = (tape[pointer] - 1) & mask
        elif command == ".":
            output_bytes.append(tape[pointer] & 255)
        elif command == ",":
            if input_pointer < len(input_bytes):
                tape[pointer] = input_bytes[input_pointer] & mask
                input_pointer += 1
            elif eof_mode == "zero": tape[pointer] = 0
            elif eof_mode == "max": tape[pointer] = mask
        elif command == "[" and tape[pointer] == 0:
            instruction = jump[instruction]
        elif command == "]" and tape[pointer] != 0:
            instruction = jump[instruction]
        instruction += 1
    decoded = output_bytes.decode("utf-8", errors="replace")
    if decoded: output(decoded)
    return {
        "pointer": pointer,
        "nonzero_cells": sum(value != 0 for value in tape),
        "output_bytes": list(output_bytes),
        "analysis": analysis,
    }


def _run_befunge(
    source: str, output: Callable[[str], None], budget: _Budget, input_text: str,
) -> dict[str, Any]:
    rows = source.splitlines() or [""]
    if len(rows) > 25 or any(len(row) > 80 for row in rows):
        raise MultiSyntaxError("Befunge-93 playfield is limited to 80 columns by 25 rows")
    grid = [[" " for _ in range(80)] for _ in range(25)]
    for y, row in enumerate(rows):
        for x, char in enumerate(row): grid[y][x] = char
    stack: list[int] = []
    x = y = 0
    dx, dy = 1, 0
    string_mode = False
    halted = False
    outputs: list[str] = []
    deterministic_turn = 0
    input_tokens = iter(input_text.split())
    input_bytes = iter(input_text.encode("utf-8"))

    def pop() -> int:
        return stack.pop() if stack else 0

    def push(value: int) -> None:
        stack.append(int(value))
        if len(stack) > MAX_COLLECTION_ITEMS:
            raise MultiSyntaxError("Befunge stack limit exceeded")

    while not halted:
        budget.tick()
        command = grid[y][x]
        advance = True
        if string_mode and command != '"':
            push(ord(command))
        elif command.isdigit():
            push(int(command))
        elif command == '"':
            string_mode = not string_mode
        elif command == "+":
            right, left = pop(), pop(); push(left + right)
        elif command == "-":
            right, left = pop(), pop(); push(left - right)
        elif command == "*":
            right, left = pop(), pop(); push(left * right)
        elif command == "/":
            right, left = pop(), pop(); push(0 if right == 0 else int(left / right))
        elif command == "%":
            right, left = pop(), pop(); push(0 if right == 0 else left % right)
        elif command == "!": push(0 if pop() else 1)
        elif command == "`": right, left = pop(), pop(); push(1 if left > right else 0)
        elif command == ">": dx, dy = 1, 0
        elif command == "<": dx, dy = -1, 0
        elif command == "^": dx, dy = 0, -1
        elif command == "v": dx, dy = 0, 1
        elif command == "?":
            directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
            dx, dy = directions[deterministic_turn % 4]
            deterministic_turn += 1
        elif command == "_": dx, dy = ((1, 0) if pop() == 0 else (-1, 0))
        elif command == "|": dx, dy = ((0, 1) if pop() == 0 else (0, -1))
        elif command == ":": value = pop(); push(value); push(value)
        elif command == "\\": right, left = pop(), pop(); push(right); push(left)
        elif command == "$": pop()
        elif command == ".": outputs.append(str(pop()) + " ")
        elif command == ",": outputs.append(chr(pop() & 255))
        elif command == "#":
            x, y = (x + dx) % 80, (y + dy) % 25
        elif command == "p":
            row, column, value = pop(), pop(), pop()
            if not 0 <= column < 80 or not 0 <= row < 25:
                raise MultiSyntaxError("Befunge 'p' target is outside the playfield")
            grid[row][column] = chr(value & 255)
        elif command == "g":
            row, column = pop(), pop()
            if not 0 <= column < 80 or not 0 <= row < 25:
                raise MultiSyntaxError("Befunge 'g' target is outside the playfield")
            push(ord(grid[row][column]))
        elif command == "&":
            try: push(int(next(input_tokens)))
            except StopIteration: push(0)
            except ValueError as error: raise MultiSyntaxError("Befunge '&' input must be an integer") from error
        elif command == "~":
            try: push(next(input_bytes))
            except StopIteration: push(0)
        elif command == "@": halted = True; advance = False
        elif command in {" ", "\n", "\r", "\t"}: pass
        else:
            raise MultiSyntaxError(f"unsupported Befunge-93 instruction {command!r} at ({x},{y})")
        if advance: x, y = (x + dx) % 80, (y + dy) % 25
    rendered = "".join(outputs)
    if rendered: output(rendered)
    return {"x": x, "y": y, "stack": stack, "output": rendered, "halted": halted}


def run_source(
    syntax: str,
    source: str,
    *,
    filename: str = "<memory>",
    input_text: str = "",
    max_steps: int = 1_000_000,
    tape_size: int = 30_000,
    cell_bits: int = 8,
    eof_mode: str = "zero",
    output: Callable[[str], None] | None = None,
    _budget: _Budget | None = None,
) -> dict[str, Any]:
    if not isinstance(source, str) or len(source) > MAX_SOURCE_CHARS:
        raise MultiSyntaxError("source must be text no longer than 1,000,000 characters")
    selected = normalize_syntax(syntax)
    if not isinstance(input_text, str) or len(input_text) > MAX_SOURCE_CHARS:
        raise MultiSyntaxError("input text must be text no longer than 1,000,000 characters")
    budget = _budget or _Budget(max_steps)
    lines: list[str] = []
    def emit_line(value: str) -> None:
        lines.append(value)
        if output is not None:
            output(value)
    emit = emit_line
    try:
        if selected == "reaper":
            from .runtime import Interpreter
            remaining_steps = budget.limit - budget.steps
            if remaining_steps < 1:
                raise MultiSyntaxError(f"execution step limit ({budget.limit}) exceeded")
            runtime = Interpreter(output=emit, max_steps=remaining_steps)
            runtime.run(source, filename)
            budget.tick(runtime.steps)
            result: Any = None
        elif selected == "python":
            engine = _PythonSubset(source, filename, emit, budget)
            result = engine.run()
        elif selected == "pipeline":
            result = _run_pipeline(source, emit, budget)
        elif selected == "lisp":
            result = _run_lisp(source, emit, budget)
        elif selected == "forth":
            result = _run_forth(source, emit, budget)
        elif selected == "brainfuck":
            result = _run_brainfuck(source, emit, budget, input_text, tape_size, cell_bits, eof_mode)
        elif selected == "befunge93":
            result = _run_befunge(source, emit, budget, input_text)
        else:
            raise MultiSyntaxError(f"syntax frontend {selected!r} is not available")
    
    except MultiSyntaxError:
        raise
    except Exception as error:
        from .errors import ReaperError
        expected = (
            ReaperError, ArithmeticError, TypeError, ValueError, IndexError,
            KeyError, NameError, RecursionError,
        )
        if isinstance(error, expected):
            raise MultiSyntaxError(f"{selected} execution failed: {type(error).__name__}: {error}") from error
        raise
    return {
        "schema": "reaper.multi-syntax-result.v1",
        "syntax": selected,
        "filename": filename,
        "output": lines,
        "result": result,
        "steps": budget.steps,
        "execution_performed": True,
    }


def parse_polyglot(source: str) -> list[tuple[str, str]]:
    if len(source) > MAX_SOURCE_CHARS:
        raise MultiSyntaxError("polyglot source exceeds the 1,000,000-character limit")
    blocks: list[tuple[str, str]] = []
    current_syntax: str | None = None
    current_lines: list[str] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        match = POLYGLOT_HEADER.match(line)
        if match:
            if current_syntax is not None:
                blocks.append((current_syntax, "\n".join(current_lines)))
            current_syntax = normalize_syntax(match.group(1))
            current_lines = []
        elif current_syntax is None:
            if line.strip():
                raise MultiSyntaxError(f"polyglot file must start with '%% syntax' (line {line_number})")
        else:
            current_lines.append(line)
    if current_syntax is not None:
        blocks.append((current_syntax, "\n".join(current_lines)))
    if not blocks:
        raise MultiSyntaxError("polyglot file contains no syntax blocks")
    if len(blocks) > MAX_POLYGLOT_BLOCKS:
        raise MultiSyntaxError(f"polyglot file exceeds {MAX_POLYGLOT_BLOCKS} syntax blocks")
    return blocks


def run_polyglot(
    source: str,
    *,
    filename: str = "<polyglot>",
    input_text: str = "",
    max_steps: int = 1_000_000,
    output: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    budget = _Budget(max_steps)
    blocks = parse_polyglot(source)
    emitted: list[str] = []
    results: list[dict[str, Any]] = []
    emit = output or emitted.append
    for index, (syntax, body) in enumerate(blocks):
        result = run_source(
            syntax, body, filename=f"{filename}#{index + 1}:{syntax}",
            input_text=input_text, max_steps=max_steps, output=emit, _budget=budget,
        )
        results.append({
            "index": index,
            "syntax": syntax,
            "steps": result["steps"],
            "output": result["output"],
            "result": result["result"],
        })
    return {
        "schema": "reaper.polyglot-program.v1",
        "filename": filename,
        "block_count": len(results),
        "blocks": results,
        "output": emitted,
        "steps": budget.steps,
        "execution_performed": True,
        "execution_order": "source",
        "state_isolation": "each block has its own language state; output is shared in source order",
    }


def _validate_python_tree(tree: ast.AST) -> None:
    allowed = {
        ast.Module, ast.Expr, ast.Constant, ast.Name, ast.Load, ast.Store,
        ast.List, ast.Tuple, ast.Set, ast.Dict, ast.BinOp, ast.UnaryOp,
        ast.BoolOp, ast.Compare, ast.IfExp, ast.Subscript, ast.Slice,
        ast.Call, ast.keyword, ast.Lambda, ast.JoinedStr, ast.FormattedValue,
        ast.Assign, ast.AnnAssign, ast.AugAssign, ast.FunctionDef, ast.arguments,
        ast.arg, ast.Return, ast.If, ast.While, ast.For, ast.Match, ast.match_case,
        ast.MatchAs, ast.MatchValue, ast.MatchSingleton, ast.MatchSequence,
        ast.MatchOr, ast.Break, ast.Continue, ast.Pass, ast.Assert,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.UAdd, ast.USub, ast.Not, ast.And, ast.Or, ast.Eq, ast.NotEq,
        ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot,
    }
    for node in ast.walk(tree):
        if type(node) not in allowed:
            raise MultiSyntaxError(f"Python subset does not support {type(node).__name__}")
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            raise MultiSyntaxError("decorators are not enabled in the safe Python subset")
        if isinstance(node, ast.arg):
            if node.annotation is not None:
                annotation = node.annotation
                if not (
                    isinstance(annotation, ast.Name) and annotation.id in _PythonSubset._annotations
                    or isinstance(annotation, ast.Constant) and annotation.value == "Any"
                    or isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name)
                    and annotation.value.id in {"list", "tuple", "dict", "set"}
                ):
                    raise MultiSyntaxError("unsupported Python boundary type annotation")


def validate_source(syntax: str, source: str, *, filename: str = "<memory>") -> dict[str, Any]:
    """Validate syntax and structure without executing user code."""
    if not isinstance(source, str) or len(source) > MAX_SOURCE_CHARS:
        raise MultiSyntaxError("source must be text no longer than 1,000,000 characters")
    selected = normalize_syntax(syntax)
    analysis: dict[str, Any] = {}
    if selected == "reaper":
        from .parser import parse
        parse(source, filename)
    elif selected == "python":
        try:
            tree = ast.parse(source, filename=filename, mode="exec")
        except SyntaxError as error:
            raise MultiSyntaxError(f"{filename}:{error.lineno}:{error.offset}: {error.msg}") from error
        except RecursionError as error:
            raise MultiSyntaxError("Python syntax nesting limit exceeded") from error
        _validate_python_tree(tree)
    elif selected == "pipeline":
        stages = _split_pipeline(source)
        for index, stage in enumerate(stages):
            try:
                tree = ast.parse(stage, mode="eval")
            except SyntaxError as error:
                raise MultiSyntaxError(f"invalid pipeline stage {index + 1}: {error.msg}") from error
            _validate_python_tree(ast.Module(body=[ast.Expr(value=tree.body)], type_ignores=[]))
            if index > 0 and not isinstance(tree.body, (ast.Name, ast.Call)):
                raise MultiSyntaxError("pipeline stages must be function names or function calls")
    elif selected == "lisp":
        _read_lisp(source)
    elif selected == "forth":
        tokens = re.findall(r'"(?:\\.|[^"\\])*"|[^\s]+', re.sub(r"\\[^\n]*", "", source))
        definition_open = False
        for token in tokens:
            if token == ":":
                if definition_open:
                    raise MultiSyntaxError("nested Forth ':' definition")
                definition_open = True
            elif token == ";":
                if not definition_open:
                    raise MultiSyntaxError("Forth ';' has no matching ':'")
                definition_open = False
        if definition_open:
            raise MultiSyntaxError("Forth definition is missing ';'")
    elif selected == "brainfuck":
        analysis = analyze_brainfuck(source)
    elif selected == "befunge93":
        rows = source.splitlines() or [""]
        if len(rows) > 25 or any(len(row) > 80 for row in rows):
            raise MultiSyntaxError("Befunge-93 playfield is limited to 80 columns by 25 rows")
        supported = set("0123456789+-*/%!`><^v?_|\"\\:$.,#pg&~@ ")
        for row_index, row in enumerate(rows):
            for column, character in enumerate(row):
                if character not in supported:
                    raise MultiSyntaxError(f"unsupported Befunge-93 instruction {character!r} at ({column},{row_index})")
    return {
        "schema": "reaper.syntax-validation.v1",
        "syntax": selected,
        "filename": filename,
        "valid": True,
        "analysis": analysis,
        "execution_performed": False,
    }


def validate_polyglot(source: str, *, filename: str = "<polyglot>") -> dict[str, Any]:
    blocks = parse_polyglot(source)
    reports = [
        validate_source(syntax, body, filename=f"{filename}#{index + 1}:{syntax}")
        for index, (syntax, body) in enumerate(blocks)
    ]
    return {
        "schema": "reaper.polyglot-validation.v1",
        "filename": filename,
        "valid": True,
        "block_count": len(reports),
        "blocks": reports,
        "execution_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaper-multisyntax",
        description="Run Reaper and registered alternative syntax frontends.",
    )
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--syntax", default="auto", help="reaper, python, pipeline, lisp, forth, brainfuck or befunge93")
    parser.add_argument("--polyglot", action="store_true", help="execute or validate %% syntax blocks in source order")
    parser.add_argument("--check", action="store_true", help="validate syntax without executing the program")
    parser.add_argument("--list", action="store_true", help="list registered syntax frontends")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--steps", type=int, default=1_000_000)
    parser.add_argument("--input", default="", help="text input for Brainfuck/Befunge programs")
    parser.add_argument("--tape-size", type=int, default=30_000)
    parser.add_argument("--cell-bits", type=int, choices=(8, 16, 32), default=8)
    parser.add_argument("--eof", choices=("zero", "keep", "max"), default="zero")
    args = parser.parse_args(argv)
    try:
        if args.list:
            if args.source or args.polyglot or args.check:
                parser.error("--list cannot be combined with a source, --polyglot or --check")
            result: Any = {"schema": "reaper.syntax-registry.v1", "syntaxes": list_syntaxes()}
        else:
            if args.source is None:
                parser.error("source is required unless --list is used")
            if args.steps < 1:
                parser.error("--steps must be positive")
            source = args.source.read_text(encoding="utf-8")
            if args.check:
                result = (
                    validate_polyglot(source, filename=str(args.source))
                    if args.polyglot
                    else validate_source(
                        detect_syntax(args.source, args.syntax, source),
                        re.sub(r"^\s*#!syntax\s+[a-z0-9_-]+\s*(?:\n|$)", "", source, count=1, flags=re.I),
                        filename=str(args.source),
                    )
                )
            elif args.polyglot:
                result = run_polyglot(
                    source, filename=str(args.source), input_text=args.input,
                    max_steps=args.steps,
                )
            else:
                syntax = detect_syntax(args.source, args.syntax, source)
                marker = re.match(r"\s*#!syntax\s+[a-z0-9_-]+\s*(?:\n|$)", source, re.I)
                if marker:
                    source = source[marker.end():]
                result = run_source(
                    syntax, source, filename=str(args.source), input_text=args.input,
                    max_steps=args.steps, tape_size=args.tape_size,
                    cell_bits=args.cell_bits, eof_mode=args.eof,
                )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif args.list:
            for item in result["syntaxes"]:
                print(f"{item['name']:<12} {item['paradigm']:<28} {item['status']}")
        elif args.check:
            print(f"Reaper syntax check: {result.get('block_count', 1)} block(s) valid")
        else:
            for line in result.get("output", []):
                print(line, end="" if line.endswith("\n") else "\n")
            if args.polyglot:
                print(f"Reaper polyglot: {result['block_count']} blocks, {result['steps']} steps")
        return 0
    except (OSError, UnicodeError, MultiSyntaxError, SyntaxError) as error:
        print(f"reaper-multisyntax: {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
