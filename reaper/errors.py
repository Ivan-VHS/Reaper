"""Typed compiler, parser, and runtime errors with optional source context."""
from __future__ import annotations

from typing import Any

from .source import Span


class ReaperError(Exception):
    """Base class for user-facing Reaper errors.

    The text representation stays backwards-compatible. Structured fields allow
    CLI, Studio, LSP, and runtime adapters to share one diagnostic contract.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        stage: str | None = None,
        span: Span | None = None,
        syntax_mode: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.span = span
        self.syntax_mode = syntax_mode or (span.syntax_mode if span is not None else None)
        self.details = dict(details or {})


class LexError(ReaperError):
    """Raised when source text cannot be tokenized."""


class ParseError(ReaperError):
    """Raised when tokens do not form a valid Reaper program."""


class ReaperRuntimeError(ReaperError):
    """Raised for invalid operations while a Reaper program is running."""


class ExecutionLimitError(ReaperRuntimeError):
    """Raised when a program exceeds its configured instruction budget."""
