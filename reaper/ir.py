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
        elif node.kind == "maza":
            self.emit("MAZA", node.value, node.token)
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
    "CALL", "PIPE_CALL", "BINARY", "AND_JUMP", "OR_JUMP", "IMPORT", "MAZA", "EXPORT",
}


def lower(tree: Node, source_name: str = "<memory>") -> CanonicalIR:
    compiler = _Lowerer()
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

            elif op == "MAZA":
                if not isinstance(argument, tuple) or len(argument) != 2:
                    raise IRVerificationError(f"{where}: MAZA requires (specifier, alias)")
                require_name(argument[0], where)
                require_name(argument[1], where)

            elif op == "UNARY":
                if not isinstance(argument, str) or argument not in {"NOT", "-"}:
                    raise IRVerificationError(f"{where}: unsupported unary operator {argument!r}")

            elif op == "BINARY":
                if not isinstance(argument, str) or argument not in binary_operators:
                    raise IRVerificationError(f"{where}: unsupported binary operator {argument!r}")

    check(module.code, module.source_name)
