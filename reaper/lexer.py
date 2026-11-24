"""Tokenizer for Reaper source files."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .errors import LexError
from .source_profile import (
    PreparedSource,
    localize_lex_message,
    prepare_source,
    span_from_offsets,
)
from .token_catalog import token_is_reserved


MAX_SOURCE_CHARS = 4_000_000
MAX_TOKEN_COUNT = 1_000_000


KEYWORDS = {
    "make", "vary", "change", "craft", "yield", "emit", "when",
    "otherwise", "each", "in", "loop", "while", "true", "false",
    "nothing", "and", "or", "not", "import", "export", "as",
}

# Ukrainian-only words are activated by the explicit Ukrainian source
# profile. This avoids newly reserving short words such as "у" and "і" in
# existing English/Russian source files.
_UKRAINIAN_ONLY_ALIASES = frozenset({
    "нехай", "змінна", "змінити", "функція", "повернути", "вивести",
    "якщо", "інакше", "кожен", "у", "поки", "істина", "хиба",
    "нічого", "і", "або", "імпорт", "експорт",
})


# Exact aliases map to canonical REAPER keyword spellings. These mappings are
# deliberately table-driven: no stemming, transliteration, or fuzzy guessing.
KEYWORD_ALIASES = {
    # Russian / MOST profile
    "пусть": "make",
    "переменная": "vary",
    "изменить": "change",
    "функция": "craft",
    "вернуть": "yield",
    "вывести": "emit",
    "если": "when",
    "иначе": "otherwise",
    "для": "each",
    "в": "in",
    "цикл": "loop",
    "пока": "while",
    "истина": "true",
    "ложь": "false",
    "ничего": "nothing",
    "и": "and",
    "или": "or",
    "не": "not",
    "импорт": "import",
    "экспорт": "export",
    "как": "as",
    "модуль": "module",
    "публичный": "pub",
    "процедура": "fn",
    "структура": "struct",
    "перечисление": "enum",
    "типаж": "trait",
    "реализация": "impl",
    "тип": "type",
    "константа": "const",
    "связать": "let",
    "изменяемый": "mut",
    "возврат": "return",
    "условие": "if",
    "альтернатива": "else",
    "выбор": "match",
    "область": "region",
    "сырой": "raw",
    "арена": "arena",
    "сигнал": "signal",
    "асинхронно": "async",
    "ожидать": "await",
    "тест": "test",
    "вычислить_при_сборке": "comptime",
    "требует": "requires",
    "гарантирует": "ensures",
    "небезопасно": "unsafe",
    "внешний": "extern",
    "где": "where",
    "уничтожить": "drop",
    "для_каждого": "for",
    "прервать": "break",
    "продолжить": "continue",
    "отложить": "defer",
    # Ukrainian profile
    "нехай": "make",
    "змінна": "vary",
    "змінити": "change",
    "функція": "craft",
    "повернути": "yield",
    "вивести": "emit",
    "якщо": "when",
    "інакше": "otherwise",
    "кожен": "each",
    "у": "in",
    "поки": "while",
    "істина": "true",
    "хиба": "false",
    "нічого": "nothing",
    "і": "and",
    "або": "or",
    "імпорт": "import",
    "експорт": "export",
}


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str
    line: int
    column: int
    # Half-open offsets into the original source text, measured in Unicode
    # code points. Defaults preserve compatibility with synthetic VM tokens.
    start: int | None = None
    end: int | None = None
    syntax_mode: str = "classic"
    locale: str = "en"


class Lexer:
    """Convert source text into a profile-aware, position-aware token stream."""

    _TWO_CHAR = {":=", "==", "!=", "<=", ">=", "//", "**", "++", "::"}
    _ONE_CHAR = set("+-*/%<>(){}[],")

    def __init__(self, source: str, filename: str = "<memory>") -> None:
        self.original_source = source
        self.prepared: PreparedSource | None = None
        self.source = source
        self.filename = filename
        self.index = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        if len(self.original_source) > MAX_SOURCE_CHARS:
            self._raise_lex_error(
                f"source exceeds the {MAX_SOURCE_CHARS}-character limit", 0, 0
            )
        self.prepared = prepare_source(self.original_source, self.filename)
        self.source = self.prepared.text
        while not self._at_end():
            char = self._peek()
            if char in " \t\r":
                self._advance()
            elif char == "\n":
                self._token("NEWLINE", "\n")
                self._advance()
            elif char == "#":
                self._skip_comment()
            elif char == '"':
                self._string()
            elif char.isdigit():
                self._number()
            elif char.isalpha() or char == "_":
                self._identifier()
            else:
                self._operator_or_punctuation()
        self._append_token(
            Token("EOF", "", self.line, self.column, len(self.source), len(self.source))
        )
        return self.tokens

    def _at_end(self) -> bool:
        return self.index >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        position = self.index + offset
        return self.source[position] if position < len(self.source) else "\0"

    def _advance(self) -> str:
        char = self.source[self.index]
        self.index += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _append_token(self, token: Token) -> None:
        if len(self.tokens) >= MAX_TOKEN_COUNT:
            start = token.start if token.start is not None else self.index
            end = token.end if token.end is not None else start
            self._raise_lex_error(
                f"token limit ({MAX_TOKEN_COUNT}) exceeded", start, end
            )
        offset = token.start if token.start is not None else self.index
        mode, locale = self._profile_at(offset)
        self.tokens.append(
            replace(token, syntax_mode=mode, locale=locale)
        )

    def _profile_at(self, offset: int) -> tuple[str, str]:
        if self.prepared is None:
            return "classic", "en"
        return self.prepared.profile_at(offset)

    def _raise_lex_error(self, message: str, start: int, end: int) -> None:
        span = span_from_offsets(self.original_source, self.filename, start, end)
        mode, locale = self._profile_at(start)
        localized = localize_lex_message(locale, message)
        raise LexError(
            f"{self.filename}:{span.line}:{span.col}: {localized}",
            span=span,
            syntax_mode=mode,
            locale=locale,
        )

    def _token(self, kind: str, value: str) -> None:
        start = self.index
        self._append_token(
            Token(kind, value, self.line, self.column, start, start + len(value))
        )

    def _skip_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _string(self) -> None:
        start_line, start_column, start_offset = self.line, self.column, self.index
        self._advance()
        value: list[str] = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
        while not self._at_end() and self._peek() != '"':
            char = self._advance()
            if char == "\n":
                self._raise_lex_error(
                    "string literal cannot span lines",
                    self.index - 1,
                    self.index,
                )
            if char == "\\":
                if self._at_end():
                    break
                escaped = self._advance()
                if escaped not in escapes:
                    self._raise_lex_error(
                        f"unknown escape sequence \\{escaped}",
                        self.index - 2,
                        self.index,
                    )
                value.append(escapes[escaped])
            else:
                value.append(char)
        if self._at_end():
            self._raise_lex_error(
                "unterminated string literal", start_offset, start_offset + 1
            )
        self._advance()
        self._append_token(
            Token(
                "STRING", "".join(value), start_line, start_column,
                start_offset, self.index,
            )
        )

    def _number(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        self._append_token(
            Token(
                "NUMBER", self.source[start:self.index], start_line, start_column,
                start, self.index,
            )
        )

    def _identifier(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        value = self.source[start:self.index]
        _mode, locale = self._profile_at(start)
        canonical = KEYWORD_ALIASES.get(value)
        if value in _UKRAINIAN_ONLY_ALIASES and locale != "uk":
            canonical = None
        kind = canonical.upper() if canonical is not None else (
            value.upper() if value in KEYWORDS else "IDENT"
        )
        self._append_token(
            Token(kind, value, start_line, start_column, start, self.index)
        )

    def _operator_or_punctuation(self) -> None:
        start_line, start_column, start = self.line, self.column, self.index
        triplet = self.source[self.index:self.index + 3]
        if token_is_reserved(triplet):
            for _ in range(3):
                self._advance()
            self._append_token(
                Token("CATALOG_OPERATOR", triplet, start_line, start_column, start, self.index)
            )
            return

        pair = self._peek() + self._peek(1)
        if pair in {"->", "|>"}:
            mode, _locale = self._profile_at(self.index)
            if mode != "flow":
                self._raise_lex_error(
                    f"'{pair}' requires @mode flow", start, start + len(pair)
                )
            line_start = self.source.rfind("\n", 0, self.index) + 1
            is_line_step = not self.source[line_start:self.index].strip(" \t")
            self._advance()
            self._advance()
            kind = "PIPE" if is_line_step else "::"
            value = pair if is_line_step else "::"
            self._append_token(
                Token(kind, value, start_line, start_column, start, self.index)
            )
            return

        if pair in self._TWO_CHAR:
            self._advance()
            self._advance()
            self._append_token(
                Token(pair, pair, start_line, start_column, start, self.index)
            )
            return

        char = self._peek()
        if char in self._ONE_CHAR or char == "=":
            self._advance()
            self._append_token(
                Token(char, char, start_line, start_column, start, self.index)
            )
            return
        self._raise_lex_error(
            f"unexpected character {char!r}", start, start + 1
        )


def tokenize(source: str, filename: str = "<memory>") -> list[Token]:
    return Lexer(source, filename).tokenize()
