"""Reference atlas for low-level languages and machine architectures.

The catalogue is descriptive engineering metadata. It does not install toolchains,
change Reaper's runtime semantics, or claim that a backend is implemented.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LanguageProfile:
    id: int
    name: str
    family: str
    memory_model: str
    compilation_model: str
    assurance: str
    design_signal: str


@dataclass(frozen=True, slots=True)
class ArchitectureProfile:
    id: int
    name: str
    family: str
    class_name: str
    data_model: str
    execution_model: str
    backend_questions: str


_LANGUAGE_ROWS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("Odin", "native alternatives", "explicit allocators; manual lifetime", "native / LLVM", "static types", "data-oriented layout and allocator context"),
    ("Jai", "native alternatives", "explicit allocator model", "native compiler", "compile-time execution", "compile-time code generation and reflection"),
    ("C3", "native alternatives", "manual lifetime; slices", "native compiler", "contracts and checked optionals", "C ABI continuity, modules and hygienic macros"),
    ("Hare", "native alternatives", "manual lifetime", "QBE/native", "static types; tagged unions", "small compiler, explicit control flow"),
    ("Myrddin", "native alternatives", "manual lifetime; no GC", "native backend", "ML-style type inference", "algebraic data and predictable runtime"),
    ("V", "native alternatives", "autofree / reference counting", "native or C translation", "static analysis", "simple syntax and generated C boundary"),
    ("Vale", "native alternatives", "generational references", "native compiler", "runtime generation checks", "memory safety without a tracing collector"),
    ("Austral", "native alternatives", "linear types", "native compiler", "linear resource proof", "single-use resources and deterministic cleanup"),
    ("Cone", "native alternatives", "selectable ownership strategies", "native compiler", "gradual static typing", "per-type memory policy and interoperability"),
    ("Kit", "native alternatives", "explicit / value-oriented", "C translation", "static types and traits", "zero-cost abstractions and rewrite rules"),
    ("Carp", "native alternatives", "ownership and borrowing", "native compiler", "static types", "functional syntax with deterministic lifetime"),
    ("Dale", "native alternatives", "manual lifetime", "LLVM", "static types", "Lisp syntax with low-level code generation"),
    ("Zed", "native alternatives", "manual layout control", "native compiler", "explicit machine representation", "alignment, cache layout and calling conventions"),
    ("Biscuit", "native alternatives", "explicit low-level ownership", "native compiler", "isolated unsafe operations", "small embedded binaries and predictable layout"),
    ("Carbon", "C++ and LLVM evolution", "C++ interop and gradual safety", "LLVM ecosystem", "checked generics roadmap", "incremental C++ migration and ABI boundary"),
    ("Cpp2", "C++ and LLVM evolution", "ownership-oriented parameter modes", "translates to C++", "safe-by-default syntax", "safer surface syntax over established C++"),
    ("Lobster", "C++ and LLVM evolution", "compile-time reference counting", "C++ / LLVM", "static type inference", "ownership graph analysis for game workloads"),
    ("Nim", "C++ and LLVM evolution", "ARC / ORC", "C / C++ / Objective-C", "static typing and AST macros", "deterministic reference management and metaprogramming"),
    ("Crystal", "C++ and LLVM evolution", "Boehm GC by default; explicit pointers", "LLVM", "static inference", "Ruby-like syntax over native compilation"),
    ("D BetterC", "C++ and LLVM evolution", "manual / user-managed", "native D compiler", "compile-time introspection", "C ABI interoperability without full D runtime"),
    ("Terra", "C++ and LLVM evolution", "manual low-level control", "LLVM", "Lua metaprogramming", "staged programming with native runtime code"),
    ("Clay", "C++ and LLVM evolution", "explicit low-level control", "native compiler", "compile-time polymorphism", "type-level computation and specialization"),
    ("Felix", "C++ and LLVM evolution", "runtime-managed fibers", "C++ translation", "static typing", "cooperative concurrency and generated state machines"),
    ("Volt", "C++ and LLVM evolution", "manual / explicit runtime policy", "native compiler", "static typing", "C/D-style systems and graphics workloads"),
    ("ATS", "verification and safety", "linear types and manual allocation", "native compiler", "dependent-type proofs", "proof-carrying pointer and buffer invariants"),
    ("F*", "verification and safety", "functional values and verified extraction", "KaRaMeL to C", "dependent types and proofs", "verified cryptographic and systems components"),
    ("Cogent", "verification and safety", "uniqueness types", "C extraction", "Isabelle/HOL proofs", "in-place updates with functional verification"),
    ("BitC", "verification and safety", "explicit representation", "native research compiler", "strong typed low-level model", "ML-like types with hardware data layout"),
    ("Habit", "verification and safety", "explicit low-level memory layout", "native research compiler", "functional type system", "register and page-table representation"),
    ("Ivory", "verification and safety", "static allocation", "safe C subset", "no-UB DSL constraints", "embedded control with bounded memory"),
    ("ParaSail", "verification and safety", "value semantics; no pointers", "native compiler", "race-free parallel model", "parallel computation without shared mutable state"),
    ("SPARK", "verification and safety", "controlled Ada storage model", "Ada toolchain", "formal contracts and proofs", "prove runtime safety and specification conformance"),
    ("nesC", "embedded and constrained", "C-like static storage", "C / TinyOS toolchain", "whole-program race analysis", "component graph and interrupt-aware concurrency"),
    ("eC", "embedded and constrained", "C-compatible object model", "native C-family compiler", "type-safe modules", "systems C with modules and reflection"),
    ("XC", "embedded and constrained", "static resource allocation", "XMOS compiler", "CSP and cycle-aware checking", "hardware channels and deterministic scheduling"),
    ("Forth", "embedded and constrained", "dictionary and stack-managed memory", "threaded / native", "interactive system model", "tiny kernels, extensible words and firmware consoles"),
    ("Factor", "embedded and constrained", "managed runtime", "native optimizing VM", "stack-effect inference", "concatenative code and native FFI"),
    ("JAL", "embedded and constrained", "device-specific static memory", "PIC assembler output", "device constraints", "banked memory, registers and compact MCU code"),
    ("Plankalkül", "embedded and constrained", "explicit structured data", "historical design", "typed bit-level model", "early arrays, records and bit-vector computation"),
    ("C--", "embedded and constrained", "backend-defined stack and registers", "compiler intermediate target", "compiler-controlled invariants", "portable low-level code generation interface"),
    ("BLISS", "historical systems", "address-oriented manual memory", "native DEC compiler", "explicit dereference semantics", "machine-oriented OS implementation"),
    ("BCPL", "historical systems", "word-addressed manual memory", "native / historical compilers", "untyped word model", "compact systems language lineage before C"),
    ("B", "historical systems", "word-oriented manual memory", "historical native compiler", "minimal type model", "direct ancestor in early Unix lineage"),
    ("PL/M", "historical systems", "static memory and port I/O", "Intel microcomputer toolchains", "hardware-oriented types", "early microprocessor OS and firmware"),
    ("PL/S", "historical systems", "system-managed storage and registers", "IBM internal compiler", "systems contracts", "mainframe kernel implementation"),
    ("ESPOL", "historical systems", "stack-architecture data model", "Burroughs compiler", "hardware-enforced descriptors", "system software for tagged stack machines"),
    ("Mesa", "historical systems", "typed modules and managed storage", "Xerox Mesa compiler", "module interfaces and exceptions", "interfaces separated from implementations"),
    ("Modula-2", "historical systems", "explicit low-level storage", "native compiler", "strict modules and types", "device interfaces, coroutines and modular OS design"),
    ("Oberon", "historical systems", "explicit record and pointer model", "native compiler", "type extension", "small integrated language and operating system"),
    ("Active Oberon", "historical systems", "object-owned concurrency", "native compiler", "active objects", "language-integrated threads and synchronization"),
    ("Component Pascal", "historical systems", "explicit SYSTEM escape hatch", "native compiler", "component modules", "isolated unsafe operations and typed components"),
    ("Sather", "historical systems", "runtime-managed object model", "C translation", "contracts and iterators", "compiled object abstractions with efficient iteration"),
    ("Alef", "historical systems", "process-local memory and channels", "Plan 9 compiler", "typed concurrent channels", "message passing for OS services"),
    ("Limbo", "historical systems", "runtime-managed module model", "Dis bytecode / JIT", "channel-oriented concurrency", "portable modules and CSP-style processes"),
    ("Newsqueak", "historical systems", "channel-owned communication model", "research interpreter", "first-class channels", "concurrent interactive systems"),
    ("Cyclone", "research and specialist", "regions and checked pointers", "native C-family compiler", "bounds and nullability checks", "safer C migration ideas and region memory"),
    ("Vault", "research and specialist", "linear resources and typestates", "research compiler", "protocol-state checking", "verify legal driver resource transitions"),
    ("Sing#", "research and specialist", "isolated software contracts", "research C# compiler", "typed channel contracts", "microkernel message boundaries"),
    ("Midori C#", "research and specialist", "isolated heaps and ownership", "native research compiler", "ownership and async contracts", "managed-language systems architecture"),
    ("Pre-Scheme", "research and specialist", "manual / restricted closure lifetime", "C translation", "static functional subset", "macro-rich systems code with small runtime"),
    ("Linear Lisp", "research and specialist", "single-reference linear ownership", "research compiler model", "linear resource discipline", "deterministic reclamation without tracing GC"),
    ("Clay generative core", "research and specialist", "explicit low-level storage", "native compiler model", "Turing-complete compile-time model", "type-level vectors, allocators and specialization"),
    ("Nimrod", "research and specialist", "historical Nim memory model", "C translation", "static inference", "historical name for early Nim lineage"),
    ("Slang", "research and specialist", "GPU resource and address-space model", "SPIR-V / DXIL / Metal / CUDA", "interfaces and generic shader types", "GPU shader systems and differentiable programming"),
    ("Mojo", "research and specialist", "ownership and borrowing model", "MLIR / native", "static systems types", "Python interoperability with low-level performance paths"),
    ("HLA", "research and specialist", "explicit stack and register model", "x86 assembler", "high-level assembler types", "structured assembly and direct machine instructions"),
)

LANGUAGES: tuple[LanguageProfile, ...] = tuple(
    LanguageProfile(index, *row) for index, row in enumerate(_LANGUAGE_ROWS, start=1)
)

_ARCHITECTURE_ROWS: tuple[tuple[str, str, str, str, str], ...] = (
    ("x86_64", "x86", "desktop / server", "LP64 or LLP64; little-endian", "CPUID, OS vector state, ABI and cache topology"),
    ("x86", "x86", "legacy desktop / embedded", "ILP32; little-endian", "SSE state, 32-bit ABI and address-space limits"),
    ("aarch64", "Arm", "mobile / desktop / server", "AArch64 data model; commonly little-endian", "NEON/SVE features, cache topology and platform ABI"),
    ("armv7-m", "Arm", "microcontroller", "32-bit MCU; target-defined ABI", "NVIC, interrupt timing, flash/RAM map and FPU"),
    ("riscv64", "RISC-V", "embedded / server", "LP64 variants; target-defined endian", "XLEN, extensions, privilege modes and ABI string"),
    ("riscv32", "RISC-V", "microcontroller / embedded", "ILP32 variants", "XLEN, extensions, interrupt controller and memory map"),
    ("loongarch64", "LoongArch", "desktop / server", "64-bit; little-endian common", "ISA extensions, ABI variant and kernel boundary"),
    ("e2k", "Elbrus", "VLIW server", "64-bit; platform ABI", "MCST compiler version, scheduling and ABI"),
    ("ppc64le", "Power ISA", "server / accelerator", "64-bit; little-endian", "VSX, ABI, NUMA and processor facilities"),
    ("s390x", "IBM Z", "mainframe", "64-bit; big-endian", "vector facility, data layout and ABI"),
    ("avr", "AVR", "8-bit microcontroller", "8-bit; Harvard memory", "program/data address spaces, flash/RAM and interrupts"),
    ("pic8", "Microchip PIC", "8-bit microcontroller", "8-bit banked Harvard memory", "register banks, page boundaries and peripherals"),
    ("xmos-xcore", "XMOS", "deterministic multicore MCU", "32-bit; tile-local resources", "hardware-thread, channel and cycle-budget model"),
    ("wasm32", "WebAssembly", "portable virtual ISA", "32-bit linear memory", "WASI capabilities, bounds and host ABI"),
)

ARCHITECTURES: tuple[ArchitectureProfile, ...] = tuple(
    ArchitectureProfile(index, *row) for index, row in enumerate(_ARCHITECTURE_ROWS, start=1)
)


def validate_atlas() -> None:
    """Raise ValueError if the immutable atlas violates its public invariants."""
    if len(LANGUAGES) != 66:
        raise ValueError(f"language atlas must contain 66 entries, got {len(LANGUAGES)}")
    if [item.id for item in LANGUAGES] != list(range(1, 67)):
        raise ValueError("language IDs must be sequential and unique")
    if len({item.name.casefold() for item in LANGUAGES}) != len(LANGUAGES):
        raise ValueError("language names must be unique")
    if len({item.name.casefold() for item in ARCHITECTURES}) != len(ARCHITECTURES):
        raise ValueError("architecture names must be unique")
    for item in (*LANGUAGES, *ARCHITECTURES):
        if not all(value.strip() for value in (item.name, item.family, item.design_signal if isinstance(item, LanguageProfile) else item.backend_questions)):
            raise ValueError(f"atlas entry {item.id} is incomplete")


def search_atlas(query: str, kind: str = "all") -> tuple[LanguageProfile | ArchitectureProfile, ...]:
    """Search names and descriptive fields without importing or executing toolchains."""
    validate_atlas()
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if kind not in {"all", "languages", "architectures"}:
        raise ValueError("kind must be all, languages, or architectures")
    needle = query.casefold().strip()
    sources: tuple[LanguageProfile | ArchitectureProfile, ...]
    if kind == "languages":
        sources = LANGUAGES
    elif kind == "architectures":
        sources = ARCHITECTURES
    else:
        sources = (*LANGUAGES, *ARCHITECTURES)
    matches: list[LanguageProfile | ArchitectureProfile] = []
    for item in sources:
        if isinstance(item, LanguageProfile):
            values = (item.name, item.family, item.memory_model, item.compilation_model, item.assurance, item.design_signal)
        else:
            values = (item.name, item.family, item.class_name, item.data_model, item.execution_model, item.backend_questions)
        if needle in " ".join(values).casefold():
            matches.append(item)
    return tuple(matches)


def format_atlas(kind: str = "all", query: str | None = None) -> str:
    """Format a stable terminal/CI view of the selected catalogue."""
    validate_atlas()
    if kind not in {"all", "languages", "architectures"}:
        raise ValueError("kind must be all, languages, or architectures")
    if query is not None:
        matches = search_atlas(query, kind)
        heading = f"Reaper systems atlas search: {query!r} ({len(matches)} match(es))"
    else:
        matches = LANGUAGES if kind == "languages" else ARCHITECTURES if kind == "architectures" else (*LANGUAGES, *ARCHITECTURES)
        heading = (
            f"Reaper systems atlas: {len(LANGUAGES)} language profiles"
            if kind == "languages"
            else f"Reaper systems atlas: {len(ARCHITECTURES)} architecture profiles"
            if kind == "architectures"
            else f"Reaper systems atlas: {len(LANGUAGES)} language profiles + {len(ARCHITECTURES)} architecture profiles"
        )
    lines = [heading, "Reference data only; entries do not imply an installed compiler or implemented Reaper backend."]
    for item in matches:
        if isinstance(item, LanguageProfile):
            lines.append(f"L{item.id:02d} | {item.name} | {item.family}")
            lines.append(f"     Memory: {item.memory_model} | Compile: {item.compilation_model}")
            lines.append(f"     Assurance: {item.assurance} | Design signal: {item.design_signal}")
        else:
            lines.append(f"A{item.id:02d} | {item.name} | {item.family} | {item.class_name}")
            lines.append(f"     Data model: {item.data_model} | Backend questions: {item.backend_questions}")
    return "\n".join(lines)


validate_atlas()
