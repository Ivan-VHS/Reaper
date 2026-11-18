"""Reaper — an independent, flow-first programming language."""

from .compiler import CompilationUnit, StaticTypeError, TypeChecker, compile_source, optimize
from .errors import ExecutionLimitError, LexError, ParseError, ReaperError, ReaperRuntimeError
from .runtime import Interpreter, run
from .citadel import CitadelRouter, RelayError, RelayNotFoundError, RelayPayloadError, RelayStats
from .vanguard import SentinelFinding, SentinelReport, VanguardSentinel

__version__ = "0.1.0"
__all__ = [
    "CompilationUnit", "CitadelRouter", "ExecutionLimitError", "Interpreter", "LexError",
    "ParseError", "ReaperError", "ReaperRuntimeError", "StaticTypeError",
    "TypeChecker", "RelayError", "RelayNotFoundError", "RelayPayloadError", "RelayStats",
    "SentinelFinding", "SentinelReport", "VanguardSentinel",
    "compile_source", "optimize", "run", "__version__",
]
