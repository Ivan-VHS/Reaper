"""DAP bridge with safe conditional breakpoints and read-only expression evaluation."""
from __future__ import annotations

import json
import math
import re
import sys
import threading
from pathlib import Path
from typing import Any

from .debugger import DebuggerStopped, DebugSnapshot, RuntimeDebugger
from .parser import Node, parse
from .runtime import Interpreter


_MAX_EXPRESSION_LENGTH = 2048
_MAX_EXPRESSION_NODES = 256
_MAX_VALUE_DEPTH = 32
_MAX_COLLECTION_ITEMS = 10_000
_HIT_CONDITION = re.compile(r"^(?:(>=|>|==)\s*)?(\d+)$|^%\s*(\d+)$")


def _is_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(float(value))


def _is_safe_value(value: Any, depth: int = 0) -> bool:
    if depth > _MAX_VALUE_DEPTH:
        return False
    if value is None or type(value) in (bool, int, float, str):
        return not isinstance(value, float) or math.isfinite(value)
    if type(value) in (list, tuple):
        return len(value) <= _MAX_COLLECTION_ITEMS and all(
            _is_safe_value(item, depth + 1) for item in value
        )
    if type(value) is dict:
        return len(value) <= _MAX_COLLECTION_ITEMS and all(
            type(key) in (str, int) and _is_safe_value(item, depth + 1)
            for key, item in value.items()
        )
    return False


def _truthy(value: Any) -> bool:
    if not _is_safe_value(value):
        raise ValueError("expression refers to a value that is not safe to inspect")
    return bool(value)


def _evaluate_node(node: Node, variables: dict[str, Any], budget: list[int], depth: int = 0) -> Any:
    budget[0] += 1
    if budget[0] > _MAX_EXPRESSION_NODES or depth > 64:
        raise ValueError("debug expression exceeds its complexity limit")

    children = node.children or []
    if node.kind == "literal":
        value = node.value
    elif node.kind == "name":
        if node.value not in variables:
            raise ValueError(f"unknown local name: {node.value}")
        value = variables[node.value]
    elif node.kind == "list":
        value = [
            _evaluate_node(child, variables, budget, depth + 1)
            for child in children
        ]
    elif node.kind == "index":
        collection = _evaluate_node(children[0], variables, budget, depth + 1)
        index = _evaluate_node(children[1], variables, budget, depth + 1)
        if type(collection) not in (list, tuple, str, dict):
            raise ValueError("indexing is limited to lists, tuples, text and dictionaries")
        if type(collection) is dict:
            if type(index) not in (str, int):
                raise ValueError("dictionary keys must be text or integers")
        elif type(index) is not int:
            raise ValueError("sequence indexes must be whole numbers")
        try:
            value = collection[index]
        except (IndexError, KeyError) as error:
            raise ValueError("index is outside the available value") from error
    elif node.kind == "unary":
        operand = _evaluate_node(children[0], variables, budget, depth + 1)
        if node.value == "NOT":
            value = not _truthy(operand)
        elif node.value == "-" and _is_number(operand):
            value = -operand
        else:
            raise ValueError("unsupported unary operation")
    elif node.kind == "binary":
        operator = node.value
        left = _evaluate_node(children[0], variables, budget, depth + 1)
        if operator == "AND":
            value = _evaluate_node(children[1], variables, budget, depth + 1) if _truthy(left) else left
        elif operator == "OR":
            value = left if _truthy(left) else _evaluate_node(children[1], variables, budget, depth + 1)
        else:
            right = _evaluate_node(children[1], variables, budget, depth + 1)
            if operator in {"==", "!="}:
                if not (_is_safe_value(left) and _is_safe_value(right)):
                    raise ValueError("equality is limited to safe values")
                value = (left == right)
                if operator == "!=":
                    value = not value
            elif operator in {"<", "<=", ">", ">="}:
                compatible = (_is_number(left) and _is_number(right)) or (
                    type(left) is str and type(right) is str
                )
                if not compatible:
                    raise ValueError("comparisons need two numbers or two text values")
                value = {
                    "<": left < right,
                    "<=": left <= right,
                    ">": left > right,
                    ">=": left >= right,
                }[operator]
            elif operator == "++":
                if type(left) is not str or type(right) is not str:
                    raise ValueError("'++' needs two text values")
                value = left + right
                if len(value) > 10_000:
                    raise ValueError("debug expression text result is too long")
            elif operator in {"+", "-", "*", "/", "//", "%", "**"}:
                if not (_is_number(left) and _is_number(right)):
                    raise ValueError(f"'{operator}' needs two numbers")
                if operator in {"/", "//", "%"} and right == 0:
                    raise ValueError("division by zero")
                if operator == "**" and abs(right) > 100:
                    raise ValueError("exponent exceeds the debug evaluation limit")
                try:
                    value = {
                        "+": lambda: left + right,
                        "-": lambda: left - right,
                        "*": lambda: left * right,
                        "/": lambda: left / right,
                        "//": lambda: left // right,
                        "%": lambda: left % right,
                        "**": lambda: left ** right,
                    }[operator]()
                except (ArithmeticError, OverflowError) as error:
                    raise ValueError(f"arithmetic failed: {error}") from error
                if not _is_number(value):
                    raise ValueError("arithmetic result is outside the finite numeric range")
            else:
                raise ValueError(f"operator '{operator}' is not available in read-only evaluation")
    else:
        # Function calls, flow calls, assignment and other executable forms are
        # intentionally excluded: inspecting a value must not run user code.
        raise ValueError(f"'{node.kind}' is not allowed in read-only evaluation")

    if not _is_safe_value(value):
        raise ValueError("expression result is not a safe inspectable value")
    return value


def evaluate_read_only(expression: str, variables: dict[str, Any]) -> Any:
    """Evaluate a bounded expression without invoking functions or mutating state."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("an expression is required")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("debug expression is too long")
    if not isinstance(variables, dict):
        raise TypeError("locals must be a dictionary")

    program = parse(expression, "<debug-evaluate>")
    statements = program.children or []
    if len(statements) != 1 or statements[0].kind != "expression":
        raise ValueError("evaluate accepts one read-only expression")
    expression_node = (statements[0].children or [None])[0]
    if expression_node is None:
        raise ValueError("expression is empty")
    return _evaluate_node(expression_node, variables, [0])


class DebugSession:
    def __init__(self, output):
        self.output = output
        self.seq = 1
        self.lock = threading.RLock()
        self.condition = threading.Condition()
        self.breakpoints: set[int] = set()
        self.breakpoint_specs: dict[int, dict[str, Any]] = {}
        self.hit_counts: dict[int, int] = {}
        self.snapshot: DebugSnapshot | None = None
        self.running = False
        self.waiting = False
        self.terminated = False
        self.worker = None
        self.debugger: RuntimeDebugger | None = None
        self.interpreter: Interpreter | None = None
        self.program = ""

    def send(self, payload):
        with self.lock:
            payload.setdefault("seq", self.seq)
            self.seq += 1
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.output.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
            self.output.flush()

    def response(self, request, body=None, success=True, message=None):
        item = {
            "type": "response",
            "request_seq": request.get("seq", 0),
            "command": request.get("command", ""),
            "success": success,
            "body": body or {},
        }
        if message:
            item["message"] = message
        self.send(item)

    def event(self, name, body=None):
        self.send({"type": "event", "event": name, "body": body or {}})

    @staticmethod
    def _hit_condition_matches(condition: str, count: int) -> bool:
        match = _HIT_CONDITION.fullmatch(condition.strip())
        if not match:
            raise ValueError("hitCondition must be N, >=N, >N, ==N or %N")
        if match.group(3) is not None:
            interval = int(match.group(3))
            if interval < 1:
                raise ValueError("hitCondition modulo must be greater than zero")
            return count % interval == 0
        operator = match.group(1) or "=="
        target = int(match.group(2))
        return {
            "==": count == target,
            ">=": count >= target,
            ">": count > target,
        }[operator]

    def _render_log_message(self, template: str, snapshot: DebugSnapshot) -> str:
        def replace(match):
            expression = match.group(1).strip()
            try:
                value = evaluate_read_only(expression, snapshot.variables)
                return str(value)
            except Exception as error:
                return f"<evaluation error: {error}>"
        return re.sub(r"\{([^{}]+)\}", replace, template)

    def pause_hook(self, snapshot: DebugSnapshot):
        spec = self.breakpoint_specs.get(snapshot.line, {})
        count = self.hit_counts.get(snapshot.line, 0) + 1
        self.hit_counts[snapshot.line] = count

        hit_condition = spec.get("hitCondition")
        if hit_condition:
            try:
                if not self._hit_condition_matches(hit_condition, count):
                    return
            except ValueError as error:
                self.event("output", {"category": "stderr", "output": f"Breakpoint hit condition: {error}\n"})

        expression = spec.get("condition")
        if expression:
            try:
                if not _truthy(evaluate_read_only(expression, snapshot.variables)):
                    return
            except Exception as error:
                self.event(
                    "output",
                    {"category": "stderr", "output": f"Breakpoint condition at line {snapshot.line}: {error}\n"},
                )

        log_message = spec.get("logMessage")
        if log_message:
            self.event("output", {
                "category": "console",
                "output": self._render_log_message(log_message, snapshot) + "\n",
            })
            return

        with self.condition:
            self.snapshot = snapshot
            self.event("stopped", {
                "reason": "step" if self.debugger and self.debugger.step_mode else "breakpoint",
                "threadId": 1,
                "allThreadsStopped": True,
            })
            self.waiting = True
            while self.waiting and not self.terminated:
                self.condition.wait()
            if self.terminated:
                raise DebuggerStopped()

    def handle(self, request):
        command = request.get("command")
        arguments = request.get("arguments") or {}

        if command == "initialize":
            self.response(request, {
                "supportsConfigurationDoneRequest": True,
                "supportsConditionalBreakpoints": True,
                "supportsHitConditionalBreakpoints": True,
                "supportsLogPoints": True,
                "supportsStepOut": True,
                "supportsEvaluateForHovers": True,
                "supportsTerminateRequest": True,
                "supportsSetVariable": False,
                "supportsStepBack": False,
                "supportsStepInTargetsRequest": False,
                "supportsDelayedStackTraceLoading": False,
            })
            self.event("initialized")
        elif command == "launch":
            path = Path(arguments.get("program", "")).expanduser().resolve()
            if not path.is_file():
                self.response(request, success=False, message="launch requires an existing .rpr program file")
            else:
                self.program = str(path)
                self.response(request)
        elif command == "setBreakpoints":
            specs: dict[int, dict[str, Any]] = {}
            response_breakpoints = []
            for item in arguments.get("breakpoints", []):
                line = item.get("line") if isinstance(item, dict) else None
                if not isinstance(line, int) or isinstance(line, bool) or line < 1:
                    continue
                spec: dict[str, Any] = {"line": line}
                valid = True
                for key in ("condition", "hitCondition", "logMessage"):
                    value = item.get(key)
                    if value is not None:
                        if not isinstance(value, str) or len(value) > _MAX_EXPRESSION_LENGTH:
                            valid = False
                        else:
                            spec[key] = value
                if spec.get("hitCondition"):
                    try:
                        self._hit_condition_matches(spec["hitCondition"], 1)
                    except ValueError:
                        valid = False
                specs[line] = spec
                response_breakpoints.append({
                    "verified": valid,
                    "line": line,
                    **({"message": "unsupported or invalid breakpoint option"} if not valid else {}),
                })
            self.breakpoint_specs = specs
            self.breakpoints = set(specs)
            self.hit_counts = {}
            self.response(request, {"breakpoints": response_breakpoints})
        elif command == "configurationDone":
            if not self.program:
                self.response(request, success=False, message="launch must precede configurationDone")
            else:
                self.response(request)
                self.start()
        elif command == "threads":
            self.response(request, {"threads": [{"id": 1, "name": "REAPER program"}]})
        elif command == "stackTrace":
            snapshot = self.snapshot
            frames = []
            if snapshot:
                frames = [{
                    "id": 1,
                    "name": snapshot.call_stack[-1] if snapshot.call_stack else Path(snapshot.filename).name,
                    "source": {"name": Path(snapshot.filename).name, "path": snapshot.filename},
                    "line": snapshot.line,
                    "column": snapshot.column,
                }]
            self.response(request, {"stackFrames": frames, "totalFrames": len(frames)})
        elif command == "scopes":
            self.response(request, {
                "scopes": [{"name": "Locals", "variablesReference": 1, "expensive": False}]
                if self.snapshot else []
            })
        elif command == "variables":
            values = self.snapshot.variables if self.snapshot else {}
            self.response(request, {"variables": [
                {"name": name, "value": repr(value), "type": type(value).__name__, "variablesReference": 0}
                for name, value in sorted(values.items())
            ]})
        elif command in ("continue", "next", "stepIn", "stepOut"):
            if not self.debugger:
                self.response(request, success=False, message="no active debug session")
            else:
                if command == "continue":
                    self.debugger.continue_execution()
                elif command == "stepOut":
                    try:
                        self.debugger.step_out()
                    except ValueError as error:
                        self.response(request, success=False, message=str(error))
                        return True
                else:
                    self.debugger.step()
                with self.condition:
                    self.waiting = False
                    self.condition.notify_all()
                self.response(request, {"allThreadsContinued": True})
        elif command == "pause":
            self.response(request, success=False, message="pause is available only at statement boundaries")
        elif command == "evaluate":
            if self.snapshot is None:
                self.response(request, success=False, message="evaluate requires a paused debug session")
            else:
                try:
                    value = evaluate_read_only(arguments.get("expression", ""), self.snapshot.variables)
                    self.response(request, {
                        "result": repr(value),
                        "type": type(value).__name__,
                        "variablesReference": 0,
                    })
                except Exception as error:
                    self.response(request, success=False, message=str(error))
        elif command in ("terminate", "disconnect"):
            self.terminated = True
            if self.debugger:
                self.debugger.stop()
            with self.condition:
                self.waiting = False
                self.condition.notify_all()
            self.response(request)
            return command != "disconnect"
        else:
            self.response(request, success=False, message=f"unsupported DAP request: {command}")
        return True

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        self.terminated = False
        self.running = True
        self.debugger = RuntimeDebugger(self.breakpoints, self.pause_hook)
        self.interpreter = Interpreter(debugger=self.debugger)

        def execute():
            try:
                source = Path(self.program).read_text(encoding="utf-8")
                self.interpreter.run(source, self.program)
                self.event("exited", {"exitCode": 0})
            except Exception as error:
                self.event("output", {"category": "stderr", "output": f"REAPER debug: {error}\n"})
                self.event("exited", {"exitCode": 1})
            finally:
                self.event("terminated")

        self.worker = threading.Thread(target=execute, name="reaper-debuggee", daemon=True)
        self.worker.start()


def read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("ascii").partition(":")
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length < 0 or length > 16 * 1024 * 1024:
        raise ValueError("invalid DAP Content-Length")
    body = stream.read(length)
    return json.loads(body.decode("utf-8")) if len(body) == length else None


def serve(stdin=None, stdout=None):
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout.buffer
    session = DebugSession(stdout)
    while True:
        request = read_message(stdin)
        if request is None:
            return 0
        if request.get("type") == "request" and not session.handle(request):
            return 0


if __name__ == "__main__":
    raise SystemExit(serve())
