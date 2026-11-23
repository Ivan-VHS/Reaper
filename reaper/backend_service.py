"""Domain services that adapt the Reaper reference runtime to backend requests."""

from __future__ import annotations

import math
from itertools import islice
from typing import Any

from .errors import ReaperError
from .parser import Node, parse
from .typecheck import TypeChecker

API_VERSION = 1


class OutputLimitExceeded(RuntimeError):
    """The captured output exceeded its configured budget."""


class BackendService:
    """Pure request-facing adapter around parsing, type checking and execution."""

    def __init__(
        self,
        *,
        max_steps: int,
        max_call_depth: int,
        max_collection_items: int,
        max_text_length: int,
        max_heap_bytes: int,
        max_output_chars: int,
    ) -> None:
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth
        self.max_collection_items = max_collection_items
        self.max_text_length = max_text_length
        self.max_heap_bytes = max_heap_bytes
        self.max_output_chars = max_output_chars

    def check_source(self, source: str) -> tuple[int, dict[str, Any]]:
        try:
            tree = parse(source, "<backend-request>")
            result = TypeChecker("<backend-request>").check(tree)
            return 200, {"api_version": API_VERSION, **result.as_dict()}
        except ReaperError as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "source_error", "message": str(error)},
            }
        except (RecursionError, ValueError) as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "source_limit", "message": str(error)},
            }

    def run_source(self, source: str, engine: str) -> tuple[int, dict[str, Any]]:
        try:
            tree = parse(source, "<backend-request>")
            type_result = TypeChecker("<backend-request>").check(tree)
            if not type_result.ok:
                return 422, {
                    "api_version": API_VERSION,
                    "ok": False,
                    "error": {"code": "type_error", "message": "source did not pass static type analysis"},
                    "diagnostics": [item.as_dict() for item in type_result.diagnostics],
                }
            if self._contains_import(tree):
                return 422, {
                    "api_version": API_VERSION,
                    "ok": False,
                    "error": {
                        "code": "restricted_effect",
                        "message": "module imports are disabled in backend execution",
                    },
                }

            from .runtime import Interpreter

            output: list[str] = []
            output_size = 0

            def capture(line: str) -> None:
                nonlocal output_size
                next_size = output_size + len(line)
                if next_size > self.max_output_chars or len(output) >= 10_000:
                    raise OutputLimitExceeded("program output limit exceeded")
                output.append(line)
                output_size = next_size

            interpreter = Interpreter(
                output=capture,
                max_steps=self.max_steps,
                max_call_depth=self.max_call_depth,
                max_collection_items=self.max_collection_items,
                max_text_length=self.max_text_length,
                allow_native_ffi=False,
                max_heap_bytes=self.max_heap_bytes,
                max_open_resources=1,
            )
            forbidden_builtins = {
                "ask",
                "file_open",
                "file_read",
                "file_write",
                "file_close",
                "with_file",
                "ffi_open",
                "ffi_bind",
                "ffi_close",
                "pytyliki_open",
                "consent_check",
                "consent_revoke",
            }
            for name in forbidden_builtins:
                interpreter.globals.values.pop(name, None)

            result = interpreter.run(source, filename="<backend-request>", engine=engine)
            return 200, {
                "api_version": API_VERSION,
                "ok": True,
                "engine": engine,
                "output": output,
                "result": self._json_safe(result),
                "steps": interpreter.steps,
            }
        except OutputLimitExceeded as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "output_limit", "message": str(error)},
            }
        except ReaperError as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "runtime_error", "message": str(error)},
            }
        except (ArithmeticError, RecursionError, TypeError, ValueError) as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "runtime_error", "message": str(error)},
            }

    @staticmethod
    def _contains_import(tree: Node) -> bool:
        pending = [tree]
        while pending:
            node = pending.pop()
            if node.kind == "import":
                return True
            pending.extend(node.children or [])
        return False

    @staticmethod
    def _json_safe(
        value: Any,
        *,
        depth: int = 0,
        seen: set[int] | None = None,
        budget: list[int] | None = None,
    ) -> Any:
        if budget is None:
            budget = [0]
        budget[0] += 1
        if budget[0] > 20_000:
            return {"type": "item_limit"}
        if depth > 24:
            return {"type": "depth_limit"}
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if seen is None:
            seen = set()
        if isinstance(value, (list, tuple, dict)):
            identity = id(value)
            if identity in seen:
                return {"type": "cycle"}
            seen.add(identity)
            try:
                if isinstance(value, dict):
                    result: dict[str, Any] = {}
                    for key, item in islice(value.items(), 10_000):
                        if isinstance(key, str):
                            result[key] = BackendServer._json_safe(
                                item, depth=depth + 1, seen=seen, budget=budget
                            )
                    return result
                return [
                    BackendServer._json_safe(
                        item, depth=depth + 1, seen=seen, budget=budget
                    )
                    for item in islice(value, 10_000)
                ]
            finally:
                seen.discard(identity)
        return {"type": type(value).__name__}
