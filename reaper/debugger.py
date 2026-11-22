"""Statement-boundary debugger hooks shared by Reaper Studio and the VM."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class DebuggerStopped(Exception):
    """Raised when a user stops a paused debug session."""


@dataclass(slots=True)
class DebugSnapshot:
    filename: str
    line: int
    column: int
    call_stack: list[str]
    variables: dict[str, Any]


def _visible_variables(environment: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    chain: list[Any] = []
    current = environment
    while current is not None:
        chain.append(current)
        current = getattr(current, "parent", None)
    for scope in reversed(chain):
        for name, binding in getattr(scope, "values", {}).items():
            result[name] = getattr(binding, "value", binding)
    return dict(sorted(result.items()))


class RuntimeDebugger:
    def __init__(
        self,
        breakpoints: set[int] | None = None,
        pause_hook: Callable[[DebugSnapshot], None] | None = None,
    ) -> None:
        self.breakpoints = set(breakpoints or ())
        self.pause_hook = pause_hook
        self.step_mode = False
        self.step_out_depth: int | None = None
        self.stop_requested = False
        self.paused = False
        self.last_snapshot: DebugSnapshot | None = None

    def add_breakpoint(self, line: int) -> None:
        if line < 1:
            raise ValueError("breakpoint line must be positive")
        self.breakpoints.add(line)

    def remove_breakpoint(self, line: int) -> None:
        self.breakpoints.discard(line)

    def before_statement(self, token: Any, environment: Any, call_stack: list[str], filename: str) -> None:
        if self.stop_requested:
            raise DebuggerStopped()

        should_stop = False
        if self.step_out_depth is not None:
            if len(call_stack) <= self.step_out_depth:
                self.step_out_depth = None
                should_stop = True
            else:
                return
        elif token.line in self.breakpoints or self.step_mode:
            should_stop = True

        if not should_stop:
            return

        snapshot = DebugSnapshot(
            filename=filename,
            line=token.line,
            column=token.column,
            call_stack=list(call_stack),
            variables=_visible_variables(environment),
        )
        self.last_snapshot = snapshot
        self.paused = True
        self.step_mode = False
        try:
            if self.pause_hook is not None:
                self.pause_hook(snapshot)
        finally:
            self.paused = False
        if self.stop_requested:
            raise DebuggerStopped()

    def continue_execution(self) -> None:
        self.step_mode = False
        self.step_out_depth = None

    def step(self) -> None:
        self.step_out_depth = None
        self.step_mode = True

    def step_out(self) -> None:
        snapshot = self.last_snapshot
        if snapshot is None or not snapshot.call_stack:
            raise ValueError("stepOut is available only inside a function")
        self.step_mode = False
        self.step_out_depth = len(snapshot.call_stack) - 1

    def stop(self) -> None:
        self.stop_requested = True
