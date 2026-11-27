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
from .transactions import RuntimeTransaction, Snapshot, TransactionConflict, TransactionError, TransactionLimitError
from .ir import CanonicalIR, IRVerificationError, lower as lower_to_ir
from .vm import BytecodeProgram, VirtualMachine, assemble as assemble_bytecode
from .modules import ModuleCycleError, ModuleError, ModuleLoader
from .memory import MemoryManager, HeapLimitError, RegionError
from .system_functions import OverrideAuthority, SystemFunctionError, WorkerBudgetExceeded
from .resources import ResourceManager, ResourceHandle
from .ffi import CAbiLibrary, NativeFunction, PytylikiBridge, FfiError
from .debugger import RuntimeDebugger, DebugSnapshot, DebuggerStopped
from .token_catalog import TOKEN_CATALOG_SIZE, token_catalog, token_info, token_is_reserved
from .thesis import ThesisLedger, ThesisLedgerError
from .embedded import EmbeddedError, McuProfile, RegisterBank, build_project as build_embedded_project, init_project as init_embedded_project

__version__ = "0.1.0"
__all__ = [
    "DivisionResult", "ExecutionLimitError", "RuntimeTransaction", "Snapshot", "TransactionConflict", "TransactionError", "TransactionLimitError", "EvolutionEngine", "EvolutionReport",
    "ThesisLedger", "ThesisLedgerError",
    "accumulate", "aggregate", "amplify", "cartesianize", "combine", "compute",
    "compound", "convolve", "couple", "cross_multiply", "expand", "exponentiate",
    "factor", "fuse", "multiply", "pair", "product", "scale",
    "Candy", "CandyLine", "GiftPlan", "GreetingEdge", "allocate_equal",
    "allocate_weighted", "build_candy_basket", "build_greeting_graph",
    "combination_count", "percent_of", "plan_gift",
    "compose", "concat", "concat_text", "merge_mappings", "pipe",
    "Interpreter", "LexError", "ParseError", "ReaperError", "ReaperRuntimeError",
    "decompose_sequence", "distribute_weighted", "divide_fraction",
    "euclidean_divmod", "factor_pairs", "recombine", "run", "split_evenly",
    "TOKEN_CATALOG_SIZE", "token_catalog", "token_info", "token_is_reserved",
    "CanonicalIR", "IRVerificationError", "lower_to_ir", "BytecodeProgram",
    "VirtualMachine", "assemble_bytecode", "ModuleCycleError", "ModuleError",
    "ModuleLoader", "MemoryManager", "HeapLimitError", "RegionError",
    "OverrideAuthority", "SystemFunctionError", "WorkerBudgetExceeded",
    "ResourceManager", "ResourceHandle", "CAbiLibrary", "NativeFunction",
    "PytylikiBridge", "FfiError", "RuntimeDebugger", "DebugSnapshot",
    "DebuggerStopped", "EmbeddedError", "McuProfile", "RegisterBank",
    "build_embedded_project", "init_embedded_project", "__version__",
]


_GIFT_PLANNER_EXPORTS = {
    "Candy", "CandyLine", "GiftPlan", "GreetingEdge", "allocate_equal",
    "allocate_weighted", "build_candy_basket", "build_greeting_graph",
    "combination_count", "percent_of", "plan_gift",
}


def __getattr__(name: str):
    if name in _GIFT_PLANNER_EXPORTS:
        from . import gift_planner
        return getattr(gift_planner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
