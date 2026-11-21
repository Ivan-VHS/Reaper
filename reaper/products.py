"""Registry and safe local services for Reaper's integrated product ecosystem.

All products are in-process capabilities of Reaper, not separate applications.
The registry is descriptive; each service below performs bounded inspection and
never executes arbitrary project code or silently mutates user files.
"""
from __future__ import annotations

import ast
from collections import defaultdict, deque
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProductSpec:
    name: str
    domain: str
    purpose: str
    capabilities: tuple[str, ...]
    primary_service: str


PRODUCTS: tuple[ProductSpec, ...] = (
    ProductSpec("Operandu", "Data & logic", "Typed values, expressions and transformations.", ("value validation", "schema inspection", "expression metadata"), "inspect_value"),
    ProductSpec("Doopraul", "Actions & workflows", "Action composition, event routing and bounded workflow planning.", ("workflow graph validation", "dependency ordering", "dry-run planning"), "plan_workflow"),
    ProductSpec("Zdoro", "Integrity & diagnostics", "Workspace health, consistency and diagnostic reporting.", ("workspace inspection", "missing-file detection", "integrity summary"), "inspect_workspace"),
    ProductSpec("Pyemont", "Development", "Project structure, source inventory and module construction support.", ("source inventory", "module discovery", "project manifest"), "inspect_project"),
    ProductSpec("Dilly", "Interface & experience", "UI token and interface-contract consistency.", ("design token lint", "label inventory", "theme contract checks"), "lint_design_tokens"),
    ProductSpec("Baplap", "Data infrastructure", "Local metadata indexing and deterministic data catalogs.", ("file catalog", "content fingerprints", "metadata index"), "index_files"),
    ProductSpec("Sretuo", "Quality engineering", "Test discovery and verification planning.", ("test discovery", "coverage target inventory", "test plan"), "plan_tests"),
    ProductSpec("Kali", "Security", "Static security hygiene checks for project source.", ("secret-pattern scan", "unsafe API inventory", "security findings"), "scan_security"),
    ProductSpec("Zalam", "Connectivity", "Versioned internal API and integration contract inspection.", ("contract validation", "integration inventory", "schema checks"), "inspect_contracts"),
    ProductSpec("Liur", "Runtime resources", "Bounded source and process resource observations.", ("source size metrics", "resource budget report", "runtime metadata"), "measure_resources"),
    ProductSpec("Keel Koh", "Knowledge", "Searchable documentation index and cross-reference inventory.", ("documentation index", "heading extraction", "link inventory"), "index_knowledge"),
    ProductSpec("Vorof", "Reverse engineering", "Static reconstruction of source structure without execution.", ("AST inventory", "symbol discovery", "dependency outline"), "inspect_structure"),
    ProductSpec("Vprof", "Profiling & metrics", "Static complexity and code-shape metrics.", ("AST metrics", "complexity estimates", "module comparison"), "profile_source"),
    ProductSpec("Profe", "Engineering standards", "Repository conventions and baseline engineering lint.", ("source convention checks", "documentation checks", "policy inventory"), "check_standards"),
    ProductSpec("Prossee", "Project planning", "Milestones, task dependencies and release planning.", ("task graph validation", "milestone planning", "critical path estimate"), "plan_project"),
    ProductSpec("Vprossee", "Verification & validation", "Traceable requirements and evidence completeness.", ("evidence matrix", "acceptance checks", "verification report"), "verify_evidence"),
    ProductSpec("Professiya", "Learning", "Structured learning paths grounded in repository documentation.", ("learning paths", "topic map", "progress checklist"), "learning_paths"),
    ProductSpec("Profevo", "Evolution", "Migration and deprecation planning with compatibility awareness.", ("deprecation inventory", "migration plan", "change impact outline"), "plan_evolution"),
)

_BY_NAME = {item.name.casefold(): item for item in PRODUCTS}


class ProductError(ValueError):
    """Invalid product request or unsafe input."""


def list_products() -> list[dict[str, Any]]:
    return [asdict(item) for item in PRODUCTS]


def get_product(name: str) -> ProductSpec:
    try:
        return _BY_NAME[name.strip().casefold()]
    except (AttributeError, KeyError) as error:
        raise ProductError(f"unknown Reaper internal product: {name!r}") from error


def _root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ProductError(f"project directory does not exist: {root}")
    return root


def _files(root: Path, suffixes: tuple[str, ...] | None = None) -> list[Path]:
    ignored = {".git", ".venv", "venv", "__pycache__", "build", "dist", ".tox"}
    result = []
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file() and (suffixes is None or path.suffix.lower() in suffixes):
            result.append(path)
    return sorted(result)


def inspect_value(value: Any, *, max_depth: int = 32, max_items: int = 100_000) -> dict[str, Any]:
    """Describe JSON-like data without evaluating expressions or invoking repr hooks."""
    count = 0
    def walk(item: Any, depth: int) -> dict[str, Any]:
        nonlocal count
        count += 1
        if count > max_items:
            raise ProductError(f"value exceeds {max_items} inspected items")
        if depth > max_depth:
            raise ProductError(f"value exceeds maximum nesting depth {max_depth}")
        if item is None or isinstance(item, (bool, int, float, str)):
            if isinstance(item, str) and len(item) > 1_000_000:
                raise ProductError("string exceeds 1000000 characters")
            return {"type": type(item).__name__, "value": item if isinstance(item, (str, bool, int, float)) or item is None else None}
        if isinstance(item, list):
            return {"type": "list", "length": len(item), "items": [walk(child, depth + 1) for child in item]}
        if isinstance(item, tuple):
            return {"type": "tuple", "length": len(item), "items": [walk(child, depth + 1) for child in item]}
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise ProductError("mapping keys must be strings")
            return {"type": "mapping", "length": len(item), "items": {key: walk(child, depth + 1) for key, child in item.items()}}
        raise ProductError(f"unsupported value type: {type(item).__name__}")
    return walk(value, 0)


def plan_workflow(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a declarative DAG and return a deterministic dry-run order."""
    if not isinstance(steps, list) or len(steps) > 10_000:
        raise ProductError("workflow must be a list of at most 10000 steps")
    by_id: dict[str, dict[str, Any]] = {}
    for step in steps:
        if not isinstance(step, dict):
            raise ProductError("each workflow step must be an object")
        step_id = step.get("id")
        deps = step.get("depends_on", [])
        if not isinstance(step_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", step_id):
            raise ProductError(f"invalid workflow step id: {step_id!r}")
        if step_id in by_id:
            raise ProductError(f"duplicate workflow step id: {step_id}")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            raise ProductError(f"depends_on for {step_id} must be a string list")
        by_id[step_id] = step
    incoming = {key: set(step.get("depends_on", [])) for key, step in by_id.items()}
    for key, deps in incoming.items():
        missing = deps - by_id.keys()
        if missing:
            raise ProductError(f"{key} depends on unknown step(s): {', '.join(sorted(missing))}")
        if key in deps:
            raise ProductError(f"{key} cannot depend on itself")
    ready = deque(sorted(key for key, deps in incoming.items() if not deps))
    order: list[str] = []
    while ready:
        current = ready.popleft()
        order.append(current)
        for candidate in sorted(incoming):
            if current in incoming[candidate]:
                incoming[candidate].remove(current)
                if not incoming[candidate] and candidate not in order and candidate not in ready:
                    ready.append(candidate)
    if len(order) != len(by_id):
        cyclic = sorted(key for key, deps in incoming.items() if deps)
        raise ProductError(f"workflow contains a dependency cycle: {', '.join(cyclic)}")
    return {"valid": True, "dry_run": True, "step_count": len(order), "execution_order": order}


def inspect_workspace(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    required = ("README.md", "pyproject.toml", "tests")
    missing = [name for name in required if not (root / name).exists()]
    return {"root": str(root), "python_files": len(_files(root, (".py",))), "test_files": len(list((root / "tests").rglob("test_*.py"))) if (root / "tests").is_dir() else 0, "missing_baseline": missing, "healthy_baseline": not missing}


def inspect_project(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    files = _files(root, (".py", ".c", ".h", ".rpr", ".json", ".toml"))
    return {"root": str(root), "file_count": len(files), "by_extension": {ext or "[no extension]": sum(p.suffix.lower() == ext for p in files) for ext in sorted({p.suffix.lower() for p in files})}, "top_level": sorted(p.name for p in root.iterdir())}


def lint_design_tokens(tokens: dict[str, str]) -> dict[str, Any]:
    if not isinstance(tokens, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in tokens.items()):
        raise ProductError("design tokens must be a string-to-string mapping")
    duplicates: dict[str, list[str]] = defaultdict(list)
    for name, value in tokens.items():
        duplicates[value.casefold()].append(name)
    return {"token_count": len(tokens), "empty_tokens": sorted(k for k, v in tokens.items() if not v.strip()), "duplicate_values": [names for names in duplicates.values() if len(names) > 1]}


def index_files(path: str | Path, *, suffixes: tuple[str, ...] = (".py", ".md", ".json", ".toml", ".rpr")) -> dict[str, Any]:
    root = _root(path)
    entries = []
    for file in _files(root, suffixes):
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        entries.append({"path": file.relative_to(root).as_posix(), "size_bytes": file.stat().st_size, "sha256": digest})
    return {"root": str(root), "count": len(entries), "entries": entries}


def plan_tests(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    tests = _files(root / "tests", (".py",)) if (root / "tests").is_dir() else []
    names = [p.relative_to(root).as_posix() for p in tests if p.name.startswith("test_")]
    return {"discovered": len(names), "tests": names, "recommendation": "Add focused regression tests for every changed public behavior."}


_SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("token-assignment", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"][^'\"]{12,}")),
)


def scan_security(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    findings = []
    for file in _files(root, (".py", ".toml", ".yml", ".yaml", ".json", ".env")):
        try:
            content = file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for label, pattern in _SECRET_PATTERNS:
            for match in pattern.finditer(content):
                findings.append({"rule": label, "path": file.relative_to(root).as_posix(), "line": content.count("\n", 0, match.start()) + 1})
    return {"findings": findings, "finding_count": len(findings), "scope": "static pattern scan; not a complete security audit"}


def inspect_contracts(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(contracts, list):
        raise ProductError("contracts must be a list")
    seen: set[str] = set()
    issues = []
    for index, item in enumerate(contracts):
        if not isinstance(item, dict):
            issues.append({"index": index, "issue": "contract is not an object"})
            continue
        name, version = item.get("name"), item.get("version")
        if not isinstance(name, str) or not name.strip():
            issues.append({"index": index, "issue": "missing contract name"})
        elif name in seen:
            issues.append({"index": index, "issue": f"duplicate contract name: {name}"})
        else:
            seen.add(name)
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version):
            issues.append({"index": index, "issue": "version must be semantic numeric form"})
    return {"contract_count": len(contracts), "valid": not issues, "issues": issues}


def measure_resources(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    files = _files(root)
    return {"file_count": len(files), "total_bytes": sum(p.stat().st_size for p in files), "largest_files": [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size} for p in sorted(files, key=lambda p: (-p.stat().st_size, p.as_posix()))[:10]], "note": "Repository snapshot metrics; not live process telemetry."}


def index_knowledge(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    docs = _files(root, (".md",))
    entries = []
    for file in docs:
        text = file.read_text(encoding="utf-8", errors="replace")
        entries.append({"path": file.relative_to(root).as_posix(), "title": next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), file.stem), "headings": [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")], "links": len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))})
    return {"document_count": len(entries), "documents": entries}


def inspect_structure(source: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ProductError(f"source parse failed: {error}") from error
    symbols = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append({"kind": type(node).__name__, "name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return {"symbols": sorted(symbols, key=lambda item: (item["line"], item["name"])), "imports": sorted(set(imports)), "node_count": sum(1 for _ in ast.walk(tree))}


def profile_source(source: str) -> dict[str, Any]:
    report = inspect_structure(source)
    tree = ast.parse(source)
    report.update({"lines": len(source.splitlines()), "functions": sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)), "classes": sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)), "branches": sum(isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.Match)) for n in ast.walk(tree))})
    return report


def check_standards(path: str | Path) -> dict[str, Any]:
    root = _root(path)
    findings = []
    for file in _files(root, (".py",)):
        try:
            source = file.read_text(encoding="utf-8")
            ast.parse(source)
        except (OSError, UnicodeError, SyntaxError) as error:
            findings.append({"path": file.relative_to(root).as_posix(), "issue": f"Python source is not parseable: {error}"})
    return {"python_files_checked": len(_files(root, (".py",))), "findings": findings, "passed": not findings}


def plan_project(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    plan = plan_workflow(tasks)
    return {"task_count": plan["step_count"], "ordered_tasks": plan["execution_order"], "valid": plan["valid"], "dry_run": True}


def verify_evidence(requirements: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(requirements, list):
        raise ProductError("requirements must be a list")
    rows = []
    for item in requirements:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ProductError("each requirement needs a string id")
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list) or not all(isinstance(value, str) and value.strip() for value in evidence):
            raise ProductError(f"evidence for {item['id']} must be a list of non-empty strings")
        rows.append({"id": item["id"], "verified": bool(evidence), "evidence_count": len(evidence)})
    return {"requirements": rows, "total": len(rows), "verified": sum(row["verified"] for row in rows), "complete": all(row["verified"] for row in rows)}


def learning_paths() -> dict[str, Any]:
    return {"paths": [{"name": "Language user", "topics": ["syntax", "values", "flow composition", "modules", "CLI"]}, {"name": "Runtime engineer", "topics": ["lexer", "parser", "interpreter", "Canonical IR", "VM", "quotas"]}, {"name": "Native contributor", "topics": ["C17 core", "AST ownership", "IR verification", "lowering", "CTest"]}, {"name": "Studio contributor", "topics": ["Tkinter workbench", "debugger", "themes", "accessibility", "UI tests"]}]}


def plan_evolution(changes: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(changes, list):
        raise ProductError("changes must be a list")
    normalized = []
    for item in changes:
        if not isinstance(item, dict) or not isinstance(item.get("component"), str):
            raise ProductError("each change needs a component")
        normalized.append({"component": item["component"], "breaking": bool(item.get("breaking", False)), "migration_required": bool(item.get("breaking", False)), "status": "proposal"})
    return {"changes": normalized, "requires_compatibility_review": any(item["breaking"] for item in normalized), "automatic_mutation": False}


def run_product(name: str, operation: str, **kwargs: Any) -> Any:
    """Dispatch a named, explicitly supported local operation."""
    get_product(name)
    handlers: dict[tuple[str, str], Any] = {
        ("Operandu", "inspect_value"): inspect_value,
        ("Doopraul", "plan_workflow"): plan_workflow,
        ("Zdoro", "inspect_workspace"): inspect_workspace,
        ("Pyemont", "inspect_project"): inspect_project,
        ("Dilly", "lint_design_tokens"): lint_design_tokens,
        ("Baplap", "index_files"): index_files,
        ("Sretuo", "plan_tests"): plan_tests,
        ("Kali", "scan_security"): scan_security,
        ("Zalam", "inspect_contracts"): inspect_contracts,
        ("Liur", "measure_resources"): measure_resources,
        ("Keel Koh", "index_knowledge"): index_knowledge,
        ("Vorof", "inspect_structure"): inspect_structure,
        ("Vprof", "profile_source"): profile_source,
        ("Profe", "check_standards"): check_standards,
        ("Prossee", "plan_project"): plan_project,
        ("Vprossee", "verify_evidence"): verify_evidence,
        ("Professiya", "learning_paths"): learning_paths,
        ("Profevo", "plan_evolution"): plan_evolution,
    }
    handler = handlers.get((get_product(name).name, operation))
    if handler is None:
        raise ProductError(f"unsupported operation {operation!r} for {name}")
    return handler(**kwargs)
