"""Reaper — a small, flow-first programming language."""

from .decomposition import (
    DivisionResult, decompose_sequence, distribute_weighted, divide_fraction,
    euclidean_divmod, factor_pairs, recombine, split_evenly,
)
from .errors import ExecutionLimitError, LexError, ParseError, ReaperError, ReaperRuntimeError
from .evolution import EvolutionEngine, EvolutionReport
from .runtime import Interpreter, run

__version__ = "0.1.0"
__all__ = [
    "DivisionResult", "ExecutionLimitError", "EvolutionEngine", "EvolutionReport",
    "Interpreter", "LexError", "ParseError", "ReaperError", "ReaperRuntimeError",
    "decompose_sequence", "distribute_weighted", "divide_fraction",
    "euclidean_divmod", "factor_pairs", "recombine", "run", "split_evenly",
    "__version__",
]
