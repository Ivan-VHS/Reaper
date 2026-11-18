"""Source-aware diagnostics for the Reaper language."""

from __future__ import annotations


class ReaperError(Exception):
    """Base class for user-facing Reaper errors."""


class LexError(ReaperError):
    """Raised when source text cannot be tokenized."""


class ParseError(ReaperError):
    """Raised when tokens do not form a valid Reaper program."""


class ReaperRuntimeError(ReaperError):
    """Raised for invalid operations while a Reaper program is running."""


class ExecutionLimitError(ReaperRuntimeError):
    """Raised when a program exceeds its configured instruction budget."""
