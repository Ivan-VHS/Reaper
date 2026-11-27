"""Bounded reference implementation of the RFS-01 rhythm-field sublanguage.

RFS-01 is parsed as a separate source unit. The ordinary Reaper parser and its
existing :: function-application operator are unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

MAX_SOURCE_BYTES = 1 * 1024 * 1024
MAX_TOKENS = 262144
MAX_NODES = 4096
MAX_LINKS = 16384
MAX_PHASES = 4096
MAX_CONTRASTS = 16384
MAX_FRAMES = 65536
MAX_PAYLOAD_BYTES = 4096
MAX_CYCLES = 108
MAX_EMITS = 256
MAX_ACTIONS = 16384
MAX_RECORDED_EVENTS = 65536
NOISE_ATTENUATION = 0.6
NOISE_FLOOR_DB = -160.0
LAYERS = {"Basement", "Corridor", "Gate", "Skyline", "Horizon"}
CHANNELS = {"Wire", "Rail", "Beat", "Current", "Bridge"}
METRICS = {"pressure", "integrity", "noise_db"}
_COMPARATORS = {"==", "!=", "<", "<=", ">", ">="}
_TOKEN_RE = re.compile(
    r'(?P<SPACE>\s+)'
    r'|(?P<COMMENT>\#[^\r\n]*)'
    r'|(?P<STRING>"(?:\\.|[^"\\])*")'
    r'|(?P<NUMBER>-?(?:\d+\.\d+|\d+))'
    r'|(?P<OP><-root|\^core|::|<>|~>|>>|<<|\|\||\^\^|>=|<=|==|!=)'
    r'|(?P<PUNCT>[{}:,\[\]])'
    r'|(?P<IDENT>[^\W\d]\w*|_)',
    re.UNICODE,
)


@dataclass(frozen=True, slots=True)
class Span:
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str
    span: Span


class RFS01Error(ValueError):
    """A source-aware RFS-01 diagnostic."""

    def __init__(self, message: str, code: str = "RFS-E001", span: Span | None = None):
        self.code = code
        self.span = span
        location = f"{span.line}:{span.column}: " if span else ""
        super().__init__(f"{code} {location}{message}")


@dataclass(frozen=True, slots=True)
class NodeSpec:
    id: str
    layer: str
    pressure: float
    load_limit: float
    integrity: float
    noise_db: float
    core_seed: str
    active: bool = False


@dataclass(frozen=True, slots=True)
class LinkSpec:
    id: str
    origin: str
    target: str
    channel: str
    blocked: bool
    weight: float


@dataclass(frozen=True, slots=True)
class SignalFrame:
    sequence: int
    origin: str
    payload: str
    trusted: bool
    manufactured: bool


@dataclass(frozen=True, slots=True)
class Comparison:
    metric: str
    operator: str
    value: float


@dataclass(frozen=True, slots=True)
class PhaseGate:
    id: str
    node: str
    first: Comparison
    second: Comparison


@dataclass(frozen=True, slots=True)
class Flow:
    left: str
    operator: str
    right: str
    span: Span


@dataclass(frozen=True, slots=True)
class Contrast:
    left: str
    operator: str
    right: str
    span: Span


@dataclass(frozen=True, slots=True)
class Recovery:
    node: str
    operator: str
    span: Span


@dataclass(frozen=True, slots=True)
class RFSProgram:
    name: str
    version: str
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    signals: tuple[SignalFrame, ...]
    phases: tuple[PhaseGate, ...]
    actions: tuple[Flow | Recovery, ...]
    contrasts: tuple[Contrast, ...]
    cycles: int
    messages: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RFSIRInstruction:
    sequence: int
    opcode: str
    operands: tuple[Any, ...]
    span: Span | None = None


@dataclass(frozen=True, slots=True)
class RFSIRModule:
    schema: str
    name: str
    version: str
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    signals: tuple[SignalFrame, ...]
    phases: tuple[PhaseGate, ...]
    instructions: tuple[RFSIRInstruction, ...]
    cycles: int


@dataclass(frozen=True, slots=True)
class RuntimeNode:
    id: str
    layer: str
    pressure: float
    load_limit: float
    integrity: float
    noise_db: float
    core_seed: str
    active: bool


def _lex(source: str) -> list[Token]:
    try:
        encoded = source.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise RFS01Error("source is not valid UTF-8") from error
    if len(encoded) > MAX_SOURCE_BYTES:
        raise RFS01Error(f"source exceeds {MAX_SOURCE_BYTES} bytes", "RFS-E401")

    tokens: list[Token] = []
    line = column = 1
    index = 0
    while index < len(source):
        match = _TOKEN_RE.match(source, index)
        if match is None:
            raise RFS01Error(f"unexpected character {source[index]!r}", span=Span(line, column))
        value = match.group(0)
        kind = match.lastgroup or ""
        start = Span(line, column)
        index = match.end()
        if kind == "SPACE":
            newlines = value.count("\n")
            if newlines:
                line += newlines
                column = len(value.rsplit("\n", 1)[-1]) + 1
            else:
                column += len(value)
            continue
        if kind == "COMMENT":
            continue
        if kind == "STRING":
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                raise RFS01Error("invalid string escape", span=start) from error
        if len(tokens) >= MAX_TOKENS:
            raise RFS01Error(f"token limit ({MAX_TOKENS}) exceeded", "RFS-E401", start)
        tokens.append(Token(kind, value, start))
        if "\n" in match.group(0):
            line += match.group(0).count("\n")
            column = len(match.group(0).rsplit("\n", 1)[-1]) + 1
        else:
            column += len(match.group(0))
    tokens.append(Token("EOF", "", Span(line, column)))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    def peek(self) -> Token:
        return self.tokens[self.position]

    def take(self) -> Token:
        token = self.peek()
        if token.kind != "EOF":
            self.position += 1
        return token

    def accept(self, value: str) -> bool:
        if self.peek().value == value:
            self.take()
            return True
        return False

    def expect(self, value: str, message: str | None = None) -> Token:
        token = self.peek()
        if token.value != value:
            raise RFS01Error(message or f"expected {value!r}, found {token.value or token.kind}", span=token.span)
        return self.take()

    def identifier(self, message: str = "expected an identifier") -> Token:
        token = self.peek()
        if token.kind != "IDENT":
            raise RFS01Error(message, span=token.span)
        if len(token.value.encode("utf-8")) > 63:
            raise RFS01Error("identifier exceeds 63 UTF-8 bytes", "RFS-E101", token.span)
        return self.take()

    def scalar(self) -> Any:
        token = self.peek()
        if token.kind == "STRING":
            return self.take().value
        if token.kind == "NUMBER":
            raw = self.take().value
            return float(raw) if "." in raw else int(raw)
        if token.kind == "IDENT":
            raw = self.take().value
            if raw == "true":
                return True
            if raw == "false":
                return False
            return raw
        raise RFS01Error("expected a scalar value", span=token.span)

    def fields(self) -> dict[str, Any]:
        self.expect("{")
        result: dict[str, Any] = {}
        while self.peek().value != "}":
            key = self.identifier("expected a field name")
            self.expect(":")
            if key.value in result:
                raise RFS01Error(f"duplicate field {key.value!r}", "RFS-E101", key.span)
            result[key.value] = self.scalar()
            if not self.accept(",") and self.peek().value != "}":
                raise RFS01Error("expected ',' or '}' after field value", span=self.peek().span)
            if self.peek().kind == "EOF":
                raise RFS01Error("unterminated field record", span=self.peek().span)
        self.expect("}")
        return result

    @staticmethod
    def _require_fields(fields: dict[str, Any], required: set[str], optional: set[str], span: Span) -> None:
        missing = required - fields.keys()
        extra = fields.keys() - required - optional
        if missing:
            raise RFS01Error(f"missing required fields: {', '.join(sorted(missing))}", "RFS-E101", span)
        if extra:
            raise RFS01Error(f"unknown fields: {', '.join(sorted(extra))}", "RFS-E101", span)

    @staticmethod
    def _number(fields: dict[str, Any], key: str, span: Span) -> float:
        value = fields[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise RFS01Error(f"field {key!r} must be a finite number", "RFS-E101", span)
        return float(value)

    @staticmethod
    def _text(
        fields: dict[str, Any],
        key: str,
        span: Span,
        allow_empty: bool = False,
        max_bytes: int = 4096,
    ) -> str:
        value = fields[key]
        if not isinstance(value, str) or (not allow_empty and not value):
            raise RFS01Error(f"field {key!r} must be text", "RFS-E101", span)
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeError as error:
            raise RFS01Error(f"field {key!r} must be valid UTF-8", "RFS-E101", span) from error
        if "\\0" in value or len(encoded) > max_bytes:
            raise RFS01Error(f"field {key!r} exceeds its UTF-8 byte limit or contains NUL", "RFS-E101", span)
        return value

    @staticmethod
    def _boolean(fields: dict[str, Any], key: str, span: Span, default: bool | None = None) -> bool:
        if key not in fields and default is not None:
            return default
        value = fields[key]
        if not isinstance(value, bool):
            raise RFS01Error(f"field {key!r} must be boolean", "RFS-E101", span)
        return value

    def parse(self) -> RFSProgram:
        self.expect("module", "RFS-01 source must start with 'module'")
        name = self.identifier("expected module name").value
        self.expect("version")
        version_token = self.peek()
        if version_token.kind != "STRING":
            raise RFS01Error("module version must be a quoted string", span=version_token.span)
        version = self.take().value
        if version != "1.0":
            raise RFS01Error(f"unsupported RFS-01 version {version!r}; expected '1.0'", "RFS-E101", version_token.span)
        self.expect("{")

        nodes: list[NodeSpec] = []
        links: list[LinkSpec] = []
        signals: list[SignalFrame] = []
        phases: list[PhaseGate] = []
        actions: list[Flow | Recovery] = []
        contrasts: list[Contrast] = []
        messages: list[str] = []
        cycles = 1
        cycles_seen = False
        declared_ids: set[str] = set()

        while self.peek().value != "}":
            token = self.peek()
            if token.kind == "EOF":
                raise RFS01Error("unterminated RFS-01 module", span=token.span)
            statement = self.take().value

            if statement in {"node", "state", "link", "signal"}:
                item = self.identifier("expected declaration identifier")
                if item.value in declared_ids:
                    raise RFS01Error(f"duplicate declaration id {item.value!r}", "RFS-E101", item.span)
                declared_ids.add(item.value)
                if statement in {"node", "state"}:
                    marker, expected_type = ("::", "Node") if statement == "node" else ("<>", "State")
                    self.expect(marker)
                    type_token = self.identifier(f"expected {expected_type} type")
                    if type_token.value != expected_type:
                        raise RFS01Error(f"declaration must use {marker} {expected_type}", "RFS-E101", type_token.span)
                    fields = self.fields()
                    self._require_fields(fields, {"layer", "pressure", "load_limit", "integrity", "noise_db", "core_seed"}, {"active"}, item.span)
                    layer = self._text(fields, "layer", item.span)
                    pressure = self._number(fields, "pressure", item.span)
                    load_limit = self._number(fields, "load_limit", item.span)
                    integrity = self._number(fields, "integrity", item.span)
                    noise_db = self._number(fields, "noise_db", item.span)
                    core_seed = self._text(fields, "core_seed", item.span, max_bytes=127)
                    active = self._boolean(fields, "active", item.span, False)
                    if layer not in LAYERS or pressure < 0 or load_limit <= 0 or not 0 <= integrity <= 1 or not -160 <= noise_db <= 24:
                        raise RFS01Error("node field is outside its declared domain", "RFS-E101", item.span)
                    nodes.append(NodeSpec(item.value, layer, pressure, load_limit, integrity, noise_db, core_seed, active))
                elif statement == "link":
                    self.expect("::")
                    type_token = self.identifier("expected Link type")
                    if type_token.value != "Link":
                        raise RFS01Error("link declaration must use :: Link", "RFS-E101", type_token.span)
                    fields = self.fields()
                    self._require_fields(fields, {"origin", "target", "channel", "weight"}, {"blocked"}, item.span)
                    origin = self._text(fields, "origin", item.span, max_bytes=63)
                    target = self._text(fields, "target", item.span, max_bytes=63)
                    channel = self._text(fields, "channel", item.span, max_bytes=16)
                    weight = self._number(fields, "weight", item.span)
                    blocked = self._boolean(fields, "blocked", item.span, False)
                    if channel not in CHANNELS or weight < 0:
                        raise RFS01Error("link channel or weight is outside its declared domain", "RFS-E101", item.span)
                    links.append(LinkSpec(item.value, origin, target, channel, blocked, weight))
                else:
                    self.expect("::")
                    type_token = self.identifier("expected Signal type")
                    if type_token.value != "Signal":
                        raise RFS01Error("signal declaration must use :: Signal", "RFS-E101", type_token.span)
                    fields = self.fields()
                    self._require_fields(fields, {"sequence", "origin", "payload", "trusted", "manufactured"}, set(), item.span)
                    sequence = self._number(fields, "sequence", item.span)
                    origin = self._text(fields, "origin", item.span)
                    payload = self._text(fields, "payload", item.span, allow_empty=True, max_bytes=MAX_PAYLOAD_BYTES)
                    if sequence < 0 or not sequence.is_integer() or len(payload.encode("utf-8")) > MAX_PAYLOAD_BYTES:
                        raise RFS01Error("signal sequence or payload exceeds its domain", "RFS-E101", item.span)
                    signals.append(SignalFrame(int(sequence), origin, payload, self._boolean(fields, "trusted", item.span), self._boolean(fields, "manufactured", item.span)))
                continue

            if statement == "phase":
                phase_id = self.identifier("expected phase identifier")
                if phase_id.value in declared_ids:
                    raise RFS01Error(f"duplicate declaration id {phase_id.value!r}", "RFS-E101", phase_id.span)
                declared_ids.add(phase_id.value)
                self.expect("on")
                node = self.identifier("expected node identifier").value
                self.expect("[")
                first = self._comparison()
                self.expect(":")
                second = self._comparison()
                self.expect("]")
                phases.append(PhaseGate(phase_id.value, node, first, second))
                if len(phases) > MAX_PHASES:
                    raise RFS01Error("phase gate limit exceeded", "RFS-E401", phase_id.span)
                continue

            if statement == "flow":
                left = self.identifier("expected flow origin").value
                operator = self.take()
                if operator.value not in {"~>", ">>", "<<"}:
                    raise RFS01Error("flow operator must be ~>, >>, or <<", span=operator.span)
                right = self.identifier("expected flow destination").value
                actions.append(Flow(left, operator.value, right, operator.span))
                continue

            if statement == "contrast":
                left = self.identifier("expected contrast operand").value
                operator = self.take()
                if operator.value not in {"||", "^^"}:
                    raise RFS01Error("contrast operator must be || or ^^", span=operator.span)
                right = self.identifier("expected contrast operand").value
                contrasts.append(Contrast(left, operator.value, right, operator.span))
                if len(contrasts) > MAX_CONTRASTS:
                    raise RFS01Error("contrast limit exceeded", "RFS-E401", operator.span)
                continue

            if statement == "recover":
                node = self.identifier("expected recovery node").value
                operator = self.take()
                if operator.value not in {"<-root", "^core"}:
                    raise RFS01Error("recovery operator must be <-root or ^core", span=operator.span)
                actions.append(Recovery(node, operator.value, operator.span))
                continue

            if statement == "cycles":
                if cycles_seen:
                    raise RFS01Error("cycles may be declared only once", "RFS-E101", token.span)
                value = self.scalar()
                if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_CYCLES:
                    raise RFS01Error(f"cycles must be an integer from 1 to {MAX_CYCLES}", "RFS-E101", token.span)
                cycles = value
                cycles_seen = True
                continue

            if statement == "emit":
                value = self.scalar()
                if not isinstance(value, str):
                    raise RFS01Error("emit expects a quoted string", "RFS-E101", token.span)
                messages.append(value)
                if len(messages) > MAX_EMITS:
                    raise RFS01Error("emit limit exceeded", "RFS-E401", token.span)
                continue

            raise RFS01Error(f"unknown statement {statement!r}", span=token.span)

        self.expect("}")
        if self.peek().kind != "EOF":
            raise RFS01Error("unexpected content after module", span=self.peek().span)
        if not nodes:
            raise RFS01Error("module must declare at least one node", "RFS-E101")
        if (
            len(nodes) > MAX_NODES or len(links) > MAX_LINKS
            or len(signals) > MAX_FRAMES or len(actions) > MAX_ACTIONS
            or len(phases) > MAX_PHASES or len(contrasts) > MAX_CONTRASTS
        ):
            raise RFS01Error("RFS-01 structural resource limit exceeded", "RFS-E401")

        self._validate_references(nodes, links, signals, phases, actions, contrasts)
        last_sequences: dict[str, int] = {}
        for frame in signals:
            previous = last_sequences.get(frame.origin)
            if previous is not None and frame.sequence <= previous:
                raise RFS01Error(
                    f"signal sequence for {frame.origin!r} must be strictly increasing",
                    "RFS-E101",
                )
            last_sequences[frame.origin] = frame.sequence
        return RFSProgram(name, version, tuple(nodes), tuple(links), tuple(signals), tuple(phases), tuple(actions), tuple(contrasts), cycles, tuple(messages))

    def _comparison(self) -> Comparison:
        metric = self.identifier("expected phase metric")
        operator = self.take()
        if metric.value not in METRICS or operator.value not in _COMPARATORS:
            raise RFS01Error("phase comparison uses an unsupported metric or comparator", "RFS-E301", metric.span)
        value = self.scalar()
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise RFS01Error("phase threshold must be a finite number", "RFS-E301", metric.span)
        return Comparison(metric.value, operator.value, float(value))

    @staticmethod
    def _validate_references(nodes, links, signals, phases, actions, contrasts) -> None:
        node_ids = {node.id for node in nodes}
        link_pairs: set[tuple[str, str]] = set()
        for link in links:
            if link.origin not in node_ids or link.target not in node_ids:
                raise RFS01Error(f"link {link.id!r} references an unknown node", "RFS-E201")
            pair = (link.origin, link.target)
            if pair in link_pairs:
                raise RFS01Error(f"duplicate directed link {pair[0]!r} -> {pair[1]!r}", "RFS-E101")
            link_pairs.add(pair)
        for frame in signals:
            if frame.origin not in node_ids:
                raise RFS01Error(f"signal references unknown origin {frame.origin!r}", "RFS-E201")
        for phase in phases:
            if phase.node not in node_ids:
                raise RFS01Error(f"phase {phase.id!r} references unknown node {phase.node!r}", "RFS-E201")
        for action in actions:
            if isinstance(action, Recovery):
                if action.node not in node_ids:
                    raise RFS01Error(f"recovery references unknown node {action.node!r}", "RFS-E201", action.span)
                continue
            if action.left not in node_ids or action.right not in node_ids:
                raise RFS01Error("flow references an unknown node", "RFS-E201", action.span)
            origin, target = (action.left, action.right) if action.operator != "<<" else (action.right, action.left)
            if (origin, target) not in link_pairs:
                raise RFS01Error(f"flow {origin!r} -> {target!r} has no declared link", "RFS-E201", action.span)
        for contrast in contrasts:
            if contrast.left not in node_ids or contrast.right not in node_ids:
                raise RFS01Error("contrast references an unknown node", "RFS-E201", contrast.span)


def compile_source(source: str) -> RFSProgram:
    """Lex, parse, type-check and validate one RFS-01 v1.0 source unit."""
    return _Parser(_lex(source)).parse()


def lower_to_ir(program: RFSProgram) -> RFSIRModule:
    """Lower the validated source model into the stable RFS-01 typed IR."""
    instructions: list[RFSIRInstruction] = []

    def emit(opcode: str, *operands: Any, span: Span | None = None) -> None:
        instructions.append(RFSIRInstruction(len(instructions), opcode, tuple(operands), span))

    flow_opcodes = {"~>": "FLOW_SIGNAL", ">>": "FLOW_PRESSURE_FORWARD", "<<": "FLOW_PRESSURE_REVERSE"}
    for action in program.actions:
        if isinstance(action, Flow):
            emit(flow_opcodes[action.operator], action.left, action.right, span=action.span)
        elif action.operator == "<-root":
            emit("RECOVER_ROOT", action.node, span=action.span)
        else:
            emit("RECOVER_CORE", action.node, span=action.span)

    for contrast in program.contrasts:
        opcode = "CONTRAST_COMPLEMENT" if contrast.operator == "||" else "CONTRAST_DIFFERENTIAL"
        emit(opcode, contrast.left, contrast.right, span=contrast.span)
    for message in program.messages:
        emit("EMIT", message)

    module = RFSIRModule(
        "rfs-01.typed-ir.v1",
        program.name,
        program.version,
        program.nodes,
        program.links,
        program.signals,
        program.phases,
        tuple(instructions),
        program.cycles,
    )
    verify_ir(module)
    return module


def verify_ir(module: RFSIRModule) -> None:
    """Reject malformed, out-of-domain, or unresolved typed IR before execution."""
    if not isinstance(module, RFSIRModule):
        raise RFS01Error("value is not an RFS-01 typed IR module", "RFS-E501")
    if module.schema != "rfs-01.typed-ir.v1" or module.version != "1.0":
        raise RFS01Error("unsupported typed IR schema or language version", "RFS-E501")
    if not isinstance(module.name, str) or not module.name:
        raise RFS01Error("typed IR module name is invalid", "RFS-E501")
    if isinstance(module.cycles, bool) or not isinstance(module.cycles, int) or not 1 <= module.cycles <= MAX_CYCLES:
        raise RFS01Error("typed IR cycle budget is outside the supported range", "RFS-E501")

    def valid_text(value: Any, max_bytes: int, allow_empty: bool = False) -> bool:
        if not isinstance(value, str) or (not allow_empty and not value) or "\\0" in value:
            return False
        try:
            return len(value.encode("utf-8", errors="strict")) <= max_bytes
        except UnicodeError:
            return False

    def finite_number(value: Any, minimum: float | None = None) -> bool:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return False
        return minimum is None or float(value) >= minimum

    if not 1 <= len(module.nodes) <= MAX_NODES:
        raise RFS01Error("typed IR node count is outside the supported range", "RFS-E501")
    if len(module.links) > MAX_LINKS or len(module.signals) > MAX_FRAMES or len(module.phases) > MAX_PHASES:
        raise RFS01Error("typed IR table exceeds a structural resource limit", "RFS-E501")
    if len(module.instructions) > MAX_ACTIONS + MAX_CONTRASTS + MAX_EMITS:
        raise RFS01Error("typed IR instruction count exceeds its resource limit", "RFS-E501")

    node_ids = [node.id for node in module.nodes]
    if any(not valid_text(node_id, 63) for node_id in node_ids) or len(node_ids) != len(set(node_ids)):
        raise RFS01Error("typed IR node identifiers are invalid or duplicated", "RFS-E501")
    known_nodes = set(node_ids)
    declaration_ids = set(node_ids)

    for node in module.nodes:
        if (
            node.layer not in LAYERS
            or not finite_number(node.pressure, 0.0)
            or not finite_number(node.load_limit, 0.0)
            or float(node.load_limit) <= 0.0
            or not finite_number(node.integrity, 0.0)
            or float(node.integrity) > 1.0
            or not finite_number(node.noise_db, -160.0)
            or float(node.noise_db) > 24.0
            or not valid_text(node.core_seed, 127)
            or not isinstance(node.active, bool)
        ):
            raise RFS01Error(f"typed IR node {node.id!r} is outside its declared domain", "RFS-E501")

    link_pairs: set[tuple[str, str]] = set()
    for link in module.links:
        if (
            not valid_text(link.id, 63)
            or link.id in declaration_ids
            or link.origin not in known_nodes
            or link.target not in known_nodes
            or link.channel not in CHANNELS
            or not isinstance(link.blocked, bool)
            or not finite_number(link.weight, 0.0)
        ):
            raise RFS01Error("typed IR link is malformed or has an unresolved reference", "RFS-E501")
        declaration_ids.add(link.id)
        pair = (link.origin, link.target)
        if pair in link_pairs:
            raise RFS01Error("typed IR contains duplicate directed links", "RFS-E501")
        link_pairs.add(pair)

    last_sequences: dict[str, int] = {}
    for frame in module.signals:
        if (
            isinstance(frame.sequence, bool)
            or not isinstance(frame.sequence, int)
            or not 0 <= frame.sequence < (1 << 64)
            or frame.origin not in known_nodes
            or not valid_text(frame.payload, MAX_PAYLOAD_BYTES, allow_empty=True)
            or not isinstance(frame.trusted, bool)
            or not isinstance(frame.manufactured, bool)
        ):
            raise RFS01Error("typed IR signal frame is malformed", "RFS-E501")
        previous = last_sequences.get(frame.origin)
        if previous is not None and frame.sequence <= previous:
            raise RFS01Error("typed IR signal sequence is not strictly increasing", "RFS-E501")
        last_sequences[frame.origin] = frame.sequence

    phase_ids: set[str] = set()
    for phase in module.phases:
        if (
            not valid_text(phase.id, 63)
            or phase.id in declaration_ids
            or phase.node not in known_nodes
        ):
            raise RFS01Error("typed IR phase is malformed or unresolved", "RFS-E501")
        declaration_ids.add(phase.id)
        phase_ids.add(phase.id)
        for comparison in (phase.first, phase.second):
            if (
                comparison.metric not in METRICS
                or comparison.operator not in _COMPARATORS
                or not finite_number(comparison.value)
            ):
                raise RFS01Error("typed IR phase comparison is invalid", "RFS-E501")

    known_opcodes = {
        "FLOW_SIGNAL", "FLOW_PRESSURE_FORWARD", "FLOW_PRESSURE_REVERSE",
        "RECOVER_ROOT", "RECOVER_CORE",
        "CONTRAST_COMPLEMENT", "CONTRAST_DIFFERENTIAL", "EMIT",
    }
    emit_count = 0
    for expected_sequence, instruction in enumerate(module.instructions):
        if instruction.sequence != expected_sequence or instruction.opcode not in known_opcodes:
            raise RFS01Error("typed IR instruction sequence or opcode is invalid", "RFS-E501", instruction.span)
        args = instruction.operands
        if instruction.opcode in {"FLOW_SIGNAL", "FLOW_PRESSURE_FORWARD", "FLOW_PRESSURE_REVERSE"}:
            if len(args) != 2 or args[0] not in known_nodes or args[1] not in known_nodes:
                raise RFS01Error("typed IR flow has invalid operands", "RFS-E501", instruction.span)
            origin, target = (args[0], args[1]) if instruction.opcode != "FLOW_PRESSURE_REVERSE" else (args[1], args[0])
            if (origin, target) not in link_pairs:
                raise RFS01Error("typed IR flow has no matching directed link", "RFS-E501", instruction.span)
        elif instruction.opcode in {"RECOVER_ROOT", "RECOVER_CORE"}:
            if len(args) != 1 or args[0] not in known_nodes:
                raise RFS01Error("typed IR recovery has an unresolved node", "RFS-E501", instruction.span)
        elif instruction.opcode in {"CONTRAST_COMPLEMENT", "CONTRAST_DIFFERENTIAL"}:
            if len(args) != 2 or args[0] not in known_nodes or args[1] not in known_nodes:
                raise RFS01Error("typed IR contrast has an unresolved operand", "RFS-E501", instruction.span)
        elif instruction.opcode == "EMIT":
            emit_count += 1
            if len(args) != 1 or not valid_text(args[0], 4096, allow_empty=True) or emit_count > MAX_EMITS:
                raise RFS01Error("typed IR emit instruction has invalid payload or exceeds its limit", "RFS-E501", instruction.span)


def compile_ir(source: str) -> RFSIRModule:
    """Compile source directly to the verified RFS-01 typed IR."""
    return lower_to_ir(compile_source(source))


class RFSRuntime:
    """Deterministic, bounded and side-effect-free RFS-01 execution engine."""

    def __init__(self, program: RFSProgram):
        self.program = program
        self.ir = lower_to_ir(program)
        self._root = {
            node.id: RuntimeNode(node.id, node.layer, node.pressure, node.load_limit, node.integrity, node.noise_db, node.core_seed, node.active)
            for node in program.nodes
        }
        self.nodes = dict(self._root)
        self.links = {(link.origin, link.target): link for link in program.links}
        self.phases: dict[str, list[PhaseGate]] = {}
        for phase in program.phases:
            self.phases.setdefault(phase.node, []).append(phase)
        self.clean_signal_counts: dict[str, int] = {}
        for frame in program.signals:
            if frame.trusted and not frame.manufactured:
                self.clean_signal_counts[frame.origin] = self.clean_signal_counts.get(frame.origin, 0) + 1
        self.events: list[dict[str, Any]] = []
        self.dropped_events = 0
        self._event_sequence = 0

    @staticmethod
    def _compare(left: float, operator: str, right: float) -> bool:
        return {
            "==": left == right,
            "!=": left != right,
            "<": left < right,
            "<=": left <= right,
            ">": left > right,
            ">=": left >= right,
        }[operator]

    def _phase_open(self, node_id: str) -> bool:
        node = self.nodes[node_id]
        return all(
            self._compare(float(getattr(node, check.metric)), check.operator, check.value)
            for phase in self.phases.get(node_id, ())
            for check in (phase.first, phase.second)
        )

    def _record(self, cycle: int, kind: str, **details: Any) -> None:
        self._event_sequence += 1
        if len(self.events) >= MAX_RECORDED_EVENTS:
            self.dropped_events += 1
            return
        self.events.append({"sequence": self._event_sequence, "cycle": cycle, "kind": kind, **details})

    def _flow(self, flow: Flow, cycle: int) -> None:
        origin_id, target_id = (flow.left, flow.right) if flow.operator != "<<" else (flow.right, flow.left)
        if not self._phase_open(origin_id):
            self._record(cycle, "phase-blocked", origin=origin_id, target=target_id, operator=flow.operator)
            return
        link = self.links[(origin_id, target_id)]
        if link.blocked:
            self._record(cycle, "link-blocked", link=link.id, operator=flow.operator)
            return
        source = self.nodes[origin_id]
        target = self.nodes[target_id]
        if flow.operator == "~>":
            frame_count = self.clean_signal_counts.get(origin_id, 0)
            if not frame_count:
                self._record(cycle, "signal-rejected", origin=origin_id, target=target_id, reason="no-trusted-frame")
                return
            attenuation_db = 20.0 * math.log10(NOISE_ATTENUATION)
            noise = max(NOISE_FLOOR_DB, target.noise_db + attenuation_db)
            self.nodes[target_id] = replace(target, noise_db=noise, active=True)
            self._record(cycle, "signal-forwarded", origin=origin_id, target=target_id, frames=frame_count, noise_db=noise)
            return
        delta = source.pressure * link.weight
        next_pressure = target.pressure + delta
        if next_pressure > target.load_limit:
            self._record(cycle, "pressure-rejected", origin=origin_id, target=target_id, attempted=delta, reason="load-limit")
            return
        self.nodes[target_id] = replace(target, pressure=next_pressure, active=True)
        self._record(cycle, "pressure-forwarded", origin=origin_id, target=target_id, amount=delta, pressure=next_pressure)

    def _recover(self, recovery: Recovery, cycle: int) -> None:
        current = self.nodes[recovery.node]
        original = self._root[recovery.node]
        if recovery.operator == "<-root":
            self.nodes[recovery.node] = original
            self._record(cycle, "root-restored", node=recovery.node)
        else:
            self.nodes[recovery.node] = replace(current, core_seed=original.core_seed)
            self._record(cycle, "core-restored", node=recovery.node)

    @staticmethod
    def reserve(node: RuntimeNode) -> float:
        load_ratio = min(node.pressure / node.load_limit, 1.0)
        return node.integrity * (1.0 - load_ratio)

    def run(self) -> dict[str, Any]:
        for cycle in range(1, self.ir.cycles + 1):
            for instruction in self.ir.instructions:
                args = instruction.operands
                if instruction.opcode in {"FLOW_SIGNAL", "FLOW_PRESSURE_FORWARD", "FLOW_PRESSURE_REVERSE"}:
                    operator = {
                        "FLOW_SIGNAL": "~>",
                        "FLOW_PRESSURE_FORWARD": ">>",
                        "FLOW_PRESSURE_REVERSE": "<<",
                    }[instruction.opcode]
                    self._flow(Flow(args[0], operator, args[1], instruction.span or Span(1, 1)), cycle)
                elif instruction.opcode == "RECOVER_ROOT":
                    self._recover(Recovery(args[0], "<-root", instruction.span or Span(1, 1)), cycle)
                elif instruction.opcode == "RECOVER_CORE":
                    self._recover(Recovery(args[0], "^core", instruction.span or Span(1, 1)), cycle)

        contrasts = []
        for instruction in self.ir.instructions:
            if instruction.opcode not in {"CONTRAST_COMPLEMENT", "CONTRAST_DIFFERENTIAL"}:
                continue
            left_id, right_id = instruction.operands
            left = self.reserve(self.nodes[left_id])
            right = self.reserve(self.nodes[right_id])
            operator = "||" if instruction.opcode == "CONTRAST_COMPLEMENT" else "^^"
            score = 1.0 - abs(left - right) if operator == "||" else abs(left - right)
            contrasts.append({"left": left_id, "operator": operator, "right": right_id, "score": score})
        messages = [
            instruction.operands[0]
            for instruction in self.ir.instructions
            if instruction.opcode == "EMIT"
        ]

        node_rows = [
            {
                "id": node.id,
                "layer": node.layer,
                "pressure": node.pressure,
                "load_limit": node.load_limit,
                "integrity": node.integrity,
                "noise_db": node.noise_db,
                "reserve": self.reserve(node),
                "core_seed": node.core_seed,
                "active": node.active,
            }
            for node in self.nodes.values()
        ]
        return {
            "schema": "rfs-01.runtime-result.v1",
            "module": self.program.name,
            "version": self.program.version,
            "ir_schema": self.ir.schema,
            "ir_instruction_count": len(self.ir.instructions),
            "status": "MeshInMotion" if any(node["active"] for node in node_rows) else "MeshIdle",
            "cycles": self.ir.cycles,
            "nodes": node_rows,
            "clean_signal_frames": sum(self.clean_signal_counts.values()),
            "rejected_signal_frames": len(self.program.signals) - sum(self.clean_signal_counts.values()),
            "contrasts": contrasts,
            "messages": messages,
            "events": self.events,
            "dropped_events": self.dropped_events,
        }


def run_source(source: str) -> dict[str, Any]:
    return RFSRuntime(compile_source(source)).run()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile and run a bounded RFS-01 source unit.")
    parser.add_argument("source", type=Path, help="path to a .rfs source file")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = run_source(args.source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, RFS01Error) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
