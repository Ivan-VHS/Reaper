"""QCS lexer, parser, AST and CLI for Reaper (QCS 1.0)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DOMAIN_REGISTRY = frozenset({
    "regfile", "irq", "mmio", "page", "pmu", "trap", "atomic", "slab",
    "boot", "bus", "contextSwitch", "heap", "arena", "borrow", "cache",
    "dma", "mmu", "bitfield", "rc", "zeroCopy", "stackGuard", "simd",
    "spinlock", "fence", "fiber", "pipeline", "affinity", "timer", "event",
    "actorBox", "batchIo", "watchdog", "crypto", "enclave", "privilege",
    "hash", "trng", "trace", "sandbox", "verify", "memTag", "tmr",
    "secretZeroize", "logic", "clock", "fpga", "dsp", "adc", "pwm", "spi",
    "i2c", "uart", "canFd", "fsm", "vm", "bytecode", "jit", "ir", "macro",
    "hypervisor", "linker", "elf64", "debug", "abi", "bridgeAll",
})
KEYWORDS = frozenset({
    "func", "protocol", "struct", "enum", "let", "var", "inout", "returns",
    "guard", "if", "else", "switch", "case", "for", "in", "while", "return",
    "defer", "break", "continue", "and", "or", "not", "true", "false",
    "nil", "some", "end",
})
FORBIDDEN = frozenset("<>|~")
DURATION_UNITS = frozenset({"ns", "us", "ms", "s", "mv", "hz", "khz", "ghz"})
NUMBER_RE = re.compile(
    r"(?:0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*|0[bB][01](?:_?[01])*|"
    r"[0-9](?:_?[0-9])*(?:\.[0-9](?:_?[0-9])*)?)"
)


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str
    span: SourceSpan


@dataclass(slots=True)
class AstNode:
    kind: str
    fields: dict[str, Any] = field(default_factory=dict)
    span: SourceSpan | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "fields": _to_data(self.fields), "span": _to_data(self.span)}


class QcsError(ValueError):
    def __init__(self, message: str, filename: str = "<memory>",
                 line: int = 1, column: int = 1, code: str = "QCS_ERROR") -> None:
        self.message, self.filename = message, filename
        self.line, self.column, self.code = line, column, code
        super().__init__(f"{filename}:{line}:{column}: {code}: {message}")


class QcsLexer:
    TWO_CHAR = {"==", "!=", "+=", "&+", "&&", "||", "++", "::"}
    PUNCTUATION = set("(){}[],.:;")
    SINGLE_OPERATORS = set("=!?+-*/%&^")

    def __init__(self, source: str, filename: str = "<memory>") -> None:
        self.source, self.filename = source, filename
        self.index, self.line, self.column = 0, 1, 1
        self.tokens: list[Token] = []

    def _peek(self, offset: int = 0) -> str:
        pos = self.index + offset
        return self.source[pos] if pos < len(self.source) else "\0"

    def _advance(self) -> str:
        char = self.source[self.index]
        self.index += 1
        if char == "\n":
            self.line, self.column = self.line + 1, 1
        else:
            self.column += 1
        return char

    def _emit(self, kind: str, value: str, start: int, line: int, col: int) -> None:
        self.tokens.append(Token(kind, value, SourceSpan(
            start, self.index, line, col, self.line, self.column
        )))

    def tokenize(self) -> list[Token]:
        while self.index < len(self.source):
            c = self._peek()
            if c in " \t\r":
                self._advance()
            elif c == "\n":
                start, line, col = self.index, self.line, self.column
                self._advance()
                self._emit("NEWLINE", "\n", start, line, col)
            elif self.source.startswith("//", self.index):
                while self._peek() not in ("\0", "\n"):
                    self._advance()
            elif self.source.startswith("/*", self.index):
                self._block_comment()
            elif self.source.startswith("[@", self.index):
                start, line, col = self.index, self.line, self.column
                self._advance(); self._advance()
                self._emit("FRAME_OPEN", "[@", start, line, col)
            elif self.source.startswith("@]", self.index):
                start, line, col = self.index, self.line, self.column
                self._advance(); self._advance()
                self._emit("FRAME_CLOSE", "@]", start, line, col)
            elif c == '"':
                self._string()
            elif c.isdigit():
                self._number()
            elif c.isalpha() or c == "_":
                self._identifier()
            elif c in FORBIDDEN:
                raise self._error(f"forbidden character {c!r}", "LEX_FORBIDDEN_CHAR")
            elif c + self._peek(1) in self.TWO_CHAR:
                start, line, col = self.index, self.line, self.column
                value = c + self._peek(1)
                self._advance(); self._advance()
                self._emit("OP", value, start, line, col)
            elif c in self.PUNCTUATION:
                start, line, col = self.index, self.line, self.column
                self._advance()
                self._emit("PUNCT", c, start, line, col)
            elif c in self.SINGLE_OPERATORS:
                start, line, col = self.index, self.line, self.column
                self._advance()
                self._emit("OP", c, start, line, col)
            else:
                raise self._error(f"unexpected character {c!r}", "LEX_UNEXPECTED_CHAR")
        span = SourceSpan(self.index, self.index, self.line, self.column, self.line, self.column)
        self.tokens.append(Token("EOF", "", span))
        return self.tokens

    def _block_comment(self) -> None:
        start, line, col = self.index, self.line, self.column
        self._advance(); self._advance()
        while self.index < len(self.source) and not self.source.startswith("*/", self.index):
            self._advance()
        if self.index >= len(self.source):
            raise QcsError("unterminated block comment", self.filename, line, col, "LEX_UNTERMINATED_COMMENT")
        self._advance(); self._advance()

    def _string(self) -> None:
        start, line, col = self.index, self.line, self.column
        self._advance()
        value: list[str] = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
        while self.index < len(self.source) and self._peek() != '"':
            ch = self._advance()
            if ch == "\n":
                raise QcsError("string literal cannot span lines", self.filename, line, col, "LEX_INVALID_STRING")
            if ch == "\\":
                if self.index >= len(self.source):
                    break
                escaped = self._advance()
                if escaped not in escapes:
                    raise QcsError(f"unknown escape sequence \\{escaped}", self.filename,
                                   self.line, self.column, "LEX_INVALID_ESCAPE")
                value.append(escapes[escaped])
            else:
                value.append(ch)
        if self._peek() != '"':
            raise QcsError("unterminated string literal", self.filename, line, col, "LEX_UNTERMINATED_STRING")
        self._advance()
        self._emit("STRING", "".join(value), start, line, col)

    def _number(self) -> None:
        start, line, col = self.index, self.line, self.column
        match = NUMBER_RE.match(self.source, self.index)
        if match is None:
            raise self._error("invalid numeric literal", "LEX_INVALID_NUMBER")
        for _ in match.group(0):
            self._advance()
        unit_start = self.index
        while self._peek().isalpha():
            self._advance()
        unit = self.source[unit_start:self.index]
        if unit and unit not in DURATION_UNITS:
            raise QcsError(f"unknown numeric suffix {unit!r}", self.filename, line, col, "LEX_INVALID_SUFFIX")
        self._emit("DURATION" if unit else "NUMBER", match.group(0) + unit, start, line, col)

    def _identifier(self) -> None:
        start, line, col = self.index, self.line, self.column
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        value = self.source[start:self.index]
        self._emit("KEYWORD" if value in KEYWORDS else "IDENT", value, start, line, col)

    def _error(self, message: str, code: str) -> QcsError:
        return QcsError(message, self.filename, self.line, self.column, code)


class QcsParser:
    PRECEDENCE = {
        "then": 1, "send": 1, "back": 1,
        "or": 2, "||": 2, "and": 3, "&&": 3,
        "==": 4, "!=": 4, "lt": 4, "le": 4, "gt": 4, "ge": 4,
        "bor": 5, "bxor": 5, "band": 5, "&": 5, "^": 5,
        "shl": 6, "shr": 6, "+": 7, "-": 7, "&+": 7, "++": 7,
        "*": 8, "/": 8, "%": 8,
    }

    def __init__(self, tokens: list[Token], source: str = "",
                 filename: str = "<memory>") -> None:
        self.tokens, self.source, self.filename = tokens, source, filename
        self.current = 0

    def parse(self) -> AstNode:
        declarations: list[AstNode] = []
        self._skip_newlines()
        while not self._at("EOF"):
            if self._at("FRAME_OPEN"):
                declarations.append(self._frame())
            elif self._at_value("func"):
                declarations.append(self._function())
            elif self._at_value("struct", "enum", "protocol"):
                declarations.append(self._opaque_type_decl())
            else:
                declarations.append(self._statement())
            self._statement_end()
        span = declarations[0].span if declarations else self._peek().span
        return AstNode("Module", {"declarations": declarations}, span)

    def _frame(self) -> AstNode:
        opening = self._expect("FRAME_OPEN", "expected [@ to open a frame")
        attributes: dict[str, AstNode] = {}
        self._skip_newlines()
        while not self._at("FRAME_CLOSE"):
            key = self._expect("IDENT", "expected a frame attribute name")
            self._expect_value(":", "expected ':' after frame attribute")
            if key.value in attributes:
                raise self._error(key, f"duplicate frame attribute {key.value!r}", "PARSE_DUPLICATE_ATTRIBUTE")
            if key.value == "state":
                marker = self._peek()
                if marker.kind == "OP" and marker.value in ("!", "?"):
                    self._advance()
                    value = AstNode("State", {"value": "required" if marker.value == "!" else "optional"}, marker.span)
                else:
                    value = self._expression()
            else:
                value = self._expression()
            attributes[key.value] = value
            self._skip_newlines()
            if not self._match_value(","):
                break
            self._skip_newlines()
        self._expect("FRAME_CLOSE", "expected @] after frame header")
        if "domain" not in attributes:
            raise self._error(opening, "frame header requires domain", "PARSE_EXPECTED_DOMAIN")
        if "state" in attributes:
            state = attributes["state"]
            state_value = state.fields.get("value") if state.kind == "State" else (
                state.fields.get("name") if state.kind == "Name" else None
            )
            if state_value not in {"required", "optional", "deferred"}:
                raise self._error(opening, "state must be !, ?, or deferred", "PARSE_INVALID_STATE")
        body: list[AstNode] = []
        self._skip_newlines()
        while not self._is_frame_end():
            if self._at("EOF"):
                raise self._error(opening, "unterminated frame; expected [@ end @]", "PARSE_UNTERMINATED_FRAME")
            if self._at("FRAME_OPEN"):
                body.append(self._frame())
            elif self._at_value("func"):
                body.append(self._function())
            elif self._at_value("struct", "enum", "protocol"):
                body.append(self._opaque_type_decl())
            else:
                body.append(self._statement())
            self._statement_end()
        self._advance()
        self._advance()
        end_close = self._expect("FRAME_CLOSE", "expected @] after end")
        span = SourceSpan(opening.span.start, end_close.span.end, opening.span.line,
                          opening.span.column, end_close.span.end_line, end_close.span.end_column)
        return AstNode("Frame", {"attributes": attributes, "domain": attributes["domain"],
                                "state": attributes.get("state"), "body": body}, span)

    def _is_frame_end(self) -> bool:
        return self._at("FRAME_OPEN") and self._peek(1).kind == "KEYWORD" and self._peek(1).value == "end"

    def _function(self) -> AstNode:
        start = self._expect_value("func", "expected func")
        name = self._expect("IDENT", "expected function name")
        self._expect_value("(", "expected '(' after function name")
        parameters: list[dict[str, Any]] = []
        self._skip_newlines()
        while not self._at_value(")"):
            mutable = self._match_value("inout")
            param = self._expect("IDENT", "expected parameter name")
            self._expect_value(":", "expected ':' after parameter name")
            parameters.append({"name": param.value, "inout": mutable, "type": self._type()})
            self._skip_newlines()
            if not self._match_value(","):
                break
            self._skip_newlines()
        self._expect_value(")", "expected ')' after parameters")
        return_type = self._type() if self._match_value("returns") else None
        body = self._block()
        span = SourceSpan(start.span.start, body.span.end, start.span.line, start.span.column,
                          body.span.end_line, body.span.end_column)
        return AstNode("Function", {"name": name.value, "parameters": parameters,
                                   "return_type": return_type, "body": body}, span)

    def _type(self) -> AstNode:
        start = self._peek()
        if self._match_value("inout"):
            return AstNode("InOutType", {"value": self._type()}, start.span)
        name = self._expect("IDENT", "expected type name")
        arguments: list[AstNode] = []
        if self._match_value("("):
            self._skip_newlines()
            while not self._at_value(")"):
                arguments.append(self._type())
                self._skip_newlines()
                if not self._match_value(","):
                    break
                self._skip_newlines()
            self._expect_value(")", "expected ')' after type arguments")
        optional = self._match_value("?")
        return AstNode("Type", {"name": name.value, "arguments": arguments, "optional": optional}, start.span)

    def _opaque_type_decl(self) -> AstNode:
        keyword = self._advance()
        name = self._expect("IDENT", "expected type declaration name")
        self._skip_newlines()
        if not self._at_value("{"):
            return AstNode("TypeDeclaration", {"declaration_kind": keyword.value, "name": name.value, "body": ""}, keyword.span)
        opening = self._advance()
        depth = 1
        while depth and not self._at("EOF"):
            token = self._advance()
            if token.value == "{":
                depth += 1
            elif token.value == "}":
                depth -= 1
        if depth:
            raise self._error(opening, "unterminated type declaration body", "PARSE_UNTERMINATED_BLOCK")
        end = self._previous()
        return AstNode("TypeDeclaration", {
            "declaration_kind": keyword.value, "name": name.value,
            "body": self.source[opening.span.start:end.span.end],
        }, SourceSpan(keyword.span.start, end.span.end, keyword.span.line, keyword.span.column,
                      end.span.end_line, end.span.end_column))

    def _block(self) -> AstNode:
        opening = self._expect_value("{", "expected '{' to start block")
        statements: list[AstNode] = []
        self._skip_newlines()
        while not self._at_value("}") and not self._at("EOF"):
            if self._at("FRAME_OPEN"):
                statements.append(self._frame())
            elif self._at_value("func"):
                statements.append(self._function())
            else:
                statements.append(self._statement())
            self._statement_end()
            self._skip_newlines()
        closing = self._expect_value("}", "expected '}' after block")
        return AstNode("Block", {"statements": statements}, SourceSpan(
            opening.span.start, closing.span.end, opening.span.line, opening.span.column,
            closing.span.end_line, closing.span.end_column))

    def _statement(self) -> AstNode:
        if self._at_value("let", "var"):
            start = self._advance()
            name = self._expect("IDENT", "expected variable name")
            type_node = self._type() if self._match_value(":") else None
            self._expect_value("=", "expected '=' in variable declaration")
            return AstNode("Variable", {"name": name.value, "mutable": start.value == "var",
                                        "type": type_node, "value": self._expression()}, start.span)
        if self._match_value("return"):
            token = self._previous()
            value = None if self._at("NEWLINE") or self._at_value("}") else self._expression()
            return AstNode("Return", {"value": value}, token.span)
        if self._at_value("guard"):
            return self._guard()
        if self._match_value("if"):
            start = self._previous()
            condition, yes = self._expression(), self._block()
            saved = self.current
            self._skip_newlines()
            no = self._block() if self._match_value("else") else None
            if no is None:
                self.current = saved
            return AstNode("If", {"condition": condition, "then": yes, "else": no}, start.span)
        if self._match_value("for"):
            start = self._previous()
            name = self._expect("IDENT", "expected loop variable")
            self._expect_value("in", "expected 'in' after loop variable")
            return AstNode("For", {"name": name.value, "iterable": self._expression(), "body": self._block()}, start.span)
        if self._match_value("while"):
            start = self._previous()
            return AstNode("While", {"condition": self._expression(), "body": self._block()}, start.span)
        if self._match_value("defer"):
            start = self._previous()
            return AstNode("Defer", {"body": self._block()}, start.span)
        left = self._expression()
        if self._match_value("="):
            return AstNode("Assignment", {"target": left, "value": self._expression()}, left.span)
        return AstNode("ExpressionStatement", {"expression": left}, left.span)

    def _guard(self) -> AstNode:
        start = self._expect_value("guard", "expected guard")
        binding = None
        if self._match_value("let") or self._match_value("var"):
            name = self._expect("IDENT", "expected optional binding name")
            self._expect_value("=", "expected '=' in guard binding")
            value = self._expression()
            binding = {"name": name.value, "value": value}
        else:
            value = self._expression()
        self._expect_value("else", "expected else after guard condition")
        return AstNode("Guard", {"binding": binding, "condition": None if binding else value,
                                 "value": value, "else": self._block()}, start.span)

    def _expression(self, minimum: int = 1) -> AstNode:
        left = self._prefix()
        while True:
            if self._match_value("."):
                member = self._expect("IDENT", "expected member name after '.'")
                left = AstNode("Member", {"base": left, "name": member.value}, left.span)
                continue
            if self._match_value("("):
                args: list[dict[str, Any]] = []
                self._skip_newlines()
                while not self._at_value(")"):
                    label = None
                    if self._at("IDENT") and self._peek(1).value == ":":
                        label = self._advance().value
                        self._advance()
                    args.append({"label": label, "value": self._expression()})
                    self._skip_newlines()
                    if not self._match_value(","):
                        break
                    self._skip_newlines()
                self._expect_value(")", "expected ')' after call arguments")
                left = AstNode("Call", {"callee": left, "arguments": args}, left.span)
                continue
            if self._match_value("["):
                index = self._expression()
                self._expect_value("]", "expected ']' after index")
                left = AstNode("Index", {"base": left, "index": index}, left.span)
                continue
            op = self._peek().value
            precedence = self.PRECEDENCE.get(op, 0)
            if precedence < minimum:
                break
            token = self._advance()
            right = self._expression(precedence + 1)
            left = AstNode("Flow" if op in {"then", "send", "back"} else "Binary",
                           {"operator": op, "left": left, "right": right}, token.span)
        return left

    def _prefix(self) -> AstNode:
        token = self._peek()
        if token.kind in {"NUMBER", "DURATION", "STRING"}:
            self._advance()
            return AstNode("Literal", {"value": token.value, "literal_kind": token.kind.lower()}, token.span)
        if token.kind == "KEYWORD" and token.value in {"true", "false", "nil"}:
            self._advance()
            return AstNode("Literal", {"value": {"true": True, "false": False, "nil": None}[token.value],
                                       "literal_kind": token.value}, token.span)
        if (token.kind == "OP" and token.value in {"!", "-", "+", "&"}) or (
            token.kind == "KEYWORD" and token.value == "not"
        ):
            self._advance()
            return AstNode("Unary", {"operator": token.value, "operand": self._expression(9)}, token.span)
        if self._match_value("("):
            expr = self._expression()
            self._expect_value(")", "expected ')' after expression")
            return expr
        if self._match_value("["):
            start = self._previous()
            items: list[AstNode] = []
            self._skip_newlines()
            while not self._at_value("]"):
                items.append(self._expression())
                self._skip_newlines()
                if not self._match_value(","):
                    break
                self._skip_newlines()
            self._expect_value("]", "expected ']' after list literal")
            return AstNode("Array", {"items": items}, start.span)
        if token.kind in {"IDENT", "KEYWORD"}:
            self._advance()
            return AstNode("Name", {"name": token.value}, token.span)
        raise self._error(token, "expected expression", "PARSE_EXPECTED_EXPRESSION")

    def _statement_end(self) -> None:
        if self._match("NEWLINE"):
            self._skip_newlines()
            return
        if self._match_value(";"):
            self._skip_newlines()
            return
        if self._at_value("}") or self._at("EOF") or self._is_frame_end() or self._at("FRAME_OPEN"):
            return
        raise self._error(self._peek(), "expected newline or ';' after statement", "PARSE_EXPECTED_STATEMENT_END")

    def _skip_newlines(self) -> None:
        while self._match("NEWLINE"):
            pass

    def _at(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _at_value(self, *values: str) -> bool:
        return self._peek().value in values

    def _match(self, kind: str) -> bool:
        if self._at(kind):
            self._advance()
            return True
        return False

    def _match_value(self, *values: str) -> bool:
        if self._at_value(*values):
            self._advance()
            return True
        return False

    def _expect(self, kind: str, message: str) -> Token:
        if not self._at(kind):
            raise self._error(self._peek(), message)
        return self._advance()

    def _expect_value(self, value: str, message: str) -> Token:
        if not self._at_value(value):
            raise self._error(self._peek(), message)
        return self._advance()

    def _advance(self) -> Token:
        token = self._peek()
        if token.kind != "EOF":
            self.current += 1
        return token

    def _peek(self, offset: int = 0) -> Token:
        return self.tokens[min(self.current + offset, len(self.tokens) - 1)]

    def _previous(self) -> Token:
        return self.tokens[max(0, self.current - 1)]

    def _error(self, token: Token, message: str, code: str = "PARSE_ERROR") -> QcsError:
        return QcsError(message, self.filename, token.span.line, token.span.column, code)


def _to_data(value: Any) -> Any:
    if isinstance(value, AstNode):
        return value.to_dict()
    if isinstance(value, SourceSpan):
        return {"start": value.start, "end": value.end, "line": value.line,
                "column": value.column, "end_line": value.end_line, "end_column": value.end_column}
    if isinstance(value, dict):
        return {key: _to_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_data(item) for item in value]
    return value


def lex(source: str, filename: str = "<memory>") -> list[Token]:
    return QcsLexer(source, filename).tokenize()


def parse(source: str, filename: str = "<memory>") -> AstNode:
    return QcsParser(lex(source, filename), source, filename).parse()


def validate(module: AstNode) -> list[str]:
    """Check registered hardware domains; this does not prove invariants."""
    diagnostics: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, AstNode):
            if value.kind == "Frame":
                domain = value.fields["domain"]
                domain_name = domain.fields.get("name") if domain.kind == "Name" else None
                if domain.kind == "Call":
                    callee = domain.fields.get("callee")
                    if isinstance(callee, AstNode) and callee.kind == "Name":
                        domain_name = callee.fields.get("name")
                if domain_name not in DOMAIN_REGISTRY:
                    diagnostics.append(f"unknown QCS domain: {domain_name or '<invalid>'}")
            for child in value.fields.values():
                visit(child)
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)
    visit(module)
    return diagnostics


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper-qcs", description="QCS lexer, parser and AST inspector")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "ast", "tokens"):
        item = sub.add_parser(command)
        item.add_argument("source", type=Path)
        item.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_cli().parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8")
        tokens = lex(source, str(args.source))
        if args.command == "tokens":
            rows = [{"kind": t.kind, "value": t.value, "line": t.span.line,
                     "column": t.span.column, "start": t.span.start, "end": t.span.end} for t in tokens]
            print(json.dumps(rows, ensure_ascii=False, indent=2) if args.json else
                  "\n".join(f"{r['line']}:{r['column']} {r['kind']:<12} {r['value']}" for r in rows))
            return 0
        module = QcsParser(tokens, source, str(args.source)).parse()
        diagnostics = validate(module)
        if diagnostics:
            for message in diagnostics:
                print(f"reaper-qcs: {message}", file=sys.stderr)
            return 1
        if args.command == "ast":
            print(json.dumps(module.to_dict(), ensure_ascii=False, indent=2))
        elif args.json:
            print(json.dumps({"ok": True, "format": "QCS 1.0",
                              "declarations": len(module.fields["declarations"])}, ensure_ascii=False))
        else:
            print(f"QCS: {args.source} is valid")
        return 0
    except (OSError, UnicodeError, QcsError) as error:
        print(f"reaper-qcs: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
