"""Source-aware diagnostics for the Reaper language."""

from __future__ import annotations


class ReaperError(Exception):
    """Base class for user-facing Reaper errors."""


class LexError(ReaperError):
    """Raised when source text cannot be tokenized."""

    def __init__(
        self,
        message: str,
        span: object | None = None,
        syntax_mode: str | None = None,
        locale: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.span = span
        self.syntax_mode = syntax_mode
        self.locale = locale


class ParseError(ReaperError):
    """Raised when tokens do not form a valid Reaper program."""

    def __init__(
        self,
        message: str,
        span: object | None = None,
        syntax_mode: str | None = None,
        locale: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.span = span
        self.syntax_mode = syntax_mode
        self.locale = locale


class ReaperRuntimeError(ReaperError):
    """Raised for invalid operations while a Reaper program is running."""


class ExecutionLimitError(ReaperRuntimeError):
    """Raised when a program exceeds its configured instruction budget."""
