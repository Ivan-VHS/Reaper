"""Versioned semantic graph IR for Reaper expressions and flow pipelines.

This module is intentionally separate from the existing stack instruction IR
consumed by the VM. It preserves typed expression structure and source
provenance; a later backend can lower it without losing source diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping

from .parser import Node, parse
from .source import SourceSpan, format_source_diagnostic

SEMANTIC_IR_VERSION = 1


@dataclass(frozen=True, slots=True)
class NodeOrigin:
    primary: SourceSpan
    related: tuple[SourceSpan, ...] = ()
    transformation: str | None = None


@dataclass(frozen=True, slots=True)
class IRNode:
    node_id: int
    span: SourceSpan
    origin: NodeOrigin
    inferred_type: str | None = field(default=None, kw_only=True)
    kind: ClassVar[str] = "IRNode"


@dataclass(frozen=True, slots=True)
class IRVar(IRNode):
    name: str
    kind: ClassVar[str] = "IRVar"


@dataclass(frozen=True, slots=True)
class IRLiteral(IRNode):
    value: Any
    kind: ClassVar[str] = "IRLiteral"


@dataclass(frozen=True, slots=True)
class IRIntrinsic(IRNode):
    name: str
    kind: ClassVar[str] = "IRIntrinsic"


@dataclass(frozen=True, slots=True)
class IRList(IRNode):
    items: tuple[IRNode, ...]
    kind: ClassVar[str] = "IRList"


@dataclass(frozen=True, slots=True)
class IRIndex(IRNode):
    collection: IRNode
    index: IRNode
    kind: ClassVar[str] = "IRIndex"


@dataclass(frozen=True, slots=True)
class IRCall(IRNode):
    callee: IRNode
    arguments: tuple[IRNode, ...]
    from_pipe: bool = False
    kind: ClassVar[str] = "IRCall"


@dataclass(frozen=True, slots=True)
class SemanticIR:
    version: int
    source_name: str
    root: IRNode


class IRLoweringError(ValueError):
    pass


class SemanticIRVerificationError(ValueError):
    pass


_OPERATOR_INTRINSICS = {
    "==": "eq", "!=": "ne", "<": "lt", "<=": "le",
    ">": "gt", ">=": "ge", "+": "add", "-": "sub",
    "*": "mul", "/": "div", "//": "floor_div", "%": "mod",
    "**": "pow", "AND": "and", "OR": "or", "++": "concat",
}


class _Lowerer:
    def __init__(self) -> None:
        self._next_id = 1

    def _id(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value

    @staticmethod
    def _origin(
        span: SourceSpan,
        *,
        related: tuple[SourceSpan, ...] = (),
        transformation: str | None = None,
    ) -> NodeOrigin:
        return NodeOrigin(primary=span, related=related, transformation=transformation)

    def expression(self, node: Node, depth: int = 0) -> IRNode:
        if depth > 4096:
            raise IRLoweringError("semantic IR lowering exceeded the 4096-node depth limit")
        children = node.children or []
        span = node.token.span

        if node.kind == "name":
            return IRVar(self._id(), span, self._origin(span), str(node.value))
        if node.kind == "literal":
            return IRLiteral(self._id(), span, self._origin(span), node.value)
        if node.kind == "list":
            return IRList(
                self._id(), span, self._origin(span),
                tuple(self.expression(child, depth + 1) for child in children),
            )
        if node.kind == "index":
            if len(children) != 2:
                raise IRLoweringError("index AST node must contain collection and index")
            return IRIndex(
                self._id(), span, self._origin(span),
                self.expression(children[0], depth + 1),
                self.expression(children[1], depth + 1),
            )
        if node.kind == "unary":
            if len(children) != 1:
                raise IRLoweringError("unary AST node must contain exactly one operand")
            name = "neg" if node.value in {"-", "MINUS"} else "not" if node.value in {"NOT", "not"} else str(node.value)
            callee = IRIntrinsic(self._id(), span, self._origin(span), name)
            argument = self.expression(children[0], depth + 1)
            return IRCall(self._id(), span, self._origin(span), callee, (argument,))
        if node.kind == "call":
            if not children:
                raise IRLoweringError("call AST node has no callee")
            callee = self.expression(children[0], depth + 1)
            arguments = tuple(self.expression(child, depth + 1) for child in children[1:])
            primary = callee.span
            origin = self._origin(primary, related=(span,), transformation="call-normalization")
            return IRCall(self._id(), primary, origin, callee, arguments)
        if node.kind == "binary":
            if len(children) != 2:
                raise IRLoweringError("binary AST node must contain exactly two operands")
            operator = str(node.value)
            if operator in {"::", "->"}:
                return self._pipe(children[0], children[1], span, depth)
            intrinsic_name = _OPERATOR_INTRINSICS.get(operator)
            if intrinsic_name is None:
                raise IRLoweringError(f"unsupported binary operator in semantic IR: {operator!r}")
            left = self.expression(children[0], depth + 1)
            right = self.expression(children[1], depth + 1)
            callee = IRIntrinsic(self._id(), span, self._origin(span), intrinsic_name)
            return IRCall(self._id(), span, self._origin(span), callee, (left, right))
        raise IRLoweringError(f"unsupported AST expression kind: {node.kind}")

    def _pipe(
        self,
        left_node: Node,
        right_node: Node,
        pipe_span: SourceSpan,
        depth: int,
    ) -> IRCall:
        """Lower a pipeline step into a call with the piped value first."""
        left = self.expression(left_node, depth + 1)
        if right_node.kind == "call":
            right_children = right_node.children or []
            if not right_children:
                raise IRLoweringError("pipeline stage call has no callee")
            callee = self.expression(right_children[0], depth + 1)
            extra_arguments = tuple(self.expression(item, depth + 1) for item in right_children[1:])
            call_site = right_children[0].token.span
            related = (pipe_span, right_node.token.span)
        else:
            callee = self.expression(right_node, depth + 1)
            extra_arguments = ()
            call_site = right_node.token.span
            related = (pipe_span,)
        origin = self._origin(call_site, related=related, transformation="pipe-lowering")
        # The piped value is always argument zero in Reaper's canonical call ABI.
        return IRCall(self._id(), call_site, origin, callee, (left, *extra_arguments), True)


def lower_expression(node: Node, source_name: str | None = None) -> SemanticIR:
    """Lower one expression (or one expression-bearing statement) to semantic IR."""
    if node.kind == "program" and len(node.children or []) == 1:
        node = (node.children or [])[0]
    if node.kind in {"emit", "expression", "yield", "declare", "change"}:
        if not node.children:
            raise IRLoweringError(f"{node.kind} statement has no expression")
        node = node.children[0]
    if node.kind in {"program", "block", "declare", "emit", "expression", "yield", "change"}:
        raise IRLoweringError("lower_expression expects one Reaper expression")
    lowerer = _Lowerer()
    module = SemanticIR(SEMANTIC_IR_VERSION, source_name or node.token.source_id, lowerer.expression(node))
    verify_semantic_ir(module)
    return module


def verify_semantic_ir(module: SemanticIR) -> None:
    """Validate node identity, structure, and provenance before later passes consume IR."""
    if not isinstance(module, SemanticIR):
        raise SemanticIRVerificationError("expected a SemanticIR module")
    if module.version != SEMANTIC_IR_VERSION:
        raise SemanticIRVerificationError(f"unsupported semantic IR version: {module.version}")
    if not module.source_name:
        raise SemanticIRVerificationError("semantic IR source_name must be non-empty")
    if not isinstance(module.root, IRNode):
        raise SemanticIRVerificationError("semantic IR root must be an IR node")

    seen_ids: set[int] = set()
    active_ids: set[int] = set()

    def visit(node: IRNode) -> None:
        if not isinstance(node, IRNode):
            raise SemanticIRVerificationError("IR child must be an IRNode")
        if type(node.node_id) is not int or node.node_id <= 0:
            raise SemanticIRVerificationError("IR node id must be a positive integer")
        if node.node_id in active_ids:
            raise SemanticIRVerificationError("semantic IR graph contains a cycle")
        if node.node_id in seen_ids:
            raise SemanticIRVerificationError("semantic IR node ids must be unique")
        if not isinstance(node.span, SourceSpan) or not isinstance(node.origin, NodeOrigin):
            raise SemanticIRVerificationError("every IR node must carry a source span and origin")
        if node.origin.primary != node.span:
            raise SemanticIRVerificationError("node origin primary span must match the node span")
        seen_ids.add(node.node_id)
        active_ids.add(node.node_id)
        if isinstance(node, IRVar):
            if not isinstance(node.name, str) or not node.name:
                raise SemanticIRVerificationError("IRVar requires a non-empty name")
        elif isinstance(node, IRLiteral):
            pass
        elif isinstance(node, IRIntrinsic):
            if not node.name:
                raise SemanticIRVerificationError("IRIntrinsic requires a name")
        elif isinstance(node, IRList):
            for item in node.items:
                visit(item)
        elif isinstance(node, IRIndex):
            visit(node.collection)
            visit(node.index)
        elif isinstance(node, IRCall):
            if not isinstance(node.arguments, tuple):
                raise SemanticIRVerificationError("IRCall arguments must be an immutable tuple")
            if node.from_pipe and not node.arguments:
                raise SemanticIRVerificationError("a lowered pipeline call must receive the piped value")
            if isinstance(node.callee, IRIntrinsic):
                expected_arity = 1 if node.callee.name in {"neg", "not"} else 2
                if len(node.arguments) != expected_arity:
                    raise SemanticIRVerificationError(
                        f"intrinsic '{node.callee.name}' requires {expected_arity} operand(s)"
                    )
            visit(node.callee)
            for argument in node.arguments:
                visit(argument)
        else:
            raise SemanticIRVerificationError(f"unknown semantic IR node kind: {type(node).__name__}")
        active_ids.remove(node.node_id)

    visit(module.root)


@dataclass(frozen=True, slots=True)
class FunctionSignature:
    parameter_types: tuple[str, ...]
    return_type: str


@dataclass(frozen=True, slots=True)
class IRDiagnostic:
    code: str
    message: str
    span: SourceSpan
    node_id: int
    node_kind: str
    stage: str = "type_check"

    def format(self, source_text: str, *, syntax_mode: str = "flow") -> str:
        return format_source_diagnostic(
            self.code, self.message, self.span, source_text,
            syntax_mode=syntax_mode, node_kind=self.node_kind,
        )


@dataclass(frozen=True, slots=True)
class IRTypeCheckResult:
    return_type: str
    diagnostics: tuple[IRDiagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


class IRTypeChecker:
    """Conservative IR checker driven by explicit variable and function contracts."""

    def __init__(
        self,
        variables: Mapping[str, str] | None = None,
        functions: Mapping[str, FunctionSignature] | None = None,
    ) -> None:
        self.variables = dict(variables or {})
        self.functions = dict(functions or {})
        self.diagnostics: list[IRDiagnostic] = []

    def check(self, module: SemanticIR) -> IRTypeCheckResult:
        self.diagnostics.clear()
        verify_semantic_ir(module)
        inferred = self._infer(module.root)
        return IRTypeCheckResult(inferred, tuple(self.diagnostics))

    def _report(self, node: IRNode, code: str, message: str) -> None:
        self.diagnostics.append(IRDiagnostic(code, message, node.span, node.node_id, node.kind))

    @staticmethod
    def _list_element(type_name: str) -> str | None:
        for opening, closing in (("List[", "]"), ("List<", ">")):
            if type_name.startswith(opening) and type_name.endswith(closing):
                return type_name[len(opening):-1]
        return None

    @classmethod
    def _canonical_type(cls, type_name: str) -> str:
        aliases = {"Str": "Text", "String": "Text", "Integer": "Int", "Boolean": "Bool"}
        if type_name in aliases:
            return aliases[type_name]
        element = cls._list_element(type_name)
        if element is not None:
            return f"List[{cls._canonical_type(element)}]"
        return type_name

    @classmethod
    def _assignable(cls, expected: str, actual: str) -> bool:
        expected = cls._canonical_type(expected)
        actual = cls._canonical_type(actual)
        if expected == "Any" or actual == "Any" or expected == actual:
            return True
        if expected == "Number" and actual in {"Int", "Float", "Number"}:
            return True
        if expected == "Float" and actual == "Int":
            return True
        expected_item = cls._list_element(expected)
        actual_item = cls._list_element(actual)
        if expected_item is not None and actual_item is not None:
            return expected_item == "Any" or cls._assignable(expected_item, actual_item)
        return False

    @staticmethod
    def _unify(left: str, right: str) -> str:
        if left == right:
            return left
        if "Any" in {left, right}:
            return "Any"
        if left in {"Int", "Float", "Number"} and right in {"Int", "Float", "Number"}:
            return "Number"
        return f"Union[{left},{right}]"

    def _infer(self, node: IRNode) -> str:
        if isinstance(node, IRLiteral):
            if node.value is None:
                return "Nothing"
            if isinstance(node.value, bool):
                return "Bool"
            if isinstance(node.value, int):
                return "Int"
            if isinstance(node.value, float):
                return "Float"
            if isinstance(node.value, str):
                return "Text"
            return "Any"
        if isinstance(node, IRVar):
            if node.name in self.variables:
                return self._canonical_type(self.variables[node.name])
            if node.name in self.functions:
                return "Function"
            self._report(node, "RPR-I0001", f"unknown variable or function '{node.name}'")
            return "Any"
        if isinstance(node, IRList):
            if not node.items:
                return "List[Any]"
            element_type = self._infer(node.items[0])
            for item in node.items[1:]:
                element_type = self._unify(element_type, self._infer(item))
            return f"List[{element_type}]"
        if isinstance(node, IRIndex):
            collection_type = self._infer(node.collection)
            index_type = self._infer(node.index)
            if not self._assignable("Int", index_type):
                self._report(node.index, "RPR-I0002", f"sequence index must be Int, got {index_type}")
            element_type = self._list_element(collection_type)
            if element_type is not None:
                return element_type
            if collection_type == "Text":
                return "Text"
            self._report(node, "RPR-I0003", f"cannot index a value of type {collection_type}")
            return "Any"
        if isinstance(node, IRCall):
            if isinstance(node.callee, IRIntrinsic):
                return self._infer_intrinsic(node)
            if isinstance(node.callee, IRVar):
                return self._infer_named_call(node, node.callee.name)
            self._infer(node.callee)
            for argument in node.arguments:
                self._infer(argument)
            self._report(node, "RPR-I0004", "indirect calls require an explicit callable contract")
            return "Any"
        if isinstance(node, IRIntrinsic):
            return "Function"
        self._report(node, "RPR-I0005", f"unsupported IR node for type inference: {node.kind}")
        return "Any"

    def _infer_named_call(self, node: IRCall, name: str) -> str:
        argument_types = [self._infer(argument) for argument in node.arguments]
        signature = self.functions.get(name)
        if signature is not None:
            if len(argument_types) != len(signature.parameter_types):
                self._report(
                    node, "RPR-I0006",
                    f"{name}() expects {len(signature.parameter_types)} arguments, got {len(argument_types)}",
                )
            for index, (actual, expected) in enumerate(zip(argument_types, signature.parameter_types), 1):
                if not self._assignable(expected, actual):
                    self._report(
                        node, "RPR-I0002",
                        f"argument {index} of '{name}' expects {self._canonical_type(expected)}, got {actual}",
                    )
            return self._canonical_type(signature.return_type)

        if name == "size":
            if len(argument_types) != 1:
                self._report(node, "RPR-I0006", f"size() expects 1 argument, got {len(argument_types)}")
            elif not (argument_types[0].startswith("List[") or argument_types[0] in {"Text", "Map", "Any"}):
                self._report(node, "RPR-I0002", f"size() expects a collection or Text, got {argument_types[0]}")
            return "Int"
        if name == "sum":
            if len(argument_types) != 1:
                self._report(node, "RPR-I0006", f"sum() expects 1 argument, got {len(argument_types)}")
                return "Number"
            element = self._list_element(argument_types[0])
            if element is None or element not in {"Int", "Float", "Number", "Any"}:
                self._report(node, "RPR-I0002", f"sum() expects a numeric list, got {argument_types[0]}")
            return "Number" if element in {"Float", "Number", "Any"} else "Int"
        if name in {"filter", "keep", "map"}:
            return self._infer_higher_order(node, name, argument_types)

        if name in self.variables:
            self._report(node, "RPR-I0004", f"'{name}' is a value, not a callable function")
        else:
            self._report(node, "RPR-I0001", f"unknown function '{name}'")
        return "Any"

    def _infer_higher_order(self, node: IRCall, name: str, argument_types: list[str]) -> str:
        if len(argument_types) != 2:
            self._report(node, "RPR-I0006", f"{name}() expects 2 arguments, got {len(argument_types)}")
            return "List[Any]"
        source_type = argument_types[0]
        element_type = self._list_element(source_type)
        if element_type is None:
            self._report(node.arguments[0], "RPR-I0002", f"{name}() expects List[T], got {source_type}")
            return "List[Any]"
        callback_node = node.arguments[1]
        callback_name = callback_node.name if isinstance(callback_node, IRVar) else None
        callback = self.functions.get(callback_name) if callback_name else None
        if callback is None:
            self._report(callback_node, "RPR-I0004", f"{name}() requires a named function with a known signature")
            return "List[Any]"
        if len(callback.parameter_types) != 1:
            self._report(callback_node, "RPR-I0006", f"callback '{callback_name}' must accept exactly one argument")
            return "List[Any]"
        if not self._assignable(callback.parameter_types[0], element_type):
            self._report(callback_node, "RPR-I0002", f"callback '{callback_name}' expects {callback.parameter_types[0]}, got {element_type}")
        callback_result = self._canonical_type(callback.return_type)
        if name in {"filter", "keep"}:
            if callback_result not in {"Bool", "Any"}:
                self._report(callback_node, "RPR-I0002", f"{name}() predicate must return Bool, got {callback_result}")
            return source_type
        return f"List[{callback_result}]"

    def _infer_intrinsic(self, node: IRCall) -> str:
        intrinsic = node.callee
        assert isinstance(intrinsic, IRIntrinsic)
        operand_types = [self._infer(argument) for argument in node.arguments]
        name = intrinsic.name
        expected_arity = 1 if name in {"neg", "not"} else 2
        if len(operand_types) != expected_arity:
            self._report(node, "RPR-I0006", f"operator '{name}' expects {expected_arity} operand(s)")
            return "Bool" if name in {"ge", "gt", "le", "lt", "eq", "ne", "and", "or", "not"} else "Any"
        if name in {"ge", "gt", "le", "lt"}:
            left, right = operand_types
            compatible = (
                left in {"Int", "Float", "Number", "Any"}
                and right in {"Int", "Float", "Number", "Any"}
            ) or (left == right == "Text") or "Any" in {left, right}
            if not compatible:
                self._report(node, "RPR-I0002", f"operator '{name}' cannot compare {left} with {right}")
            return "Bool"
        if name in {"eq", "ne"}:
            left, right = operand_types
            if not (
                self._assignable(left, right)
                or self._assignable(right, left)
                or "Any" in {left, right}
            ):
                self._report(node, "RPR-I0002", f"operator '{name}' cannot compare {left} with {right}")
            return "Bool"
        if name in {"add", "sub", "mul", "div", "floor_div", "mod", "pow", "neg"}:
            if not operand_types or any(item not in {"Int", "Float", "Number", "Any"} for item in operand_types):
                self._report(node, "RPR-I0002", f"operator '{name}' requires numeric operands, got {', '.join(operand_types)}")
                return "Any"
            return "Float" if "Float" in operand_types or name == "div" else "Int"
        if name in {"and", "or", "not"}:
            if any(item not in {"Bool", "Int", "Any"} for item in operand_types):
                self._report(node, "RPR-I0002", f"operator '{name}' requires boolean-compatible operands")
            return "Bool"
        if name == "concat":
            if len(operand_types) != 2 or any(item not in {"Text", "Any"} for item in operand_types):
                self._report(node, "RPR-I0002", "operator '++' requires Text operands")
            return "Text"
        self._report(node, "RPR-I0005", f"unknown intrinsic '{name}'")
        return "Any"


def typecheck_ir(
    module: SemanticIR,
    *,
    variables: Mapping[str, str] | None = None,
    functions: Mapping[str, FunctionSignature] | None = None,
) -> IRTypeCheckResult:
    return IRTypeChecker(variables, functions).check(module)


@dataclass(frozen=True, slots=True)
class SemanticAnalysisResult:
    module: SemanticIR
    type_check: IRTypeCheckResult

    @property
    def ok(self) -> bool:
        return self.type_check.ok


def analyze_expression_source(
    source_text: str,
    source_name: str = "<memory>",
    *,
    variables: Mapping[str, str] | None = None,
    functions: Mapping[str, FunctionSignature] | None = None,
) -> SemanticAnalysisResult:
    """Run parse -> semantic lowering -> contract-aware type checking for one expression."""
    tree = parse(source_text, source_name)
    module = lower_expression(tree, source_name)
    result = typecheck_ir(module, variables=variables, functions=functions)
    return SemanticAnalysisResult(module, result)


def format_diagnostic(
    diagnostic: IRDiagnostic,
    source_text: str,
    *,
    syntax_mode: str = "flow",
) -> str:
    return diagnostic.format(source_text, syntax_mode=syntax_mode)
