"""Canonical stack IR lowering for the Reaper AST."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .parser import Node


@dataclass(frozen=True, slots=True)
class IRInstruction:
    op: str
    argument: Any
    token: Any


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
    def __init__(self) -> None:
        self.code: list[IRInstruction] = []

    def emit(self, op: str, argument: Any, token: Any) -> int:
        self.code.append(IRInstruction(op, argument, token))
        return len(self.code) - 1

    def patch(self, index: int, argument: Any) -> None:
        old = self.code[index]
        self.code[index] = IRInstruction(old.op, argument, old.token)

    def statements(self, nodes: list[Node] | None) -> None:
        for node in nodes or []:
            self.statement(node)

    def scoped_block(self, block: Node) -> None:
        self.emit("ENTER_SCOPE", None, block.token)
        self.statements(block.children)
        self.emit("EXIT_SCOPE", None, block.token)

    def statement(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "declare":
            self.expression(children[0])
            self.emit("DEFINE", node.value, node.token)
        elif node.kind == "change":
            self.expression(children[0])
            self.emit("ASSIGN", node.value, node.token)
        elif node.kind == "emit":
            self.expression(children[0])
            self.emit("EMIT", None, node.token)
        elif node.kind == "yield":
            if children:
                self.expression(children[0])
            else:
                self.emit("CONST", None, node.token)
            self.emit("RETURN", None, node.token)
        elif node.kind == "function":
            name, parameters = node.value
            nested = _Lowerer()
            nested.statements(children[0].children)
            nested.emit("CONST", None, node.token)
            nested.emit("RETURN", None, node.token)
            function = IRFunction(name, tuple(parameters), tuple(nested.code))
            self.emit("MAKE_FUNCTION", function, node.token)
            self.emit("DEFINE", (name, False), node.token)
        elif node.kind == "when":
            self.expression(children[0])
            no_jump = self.emit("JUMP_IF_FALSE", None, node.token)
            self.scoped_block(children[1])
            if len(children) == 3:
                end_jump = self.emit("JUMP", None, node.token)
                self.patch(no_jump, len(self.code))
                self.scoped_block(children[2])
                self.patch(end_jump, len(self.code))
            else:
                self.patch(no_jump, len(self.code))
        elif node.kind == "each":
            self.expression(children[0])
            self.emit("ITER_INIT", node.value, node.token)
            loop_start = len(self.code)
            next_index = self.emit("ITER_NEXT", (node.value, None), node.token)
            self.statements(children[1].children)
            self.emit("EXIT_SCOPE", None, node.token)
            self.emit("JUMP", loop_start, node.token)
            self.patch(next_index, (node.value, len(self.code)))
            self.emit("ITER_END", None, node.token)
        elif node.kind == "while":
            loop_start = len(self.code)
            self.expression(children[0])
            exit_jump = self.emit("JUMP_IF_FALSE", None, node.token)
            self.scoped_block(children[1])
            self.emit("JUMP", loop_start, node.token)
            self.patch(exit_jump, len(self.code))
        elif node.kind == "expression":
            self.expression(children[0])
            self.emit("POP", None, node.token)
        elif node.kind == "block":
            self.scoped_block(node)
        elif node.kind == "import":
            self.emit("IMPORT", node.value, node.token)
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
            self.emit("EXPORT", name, node.token)
        else:
            raise IRVerificationError(f"cannot lower statement kind: {node.kind}")

    def expression(self, node: Node) -> None:
        children = node.children or []
        if node.kind == "literal":
            self.emit("CONST", node.value, node.token)
        elif node.kind == "name":
            self.emit("LOAD", node.value, node.token)
        elif node.kind == "list":
            for item in children:
                self.expression(item)
            self.emit("BUILD_LIST", len(children), node.token)
        elif node.kind == "map":
            for item in children:
                self.expression(item)
            self.emit("BUILD_MAP", len(children) // 2, node.token)
        elif node.kind == "member":
            self.expression(children[0])
            self.emit("MEMBER", node.value, node.token)
        elif node.kind == "index":
            self.expression(children[0])
            self.expression(children[1])
            self.emit("INDEX", None, node.token)
        elif node.kind == "unary":
            self.expression(children[0])
            self.emit("UNARY", node.value, node.token)
        elif node.kind == "call":
            self.expression(children[0])
            for argument in children[1:]:
                self.expression(argument)
            self.emit("CALL", len(children) - 1, node.token)
        elif node.kind == "binary":
            operator = node.value
            if operator == "AND":
                self.expression(children[0])
                index = self.emit("AND_JUMP", None, node.token)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "OR":
                self.expression(children[0])
                index = self.emit("OR_JUMP", None, node.token)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "??":
                self.expression(children[0])
                index = self.emit("COALESCE_JUMP", None, node.token)
                self.expression(children[1])
                self.patch(index, len(self.code))
            elif operator == "::":
                self.expression(children[0])
                right = children[1]
                if right.kind == "call":
                    self.expression(right.children[0])
                    for argument in right.children[1:]:
                        self.expression(argument)
                    self.emit("PIPE_CALL", len(right.children) - 1, node.token)
                else:
                    self.expression(right)
                    self.emit("PIPE_CALL", 0, node.token)
            else:
                self.expression(children[0])
                self.expression(children[1])
                self.emit("BINARY", operator, node.token)
        else:
            raise IRVerificationError(f"cannot lower expression kind: {node.kind}")


_ALLOWED = {
    "CONST", "LOAD", "DEFINE", "ASSIGN", "EMIT", "RETURN", "MAKE_FUNCTION",
    "JUMP_IF_FALSE", "JUMP", "ENTER_SCOPE", "EXIT_SCOPE", "ITER_INIT",
    "ITER_NEXT", "ITER_END", "POP", "BUILD_LIST", "INDEX", "UNARY",
    "CALL", "PIPE_CALL", "BINARY", "AND_JUMP", "OR_JUMP", "COALESCE_JUMP",
    "BUILD_MAP", "MEMBER", "IMPORT", "EXPORT",
}


def lower(tree: Node, source_name: str = "<memory>") -> CanonicalIR:
    compiler = _Lowerer()
    compiler.statements(tree.children)
    module = CanonicalIR(tuple(compiler.code), source_name)
    verify(module)
    return module


def verify(module: CanonicalIR) -> None:
    if not isinstance(module, CanonicalIR):
        raise IRVerificationError("expected a CanonicalIR module")

    def check(code: tuple[IRInstruction, ...], label: str) -> None:
        for index, instruction in enumerate(code):
            if instruction.op not in _ALLOWED:
                raise IRVerificationError(f"{label}: unknown IR operation at {index}: {instruction.op}")
            if instruction.op in {"JUMP", "JUMP_IF_FALSE", "AND_JUMP", "OR_JUMP", "COALESCE_JUMP"}:
                target = instruction.argument
                if not isinstance(target, int) or target < 0 or target > len(code):
                    raise IRVerificationError(f"{label}: invalid jump target at {index}")
            if instruction.op == "MAKE_FUNCTION":
                if not isinstance(instruction.argument, IRFunction):
                    raise IRVerificationError(f"{label}: MAKE_FUNCTION requires an IRFunction")
                check(instruction.argument.code, instruction.argument.name)

    check(module.code, module.source_name)
