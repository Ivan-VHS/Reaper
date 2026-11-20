"""Reaper — a small, flow-first programming language."""

from .composition import compose, concat, concat_text, merge_mappings, pipe
from .arithmetic import (
    accumulate, aggregate, amplify, cartesianize, combine, compute, compound,
    convolve, couple, cross_multiply, expand, exponentiate, factor, fuse,
    multiply, pair, product, scale,
)
from .decomposition import (
    DivisionResult, decompose_sequence, distribute_weighted, divide_fraction,
    euclidean_divmod, factor_pairs, recombine, split_evenly,
)
from .errors import ExecutionLimitError, LexError, ParseError, ReaperError, ReaperRuntimeError
from .evolution import EvolutionEngine, EvolutionReport
from .runtime import Interpreter, run
from .token_catalog import TOKEN_CATALOG_SIZE, token_catalog, token_info, token_is_reserved

__version__ = "0.1.0"
__all__ = [
    "DivisionResult", "ExecutionLimitError", "EvolutionEngine", "EvolutionReport",
    "accumulate", "aggregate", "amplify", "cartesianize", "combine", "compute",
    "compound", "convolve", "couple", "cross_multiply", "expand", "exponentiate",
    "factor", "fuse", "multiply", "pair", "product", "scale",
    "compose", "concat", "concat_text", "merge_mappings", "pipe",
    "Interpreter", "LexError", "ParseError", "ReaperError", "ReaperRuntimeError",
    "decompose_sequence", "distribute_weighted", "divide_fraction",
    "euclidean_divmod", "factor_pairs", "recombine", "run", "split_evenly",
    "TOKEN_CATALOG_SIZE", "token_catalog", "token_info", "token_is_reserved",
    "__version__",
]
