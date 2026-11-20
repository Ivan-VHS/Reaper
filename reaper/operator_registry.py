"""Canonical registry for Reaper's 666 punctuation operators."""
from __future__ import annotations
from dataclasses import asdict, dataclass
OPERATOR_COUNT = 666
GLYPH_ALPHABET = ":;=+"
LEGACY_GLYPH_OPERATORS = frozenset({":=", "==", "++"})
_FAMILIES = (
    (1, 120, "memory", "Memory, buffers, arenas and slices"),
    (121, 240, "flow", "Pipelines, control flow and synchronization"),
    (241, 360, "binding", "Bindings, contracts and types"),
    (361, 480, "arithmetic", "Arithmetic, accumulation and shifts"),
    (481, 580, "metric", "Vectors, metrics and geometry"),
    (581, 666, "system", "System hooks, diagnostics and metadata"),
)
_ANCHORS = [
    [
        ";;:",
        "memory_commit",
        "Close the active memory block and record its state."
    ],
    [
        "::;",
        "buffer_view",
        "Create a bounded view over an existing buffer."
    ],
    [
        "::=",
        "strict_define",
        "Declare a binding using the strict definition form."
    ],
    [
        ":++",
        "prefix_increment",
        "Increment a mutable numeric binding and return the new value."
    ],
    [
        "::",
        "pipeline",
        "Pass the left value as the first argument to the right operation."
    ],
    [
        ":;",
        "expression_boundary",
        "Reserved expression-step boundary."
    ],
    [
        "=::",
        "contract_equal",
        "Compare values using type-strict structural equality."
    ],
    [
        "++:",
        "sequence_concat",
        "Concatenate two lists into a new bounded list."
    ],
    [
        ":;:",
        "debug_checkpoint",
        "Record a diagnostic checkpoint."
    ],
    [
        ";::",
        "aligned_buffer",
        "Reserve an aligned buffer."
    ],
    [
        ":::",
        "metric_context",
        "Enter a metric or vector computation context."
    ],
    [
        ";;;",
        "frame_terminate",
        "Terminate a frame or stream."
    ],
    [
        ":=:",
        "atomic_exchange",
        "Atomically exchange two mutable locations."
    ],
    [
        ":+:",
        "stride_step",
        "Set an iteration or buffer stride."
    ],
    [
        ";+:",
        "capacity_reserve",
        "Reserve collection capacity without adding elements."
    ],
    [
        ":+;",
        "buffer_clear",
        "Clear a buffer while retaining its allocation."
    ],
    [
        "=:=",
        "strict_identity",
        "Compare identity under a strict identity rule."
    ],
    [
        ":==",
        "compatible_rebind",
        "Rebind a value after compatibility validation."
    ],
    [
        "==:",
        "closure_capture",
        "Capture a value in a closure context."
    ],
    [
        "++;",
        "stream_advance",
        "Advance a stream by one element."
    ],
    [
        ";++;",
        "batch_advance",
        "Advance a stream window by one batch."
    ],
    [
        "::+",
        "vector_projection",
        "Project a vector onto a direction."
    ],
    [
        "+::",
        "vector_norm",
        "Compute a vector norm or deviation magnitude."
    ],
    [
        ":;;",
        "metric_distance",
        "Compute the distance between two metric objects."
    ],
    [
        ";:;",
        "sequence_filter",
        "Filter sequence elements using a predicate."
    ],
    [
        ";;=",
        "snapshot_freeze",
        "Freeze a value or state snapshot."
    ],
    [
        "=;;",
        "snapshot_rollback",
        "Restore the latest checkpoint."
    ],
    [
        ":+=",
        "accumulate_assign",
        "Add to an accumulator and store the result."
    ],
    [
        "++=",
        "structure_merge",
        "Merge compatible structures or sequences."
    ],
    [
        ";=:",
        "destructure",
        "Destructure a tuple or record into bindings."
    ],
    [
        ":=;",
        "binding_close",
        "Close the current binding chain."
    ],
    [
        "::;;",
        "frame_open",
        "Open an isolated evaluation frame."
    ],
    [
        ";;::",
        "frame_close",
        "Close a frame and return its result."
    ],
    [
        ":+++",
        "multi_advance",
        "Advance by a bounded multi-element offset."
    ],
    [
        "+++:",
        "multi_concat",
        "Concatenate multiple buffers or sequences."
    ],
    [
        ";::;",
        "stream_partition",
        "Split a stream into labelled segments."
    ],
    [
        "::;:",
        "graph_node",
        "Declare a dependency-graph node."
    ],
    [
        ":;::",
        "graph_edge",
        "Connect two graph nodes with a directed data edge."
    ],
    [
        "=::=",
        "structural_equivalence",
        "Compare metric or structural equivalence."
    ],
    [
        ":==:",
        "epsilon_tolerance",
        "Set an epsilon tolerance for approximate comparison."
    ],
    [
        ";;+:",
        "conditional_break",
        "Stop a loop or pipeline when its guard is true."
    ],
    [
        "+:;;",
        "bounded_repeat",
        "Repeat an operation a bounded number of times."
    ],
    [
        "::=+",
        "metric_energy",
        "Evaluate an energy measure or power."
    ],
    [
        ";=;",
        "orthogonality_test",
        "Test orthogonality or component independence."
    ],
    [
        ":==+",
        "approximate_compare",
        "Compare values within a configured tolerance."
    ],
    [
        ";;=;",
        "critical_stop",
        "Stop execution with a critical diagnostic."
    ],
    [
        ":;=:",
        "guard_check",
        "Check a guard condition before executing a branch."
    ],
    [
        "::=;",
        "buffer_checksum",
        "Compute a checksum for a buffer or state snapshot."
    ]
]
_IMPLEMENTED_IDS = frozenset({3, 4, 5, 7, 8})
@dataclass(frozen=True, slots=True)
class OperatorSpec:
    id: int
    glyph: str
    family: str
    family_description: str
    name: str
    description: str
    status: str
    def to_dict(self) -> dict[str, object]:
        return asdict(self)
def family_for_id(operator_id: int) -> tuple[str, str]:
    for first, last, name, description in _FAMILIES:
        if first <= operator_id <= last:
            return name, description
    raise ValueError(f"operator id must be in 1..{OPERATOR_COUNT}")
def _encode_base4(value: int) -> str:
    if value < 0 or value >= 4**5:
        raise ValueError("base-4 operator code is out of range")
    digits = [":"] * 5
    for position in range(4, -1, -1):
        digits[position] = GLYPH_ALPHABET[value % 4]
        value //= 4
    return "".join(digits)
def _build_catalog() -> tuple[OperatorSpec, ...]:
    if len(_ANCHORS) != 48:
        raise RuntimeError("the anchor registry must contain exactly 48 entries")
    glyphs = [entry[0] for entry in _ANCHORS]
    if len(set(glyphs)) != len(glyphs):
        raise RuntimeError("duplicate anchor glyph")
    if any(not glyph or len(glyph) > 4 or any(c not in GLYPH_ALPHABET for c in glyph) for glyph in glyphs):
        raise RuntimeError("anchor glyphs must use 1..4 characters from ':;=+'")
    entries: list[OperatorSpec] = []
    for operator_id, (glyph, name, description) in enumerate(_ANCHORS, start=1):
        family, family_description = family_for_id(operator_id)
        entries.append(OperatorSpec(operator_id, glyph, family, family_description, name, description,
                                    "implemented" if operator_id in _IMPLEMENTED_IDS else "reserved"))
    for offset in range(OPERATOR_COUNT - len(_ANCHORS)):
        operator_id = len(_ANCHORS) + offset + 1
        family, family_description = family_for_id(operator_id)
        entries.append(OperatorSpec(operator_id, _encode_base4(offset), family, family_description,
                                    f"{family}_reserved_{operator_id:03d}",
                                    f"Generated {family} extension slot {operator_id:03d}; semantics are unassigned.",
                                    "reserved"))
    if len(entries) != OPERATOR_COUNT or len({item.glyph for item in entries}) != OPERATOR_COUNT:
        raise RuntimeError("operator catalogue must contain 666 unique glyphs")
    return tuple(entries)
OPERATORS = _build_catalog()
_BY_ID = {item.id: item for item in OPERATORS}
_BY_GLYPH = {item.glyph: item for item in OPERATORS}
def operator_by_id(operator_id: int) -> OperatorSpec | None:
    return _BY_ID.get(operator_id)
def operator_by_glyph(glyph: str) -> OperatorSpec | None:
    return _BY_GLYPH.get(glyph)
def operator_catalog() -> tuple[OperatorSpec, ...]:
    return OPERATORS
def glyph_for_id(operator_id: int) -> str:
    item = operator_by_id(operator_id)
    if item is None:
        raise ValueError(f"operator id must be in 1..{OPERATOR_COUNT}")
    return item.glyph
