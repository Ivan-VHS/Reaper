"""Reaper — an independent, flow-first programming language."""

from .compiler import CompilationUnit, StaticTypeError, TypeChecker, compile_source, optimize
from .errors import ExecutionLimitError, LexError, ParseError, ReaperError, ReaperRuntimeError
from .runtime import Interpreter, run

__version__ = "0.1.0"
__all__ = [
    "CompilationUnit", "ExecutionLimitError", "Interpreter", "LexError",
    "ParseError", "ReaperError", "ReaperRuntimeError", "StaticTypeError",
    "TypeChecker", "compile_source", "optimize", "run", "__version__",
]
