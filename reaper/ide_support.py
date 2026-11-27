"""Pure, testable editor services used by Reaper Studio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from collections.abc import Iterable, Mapping
from typing import Any, Iterator

from .syntax_profiles import keyword_spellings

SOURCE_EXTENSIONS = frozenset({".rpr", ".most", ".most-uk", ".rclass", ".rflow", ".js", ".mjs", ".cjs"})
IGNORED_DIRECTORIES = frozenset({"__pycache__", "node_modules", "build", "dist", ".venv"})
KEYWORDS = frozenset({
    "make", "vary", "change", "craft", "yield", "emit", "when", "otherwise",
    "each", "in", "loop", "while", "true", "false", "nothing", "and", "or",
    "not", "module", "import", "as", "pub", "export", "fn", "struct", "enum",
    "trait", "impl", "type", "const", "let", "mut", "return", "if", "else",
    "match", "region", "raw", "arena", "signal", "async", "await", "test",
    "comptime", "requires", "ensures", "unsafe", "extern", "drop", "where",
    "for", "break", "continue", "defer", "пусть", "переменная", "изменить",
    "функция", "вернуть", "вывести", "если", "иначе", "для", "в", "цикл",
    "пока", "истина", "ложь", "ничего", "и", "или", "не", "импорт",
    "экспорт", "как", "модуль", "публичный", "процедура", "структура",
    "перечисление", "типаж", "реализация", "тип", "константа", "связать",
    "изменяемый", "возврат", "условие", "альтернатива", "выбор", "область",
    "сырой", "арена", "сигнал", "асинхронно", "ожидать", "тест",
    "вычислить_при_сборке", "требует", "гарантирует", "небезопасно",
    "внешний", "где", "уничтожить", "для_каждого", "прервать",
    "продолжить", "отложить",
})
_TOKEN_PATTERN = re.compile(
    r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)'
    r'|(?P<string>"(?:\\.|[^"\\])*")'
    r'|(?P<number>\b(?:0x[0-9A-Fa-f]+|[0-9]+(?:\.[0-9]+)?)\b)'
    r'|(?P<identifier>[^\W\d]\w*)',
    re.UNICODE,
)



DIAGNOSTIC_SEVERITIES = frozenset({"error", "warning", "information", "hint"})


@dataclass(frozen=True, slots=True)
class IdeDiagnostic:
    """Stable IDE diagnostic record with one-based source coordinates."""

    file: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    severity: str
    code: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "range": {
                "start": {"line": self.start_line, "column": self.start_column},
                "end": {"line": self.end_line, "column": self.end_column},
            },
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


def normalize_diagnostics(
    source_file: str | Path,
    diagnostics: Iterable[Any],
) -> tuple[IdeDiagnostic, ...]:
    """Normalize compiler-owned diagnostics without inventing semantic ranges.

    The current typechecker exposes a point location rather than a source span,
    so the end position equals the start position until the compiler provides a
    real range. Coordinates remain one-based, matching native diagnostics and
    the Tk editor contract.
    """
    file_name = str(source_file)
    normalized: list[IdeDiagnostic] = []

    def field(item: Any, name: str, default: Any = None) -> Any:
        if isinstance(item, Mapping):
            return item.get(name, default)
        return getattr(item, name, default)

    def positive_position(value: Any, fallback: int) -> int:
        if isinstance(value, bool):
            return fallback
        try:
            position = int(value)
        except (TypeError, ValueError, OverflowError):
            return fallback
        return max(1, position)

    for item in diagnostics:
        line = positive_position(field(item, "line", 1), 1)
        column = positive_position(field(item, "column", 1), 1)
        end_line = positive_position(field(item, "end_line", line), line)
        end_column = positive_position(field(item, "end_column", column), column)
        if (end_line, end_column) < (line, column):
            end_line, end_column = line, column

        severity = str(field(item, "severity", "error")).lower()
        if severity not in DIAGNOSTIC_SEVERITIES:
            severity = "error"
        code = str(field(item, "code", "RPR-UNKNOWN")).strip() or "RPR-UNKNOWN"
        message = str(field(item, "message", ""))

        normalized.append(IdeDiagnostic(
            file=file_name,
            start_line=line,
            start_column=column,
            end_line=end_line,
            end_column=end_column,
            severity=severity,
            code=code,
            message=message,
        ))

    return tuple(sorted(
        normalized,
        key=lambda diagnostic: (
            diagnostic.start_line,
            diagnostic.start_column,
            diagnostic.severity,
            diagnostic.code,
            diagnostic.message,
        ),
    ))


@dataclass(frozen=True, slots=True)
class HighlightSpan:
    kind: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    path: Path
    is_directory: bool
    depth: int


def highlight_spans(
    source: str,
    filename: str = "<memory>",
    syntax: str | None = None,
) -> tuple[HighlightSpan, ...]:
    """Return profile-aware, non-overlapping spans without changing source text."""
    spans: list[HighlightSpan] = []
    active_keywords = KEYWORDS | keyword_spellings(syntax, filename)
    for match in _TOKEN_PATTERN.finditer(source):
        kind = match.lastgroup
        if kind == "identifier" and match.group() in active_keywords:
            kind = "keyword"
        if kind in {"keyword", "string", "number", "comment"}:
            spans.append(HighlightSpan(kind, match.start(), match.end()))
    return tuple(spans)


def iter_project_entries(
    root: Path,
    *,
    max_depth: int = 5,
    max_entries: int = 2000,
) -> Iterator[ProjectEntry]:
    """Yield a deterministic, bounded source-file tree without following symlinks."""
    if max_depth < 0 or max_entries < 1:
        raise ValueError("project tree limits must be non-negative depth and positive entries")
    root = Path(root)
    emitted = 0

    def walk(folder: Path, depth: int) -> Iterator[ProjectEntry]:
        nonlocal emitted
        if depth >= max_depth or emitted >= max_entries:
            return
        try:
            children = sorted(folder.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold()))
        except OSError:
            return
        for child in children:
            if emitted >= max_entries:
                return
            if child.name.startswith(".") or child.is_symlink():
                continue
            is_directory = child.is_dir()
            if is_directory and child.name in IGNORED_DIRECTORIES:
                continue
            if not is_directory and child.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            emitted += 1
            yield ProjectEntry(child, is_directory, depth + 1)
            if is_directory:
                yield from walk(child, depth + 1)

    yield from walk(root, 0)
