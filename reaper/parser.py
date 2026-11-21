"""Recursive-descent statements and Pratt expressions for Reaper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ParseError
from .lexer import Token, tokenize


@dataclass(slots=True)
class Node:
    kind: str
    token: Token
    value: Any = None
    children: list["Node"] | None = None


_PRECEDENCE = {
    "::": 1,
    "??": 2,
    "OR": 3,
    "AND": 4,
    "==": 5, "!=": 5, "<": 5, "<=": 5, ">": 5, ">=": 5, "IN": 5,
    "++": 6,
    "+": 7, "-": 7,
    "*": 8, "/": 8, "//": 8, "%": 8,
    "**": 9,
}


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<memory>") -> None:
        self.tokens = tokens
        self.filename = filename
        self.current = 0

    def parse(self) -> Node:
        statements: list[Node] = []
        self._skip_newlines()
        while not self._check("EOF"):
            statements.append(self._statement())
            self._statement_end()
        return Node("program", self._peek(), children=statements)

    def _statement(self) -> Node:
        if self._match("IMPORT"):
            token = self._previous()
            specifier = self._consume("STRING", "expected a quoted .rpr path after 'import'")
            alias = None
            if self._match("AS"):
                alias = self._consume("IDENT", "expected an import alias after 'as'").value
            return Node("import", token, value=(specifier.value, alias))
        if self._match("EXPORT"):
            token = self._previous()
            if self._peek().kind in {"MAKE", "VARY", "LET", "MUT", "CONST", "CRAFT", "FN"}:
                declaration = self._statement()
                if declaration.kind not in {"declare", "function"}:
                    raise self._error(token, "inline export must declare a name or craft")
                return Node("export", token, children=[declaration])
            name = self._consume("IDENT", "expected a name after 'export'")
            return Node("export", token, value=name.value)
        if self._match("MAKE", "VARY", "LET", "MUT", "CONST"):
            declaration = self._previous()
            name = self._consume("IDENT", "expected a name after declaration")
            if not self._match(":=", "="):
                raise self._error(self._peek(), "expected '=' or ':=' after the name")
            value = self._expression()
            return Node("declare", declaration, value=(name.value, declaration.kind in {"VARY", "MUT"}), children=[value])
        if self._match("CHANGE"):
            token = self._previous()
            name = self._consume("IDENT", "expected a mutable name after 'change'")
            if not self._match(":=", "="):
                raise self._error(self._peek(), "expected '=' or ':=' after the name")
            return Node("change", token, value=name.value, children=[self._expression()])
        if self._match("EMIT"):
            token = self._previous()
            return Node("emit", token, children=[self._expression()])
        if self._match("YIELD", "RETURN"):
            token = self._previous()
            if self._check("NEWLINE") or self._check("}") or self._check("EOF"):
                return Node("yield", token)
            return Node("yield", token, children=[self._expression()])
        if self._match("CRAFT", "FN"):
            return self._function_declaration(self._previous())
        if self._match("WHEN", "IF"):
            return self._when(self._previous())
        if self._match("EACH", "FOR"):
            return self._each(self._previous())
        if self._match("LOOP"):
            token = self._previous()
            self._consume("WHILE", "expected 'while' after 'loop'")
            condition = self._expression()
            body = self._block()
            return Node("while", token, children=[condition, body])
        if self._match("WHILE"):
            token = self._previous()
            condition = self._expression()
            return Node("while", token, children=[condition, self._block()])
        if self._match("BREAK", "CONTINUE"):
            token = self._previous()
            return Node("break" if token.kind == "BREAK" else "continue", token)
        if self._check("IDENT") and self._peek_next().kind in {"=", ":="}:
            token = self._advance()
            self._advance()
            return Node("change", token, value=token.value, children=[self._expression()])
        expression = self._expression()
        return Node("expression", expression.token, children=[expression])

    def _function_declaration(self, token: Token) -> Node:
        name = self._consume("IDENT", "expected a function name after 'craft'")
        self._consume("(", "expected '(' after function name")
        params: list[str] = []
        self._skip_newlines()
        if not self._check(")"):
            while True:
                params.append(self._consume("IDENT", "expected a parameter name").value)
                self._skip_newlines()
                if not self._match(","):
                    break
                self._skip_newlines()
        self._consume(")", "expected ')' after parameters")
        body = self._block()
        return Node("function", token, value=(name.value, params), children=[body])

    def _when(self, token: Token) -> Node:
        condition = self._expression()
        yes = self._block()
        newline_position = self.current
        self._skip_newlines()
        no = None
        if self._match("OTHERWISE", "ELSE"):
            no = self._block()
        else:
            self.current = newline_position
        return Node("when", token, children=[condition, yes, no] if no else [condition, yes])

    def _each(self, token: Token) -> Node:
        name = self._consume("IDENT", "expected an iteration variable after 'each'")
        self._consume("IN", "expected 'in' after iteration variable")
        iterable = self._expression()
        body = self._block()
        return Node("each", token, value=name.value, children=[iterable, body])

    def _block(self) -> Node:
        self._consume("{", "expected '{' to start a block")
        statements: list[Node] = []
        self._skip_newlines()
        while not self._check("}") and not self._check("EOF"):
            statements.append(self._statement())
            self._statement_end()
        self._consume("}", "expected '}' after block")
        return Node("block", self._previous(), children=statements)

    def _expression(self, minimum: int = 1) -> Node:
        left = self._prefix()
        while True:
            if self._match("("):
                left = self._call(left, self._previous())
                continue
            if self._match("["):
                token = self._previous()
                index = self._expression()
                self._consume("]", "expected ']' after index")
                left = Node("index", token, children=[left, index])
                continue
            if self._match("."):
                token = self._previous()
                field = self._consume("IDENT", "expected a field name after '.'")
                left = Node("member", token, value=field.value, children=[left])
                continue
            if self._check("CATALOG_OPERATOR"):
                raise self._error(self._peek(), "catalogue operator is reserved; executable semantics are not registered")
            operator = self._peek().kind
            precedence = _PRECEDENCE.get(operator, 0)
            if precedence < minimum:
                break
            token = self._advance()
            self._skip_newlines()
            next_minimum = precedence if operator in {"**", "??"} else precedence + 1
            right = self._expression(next_minimum)
            left = Node("binary", token, value=operator, children=[left, right])
        return left

    def _call(self, callee: Node, token: Token) -> Node:
        arguments: list[Node] = []
        self._skip_newlines()
        if not self._check(")"):
            while True:
                arguments.append(self._expression())
                self._skip_newlines()
                if not self._match(","):
                    break
                self._skip_newlines()
        self._consume(")", "expected ')' after arguments")
        return Node("call", token, children=[callee, *arguments])

    def _prefix(self) -> Node:
        if self._check("CATALOG_OPERATOR"):
            raise self._error(self._peek(), "catalogue operator is reserved; executable semantics are not registered")
        if self._match("NUMBER"):
            token = self._previous()
            return Node("literal", token, value=float(token.value) if "." in token.value else int(token.value))
        if self._match("STRING"):
            token = self._previous()
            return Node("literal", token, value=token.value)
        if self._match("TRUE", "FALSE", "NOT", "-", "("):
            token = self._previous()
            if token.kind == "(":
                expression = self._expression()
                self._consume(")", "expected ')' after expression")
                return expression
            if token.kind in {"TRUE", "FALSE"}:
                return Node("literal", token, value=token.kind == "TRUE")
            return Node("unary", token, value=token.kind, children=[self._expression(9)])
        if self._match("NOTHING"):
            token = self._previous()
            return Node("literal", token, value=None)
        if self._match("IDENT"):
            token = self._previous()
            return Node("name", token, value=token.value)
        if self._match("{"):
            token = self._previous()
            entries: list[Node] = []
            self._skip_newlines()
            if not self._check("}"):
                while True:
                    entries.append(self._expression())
                    self._consume(":", "expected ':' between a map key and value")
                    entries.append(self._expression())
                    self._skip_newlines()
                    if not self._match(","):
                        break
                    self._skip_newlines()
            self._consume("}", "expected '}' after map literal")
            return Node("map", token, children=entries)
        if self._match("["):
            token = self._previous()
            items: list[Node] = []
            self._skip_newlines()
            if not self._check("]"):
                while True:
                    items.append(self._expression())
                    self._skip_newlines()
                    if not self._match(","):
                        break
                    self._skip_newlines()
            self._consume("]", "expected ']' after list")
            return Node("list", token, children=items)
        raise self._error(self._peek(), "expected an expression")

    def _statement_end(self) -> None:
        if self._match("NEWLINE"):
            self._skip_newlines()
            return
        if self._check("}") or self._check("EOF"):
            return
        raise self._error(self._peek(), "expected a new line after this statement")

    def _skip_newlines(self) -> None:
        while self._match("NEWLINE"):
            pass

    def _match(self, *kinds: str) -> bool:
        if self._peek().kind in kinds:
            self._advance()
            return True
        return False

    def _consume(self, kind: str, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        raise self._error(self._peek(), message)

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _advance(self) -> Token:
        if not self._check("EOF"):
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _peek_next(self) -> Token:
        return self.tokens[min(self.current + 1, len(self.tokens) - 1)]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParseError:
        return ParseError(f"{self.filename}:{token.line}:{token.column}: {message} (found {token.value or token.kind})")


def parse(source: str, filename: str = "<memory>") -> Node:
    return Parser(tokenize(source, filename), filename).parse()
