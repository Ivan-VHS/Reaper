"""One diagnostic envelope shared by the compiler, runtime, CLI, and editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import (
    ExecutionLimitError,
    LexError,
    ParseError,
    ReaperError,
    ReaperRuntimeError,
)
from .source import SourceMap, Span


@dataclass(frozen=True, slots=True)
class Diagnostic:
    stage: str
    code: str
    message: str
    span: Span | None = None
    syntax_mode: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    severity: str = "error"

    def __post_init__(self) -> None:
        if not self.stage or not self.code or not self.message:
            raise ValueError("diagnostics require stage, code, and message")
        if self.severity not in {"error", "warning", "information", "hint"}:
            raise ValueError("unsupported diagnostic severity")
        if self.syntax_mode is None and self.span is not None:
            object.__setattr__(self, "syntax_mode", self.span.syntax_mode)

    def to_dict(self, source_map: SourceMap | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "stage": self.stage,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "syntax_mode": self.syntax_mode,
            "span": self.span.to_dict() if self.span is not None else None,
            "details": dict(self.details),
        }
        if self.span is not None:
            result["line"] = self.span.line
            result["column"] = self.span.column
            if source_map is not None:
                try:
                    buffer, line, column = source_map.resolve(self.span)
                except KeyError:
                    pass
                else:
                    result["location"] = {
                        "source_id": buffer.source_id,
                        "line": line,
                        "column": column,
                        "excerpt": buffer.excerpt(self.span),
                    }
        return result


_ERROR_DEFAULTS: tuple[tuple[type[BaseException], str, str], ...] = (
    (ExecutionLimitError, "RPR-R0002", "runtime"),
    (LexError, "RPR-E0001", "lexer"),
    (ParseError, "RPR-E0013", "parser"),
    (ReaperRuntimeError, "RPR-R0001", "runtime"),
    (ReaperError, "RPR-E0000", "compiler"),
)


def diagnostic_from_error(
    error: BaseException,
    *,
    syntax_mode: str | None = None,
    source_map: SourceMap | None = None,
) -> Diagnostic:
    """Convert a Reaper exception to the stable cross-layer diagnostic shape."""
    code = getattr(error, "code", None)
    stage = getattr(error, "stage", None)
    if code is None or stage is None:
        for error_type, default_code, default_stage in _ERROR_DEFAULTS:
            if isinstance(error, error_type):
                code = code or default_code
                stage = stage or default_stage
                break
    code = code or "RPR-E0000"
    stage = stage or "compiler"
    span = getattr(error, "span", None)
    mode = syntax_mode or getattr(error, "syntax_mode", None)
    if mode is None and span is not None:
        mode = span.syntax_mode
    details = getattr(error, "details", None) or {}
    diagnostic = Diagnostic(
        stage=stage,
        code=code,
        message=str(error),
        span=span,
        syntax_mode=mode,
        details=dict(details),
    )
    # Resolve eagerly when requested so an invalid source reference is surfaced
    # at the adapter boundary, not silently turned into a wrong line number.
    if source_map is not None and span is not None:
        source_map.resolve(span)
    return diagnostic


def diagnostic_to_dict(
    error: BaseException,
    *,
    syntax_mode: str | None = None,
    source_map: SourceMap | None = None,
) -> dict[str, Any]:
    return diagnostic_from_error(
        error, syntax_mode=syntax_mode, source_map=source_map
    ).to_dict(source_map)
