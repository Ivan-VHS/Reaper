"""Canonical stack IR lowering for the Reaper AST."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .parser import Node
from .source_profile import SourceSpan, span_for_node, span_for_token


@dataclass(frozen=True, slots=True)
class IRInstruction:
    op: str
    argument: Any
    token: Any
    span: SourceSpan | None = None
    syntax_mode: str = "classic"
    locale: str = "en"


@dataclass(frozen=True, slots=True)
class IRFunction:
    name: str
    parameters: tuple[str, ...]
    code: tuple[IRInstruction, ...]


@dataclass(frozen=True, slots=True)
class CanonicalIR:
    code: tuple[IRInstruction, ...]
    source_name: str = "<memory>"


class IRVerificationError(ValueError):
    pass


class _Lowerer:
    def __init__(self, source_name: str = "<memory>") -> None:
        self.source_name = source_name
        self.code: list[IRInstruction] = []

    def emit(self, op: str, argument: Any, source: Any) -> int:
        if isinstance(source, Node):
            token = source.token
            span = span_for_node(source, self.source_name)
        else:
            token = source
            span = span_for_token(token, self.source_name)
        self.code.append(
            IRInstruction(
                op,
                argument,
                token,
                span,
                getattr(token, "syntax_mode", "classic"),
                getattr(token, "locale", "en"),
            )
        )
        return len(self.code) - 1

    def patch(self, index: int, argument: Any) -> None:
        old = self.code[index]
        self.code[index] = IRInstruction(
            old.op,
            argument,
            old.token,
            old.span,
            old.syntax_mode,
            old.locale,
        )

    def statements(self, nodes: list[Node] | None) -> None:
        for node in nodes or []:
            self.statement(node)

    def scoped_block(self, block: Node) -> None:
        self.emit("ENTER_SCOPE", None, block.start_token or block)
        self.statements(block.children)
        self.emit("EXIT_SCOPE", None, block.token)

    def statement(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "declare":
            self.expression(children[0])
            self.emit("DEFINE", node.value, node)
        elif node.kind == "change":
            self.expression(children[0])
            self.emit("ASSIGN", node.value, node)
        elif node.kind == "emit":
            self.expression(children[0])
            self.emit("EMIT", None, node)
        elif node.kind == "yield":
            if children:
                self.expression(children[0])
            else:
                self.emit("CONST", None, node)
            self.emit("RETURN", None, node)
        elif node.kind == "function":
            name, parameters = node.value
            nested = _Lowerer(self.source_name)
            nested.statements(children[0].children)
            nested.emit("CONST", None, node)
            nested.emit("RETURN", None, node)
            function = IRFunction(name, tuple(parameters), tuple(nested.code))
            self.emit("MAKE_FUNCTION", function, node)
            self.emit("DEFINE", (name, False), node)
        elif node.kind == "when":
            self.expression(children[0])
            no_jump = self.emit("JUMP_IF_FALSE", None, node)
            self.scoped_block(children[1])
            if len(children) == 3:
                end_jump = self.emit("JUMP", None, node)
                self.patch(no_jump, len(self.code))
                self.scoped_block(children[2])
                self.patch(end_jump, len(self.code))
            else:
                self.patch(no_jump, len(self.code))
        elif node.kind == "each":
            self.expression(children[0])
            self.emit("ITER_INIT", node.value, node)
            loop_start = len(self.code)
            next_index = self.emit("ITER_NEXT", (node.value, None), node)
            self.statements(children[1].children)
            self.emit("EXIT_SCOPE", None, node)
            self.emit("JUMP", loop_start, node)
            self.patch(next_index, (node.value, len(self.code)))
            self.emit("ITER_END", None, node)
        elif node.kind == "while":
            loop_start = len(self.code)
            self.expression(children[0])
            exit_jump = self.emit("JUMP_IF_FALSE", None, node)
            self.scoped_block(children[1])
            self.emit("JUMP", loop_start, node)
            self.patch(exit_jump, len(self.code))
        elif node.kind == "expression":
            self.expression(children[0])
            self.emit("POP", None, node)
        elif node.kind == "block":
            self.scoped_block(node)
        elif node.kind == "import":
            self.emit("IMPORT", node.value, node)
        elif node.kind == "export":
            if children:
                child = children[0]
                self.statement(child)
                if child.kind == "declare":
                    name = child.value[0]
                elif child.kind == "function":
                    name = child.value[0]
                else:
                    raise IRVerificationError("only declarations and functions can be exported inline")
            else:
                name = node.value
            self.emit("EXPORT", name, node)
        else:
            raise IRVerificationError(f"cannot lower statement kind: {node.kind}")

    def expression(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "literal":
            self.emit("CONST", node.value, node)
        elif node.kind == "name":
            self.emit("LOAD", node.value, node)
        elif node.kind == "list":
            for item in children:
                self.expression(item)
            self.emit("BUILD_LIST", len(children), node)
        elif node.kind == "index":
            self.expression(children[0])
            self.expression(children[1])
            self.emit("INDEX", None, node)
        elif node.kind == "unary":
            self.expression(children[0])
            self.emit("UNARY", node.value, node)
        elif node.kind == "call":
            self.expression(children[0])
            for argument in children[1:]:
                self.expression(argument)
            self.emit("CALL", len(children) - 1, node)
        elif node.kind == "binary":
            operator = node.value
            if operator == "AND":
                self.expression(children[0])
                index = self.emit("AND_JUMP", None, node)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "OR":
                self.expression(children[0])
                index = self.emit("OR_JUMP", None, node)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "::":
                self.expression(children[0])
                right = children[1]
                if right.kind == "call":
                    self.expression(right.children[0])
                    for argument in right.children[1:]:
                        self.expression(argument)
                    self.emit("PIPE_CALL", len(right.children) - 1, node)
                else:
                    self.expression(right)
                    self.emit("PIPE_CALL", 0, node)
            else:
                self.expression(children[0])
                self.expression(children[1])
                self.emit("BINARY", operator, node)
        else:
            raise IRVerificationError(f"cannot lower expression kind: {node.kind}")


_ALLOWED = {
    "CONST", "LOAD", "DEFINE", "ASSIGN", "EMIT", "RETURN", "MAKE_FUNCTION",
    "JUMP_IF_FALSE", "JUMP", "ENTER_SCOPE", "EXIT_SCOPE", "ITER_INIT",
    "ITER_NEXT", "ITER_END", "POP", "BUILD_LIST", "INDEX", "UNARY",
    "CALL", "PIPE_CALL", "BINARY", "AND_JUMP", "OR_JUMP", "IMPORT", "EXPORT",
}


def lower(tree: Node, source_name: str = "<memory>") -> CanonicalIR:
    compiler = _Lowerer(source_name)
    compiler.statements(tree.children)
    module = CanonicalIR(tuple(compiler.code), source_name)
    verify(module)
    return module


def verify(module: CanonicalIR) -> None:
    """Validate IR structure and operands before a VM can consume the module."""
    if not isinstance(module, CanonicalIR):
        raise IRVerificationError("expected a CanonicalIR module")
    if not isinstance(module.code, tuple):
        raise IRVerificationError("module code must be an immutable instruction tuple")
    if not isinstance(module.source_name, str) or not module.source_name:
        raise IRVerificationError("module source_name must be non-empty text")

    binary_operators = {
        "==", "!=", "<", "<=", ">", ">=", "++",
        "+", "-", "*", "/", "//", "%", "**",
    }

    def require_name(value: Any, label: str) -> None:
        if not isinstance(value, str) or not value:
            raise IRVerificationError(f"{label}: expected a non-empty name")

    def check(code: tuple[IRInstruction, ...], label: str) -> None:
        if not isinstance(code, tuple):
            raise IRVerificationError(f"{label}: instruction code must be a tuple")

        for index, instruction in enumerate(code):
            where = f"{label}: instruction {index}"
            if not isinstance(instruction, IRInstruction):
                raise IRVerificationError(f"{where}: expected an IRInstruction")
            if not isinstance(instruction.op, str) or instruction.op not in _ALLOWED:
                raise IRVerificationError(f"{where}: unknown IR operation: {instruction.op!r}")

            op = instruction.op
            argument = instruction.argument

            if instruction.span is not None:
                if not isinstance(instruction.span, SourceSpan):
                    raise IRVerificationError(f"{where}: invalid source span metadata")
                span = instruction.span
                if (
                    not isinstance(span.file, str)
                    or not span.file
                    or type(span.line) is not int
                    or type(span.col) is not int
                    or type(span.start) is not int
                    or type(span.end) is not int
                    or span.line < 1
                    or span.col < 1
                    or span.start < 0
                    or span.end < span.start
                ):
                    raise IRVerificationError(f"{where}: malformed source span metadata")
                if (
                    not isinstance(instruction.syntax_mode, str)
                    or instruction.syntax_mode not in {"classic", "flow"}
                ):
                    raise IRVerificationError(f"{where}: unsupported syntax profile metadata")
                if (
                    not isinstance(instruction.locale, str)
                    or instruction.locale not in {"en", "ru", "uk", "most"}
                ):
                    raise IRVerificationError(f"{where}: unsupported locale metadata")

            if op in {"JUMP", "JUMP_IF_FALSE", "AND_JUMP", "OR_JUMP"}:
                if type(argument) is not int or argument < 0 or argument > len(code):
                    raise IRVerificationError(f"{where}: invalid jump target")

            elif op in {"CALL", "PIPE_CALL", "BUILD_LIST"}:
                if type(argument) is not int or argument < 0:
                    raise IRVerificationError(f"{where}: argument count must be a non-negative integer")

            elif op == "DEFINE":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: DEFINE requires (name, mutable)")
                require_name(argument[0], where)
                if type(argument[1]) is not bool:
                    raise IRVerificationError(f"{where}: DEFINE mutable flag must be boolean")

            elif op in {"LOAD", "ASSIGN", "EXPORT", "ITER_INIT"}:
                require_name(argument, where)

            elif op == "ITER_NEXT":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: ITER_NEXT requires (name, target)")
                require_name(argument[0], where)
                target = argument[1]
                if type(target) is not int or target < 0 or target > len(code):
                    raise IRVerificationError(f"{where}: invalid iterator exit target")

            elif op == "MAKE_FUNCTION":
                function = argument
                if not isinstance(function, IRFunction):
                    raise IRVerificationError(f"{where}: MAKE_FUNCTION requires an IRFunction")
                require_name(function.name, where)
                if not isinstance(function.parameters, tuple):
                    raise IRVerificationError(f"{where}: function parameters must be a tuple")
                for parameter in function.parameters:
                    require_name(parameter, where)
                if len(set(function.parameters)) != len(function.parameters):
                    raise IRVerificationError(f"{where}: function parameter names must be unique")
                check(function.code, function.name)

            elif op == "IMPORT":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: IMPORT requires (specifier, alias)")
                require_name(argument[0], where)
                if argument[1] is not None:
                    require_name(argument[1], where)

            elif op == "UNARY":
                if not isinstance(argument, str) or argument not in {"NOT", "-"}:
                    raise IRVerificationError(f"{where}: unsupported unary operator {argument!r}")

            elif op == "BINARY":
                if not isinstance(argument, str) or argument not in binary_operators:
                    raise IRVerificationError(f"{where}: unsupported binary operator {argument!r}")

    check(module.code, module.source_name)
