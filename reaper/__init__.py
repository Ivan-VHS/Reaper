"""Reaper — a small, flow-first programming language."""

from .errors import ExecutionLimitError, LexError, ParseError, ReaperError, ReaperRuntimeError
from .runtime import Interpreter, run
from .reaper_systems import (
    ARCHITECTURE_FEATURES,
    ArchitectureError,
    CapabilityError,
    EpochArena,
    EpochReport,
    FFIPermissions,
    ForeignFunction,
    ForeignFunctionSpec,
    HealthReport,
    HotspotProfiler,
    IRModule,
    IRNode,
    MailboxFull,
    MissingEffectError,
    ProfileSnapshot,
    ProfileTier,
    RelayNetwork,
    SnapshotCodec,
    SovereignUnit,
    StateSnapshot,
    VanguardSentinel,
    architecture_summary,
    effect_scope,
    require_effect,
    requires_effects,
)

__version__ = "0.1.0"
__all__ = [
    "ARCHITECTURE_FEATURES", "ArchitectureError", "CapabilityError",
    "EpochArena", "EpochReport", "ExecutionLimitError", "FFIPermissions",
    "ForeignFunction", "ForeignFunctionSpec", "HealthReport", "HotspotProfiler",
    "IRModule", "IRNode", "Interpreter", "LexError", "MailboxFull",
    "MissingEffectError", "ParseError", "ProfileSnapshot", "ProfileTier",
    "ReaperError", "ReaperRuntimeError", "RelayNetwork", "SnapshotCodec",
    "SovereignUnit", "StateSnapshot", "VanguardSentinel", "architecture_summary",
    "effect_scope", "require_effect", "requires_effects", "run", "__version__",
]
