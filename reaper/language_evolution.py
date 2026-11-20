"""OmniCore: bounded ingestion and evidence-led evolution proposals for Reaper.

M1 is deliberately read-only: it never executes foreign code or changes a language
core. Python uses its standard AST; optional Tree-sitter grammars are used when
already installed, otherwise a conservative structural adapter preserves uncertainty.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, Iterable

SCHEMA = "reaper-omnicore-report/v1"
MEMORY_SCHEMA = "reaper-omnicore-memory/v1"
DEFAULT_FILES, DEFAULT_FILE_BYTES, DEFAULT_TOTAL_BYTES = 2_000, 2_000_000, 50_000_000
MAX_NODES = 2_500
IGNORED = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules", "vendor", "third_party", "build", "dist", "target", "out", "coverage", "site-packages", "Pods", "DerivedData"}
EXT = {
    ".py": "python", ".pyi": "python", ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".rs": "rust", ".go": "go", ".java": "java", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".cs": "csharp", ".kt": "kotlin", ".swift": "swift", ".rb": "ruby",
    ".php": "php", ".scala": "scala", ".lua": "lua", ".pl": "perl", ".jl": "julia", ".zig": "zig", ".nim": "nim",
    ".ex": "elixir", ".exs": "elixir", ".erl": "erlang", ".dart": "dart", ".sql": "sql", ".sh": "shell", ".bash": "shell",
    ".ps1": "powershell", ".hs": "haskell", ".ml": "ocaml", ".clj": "clojure", ".elm": "elm", ".sol": "solidity",
    ".move": "move", ".wat": "webassembly-text", ".asm": "assembly", ".s": "assembly", ".rpr": "reaper",
}
GRAMMARS = {".g4": "antlr", ".peg": "peg", ".peggy": "peg", ".pest": "pest", ".lark": "lark", ".ebnf": "ebnf", ".bnf": "bnf", ".y": "bison", ".yy": "bison", ".lex": "lex", ".l": "lex"}
MANIFESTS = {"pyproject.toml": "python", "setup.py": "python", "requirements.txt": "python-deps", "package.json": "node", "tsconfig.json": "typescript", "Cargo.toml": "rust", "go.mod": "go", "CMakeLists.txt": "cmake", "Makefile": "make", "meson.build": "meson", "build.gradle": "gradle", "pom.xml": "maven", "composer.json": "php", "Gemfile": "ruby", "Package.swift": "swift", "mix.exs": "elixir", "pubspec.yaml": "dart", "BUILD.bazel": "bazel", "flake.nix": "nix", "Dockerfile": "container"}
TEST_DIRS = {"test", "tests", "spec", "specs", "fixtures", "conformance", "integration"}


@dataclass(frozen=True, slots=True)
class UASTNode:
    kind: str
    name: str | None
    start_line: int
    end_line: int
    confidence: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)
    children: tuple["UASTNode", ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "start_line": self.start_line, "end_line": self.end_line,
                "confidence": self.confidence, "attributes": self.attributes,
                "children": [node.to_dict() for node in self.children]}


@dataclass(frozen=True, slots=True)
class Evidence:
    feature: str
    count: int
    files: tuple[str, ...]
    languages: tuple[str, ...]
    confidence: float
    details: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvolutionProposal:
    proposal_id: str
    feature: str
    profile: str
    classification: str
    status: str
    utility_score: float
    complexity_cost: float
    evidence_count: int
    source_files: tuple[str, ...]
    rationale: str
    guardrails: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FileAnalysis:
    path: str
    language: str
    sha256: str
    bytes: int
    lines: int
    parser: str
    node_counts: dict[str, int]
    symbols: tuple[str, ...]
    opaque_regions: tuple[dict[str, Any], ...]
    evidence: tuple[Evidence, ...]
    is_test: bool
    uast: tuple[UASTNode, ...] = ()

    def to_dict(self, include_uast: bool = False) -> dict[str, Any]:
        result = {"path": self.path, "language": self.language, "sha256": self.sha256, "bytes": self.bytes,
                  "lines": self.lines, "parser": self.parser, "node_counts": self.node_counts,
                  "symbols": list(self.symbols), "opaque_regions": list(self.opaque_regions),
                  "evidence": [item.to_dict() for item in self.evidence], "is_test": self.is_test}
        if include_uast:
            result["uast"] = [item.to_dict() for item in self.uast]
        return result


@dataclass(frozen=True, slots=True)
class IngestionArtifact:
    path: str
    kind: str
    sha256: str
    bytes: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AbsorptionReport:
    root: str
    mode: str
    files_discovered: int
    files_analyzed: int
    bytes_analyzed: int
    languages: dict[str, int]
    artifacts: tuple[IngestionArtifact, ...]
    files: tuple[FileAnalysis, ...]
    evidence: tuple[Evidence, ...]
    proposals: tuple[EvolutionProposal, ...]
    skipped: dict[str, int]
    warnings: tuple[str, ...]
    protected_paths: tuple[str, ...] = field(default=(), repr=False)

    def to_dict(self, include_uast: bool = False) -> dict[str, Any]:
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []
        languages: set[str] = set()
        for item in self.files:
            language_id = f"language:{item.language}"
            if item.language not in languages:
                nodes.append({"id": language_id, "kind": "language", "label": item.language})
                languages.add(item.language)
            source_id = f"source:{item.sha256[:16]}"
            nodes.append({"id": source_id, "kind": "source", "label": item.path})
            edges.append({"from": source_id, "relation": "written-in", "to": language_id})
        for item in self.evidence:
            concept_id = f"concept:{item.feature}"
            nodes.append({"id": concept_id, "kind": "concept", "label": item.feature})
            for language in item.languages:
                language_id = f"language:{language}"
                if language not in languages:
                    nodes.append({"id": language_id, "kind": "language", "label": language})
                    languages.add(language)
                edges.append({"from": concept_id, "relation": "observed-in", "to": language_id})
        for item in self.proposals:
            proposal_id = f"proposal:{item.proposal_id}"
            nodes.append({"id": proposal_id, "kind": "proposal", "label": item.feature})
            edges.append({"from": proposal_id, "relation": "proposes-evolution-of", "to": f"concept:{item.feature}"})
        return {"schema": SCHEMA, "engine": "OmniCore Language Evolution Engine", "engine_version": "0.1.0-m1",
                "root": self.root, "mode": self.mode, "files_discovered": self.files_discovered,
                "files_analyzed": self.files_analyzed, "bytes_analyzed": self.bytes_analyzed,
                "languages": self.languages, "artifacts": [item.to_dict() for item in self.artifacts],
                "files": [item.to_dict(include_uast) for item in self.files],
                "knowledge_graph": {"nodes": nodes, "edges": edges},
                "evidence": [item.to_dict() for item in self.evidence],
                "proposals": [item.to_dict() for item in self.proposals], "skipped": self.skipped,
                "warnings": list(self.warnings),
                "execution_policy": {"foreign_code_executed": False, "toolchains_invoked": False,
                                     "network_access": False, "source_files_modified": False,
                                     "language_core_modified": False}}

    def to_json(self, include_uast: bool = False) -> str:
        return json.dumps(self.to_dict(include_uast), ensure_ascii=False, indent=2, sort_keys=True)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _walk(nodes: Iterable[UASTNode]) -> Iterable[UASTNode]:
    for node in nodes:
        yield node
        yield from _walk(node.children)


def _python_ast(source: str) -> tuple[UASTNode, ...]:
    kinds: dict[type[ast.AST], str] = {
        ast.FunctionDef: "FunctionDecl", ast.AsyncFunctionDef: "FunctionDecl", ast.ClassDef: "TypeDecl",
        ast.Import: "ImportDecl", ast.ImportFrom: "ImportDecl", ast.Assign: "BindingDecl", ast.AnnAssign: "BindingDecl",
        ast.AugAssign: "Mutation", ast.If: "Branch", ast.IfExp: "ConditionalExpr", ast.For: "Loop", ast.AsyncFor: "Loop",
        ast.While: "Loop", ast.Match: "PatternMatch", ast.Try: "ErrorBoundary", ast.With: "ResourceScope",
        ast.AsyncWith: "ResourceScope", ast.Return: "Return", ast.Yield: "Yield", ast.YieldFrom: "Yield",
        ast.Call: "Call", ast.Await: "Await", ast.Raise: "Raise", ast.Assert: "Assertion", ast.Lambda: "Lambda",
        ast.Dict: "MapLiteral", ast.List: "SequenceLiteral", ast.Set: "SetLiteral", ast.Tuple: "TupleLiteral",
        ast.ListComp: "Comprehension", ast.SetComp: "Comprehension", ast.DictComp: "Comprehension",
        ast.GeneratorExp: "Comprehension", ast.BinOp: "BinaryExpr", ast.BoolOp: "BooleanExpr", ast.Compare: "CompareExpr",
    }
    budget = [MAX_NODES]
    def visit(item: ast.AST) -> UASTNode | None:
        if budget[0] <= 0:
            return None
        budget[0] -= 1
        name = getattr(item, "name", None)
        if isinstance(item, ast.Call):
            name = item.func.id if isinstance(item.func, ast.Name) else ast.unparse(item.func)[:100]
        if isinstance(item, (ast.Assign, ast.AnnAssign)):
            target = item.targets[0] if isinstance(item, ast.Assign) else item.target
            name = target.id if isinstance(target, ast.Name) else None
        children = tuple(child for node in ast.iter_child_nodes(item) if (child := visit(node)) is not None)
        line = int(getattr(item, "lineno", 1))
        return UASTNode(kinds.get(type(item), "SyntaxNode"), name, line,
                        int(getattr(item, "end_lineno", line)), 1.0,
                        {"python_ast": type(item).__name__}, children)
    tree = ast.parse(source)
    return tuple(node for item in tree.body if (node := visit(item)) is not None)


def _tree_sitter(source: str, language: str) -> tuple[UASTNode, ...] | None:
    aliases = {"cpp": "cpp", "c": "c", "rust": "rust", "javascript": "javascript", "typescript": "typescript",
               "csharp": "c_sharp", "go": "go", "java": "java", "ruby": "ruby", "php": "php", "kotlin": "kotlin", "swift": "swift"}
    name = aliases.get(language)
    if not name:
        return None
    try:
        try:
            from tree_sitter_language_pack import get_parser
        except ImportError:
            from tree_sitter_languages import get_parser
        parser = get_parser(name)
        root = parser.parse(source.encode("utf-8")).root_node
    except (ImportError, LookupError, RuntimeError, TypeError, ValueError):
        return None
    kinds = {"function_definition": "FunctionDecl", "function_declaration": "FunctionDecl", "function_item": "FunctionDecl",
             "method_definition": "FunctionDecl", "class_definition": "TypeDecl", "class_declaration": "TypeDecl",
             "struct_item": "TypeDecl", "enum_item": "TypeDecl", "call_expression": "Call", "if_statement": "Branch",
             "for_statement": "Loop", "while_statement": "Loop", "match_expression": "PatternMatch",
             "try_statement": "ErrorBoundary", "import_statement": "ImportDecl", "return_statement": "Return"}
    raw = source.encode("utf-8")
    budget = [MAX_NODES]
    def visit(item: Any) -> UASTNode | None:
        if budget[0] <= 0:
            return None
        budget[0] -= 1
        kind = str(item.type)
        line = int(item.start_point[0]) + 1
        end = int(item.end_point[0]) + 1
        if kind == "ERROR" or bool(getattr(item, "is_missing", False)):
            return UASTNode("OpaqueNode", None, line, end, 0.0, {"tree_sitter_type": kind})
        children = tuple(node for child in item.children if (node := visit(child)) is not None)
        canonical = kinds.get(kind, "Module" if kind in {"source_file", "program", "translation_unit"} else "SyntaxNode")
        return UASTNode(canonical, None, line, end, 0.95, {"tree_sitter_type": kind}, children)
    root_node = visit(root)
    return (root_node,) if root_node else None


def _structural(source: str) -> tuple[tuple[UASTNode, ...], list[dict[str, Any]]]:
    patterns = (("FunctionDecl", r"^\s*(?:(?:pub|public|private|static|async|export|extern|unsafe)\s+)*(?:fn|func|function|def|fun|sub)\s+([\w$]+)"),
                ("TypeDecl", r"^\s*(?:(?:pub|public|private|export|abstract)\s+)*(?:class|struct|record|enum|interface|trait|union|type)\s+([\w$]+)"),
                ("ImportDecl", r"^\s*(?:import|from|use|require|include|#include|package)\b"),
                ("Branch", r"^\s*(?:if|else\s+if|elif|else|switch|case|when)\b"),
                ("Loop", r"^\s*(?:for|foreach|while|loop|do)\b"),
                ("ErrorBoundary", r"^\s*(?:try|catch|except|finally)\b"),
                ("Return", r"^\s*(?:return|yield|throw|raise)\b"),
                ("BindingDecl", r"^\s*(?:let|const|var|val|make|vary|mut)\s+([\w$]+)"))
    nodes: list[UASTNode] = []
    opaque: list[dict[str, Any]] = []
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    token_re = re.compile(r"//[^\n]*|/\*.*?\*/|\#[^\n]*|--[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[(){}\[\]]", re.S)
    for match in token_re.finditer(source):
        value = match.group()
        line = source.count("\n", 0, match.start()) + 1
        if value.startswith(("//", "/*", "#", "--", "\"", "'")):
            continue
        if value in "({[":
            stack.append((value, line))
        elif value in pairs:
            if not stack or stack[-1][0] != pairs[value]:
                opaque.append({"line": line, "reason": "unmatched closing delimiter", "token": value})
            else:
                stack.pop()
    opaque.extend({"line": line, "reason": "unclosed delimiter", "token": value} for value, line in stack)
    for line_no, line in enumerate(source.splitlines(), 1):
        if not line.strip():
            continue
        for kind, pattern in patterns:
            match = re.search(pattern, line)
            if match:
                nodes.append(UASTNode(kind, match.group(1) if match.lastindex else None, line_no, line_no, .82, {"adapter": "structural-heuristic"}))
                break
        else:
            nodes.append(UASTNode("Statement", None, line_no, line_no, .55, {"adapter": "structural-heuristic"}))
    for line_no, line in enumerate(source.splitlines(), 1):
        for match in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", line):
            if match.group(1) not in {"if", "for", "while", "switch", "match", "catch", "return", "sizeof"}:
                nodes.append(UASTNode("Call", match.group(1), line_no, line_no, .68, {"adapter": "structural-heuristic"}))
    nodes.extend(UASTNode("OpaqueNode", None, int(item["line"]), int(item["line"]), 0.0, item) for item in opaque)
    nodes.sort(key=lambda item: (item.start_line, item.kind, item.name or ""))
    return tuple(nodes[:MAX_NODES]), opaque


def _features(source: str, nodes: Iterable[UASTNode]) -> Counter[str]:
    text, low = source, source.lower()
    node_counts = Counter(node.kind for node in _walk(nodes))
    patterns = {
        "async_await": r"\b(?:async|await|coroutine|goroutine|spawn)\b",
        "ownership_borrowing": r"\b(?:borrow|borrowing|move|ownership|unsafe)\b|&\s*mut\b|\b(?:Box|Rc|Arc|RefCell)\s*<",
        "error_values": r"\b(?:Result|Option|Either|Ok|Err|Some|None|try|catch|except|throws|throw|raise)\b",
        "pipeline_composition": r"::|\|>|\b(?:map|filter|fold|reduce|compose|pipe)\s*\(",
        "resource_scopes": r"\b(?:defer|using|with|finally|Drop|close|dispose)\b",
        "effects_io": r"\b(?:read|write|open|close|print|input|socket|connect|send|recv|spawn|exec)\s*\(",
        "memory_management": r"\b(?:malloc|calloc|realloc|free|new|delete|alloc|dealloc|Box|Arc|Rc)\b",
        "metaprogramming": r"\b(?:macro|template|quote|quasiquote|decorator|eval|reflection)\b|#\s*\[",
        "contracts": r"\b(?:assert|requires|ensures|invariant|precondition|postcondition)\b",
    }
    counts = Counter({key: len(re.findall(pattern, text if key == "ownership_borrowing" else low)) for key, pattern in patterns.items()})
    counts["algebraic_types"] = node_counts["PatternMatch"] + node_counts["TypeDecl"] * int(bool(re.search(r"\b(?:enum|union|variant|sealed)\b", low)))
    return Counter({key: value for key, value in counts.items() if value > 0})


CATALOG = {
    "async_await": ("concurrency", "semantic-gap", .52, .74, "Structured asynchronous execution recurs in the absorbed sources."),
    "ownership_borrowing": ("systems", "semantic-gap", .68, .82, "Ownership and borrowing require typed lifetime and native memory rules."),
    "algebraic_types": ("systems", "semantic-gap", .63, .72, "Variant types or pattern matching recur in the source set."),
    "error_values": ("systems", "compositional-gap", .64, .48, "Result/Option and exception patterns recur; compare a canonical API before syntax."),
    "pipeline_composition": ("dataflow", "direct-or-compositional", .42, .28, "Compare external pipelines with Reaper's existing :: operator."),
    "resource_scopes": ("systems", "semantic-gap", .58, .66, "Deterministic cleanup or resource scopes recur."),
    "effects_io": ("interop", "semantic-gap", .48, .62, "I/O and process/network effects need explicit capability boundaries."),
    "memory_management": ("systems", "semantic-gap", .61, .79, "Explicit allocation patterns require ownership and allocator semantics."),
    "metaprogramming": ("interop", "compositional-gap", .46, .63, "Macro/template/reflection patterns may fit scoped adapters."),
    "contracts": ("systems", "compositional-gap", .57, .44, "Contracts recur; evaluate a typed library before new primitives."),
}


def _evidence(rows: list[tuple[str, str, Counter[str]]]) -> tuple[Evidence, ...]:
    aggregate: dict[str, int] = Counter()
    sources: dict[str, set[str]] = {}
    langs: dict[str, set[str]] = {}
    for path, language, counts in rows:
        for feature, count in counts.items():
            aggregate[feature] += count
            sources.setdefault(feature, set()).add(path)
            langs.setdefault(feature, set()).add(language)
    return tuple(Evidence(key, count, tuple(sorted(sources[key])), tuple(sorted(langs[key])),
                          round(min(.92, .42 + .07 * min(count, 5) + .04 * min(len(sources[key]), 4)), 3),
                          ("static lexical/structural evidence; validate with parser or trace",))
                 for key, count in sorted(aggregate.items()))


def _proposals(items: tuple[Evidence, ...], minimum: int) -> tuple[EvolutionProposal, ...]:
    result = []
    for item in items:
        if item.feature not in CATALOG or item.count < minimum:
            continue
        profile, kind, base, cost, reason = CATALOG[item.feature]
        utility = round(min(.99, base + min(.20, .05 * (len(item.files) - 1)) + (item.confidence - .5) * .15), 3)
        status = "review-required" if utility >= cost else "below-complexity-threshold"
        if item.feature == "pipeline_composition":
            status = "compare-with-existing-core"
        digest = hashlib.sha256((item.feature + "\n" + "\n".join(item.files)).encode()).hexdigest()[:12]
        result.append(EvolutionProposal(f"lang-evo-{digest}", item.feature, profile, kind, status, utility, cost,
                                        item.count, item.files, reason,
                                        ("No automatic grammar, type, IR, runtime or source changes.",
                                         "Require versioned specification, positive/negative tests and compatibility evidence.",
                                         "Use isolated staging, rollback snapshot and maintainer approval.")))
    return tuple(sorted(result, key=lambda item: (item.status != "review-required", item.feature)))


def _artifact(path: Path) -> tuple[str, str] | None:
    if path.name in MANIFESTS:
        return "build-manifest", MANIFESTS[path.name]
    if path.suffix.lower() in GRAMMARS:
        return "grammar", GRAMMARS[path.suffix.lower()]
    if path.name.lower().endswith((".trace", ".trace.json", ".trace.jsonl", ".profile.json", ".jsonl")):
        return "runtime-trace", "jsonl"
    return None


def _read(path: Path, limit: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError("not a regular file")
        if info.st_size > limit:
            raise OverflowError("file-size-limit")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            data = handle.read(limit + 1)
        if len(data) > limit:
            raise OverflowError("file-size-limit")
        return data
    finally:
        if fd >= 0:
            os.close(fd)


def _artifact_metadata(kind: str, name: str, text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"adapter": name}
    if kind == "runtime-trace":
        events, types = Counter(), Counter()
        valid = malformed = 0
        for line in text.splitlines()[:100_000]:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    malformed += 1
                    continue
                valid += 1
                event = row.get("event") or row.get("kind") or row.get("type")
                if isinstance(event, str):
                    events[event[:80]] += 1
                for key in ("argument_type", "return_type", "value_type", "runtime_type"):
                    if isinstance(row.get(key), str):
                        types[row[key][:100]] += 1
            except json.JSONDecodeError:
                malformed += 1
        result.update(valid_records=valid, malformed_records=malformed, events=dict(events.most_common(40)), observed_types=dict(types.most_common(40)))
    elif kind == "grammar":
        result.update(nonempty_lines=sum(bool(line.strip()) for line in text.splitlines()),
                      rule_candidates=len(re.findall(r"(?m)^\s*[\w.:-]+\s*(?::|=)", text)))
    elif name == "rust":
        result["declared_rust_version"] = (re.search(r'(?m)^rust-version\s*=\s*["\']([^"\']+)', text) or [None, None])[1]
    elif name == "go":
        result["declared_go_version"] = (re.search(r"(?m)^go\s+([\d.]+)", text) or [None, None])[1]
    elif name == "node":
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                result["project_name"] = data.get("name")
                result["runtime_constraints"] = data.get("engines", {}) if isinstance(data.get("engines"), dict) else {}
        except json.JSONDecodeError:
            result["parse_warning"] = "invalid JSON manifest"
    elif name == "python":
        match = re.search(r'(?m)^requires-python\s*=\s*["\']([^"\']+)', text)
        if match:
            result["requires_python"] = match.group(1)
    return result


class OmniCoreEngine:
    """Analyze a local source tree under fixed budgets; never execute its contents."""
    def __init__(self, root: str | Path, *, max_files: int = DEFAULT_FILES, max_file_bytes: int = DEFAULT_FILE_BYTES,
                 max_total_bytes: int = DEFAULT_TOTAL_BYTES, min_occurrences: int = 2, mode: str = "read-only"):
        self.root = Path(root).expanduser().resolve()
        if min(max_files, max_file_bytes, max_total_bytes, min_occurrences) < 1:
            raise ValueError("all ingestion limits must be positive")
        if mode not in {"read-only", "co-design", "autonomous", "revision"}:
            raise ValueError("mode must be read-only, co-design, autonomous or revision")
        self.limits = (max_files, max_file_bytes, max_total_bytes)
        self.minimum, self.mode = min_occurrences, mode

    def _paths(self) -> list[Path]:
        if not self.root.exists():
            raise ValueError(f"input path does not exist: {self.root}")
        if self.root.is_file():
            return [self.root]
        found = []
        for base, dirs, names in os.walk(self.root, topdown=True, followlinks=False):
            parent = Path(base)
            dirs[:] = sorted(name for name in dirs if name not in IGNORED and not (parent / name).is_symlink())
            found.extend(parent / name for name in sorted(names) if not (parent / name).is_symlink() and (parent / name).is_file())
        return sorted(found, key=lambda path: path.relative_to(self.root).as_posix())

    def run(self) -> AbsorptionReport:
        paths = self._paths()
        max_files, max_file_bytes, max_total_bytes = self.limits
        files, artifacts, rows = [], [], []
        skipped, languages = Counter(), Counter()
        warnings, total = [], 0
        candidates = 0
        for path in paths:
            relative = path.relative_to(self.root).as_posix() if self.root.is_dir() else path.name
            kind = _artifact(path)
            language = EXT.get(path.suffix)
            if language is None and kind is None:
                skipped["unsupported-file"] += 1
                continue
            candidates += 1
            if candidates > max_files:
                skipped["file-count-limit"] += 1
                continue
            remaining = max_total_bytes - total
            if remaining <= 0:
                skipped["total-byte-limit"] += 1
                continue
            try:
                raw = _read(path, min(max_file_bytes, remaining))
            except OverflowError:
                skipped["file-size-limit"] += 1
                continue
            except OSError:
                skipped["unreadable-or-nonregular"] += 1
                continue
            if b"\0" in raw:
                skipped["binary-file"] += 1
                continue
            try:
                source = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                skipped["non-utf8-file"] += 1
                continue
            total += len(raw)
            digest = _sha(raw)
            if kind:
                artifact_kind, adapter = kind
                metadata = _artifact_metadata(artifact_kind, adapter, source)
                artifacts.append(IngestionArtifact(relative, artifact_kind, digest, len(raw), metadata))
                if artifact_kind == "runtime-trace":
                    observations = sum(metadata.get("observed_types", {}).values())
                    if observations:
                        rows.append((relative, "runtime-trace", Counter({"runtime_type_observations": observations})))
                continue
            parser_name, opaque = "structural-lexer", []
            try:
                if language == "python":
                    nodes, parser_name = _python_ast(source), "python-ast"
                else:
                    nodes = _tree_sitter(source, language)
                    if nodes is not None:
                        parser_name = "tree-sitter"
                    else:
                        nodes, opaque = _structural(source)
            except (SyntaxError, ValueError, RecursionError) as error:
                nodes, opaque = _structural(source)
                opaque.append({"line": getattr(error, "lineno", 1) or 1,
                               "reason": f"parser recovery: {type(error).__name__}: {str(error)[:160]}"})
                parser_name = "python-ast-with-opaque-recovery"
            flat = tuple(_walk(nodes))
            counts = Counter(node.kind for node in flat)
            symbols = tuple(sorted({node.name for node in flat if node.name and node.kind in {"FunctionDecl", "TypeDecl", "BindingDecl"}})[:200])
            opaque += [dict(node.attributes, line=node.start_line) for node in flat if node.kind == "OpaqueNode"]
            feature_counts = _features(source, flat)
            rows.append((relative, language, feature_counts))
            languages[language] += 1
            local_evidence = tuple(Evidence(key, value, (relative,), (language,), .65, ("static lexical/structural signal",))
                                   for key, value in sorted(feature_counts.items()))
            files.append(FileAnalysis(relative, language, digest, len(raw), len(source.splitlines()), parser_name,
                                      dict(sorted(counts.items())), symbols, tuple(opaque[:100]), local_evidence,
                                      any(part.lower() in TEST_DIRS for part in path.parts), tuple(nodes)))
        evidence = _evidence(rows)
        proposals = _proposals(evidence, self.minimum)
        if not files and not artifacts:
            warnings.append("No supported source, grammar, build-manifest or runtime-trace artifacts were found.")
        if any(item.parser == "structural-lexer" for item in files):
            warnings.append("Non-Python structural parsing is heuristic, not a complete parser or type checker.")
        if artifacts and not any(item.kind == "runtime-trace" for item in artifacts):
            warnings.append("No runtime trace found; dynamic types and execution invariants remain unobserved.")
        protected = tuple(path.relative_to(self.root).as_posix() if self.root.is_dir() else path.name for path in paths)
        return AbsorptionReport(str(self.root), self.mode, len(paths), len(files), total, dict(sorted(languages.items())),
                                tuple(artifacts), tuple(files), evidence, proposals, dict(sorted(skipped.items())),
                                tuple(dict.fromkeys(warnings)), protected)


def _atomic_write(path: Path, text: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _guard_output(path: Path, report: AbsorptionReport) -> None:
    dest, root = path.expanduser().resolve(), Path(report.root).resolve()
    protected = {str((root / name).resolve()) for name in report.protected_paths}
    protected.update(str((root / item.path).resolve()) for item in report.files + report.artifacts)
    if dest == root or str(dest) in protected:
        raise ValueError("output path would overwrite the scanned input, source or artifact")


def _persist_memory(path: Path, report: AbsorptionReport) -> None:
    data = {"schema": MEMORY_SCHEMA, "sources": {}, "features": {}, "decisions": []}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != MEMORY_SCHEMA:
            raise ValueError(f"evolution memory must use schema {MEMORY_SCHEMA}")
    for item in report.files:
        data.setdefault("sources", {})[item.path] = {"sha256": item.sha256, "language": item.language, "bytes": item.bytes}
    for item in report.evidence:
        prior = data.setdefault("features", {}).setdefault(item.feature, {"count": 0, "files": [], "languages": [], "confidence": 0.0})
        prior["count"] = max(int(prior.get("count", 0)), item.count)
        prior["files"] = sorted(set(prior.get("files", [])) | set(item.files))
        prior["languages"] = sorted(set(prior.get("languages", [])) | set(item.languages))
        prior["confidence"] = max(float(prior.get("confidence", 0)), item.confidence)
    known = {item.get("proposal_id") for item in data.setdefault("decisions", []) if isinstance(item, dict)}
    for item in report.proposals:
        if item.proposal_id not in known:
            data["decisions"].append({"proposal_id": item.proposal_id, "feature": item.feature, "status": item.status})
    data["knowledge_graph"] = report.to_dict()["knowledge_graph"]
    data["last_report"] = {"root": report.root, "files_analyzed": report.files_analyzed,
                            "proposal_ids": [item.proposal_id for item in report.proposals]}
    _atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def format_report(report: AbsorptionReport) -> str:
    lines = ["OmniCore Language Evolution Engine — absorption report", f"Root: {report.root}", f"Mode: {report.mode}",
             f"Source files: {report.files_analyzed}/{report.files_discovered}; {report.bytes_analyzed} bytes",
             "Languages: " + (", ".join(f"{key}={value}" for key, value in report.languages.items()) or "none"),
             f"Artifacts: {len(report.artifacts)} (grammars, manifests, traces)", f"Semantic evidence: {len(report.evidence)}"]
    lines.extend(f"  - {item.feature}: {item.count} signal(s), {len(item.files)} file(s), confidence={item.confidence:.2f} [heuristic]" for item in report.evidence)
    lines.append(f"Evolution proposals: {len(report.proposals)} (proposal-only)")
    lines.extend(f"  - {item.proposal_id} {item.feature}: {item.status}; utility={item.utility_score:.2f}; cost={item.complexity_cost:.2f}" for item in report.proposals)
    lines.extend(f"Warning: {item}" for item in report.warnings)
    if report.skipped:
        lines.append("Skipped: " + ", ".join(f"{key}={value}" for key, value in report.skipped.items()))
    lines.append("Safety: no foreign execution, no network, no source or language-core changes.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper absorb", description="Ingest external language sources and propose Reaper language extensions.")
    parser.add_argument("path", type=Path, help="source file or repository directory")
    parser.add_argument("--mode", choices=("read-only", "co-design", "autonomous", "revision"), default="read-only")
    parser.add_argument("--min-occurrences", type=int, default=2)
    parser.add_argument("--max-files", type=int, default=DEFAULT_FILES)
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_FILE_BYTES)
    parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_TOTAL_BYTES)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--include-uast", action="store_true", help="include normalized AST nodes in JSON output")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--proposal-dir", type=Path)
    parser.add_argument("--memory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.include_uast and not args.json:
        parser.error("--include-uast requires --json")
    try:
        report = OmniCoreEngine(args.path, max_files=args.max_files, max_file_bytes=args.max_file_bytes,
                                max_total_bytes=args.max_total_bytes, min_occurrences=args.min_occurrences,
                                mode=args.mode).run()
        payload = report.to_json(args.include_uast) + "\n"
        if args.output:
            _guard_output(args.output, report)
            _atomic_write(args.output, payload)
        if args.proposal_dir:
            args.proposal_dir.mkdir(parents=True, exist_ok=True)
            for item in report.proposals:
                path = args.proposal_dir / f"{item.proposal_id}.json"
                _guard_output(path, report)
                _atomic_write(path, json.dumps(item.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        if args.memory:
            _guard_output(args.memory, report)
            _persist_memory(args.memory, report)
        print(payload, end="") if args.json else print(format_report(report))
        return 0
    except (OSError, ValueError, OverflowError, json.JSONDecodeError) as error:
        print(f"reaper absorb: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
