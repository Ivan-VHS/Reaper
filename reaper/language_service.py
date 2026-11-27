"""Versioned, error-tolerant editor services, isolated from compiler execution."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re, threading
from .errors import LexError, ReaperError
from .diagnostic_catalog import explain_diagnostic
from .lexer import KEYWORD_ALIASES
from .parser import parse
from .syntax_profiles import keyword_spellings, resolve_syntax_profile

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[^\W\d]\w*", re.UNICODE)
DECLARATIONS = {"make","vary","craft","fn","let","const","struct","enum","type"}
DECL_ALIASES = {alias for alias, canonical in KEYWORD_ALIASES.items() if canonical in DECLARATIONS}
DECL = re.compile(r"\b(" + "|".join(map(re.escape, sorted(DECLARATIONS | DECL_ALIASES))) + r")\s+([\w]+)")
KEYWORDS = {"make","vary","change","craft","yield","emit","when","otherwise","each","in","loop","while","true","false","nothing","and","or","not","import","export","as"} | set(KEYWORD_ALIASES) | set(KEYWORD_ALIASES.values())
BUILTINS = {"text","number","length","range","map","keep","fold","sum","min","max","sort","reverse","unique","join","split"}

@dataclass(frozen=True, slots=True)
class Span:
    line: int
    start: int
    end: int

@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    kind: str
    uri: str
    span: Span

@dataclass(frozen=True, slots=True)
class Diagnostic:
    message: str
    severity: str
    span: Span
    code: str
    help: str | None = None

@dataclass(frozen=True, slots=True)
class Snapshot:
    uri: str
    version: int
    text: str

@dataclass(frozen=True, slots=True)
class Analysis:
    snapshot: Snapshot
    symbols: tuple[Symbol, ...]
    identifiers: tuple[tuple[str, Span], ...]
    diagnostics: tuple[Diagnostic, ...]

class LanguagePluginRegistry:
    """Lazy extension registry; factories run only when a matching file opens."""
    def __init__(self):
        self._factories = {}
        self._instances = {}
        self._lock = threading.RLock()
    def register(self, language_id, extensions, factory):
        with self._lock:
            for ext in extensions: self._factories[ext.lower()] = (language_id, factory)
    def activate(self, filename):
        with self._lock:
            entry = self._factories.get(Path(filename).suffix.lower())
            if not entry: return None
            language_id, factory = entry
            if language_id not in self._instances: self._instances[language_id] = factory()
            return self._instances[language_id]

def _offset(text, pos):
    lines = text.splitlines(keepends=True)
    line = max(0, min(pos["line"], len(lines)))
    if line == len(lines): return len(text)
    prefix, units, index, target = lines[line], 0, 0, max(0, pos["character"])
    while index < len(prefix) and units < target:
        units += len(prefix[index].encode("utf-16-le")) // 2
        index += 1
    return sum(map(len, lines[:line])) + index

def _scan(snapshot):
    profile = resolve_syntax_profile(filename=snapshot.uri)
    declaration_spellings = DECLARATIONS | {
        alias for alias, canonical in profile.keyword_aliases.items()
        if canonical in DECLARATIONS
    }
    declaration_pattern = re.compile(
        r"\b(" + "|".join(map(re.escape, sorted(declaration_spellings))) + r")\s+([\w]+)"
    )
    symbols, identifiers, diagnostics, stack = [], [], [], []
    for row, source in enumerate(snapshot.text.splitlines()):
        clean = re.sub(r'"(?:\\.|[^"\\])*"|#.*$', lambda m: " " * len(m.group()), source)
        for match in IDENT.finditer(clean):
            identifiers.append((match.group(), Span(row, match.start(), match.end())))
        for match in declaration_pattern.finditer(clean):
            name = match.group(2)
            canonical = profile.keyword_aliases.get(match.group(1), match.group(1))
            kind = "function" if canonical in {"craft", "fn"} else "variable"
            symbols.append(Symbol(name, kind, snapshot.uri,
                                  Span(row, match.start(2), match.end(2))))
        for col, char in enumerate(clean):
            if char in "([{": stack.append((char, row, col))
            elif char in ")]}":
                expected = {")":"(", "]":"[", "}":"{"}[char]
                if stack and stack[-1][0] == expected: stack.pop()
                else: diagnostics.append(Diagnostic("unexpected closing delimiter", "error",
                                                     Span(row,col,col+1), "RPR-E0014",
                                                     "Close the matching opener or remove the extra closing delimiter."))
    for char,row,col in stack:
        diagnostics.append(Diagnostic("unclosed delimiter " + char, "hint",
                                      Span(row,col,col+1), "RPR-W0001",
                                      "Add the matching closing delimiter, or remove the incomplete opener."))
    try:
        tree = parse(snapshot.text, snapshot.uri)
        from .typecheck import TypeChecker
        checked = TypeChecker(snapshot.uri).check(tree)
        for item in checked.diagnostics:
            start = max(0, item.column - 1)
            diagnostics.append(Diagnostic(
                item.message,
                item.severity,
                Span(max(0, item.line - 1), start, start + 1),
                item.code,
                None,
            ))
    except (ReaperError, ValueError) as error:
        parts = str(error).rsplit(":", 3)
        try:
            row, column, message = int(parts[-3]) - 1, int(parts[-2]) - 1, parts[-1].strip()
        except (ValueError, IndexError):
            row, column, message = 0, 0, str(error)
        code = "RPR-E0001" if isinstance(error, LexError) else "RPR-E0013"
        definition = explain_diagnostic(code)
        diagnostics.append(Diagnostic(message, "error",
                                      Span(max(0, row), max(0, column), max(0, column) + 1),
                                      code, definition["help"] if definition else None))
    return Analysis(snapshot, tuple(symbols), tuple(identifiers), tuple(diagnostics))

class LanguageService:
    """Fast document updates; stale background analyses are never published."""
    def __init__(self, workers=1):
        self._docs, self._results, self._jobs = {}, {}, {}
        self._lock = threading.RLock()
        self._pool = ThreadPoolExecutor(max_workers=max(1,workers), thread_name_prefix="reaper-index")
    def open(self, uri, text, version=1):
        snap = Snapshot(uri, version, text)
        with self._lock: self._docs[uri] = snap
        self.schedule(snap)
        return snap
    def change(self, uri, version, edits):
        with self._lock:
            old = self._docs[uri]
            if version <= old.version: return old
            text = old.text
            for edit in edits:
                replacement = edit["text"]
                if "range" not in edit: text = replacement
                else:
                    start, end = edit["range"]["start"], edit["range"]["end"]
                    a, b = _offset(text,start), _offset(text,end)
                    if b < a: raise ValueError("invalid edit range")
                    text = text[:a] + replacement + text[b:]
            snap = Snapshot(uri, version, text)
            self._docs[uri] = snap
        self.schedule(snap)
        return snap
    def schedule(self, snap):
        with self._lock:
            previous = self._jobs.get(snap.uri)
            if previous: previous.cancel()
            job = self._pool.submit(_scan, snap)
            self._jobs[snap.uri] = job
            job.add_done_callback(lambda f, s=snap: self._publish(s,f))
            return job
    def _publish(self, snap, job):
        if job.cancelled(): return
        try: result = job.result()
        except Exception: return
        with self._lock:
            if self._docs.get(snap.uri) == snap: self._results[snap.uri] = result
    def analyze(self, uri):
        with self._lock: snap = self._docs[uri]
        result = _scan(snap)
        with self._lock:
            if self._docs.get(uri) == snap: self._results[uri] = result
        return result
    def result(self, uri):
        with self._lock:
            current = self._docs.get(uri)
            cached = self._results.get(uri)
            if current is None or cached is None or cached.snapshot != current:
                return None
            return cached
    def completion(self, uri, prefix=""):
        result = self.result(uri) or self.analyze(uri)
        names = {s.name:s.kind for s in result.symbols}
        for name,_ in result.identifiers: names.setdefault(name,"variable")
        for name in KEYWORDS | keyword_spellings(filename=result.snapshot.uri):
            names.setdefault(name,"keyword")
        for name in BUILTINS: names.setdefault(name,"function")
        ranked = sorted(names, key=lambda n:(not n.startswith(prefix),
                         -SequenceMatcher(None,prefix,n).ratio(), n.casefold()))
        return [{"label":n,"kind":names[n],"sortText":f"{i:04d}"} for i,n in enumerate(ranked[:100])]
    def definition(self, uri, name):
        result = self.result(uri) or self.analyze(uri)
        return next((s for s in result.symbols if s.name == name), None)
    def references(self, uri, name):
        result = self.result(uri) or self.analyze(uri)
        return [span for value,span in result.identifiers if value == name]
    def rename(self, uri, name, replacement):
        active_keywords = KEYWORDS | keyword_spellings(filename=uri)
        if not IDENT.fullmatch(replacement) or replacement in active_keywords or replacement in BUILTINS:
            raise ValueError("replacement must be a non-keyword identifier")
        return [(span,replacement) for span in self.references(uri,name)]
    def _workspace_analyses(self):
        """Return bounded analyses for documents the editor has already opened.

        This is deliberately not a disk crawler: the LSP workspace consists only
        of explicitly opened buffers, and results remain lexical rather than semantic.
        """
        with self._lock:
            uris = sorted(self._docs)
            total_chars = sum(len(self._docs[uri].text) for uri in uris)
        if len(uris) > 512:
            raise ValueError("workspace search is limited to 512 open documents")
        if total_chars > 8_000_000:
            raise ValueError("workspace search is limited to 8 million characters")
        return [self.result(uri) or self.analyze(uri) for uri in uris]

    def workspace_symbols(self, query="", limit=100):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("workspace symbol limit must be between 1 and 500")
        needle = str(query).casefold()
        matches = []
        for analysis in self._workspace_analyses():
            for symbol in analysis.symbols:
                if needle in symbol.name.casefold():
                    matches.append(symbol)
                    if len(matches) >= limit:
                        return matches
        return matches

    def workspace_definitions(self, name):
        needle = str(name)
        return [symbol for symbol in self.workspace_symbols(needle, 500)
                if symbol.name == needle]

    def workspace_references(self, name):
        needle = str(name)
        references = []
        for analysis in self._workspace_analyses():
            for value, span in analysis.identifiers:
                if value == needle:
                    references.append((analysis.snapshot.uri, span))
        return references

    def close(self, uri):
        with self._lock:
            self._docs.pop(uri,None); self._results.pop(uri,None)
            job = self._jobs.pop(uri,None)
            if job: job.cancel()
    def shutdown(self):
        self._pool.shutdown(wait=True, cancel_futures=True)
