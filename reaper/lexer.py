"""Tokenizer for Reaper source files."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import LexError
from .token_catalog import token_is_reserved
from .syntax_profiles import REAPER_KEYWORD_ALIASES as KEYWORD_ALIASES, resolve_syntax_profile


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


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


class Lexer:
    """Convert source text into a position-aware token stream."""

    _TWO_CHAR = {":=", "==", "!=", "<=", ">=", "//", "**", "++", "::"}
    _ONE_CHAR = set("+-*/%<>(){}[],")

    def __init__(self, source: str, filename: str = "<memory>", syntax: str | None = None) -> None:
        self.source = source
        self.filename = filename
        self.profile = resolve_syntax_profile(syntax, filename)
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
        self._append_token(Token("EOF", "", self.line, self.column))
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
            raise LexError(
                f"{self.filename}:{self.line}:{self.column}: "
                f"token limit ({MAX_TOKEN_COUNT}) exceeded"
            )
        self.tokens.append(token)

    def _token(self, kind: str, value: str) -> None:
        self._append_token(Token(kind, value, self.line, self.column))

    def _skip_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _string(self) -> None:
        start_line, start_column = self.line, self.column
        self._advance()
        value: list[str] = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
        while not self._at_end() and self._peek() != '"':
            char = self._advance()
            if char == "\n":
                raise LexError(f"{self.filename}:{start_line}:{start_column}: string literal cannot span lines")
            if char == "\\":
                if self._at_end():
                    break
                escaped = self._advance()
                if escaped not in escapes:
                    raise LexError(
                        f"{self.filename}:{self.line}:{self.column}: unknown escape sequence \\{escaped}"
                    )
                value.append(escapes[escaped])
            else:
                value.append(char)
        if self._at_end():
            raise LexError(f"{self.filename}:{start_line}:{start_column}: unterminated string literal")
        self._advance()
        self._append_token(Token("STRING", "".join(value), start_line, start_column))

    def _number(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        self._append_token(Token("NUMBER", self.source[start:self.index], start_line, start_column))

    def _identifier(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        value = self.source[start:self.index]
        canonical = self.profile.keyword_aliases.get(value)
        kind = canonical.upper() if canonical is not None else (
            value.upper() if value in KEYWORDS else "IDENT"
        )
        self._append_token(Token(kind, value, start_line, start_column))

    def _operator_or_punctuation(self) -> None:
        start_line, start_column = self.line, self.column
        triplet = self.source[self.index:self.index + 3]
        if token_is_reserved(triplet):
            for _ in range(3):
                self._advance()
            self._append_token(Token("CATALOG_OPERATOR", triplet, start_line, start_column))
            return
        pair = self._peek() + self._peek(1)
        if pair in self._TWO_CHAR:
            self._advance()
            self._advance()
            self._append_token(Token(pair, pair, start_line, start_column))
            return
        char = self._peek()
        if char in self._ONE_CHAR or char == "=":
            self._advance()
            self._append_token(Token(char, char, start_line, start_column))
            return
        raise LexError(f"{self.filename}:{self.line}:{self.column}: unexpected character {char!r}")


def tokenize(source: str, filename: str = "<memory>", syntax: str | None = None) -> list[Token]:
    return Lexer(source, filename, syntax).tokenize()
