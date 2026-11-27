"""Bytecode assembler and stack virtual machine over Canonical IR."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .debugger import DebuggerStopped
from .errors import ReaperRuntimeError
from .ir import CanonicalIR, IRFunction, IRInstruction, verify
from .runtime import Builtin, Environment, _is_register_number
from .lexer import Token


_OPCODES = {
    name: index for index, name in enumerate((
        "CONST", "LOAD", "DEFINE", "DEFINE_REGISTER", "ASSIGN", "EMIT", "RETURN", "MAKE_FUNCTION",
        "JUMP_IF_FALSE", "JUMP", "ENTER_SCOPE", "EXIT_SCOPE", "ITER_INIT",
        "ITER_NEXT", "ITER_END", "POP", "BUILD_LIST", "INDEX", "UNARY",
        "CALL", "PIPE_CALL", "BINARY", "AND_JUMP", "OR_JUMP", "IMPORT", "EXPORT",
    ), start=1)
}
_OPCODE_NAMES = {value: key for key, value in _OPCODES.items()}


@dataclass(frozen=True, slots=True)
class BytecodeInstruction:
    opcode: int
    argument: Any
    token: Token


@dataclass(frozen=True, slots=True)
class BytecodeProgram:
    code: tuple[BytecodeInstruction, ...]
    source_name: str


@dataclass(slots=True)
class BytecodeFunction:
    __reaper_bytecode__ = True
    name: str
    parameters: tuple[str, ...]
    code: tuple[BytecodeInstruction, ...]
    closure: Environment


def assemble(module: CanonicalIR) -> BytecodeProgram:
    verify(module)

    def encode(code: tuple[IRInstruction, ...]) -> tuple[BytecodeInstruction, ...]:
        result = []
        for instruction in code:
            argument = instruction.argument
            if instruction.op == "MAKE_FUNCTION":
                function = argument
                argument = (function.name, function.parameters, encode(function.code))
            result.append(BytecodeInstruction(_OPCODES[instruction.op], argument, instruction.token))
        return tuple(result)

    return BytecodeProgram(encode(module.code), module.source_name)


class VirtualMachine:
    def __init__(self, interpreter: Any, program: BytecodeProgram) -> None:
        self.interpreter = interpreter
        self.program = program
        self.iteration_stack: list[Any] = []

    def run(self) -> Any:
        return self._execute(self.program.code, self.interpreter.globals, allow_return=False)

    def call_function(self, function: BytecodeFunction, arguments: list[Any], token: Token) -> Any:
        if len(arguments) != len(function.parameters):
            raise self.interpreter._error(
                token, f"{function.name}() expects {len(function.parameters)} arguments, got {len(arguments)}"
            )
        if self.interpreter.call_depth >= self.interpreter.max_call_depth:
            raise self.interpreter._error(token, f"call-depth limit ({self.interpreter.max_call_depth}) exceeded")
        local = Environment(function.closure)
        for name, value in zip(function.parameters, arguments):
            local.define(name, value)
        self.interpreter.call_depth += 1
        self.interpreter.call_stack.append(function.name)
        try:
            return self._execute(function.code, local, allow_return=True)
        finally:
            self.interpreter.call_stack.pop()
            self.interpreter.call_depth -= 1

    def _execute(self, code: tuple[BytecodeInstruction, ...], environment: Environment, allow_return: bool) -> Any:
        stack: list[Any] = []
        scopes: list[Environment] = []
        iterators: list[Any] = []
        ip = 0
        result = None
        while ip < len(code):
            instruction = code[ip]
            ip += 1
            name = _OPCODE_NAMES[instruction.opcode]
            token = instruction.token
            self.interpreter._current_environment = environment
            self.interpreter._tick(token)

            if self.interpreter.debugger is not None and name in {
                "DEFINE", "ASSIGN", "EMIT", "RETURN", "MAKE_FUNCTION", "IMPORT", "EXPORT", "ITER_NEXT",
            }:
                self.interpreter.debugger.before_statement(
                    token, environment, self.interpreter.call_stack, self.interpreter.filename
                )

            if name == "CONST":
                stack.append(instruction.argument)
            elif name == "LOAD":
                stack.append(environment.get(instruction.argument))
            elif name == "DEFINE":
                value = stack.pop()
                variable, mutable = instruction.argument
                environment.define(variable, self.interpreter.memory.track(value), mutable)
            elif name == "DEFINE_REGISTER":
                value = stack.pop()
                if not _is_register_number(value):
                    raise self.interpreter._error(token, "'reg' requires a finite numeric value")
                environment.define(instruction.argument, self.interpreter.memory.track(value), mutable=True, register=True)
            elif name == "ASSIGN":
                environment.change(
                    instruction.argument,
                    self.interpreter.memory.track(stack.pop()),
                    token,
                    self.interpreter.filename,
                )
            elif name == "EMIT":
                result = stack.pop()
                self.interpreter.output(self.interpreter._display(result))
            elif name == "RETURN":
                value = stack.pop()
                if not allow_return:
                    raise self.interpreter._error(token, "yield can only be used inside a craft function")
                return self.interpreter.memory.track(value)
            elif name == "MAKE_FUNCTION":
                function_name, parameters, function_code = instruction.argument
                stack.append(BytecodeFunction(function_name, parameters, function_code, environment))
            elif name == "JUMP_IF_FALSE":
                if not self.interpreter._truthy(stack.pop()):
                    ip = instruction.argument
            elif name == "JUMP":
                ip = instruction.argument
            elif name == "ENTER_SCOPE":
                scopes.append(environment)
                environment = Environment(environment)
            elif name == "EXIT_SCOPE":
                if not scopes:
                    raise self.interpreter._error(token, "scope stack underflow")
                environment = scopes.pop()
            elif name == "ITER_INIT":
                iterable = stack.pop()
                if not isinstance(iterable, (list, tuple, str, range)):
                    raise self.interpreter._error(token, "'each' needs a list, text, or range")
                self.interpreter._check_collection_size(iterable, token)
                iterators.append(iter(iterable))
            elif name == "ITER_NEXT":
                variable, end_target = instruction.argument
                if not iterators:
                    raise self.interpreter._error(token, "iterator stack underflow")
                try:
                    item = next(iterators[-1])
                except StopIteration:
                    ip = end_target
                else:
                    scopes.append(environment)
                    environment = Environment(environment)
                    environment.define(variable, item)
            elif name == "ITER_END":
                if not iterators:
                    raise self.interpreter._error(token, "iterator stack underflow")
                iterators.pop()
            elif name == "POP":
                if stack:
                    stack.pop()
            elif name == "BUILD_LIST":
                count = instruction.argument
                values = stack[-count:] if count else []
                if count:
                    del stack[-count:]
                stack.append(self.interpreter.memory.track(list(values)))
            elif name == "INDEX":
                index = stack.pop()
                collection = stack.pop()
                try:
                    if isinstance(collection, dict):
                        stack.append(collection[index])
                    else:
                        if isinstance(index, bool) or not isinstance(index, int):
                            raise TypeError("sequence indexes must be whole numbers")
                        stack.append(collection[index])
                except (IndexError, KeyError, TypeError) as error:
                    raise self.interpreter._error(token, f"cannot read this index: {error}") from error
            elif name == "UNARY":
                value = stack.pop()
                if instruction.argument == "NOT":
                    stack.append(not self.interpreter._truthy(value))
                elif instruction.argument == "-" and self.interpreter._is_number(value):
                    stack.append(-value)
                else:
                    raise self.interpreter._error(token, "unary '-' expects a number")
            elif name == "CALL":
                count = instruction.argument
                arguments = stack[-count:] if count else []
                if count:
                    del stack[-count:]
                callee = stack.pop()
                stack.append(self._call(callee, arguments, token))
            elif name == "PIPE_CALL":
                count = instruction.argument
                arguments = stack[-count:] if count else []
                if count:
                    del stack[-count:]
                callee = stack.pop()
                piped = stack.pop()
                stack.append(self._call(callee, [piped, *arguments], token))
            elif name == "BINARY":
                right = stack.pop()
                left = stack.pop()
                stack.append(self.interpreter._binary(instruction.argument, left, right, token))
            elif name == "AND_JUMP":
                if not self.interpreter._truthy(stack[-1]):
                    ip = instruction.argument
                else:
                    stack.pop()
            elif name == "OR_JUMP":
                if self.interpreter._truthy(stack[-1]):
                    ip = instruction.argument
                else:
                    stack.pop()
            elif name == "IMPORT":
                specifier, alias = instruction.argument
                exports = self.interpreter.module_loader.load(specifier, self.interpreter.filename)
                if alias:
                    environment.define(alias, exports)
                else:
                    for symbol, value in exports.items():
                        environment.define(symbol, value)
            elif name == "EXPORT":
                symbol = instruction.argument
                if symbol not in environment.values:
                    raise self.interpreter._error(token, f"cannot export undefined local name '{symbol}'")
                environment.exports.add(symbol)
            else:
                raise self.interpreter._error(token, f"unknown bytecode opcode {name}")
        return result

    def _call(self, callee: Any, arguments: list[Any], token: Token) -> Any:
        if isinstance(callee, BytecodeFunction):
            return self.call_function(callee, arguments, token)
        return self.interpreter._call(callee, arguments, token)


def compile_source(tree: Any, source_name: str = "<memory>") -> BytecodeProgram:
    from .ir import lower
    return assemble(lower(tree, source_name))
