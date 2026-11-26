"""Deterministic .rpr module loading, export isolation, and dependency graphs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ReaperRuntimeError
from .parser import Node, parse


class ModuleError(ReaperRuntimeError):
    """A module could not be resolved, parsed, or loaded."""


class ModuleCycleError(ModuleError):
    """An import would create a dependency cycle."""


class ModuleLoader:
    def __init__(self, interpreter: Any, max_depth: int = 64, max_source_bytes: int = 2_000_000) -> None:
        self.interpreter = interpreter
        self.max_depth = max_depth
        self.max_source_bytes = max_source_bytes
        self.cache: dict[str, dict[str, Any]] = {}
        self.graph: dict[str, set[str]] = {}
        self.loading: list[str] = []

    @staticmethod
    def _canonical(path: Path) -> str:
        return str(path.resolve())

    def begin_root(self, filename: str) -> str | None:
        if filename.startswith("<") and filename.endswith(">"):
            return None
        root = self._canonical(Path(filename))
        self.graph.setdefault(root, set())
        if root not in self.loading:
            self.loading.append(root)
        return root

    def end_root(self, root: str | None) -> None:
        if root and self.loading and self.loading[-1] == root:
            self.loading.pop()

    def resolve(self, specifier: str, importer: str) -> Path:
        if not isinstance(specifier, str) or not specifier.strip():
            raise ModuleError("import path must be non-empty text")
        base = Path(importer).resolve().parent if not importer.startswith("<") else Path.cwd()
        target = (base / specifier).resolve()
        if target.suffix.lower() != ".rpr":
            raise ModuleError(f"Reaper modules must use the .rpr extension: {target}")
        return target

    def load(self, specifier: str, importer: str, *, reload: bool = False) -> dict[str, Any]:
        target = self.resolve(specifier, importer)
        target_name = self._canonical(target)
        importer_name = self._canonical(Path(importer)) if not importer.startswith("<") else importer
        self.graph.setdefault(importer_name, set()).add(target_name)
        if target_name in self.loading:
            start = self.loading.index(target_name)
            chain = self.loading[start:] + [target_name]
            raise ModuleCycleError("cyclic .rpr import: " + " -> ".join(chain))
        if target_name in self.cache and not reload:
            return dict(self.cache[target_name])
        if len(self.loading) >= self.max_depth:
            raise ModuleError(f"module import depth limit ({self.max_depth}) exceeded")
        try:
            source_bytes = target.read_bytes()
        except OSError as error:
            raise ModuleError(f"cannot read module {target}: {error}") from error
        if len(source_bytes) > self.max_source_bytes:
            raise ModuleError(f"module source limit ({self.max_source_bytes} bytes) exceeded: {target}")
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeError as error:
            raise ModuleError(f"module is not valid UTF-8: {target}") from error

        self.loading.append(target_name)
        previous_filename = self.interpreter.filename
        module_env = self.interpreter.globals.__class__(self.interpreter.globals)
        try:
            self.interpreter.filename = target_name
            tree = parse(source, target_name)
            self.interpreter._execute_block(tree, module_env, create_scope=False)
            missing = sorted(name for name in module_env.exports if name not in module_env.values)
            if missing:
                raise ModuleError(f"{target}: exported name(s) were not defined: {', '.join(missing)}")
            exports = {name: module_env.values[name].value for name in sorted(module_env.exports)}
            self.cache[target_name] = exports
            return dict(exports)
        finally:
            self.interpreter.filename = previous_filename
            if self.loading and self.loading[-1] == target_name:
                self.loading.pop()

    def graph_dict(self) -> dict[str, list[str]]:
        return {source: sorted(targets) for source, targets in sorted(self.graph.items())}

    def scan(self, entry: str) -> dict[str, list[str]]:
        """Parse imports recursively without executing any source."""
        self.graph.clear()
        self.loading.clear()
        root_path = Path(entry).resolve()
        root = self._canonical(root_path)
        self.graph[root] = set()
        visiting: list[str] = []

        def walk(path: Path) -> None:
            name = self._canonical(path)
            if name in visiting:
                cycle = visiting[visiting.index(name):] + [name]
                raise ModuleCycleError("cyclic .rpr import: " + " -> ".join(cycle))
            if name in self.graph and name != root and self.graph[name] == set():
                # A parsed leaf is already complete.
                pass
            if name in visiting:
                return
            if len(visiting) >= self.max_depth:
                raise ModuleError(f"module import depth limit ({self.max_depth}) exceeded")
            try:
                raw = path.read_bytes()
            except OSError as error:
                raise ModuleError(f"cannot read module {path}: {error}") from error
            if len(raw) > self.max_source_bytes:
                raise ModuleError(f"module source limit ({self.max_source_bytes} bytes) exceeded: {path}")
            source = raw.decode("utf-8")
            tree = parse(source, name)
            imports: list[str] = []

            def visit(node: Node) -> None:
                if node.kind in {"import", "maza"}:
                    imports.append(node.value[0])
                for child in node.children or []:
                    visit(child)

            visit(tree)
            visiting.append(name)
            self.graph.setdefault(name, set())
            try:
                for specifier in imports:
                    target = self.resolve(specifier, name)
                    target_name = self._canonical(target)
                    self.graph[name].add(target_name)
                    if target_name in visiting:
                        cycle = visiting[visiting.index(target_name):] + [target_name]
                        raise ModuleCycleError("cyclic .rpr import: " + " -> ".join(cycle))
                    if target_name not in self.graph:
                        walk(target)
            finally:
                visiting.pop()

        walk(root_path)
        return self.graph_dict()
