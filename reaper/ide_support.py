"""Pure, testable editor services used by Reaper Studio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterator

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
