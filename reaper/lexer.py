"""Tokenizer for Reaper source files."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import LexError
from .token_catalog import token_is_reserved
from .source import SourceBuffer, Span


MAX_SOURCE_CHARS = 4_000_000
MAX_TOKEN_COUNT = 1_000_000


KEYWORDS = {
    "make", "vary", "change", "craft", "yield", "emit", "when",
    "otherwise", "each", "in", "loop", "while", "true", "false",
    "nothing", "and", "or", "not", "import", "export", "as",
}

# Exact Russian spellings map to canonical REAPER keyword spellings.
# "runtime" aliases are accepted by the 0.1 reference grammar; additional words
# are reserved lexically for the evolving native grammar and do not imply parsing.
KEYWORD_ALIASES = {
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
}


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str
    line: int
    column: int
    start_offset: int = 0
    end_offset: int = 0
    source_id: str = "<memory>"
    syntax_mode: str = "reaper-classic"
    end_line: int | None = None
    end_column: int | None = None

    @property
    def span(self) -> Span:
        return Span(
            self.source_id, self.start_offset, self.end_offset,
            self.line, self.column, self.syntax_mode,
            self.end_line, self.end_column,
        )


class Lexer:
    """Convert source text into a position-aware token stream."""

    _TWO_CHAR = {":=", "==", "!=", "<=", ">=", "//", "**", "++", "::", "->"}
    _ONE_CHAR = set("+-*/%<>(){}[],")

    def __init__(
        self,
        source: str | SourceBuffer,
        filename: str = "<memory>",
        *,
        keyword_aliases: dict[str, str] | None = None,
    ) -> None:
        self.buffer = source if isinstance(source, SourceBuffer) else SourceBuffer.from_text(
            source, filename
        )
        self.source = self.buffer.text
        self.filename = self.buffer.source_id
        self.keyword_aliases = KEYWORD_ALIASES if keyword_aliases is None else keyword_aliases
        self.index = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        if len(self.source) > MAX_SOURCE_CHARS:
            raise LexError(
                f"{self.filename}: source exceeds the {MAX_SOURCE_CHARS}-character limit"
            )
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
        self._append_token(Token(
            "EOF", "", self.line, self.column,
            self.index, self.index, self.buffer.source_id, self.buffer.syntax_mode,
            self.line, self.column,
        ))
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

    def _lex_error(self, message: str, start: int | None = None, end: int | None = None) -> LexError:
        start_offset = self.index if start is None else start
        end_offset = start_offset if end is None else end
        span = self.buffer.span(start_offset, end_offset)
        return LexError(
            f"{self.filename}:{span.line}:{span.column}: {message}",
            code="RPR-E0001",
            stage="lexer",
            span=span,
            syntax_mode=self.buffer.syntax_mode,
        )

    def _append_token(self, token: Token) -> None:
        if len(self.tokens) >= MAX_TOKEN_COUNT:
            raise self._lex_error(f"token limit ({MAX_TOKEN_COUNT}) exceeded")
        self.tokens.append(token)

    def _token(self, kind: str, value: str) -> None:
        start = self.index
        self._append_token(Token(
            kind, value, self.line, self.column,
            start, start + len(value), self.buffer.source_id, self.buffer.syntax_mode,
            self.line, self.column + len(value),
        ))

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
                raise self._lex_error(
                    "string literal cannot span lines", start_offset, self.index
                )
            if char == "\\":
                if self._at_end():
                    break
                escaped = self._advance()
                if escaped not in escapes:
                    raise self._lex_error(
                        f"unknown escape sequence \\{escaped}",
                        self.index - 2,
                        self.index,
                    )
                value.append(escapes[escaped])
            else:
                value.append(char)
        if self._at_end():
            raise self._lex_error(
                "unterminated string literal", start_offset, self.index
            )
        self._advance()
        self._append_token(Token(
            "STRING", "".join(value), start_line, start_column,
            start_offset, self.index, self.buffer.source_id, self.buffer.syntax_mode,
            self.line, self.column,
        ))

    def _number(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        self._append_token(Token(
            "NUMBER", self.source[start:self.index], start_line, start_column,
            start, self.index, self.buffer.source_id, self.buffer.syntax_mode,
            self.line, self.column,
        ))

    def _identifier(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        value = self.source[start:self.index]
        canonical = self.keyword_aliases.get(value)
        kind = canonical.upper() if canonical is not None else (
            value.upper() if value in KEYWORDS else "IDENT"
        )
        self._append_token(Token(
            kind, value, start_line, start_column,
            start, self.index, self.buffer.source_id, self.buffer.syntax_mode,
            self.line, self.column,
        ))

    def _operator_or_punctuation(self) -> None:
        start_offset = self.index
        start_line, start_column = self.line, self.column
        triplet = self.source[self.index:self.index + 3]
        if token_is_reserved(triplet):
            for _ in range(3):
                self._advance()
            self._append_token(Token(
                "CATALOG_OPERATOR", triplet, start_line, start_column,
                start_offset, self.index, self.buffer.source_id, self.buffer.syntax_mode,
                self.line, self.column,
            ))
            return
        pair = self._peek() + self._peek(1)
        if pair in self._TWO_CHAR:
            self._advance()
            self._advance()
            self._append_token(Token(
                pair, pair, start_line, start_column,
                start_offset, self.index, self.buffer.source_id, self.buffer.syntax_mode,
                self.line, self.column,
            ))
            return
        char = self._peek()
        if char in self._ONE_CHAR or char == "=":
            self._advance()
            self._append_token(Token(
                char, char, start_line, start_column,
                start_offset, self.index, self.buffer.source_id, self.buffer.syntax_mode,
                self.line, self.column,
            ))
            return
        raise self._lex_error(f"unexpected character {char!r}", start_offset, start_offset + 1)


def tokenize(
    source: str | SourceBuffer,
    filename: str = "<memory>",
    *,
    keyword_aliases: dict[str, str] | None = None,
) -> list[Token]:
    return Lexer(source, filename, keyword_aliases=keyword_aliases).tokenize()
