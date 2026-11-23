"""Versioned syntax profiles for the Reaper front end.

Profiles change surface spelling and file selection only. They never define
runtime semantics: every built-in profile feeds the same parser, AST, type
checker, canonical IR, and execution engines.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from threading import RLock
from types import MappingProxyType
from typing import Mapping


class SyntaxProfileError(ValueError):
    """A syntax profile is unknown or conflicts with a registered profile."""


@dataclass(frozen=True, slots=True)
class SyntaxProfile:
    profile_id: str
    version: str
    extensions: tuple[str, ...]
    keyword_aliases: Mapping[str, str]
    description: str
    experimental: bool = False
    grammar_id: str = "reaper-core-v1"


# Exact-match compatibility aliases already used by the .rpr and MOST lexer.
REAPER_KEYWORD_ALIASES = {
    "пусть": "make", "переменная": "vary", "изменить": "change",
    "функция": "craft", "вернуть": "yield", "вывести": "emit",
    "если": "when", "иначе": "otherwise", "для": "each", "в": "in",
    "цикл": "loop", "пока": "while", "истина": "true", "ложь": "false",
    "ничего": "nothing", "и": "and", "или": "or", "не": "not",
    "импорт": "import", "экспорт": "export", "как": "as",
    "модуль": "module", "публичный": "pub", "процедура": "fn",
    "структура": "struct", "перечисление": "enum", "типаж": "trait",
    "реализация": "impl", "тип": "type", "константа": "const",
    "связать": "let", "изменяемый": "mut", "возврат": "return",
    "условие": "if", "альтернатива": "else", "выбор": "match",
    "область": "region", "сырой": "raw", "арена": "arena",
    "сигнал": "signal", "асинхронно": "async", "ожидать": "await",
    "тест": "test", "вычислить_при_сборке": "comptime",
    "требует": "requires", "гарантирует": "ensures",
    "небезопасно": "unsafe", "внешний": "extern", "где": "where",
    "уничтожить": "drop", "для_каждого": "for", "прервать": "break",
    "продолжить": "continue", "отложить": "defer",
}

CLASSIC_KEYWORD_ALIASES = {
    "let": "make", "var": "vary", "set": "change",
    "fn": "craft", "return": "yield", "print": "emit",
    "if": "when", "else": "otherwise", "for": "each",
}

MOST_UK_KEYWORD_ALIASES = {
    "нехай": "make", "змінна": "vary", "змінити": "change",
    "функція": "craft", "повернути": "yield", "вивести": "emit",
    "якщо": "when", "інакше": "otherwise", "кожен": "each",
    "у": "in", "в": "in", "цикл": "loop", "поки": "while",
    "істина": "true", "хиба": "false", "нічого": "nothing",
    "і": "and", "або": "or", "не": "not", "імпорт": "import",
    "експорт": "export", "як": "as",
}

CORE_KEYWORDS = frozenset({
    "make", "vary", "change", "craft", "yield", "emit", "when",
    "otherwise", "each", "in", "loop", "while", "true", "false",
    "nothing", "and", "or", "not", "import", "export", "as",
    "module", "pub", "fn", "struct", "enum", "trait", "impl", "type",
    "const", "let", "mut", "return", "if", "else", "match", "region",
    "raw", "arena", "signal", "async", "await", "test", "comptime",
    "requires", "ensures", "unsafe", "extern", "drop", "where", "for",
    "break", "continue", "defer",
})

_PROFILES: dict[str, SyntaxProfile] = {}
_EXTENSIONS: dict[str, str] = {}
_LOCK = RLock()


def register_syntax_profile(profile: SyntaxProfile, *, replace: bool = False) -> SyntaxProfile:
    """Register an exact-alias profile; custom grammars need an AST adapter."""
    if not isinstance(profile, SyntaxProfile):
        raise TypeError("profile must be a SyntaxProfile")
    profile_id, version = profile.profile_id.strip(), profile.version.strip()
    if not profile_id or not version:
        raise SyntaxProfileError("profile id and version must be non-empty")
    if not profile.extensions:
        raise SyntaxProfileError("a syntax profile must declare at least one extension")
    extensions = tuple(dict.fromkeys(ext.casefold() for ext in profile.extensions))
    if any(not ext.startswith(".") or ext == "." or "/" in ext or "\\" in ext for ext in extensions):
        raise SyntaxProfileError("profile extensions must be simple dotted suffixes")
    aliases: dict[str, str] = {}
    for source, canonical in profile.keyword_aliases.items():
        if not isinstance(source, str) or not source or not isinstance(canonical, str) or not canonical:
            raise SyntaxProfileError("keyword aliases must map non-empty strings to non-empty strings")
        if source != canonical:
            aliases[source] = canonical
    frozen = SyntaxProfile(
        profile_id, version, extensions, MappingProxyType(dict(sorted(aliases.items()))),
        profile.description.strip(), bool(profile.experimental),
        profile.grammar_id.strip() or "reaper-core-v1",
    )
    with _LOCK:
        if profile_id in _PROFILES and not replace:
            raise SyntaxProfileError(f"syntax profile already registered: {profile_id}")
        for extension in extensions:
            owner = _EXTENSIONS.get(extension)
            if owner and owner != profile_id and not replace:
                raise SyntaxProfileError(f"extension {extension} is already assigned to {owner}")
        if replace:
            for extension, owner in tuple(_EXTENSIONS.items()):
                if owner == profile_id:
                    del _EXTENSIONS[extension]
        _PROFILES[profile_id] = frozen
        for extension in extensions:
            _EXTENSIONS[extension] = profile_id
    return frozen


def get_syntax_profile(profile_id: str) -> SyntaxProfile:
    with _LOCK:
        try:
            return _PROFILES[profile_id]
        except KeyError as error:
            raise SyntaxProfileError(f"unknown syntax profile: {profile_id}") from error


def resolve_syntax_profile(
    syntax: str | SyntaxProfile | None = None,
    filename: str | None = None,
) -> SyntaxProfile:
    """Prefer explicit selection, then a registered extension; never inspect content."""
    if isinstance(syntax, SyntaxProfile):
        return syntax
    if syntax is not None:
        return get_syntax_profile(str(syntax))
    if filename:
        extension = PurePath(str(filename).split("?", 1)[0]).suffix.casefold()
        with _LOCK:
            profile_id = _EXTENSIONS.get(extension)
            if profile_id:
                return _PROFILES[profile_id]
    # Historical API compatibility for in-memory and unregistered filenames.
    return get_syntax_profile("reaper")


def available_syntax_profiles() -> tuple[SyntaxProfile, ...]:
    with _LOCK:
        return tuple(_PROFILES[key] for key in sorted(_PROFILES))


def supported_source_extensions() -> frozenset[str]:
    with _LOCK:
        return frozenset(_EXTENSIONS)


def keyword_spellings(profile: str | SyntaxProfile | None = None, filename: str | None = None) -> frozenset[str]:
    selected = resolve_syntax_profile(profile, filename)
    return CORE_KEYWORDS | frozenset(selected.keyword_aliases)


def canonical_keyword(word: str, profile: str | SyntaxProfile | None = None, filename: str | None = None) -> str:
    selected = resolve_syntax_profile(profile, filename)
    return selected.keyword_aliases.get(word, word)


register_syntax_profile(SyntaxProfile(
    "reaper", "0.1", (".rpr",), REAPER_KEYWORD_ALIASES,
    "Canonical Reaper syntax with backward-compatible exact MOST aliases.",
))
register_syntax_profile(SyntaxProfile(
    "reaper-flow", "0.1", (".rflow",), REAPER_KEYWORD_ALIASES,
    "Flow-first Reaper syntax, including canonical pipeline expressions.",
))
register_syntax_profile(SyntaxProfile(
    "most-ru", "0.2.0", (".most",), REAPER_KEYWORD_ALIASES,
    "Russian MOST surface vocabulary mapped to canonical Reaper tokens.",
))
register_syntax_profile(SyntaxProfile(
    "most-uk", "0.1.0", (".most-uk",), MOST_UK_KEYWORD_ALIASES,
    "Ukrainian MOST surface vocabulary mapped to canonical Reaper tokens.",
))
register_syntax_profile(SyntaxProfile(
    "classic", "0.1.0", (".rclass",), CLASSIC_KEYWORD_ALIASES,
    "Classic imperative spellings mapped to the Reaper core statement grammar.",
))
