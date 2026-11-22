"""Named, evidence-oriented engineering tracks for Reaper.

The registry is descriptive metadata. It does not enable experimental execution,
network access, code rewriting, or additional runtime privileges.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemTrack:
    id: int
    name: str
    focus: str
    runtime_contract: str
    acceptance: str


TRACKS: tuple[SystemTrack, ...] = (
    SystemTrack(
        1,
        "Chrome Ironclad",
        "Runtime reliability",
        "Preserve interpreter invariants and fail with typed language errors.",
        "Invalid programs fail deterministically without corrupting interpreter state.",
    ),
    SystemTrack(
        2,
        "Velocity Tempest",
        "Performance",
        "Measure lexing, parsing, and evaluation separately.",
        "Benchmarks record Python version, workload, and repeatable baseline.",
    ),
    SystemTrack(
        3,
        "Midnight Monolith",
        "Modularity",
        "Keep lexer, parser, runtime, and CLI boundaries explicit.",
        "Imports remain acyclic and public contracts are tested.",
    ),
    SystemTrack(
        4,
        "Raven Vortex",
        "Diagnostics",
        "Attach filename and source position to user-facing errors.",
        "Malformed input reports stable, actionable locations.",
    ),
    SystemTrack(
        5,
        "Circuit Cobalt",
        "Execution core",
        "Keep value and operator semantics centralized.",
        "Type and operator edge cases have conformance tests.",
    ),
    SystemTrack(
        6,
        "Thunder Phantom",
        "Cooperative execution",
        "Keep execution budgets and interruption behavior explicit.",
        "Long-running loops stop at the configured budget.",
    ),
    SystemTrack(
        7,
        "Phantom Radiance",
        "Public API",
        "Keep CLI options and Python entry points discoverable.",
        "Help output and API exports match supported behavior.",
    ),
    SystemTrack(
        8,
        "Velvet Gravitas",
        "Developer experience",
        "Keep diagnostics and examples consistent and readable.",
        "Examples parse and documentation commands are reproducible.",
    ),
    SystemTrack(
        9,
        "Obsidian Inferno",
        "Error recovery",
        "Convert expected runtime failures into source-aware errors.",
        "No expected input failure leaks an unhandled implementation exception.",
    ),
    SystemTrack(
        10,
        "Horizon Spectral",
        "Portability",
        "Avoid platform-specific assumptions in language semantics.",
        "Supported Python versions run the same conformance suite.",
    ),
    SystemTrack(
        11,
        "Crimson Overdrive",
        "Compilation roadmap",
        "Keep future bytecode/native work behind a stable semantic reference.",
        "Any backend must pass the interpreter conformance suite.",
    ),
    SystemTrack(
        12,
        "Voltage Citadel",
        "Security",
        "Retain explicit effects and deny-by-default host integration.",
        "Programs cannot access filesystem, network, or subprocess APIs implicitly.",
    ),
    SystemTrack(
        13,
        "Shadow Nemesis",
        "Testing",
        "Test parser boundaries, runtime limits, and error paths.",
        "New language behavior includes positive and negative tests.",
    ),
    SystemTrack(
        14,
        "Mirage Aether",
        "Distributed execution",
        "Specify serialization and trust boundaries before remote execution.",
        "No distributed mode is exposed without a real, tested transport.",
    ),
    SystemTrack(
        15,
        "Titanium Riptide",
        "Resource control",
        "Bound steps, call depth, collection sizes, and text growth.",
        "Limits are validated before unbounded work can occur.",
    ),
    SystemTrack(
        16,
        "Eclipse Outlaw",
        "Extensibility",
        "Version built-ins and future extension interfaces.",
        "Unknown extension names fail safely and compatibility is documented.",
    ),
    SystemTrack(
        17,
        "Neutron Zenith",
        "Profiling",
        "Separate measured runtime data from estimates.",
        "Profiles identify workload and never assert unsupported speedups.",
    ),
    SystemTrack(
        18,
        "Scarlet Avalanche",
        "Automation",
        "Run the same standard-library suite in CI.",
        "CI validates supported Python versions on every pull request.",
    ),
    SystemTrack(
        19,
        "Quantum Paradox",
        "Experimental features",
        "Keep prototypes opt-in and isolated from stable syntax.",
        "Experiments cannot change default language behavior.",
    ),
    SystemTrack(
        20,
        "Reactor Afterglow",
        "Observability",
        "Expose deterministic status and execution counters.",
        "Reported counters have defined semantics and are test-covered.",
    ),
)


def validate_registry() -> None:
    """Raise ValueError if the built-in registry violates its public contract."""
    if len(TRACKS) != 20:
        raise ValueError("the Reaper system registry must contain exactly 20 tracks")

    ids = [track.id for track in TRACKS]
    names = [track.name for track in TRACKS]

    if ids != list(range(1, 21)):
        raise ValueError("system track IDs must be unique and sequential from 1 to 20")

    if len(set(names)) != len(names):
        raise ValueError("system track names must be unique")

    for track in TRACKS:
        fields = (
            track.name,
            track.focus,
            track.runtime_contract,
            track.acceptance,
        )
        if not all(field.strip() for field in fields):
            raise ValueError(f"system track {track.id} has an empty contract")


def format_tracks() -> str:
    """Return a stable, plain-text overview suitable for terminals and CI logs."""
    validate_registry()

    lines = ["Reaper engineering systems (contract catalogue; not feature claims):"]
    for track in TRACKS:
        lines.append(f"{track.id:02d} | {track.name} | {track.focus}")
        lines.append(f"    Contract: {track.runtime_contract}")
        lines.append(f"    Accept:   {track.acceptance}")

    return "\n".join(lines)
