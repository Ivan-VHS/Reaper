"""Execute the eight Brainfuck instructions in a bounded 8-bit tape VM."""
from __future__ import annotations

from typing import Any

from .common import ApplicationInputError, require_integer, require_text

_COMMANDS = set("><+-.,[]")


def _jumps(program: str) -> dict[int, int]:
    stack: list[int] = []
    result: dict[int, int] = {}
    for index, command in enumerate(program):
        if command == "[":
            stack.append(index)
        elif command == "]":
            if not stack:
                raise ApplicationInputError(f"unmatched closing bracket at instruction {index}")
            opening = stack.pop()
            result[opening] = index
            result[index] = opening
    if stack:
        raise ApplicationInputError(f"unmatched opening bracket at instruction {stack[-1]}")
    return result


def run(payload: dict[str, Any]) -> dict[str, Any]:
    source = require_text(payload.get("code"), "code", allow_empty=True)
    program = "".join(character for character in source if character in _COMMANDS)
    input_text = payload.get("input", "")
    if not isinstance(input_text, str):
        raise ApplicationInputError("input must be text")
    tape_size = require_integer(payload.get("tape_size", 256), "tape_size", minimum=1, maximum=65536)
    max_steps = require_integer(payload.get("max_steps", 1_000_000), "max_steps", minimum=1, maximum=10_000_000)
    jumps = _jumps(program)
    tape = [0] * tape_size
    pointer = 0
    pc = 0
    steps = 0
    input_index = 0
    output: list[str] = []

    while pc < len(program):
        steps += 1
        if steps > max_steps:
            raise ApplicationInputError(f"step_limit_exceeded: {max_steps}")
        command = program[pc]
        if command == ">":
            pointer += 1
            if pointer >= tape_size:
                raise ApplicationInputError("tape_pointer_overflow")
        elif command == "<":
            pointer -= 1
            if pointer < 0:
                raise ApplicationInputError("tape_pointer_underflow")
        elif command == "+":
            tape[pointer] = (tape[pointer] + 1) & 0xFF
        elif command == "-":
            tape[pointer] = (tape[pointer] - 1) & 0xFF
        elif command == ".":
            if len(output) >= 1_000_000:
                raise ApplicationInputError("output_limit_exceeded")
            output.append(chr(tape[pointer]))
        elif command == ",":
            tape[pointer] = ord(input_text[input_index]) & 0xFF if input_index < len(input_text) else 0
            input_index += 1
        elif command == "[" and tape[pointer] == 0:
            pc = jumps[pc]
        elif command == "]" and tape[pointer] != 0:
            pc = jumps[pc]
        pc += 1

    return {
        "output": "".join(output),
        "instructions": len(program),
        "steps": steps,
        "final_pointer": pointer,
        "tape_prefix": tape[:min(16, tape_size)],
    }
