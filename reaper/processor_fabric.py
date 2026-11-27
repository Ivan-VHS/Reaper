"""Reaper-owned typed adapter for imported Pytyliki Processor Fabric data.

The adapter consumes a validated import report and Reaper-owned semantic/resource
bindings. It emits a typed semantic graph sidecar; it does not emit the legacy
stack-machine bytecode IR or execute hardware effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .semantic_graph import SemanticGraph, SemanticNode


class ProcessorFabricTypedIRError(ValueError):
    """Stable diagnostic for a rejected processor typed-IR import."""


@dataclass(frozen=True, slots=True)
class ProcessorInputBinding:
    """Connect a typed resource/process value to one operation input port."""

    source_kind: str
    source_id: int
    target_port: int


@dataclass(frozen=True, slots=True)
class ProcessorSemanticBinding:
    """Reaper-resolved operation signature for one Hardware AST semantic ID."""

    semantic_id: str
    operation: str
    input_types: tuple[str, ...]
    output_type: str
    effects: tuple[str, ...]
    inputs: tuple[ProcessorInputBinding, ...]


@dataclass(frozen=True, slots=True)
class ProcessorResourceBinding:
    """Reaper-owned type/effect/ownership interpretation of one PPF resource node."""

    ppf_node_id: int
    semantic_ref: str
    kind: str
    value_type: str
    effects: tuple[str, ...]
    owner: str
    generation: int
    dma_state: str | None = None
    coherency: str | None = None


def _fail(code: str, message: str) -> None:
    raise ProcessorFabricTypedIRError(f"{code}: {message}")


def _record(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail("RPR-PFT-0001", f"{label} must be an object")
    return value


def _bounded_int(value: Any, label: str, minimum: int = 0,
                 maximum: int = 2**53 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > maximum:
        _fail("RPR-PFT-0002", f"{label} is outside the integer bounds")
    return value


def _text(value: Any, label: str, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        _fail("RPR-PFT-0003", f"{label} must be non-empty bounded text")
    return value


def _acyclic(adjacency: Mapping[int, Sequence[int]], label: str) -> None:
    marks: dict[int, int] = {}

    def visit(node_id: int) -> None:
        mark = marks.get(node_id, 0)
        if mark == 1:
            _fail("RPR-PFT-0004", f"{label} contains a cycle")
        if mark == 2:
            return
        marks[node_id] = 1
        for dependency in adjacency.get(node_id, ()):
            visit(dependency)
        marks[node_id] = 2

    for node_id in sorted(adjacency):
        visit(node_id)


def lower_processor_fabric(
    import_report: Mapping[str, Any],
    source_bytes: bytes,
    *,
    semantic_bindings: Mapping[str, ProcessorSemanticBinding],
    resource_bindings: Mapping[int, ProcessorResourceBinding],
    granted_effects: Sequence[str] = (),
) -> dict[str, Any]:
    """Verify producer evidence and lower resolved constructs to Reaper SemanticGraph.

    Bindings are deliberately supplied by Reaper's own resolver/Typed Registry.
    Producer metadata can identify nodes and source spans, but cannot declare
    their types, effects, capabilities or ownership as verified.
    """
    report = _record(import_report, "processor fabric import report")
    source = _record(report.get("source"), "source")
    host = _record(report.get("host_evidence"), "host_evidence")
    fabric = _record(report.get("fabric"), "fabric")
    source_digest = _text(source.get("sha256"), "source.sha256", 64)
    if len(source_digest) != 64 or any(c not in "0123456789abcdef" for c in source_digest):
        _fail("RPR-PFT-0005", "source.sha256 must be lowercase SHA-256")
    import hashlib
    actual_digest = hashlib.sha256(source_bytes).hexdigest()
    if actual_digest != source_digest:
        _fail("RPR-PFT-0006", "source bytes do not match the imported digest")
    source_length = _bounded_int(source.get("byte_length"), "source.byte_length", 1, 1_048_576)
    if len(source_bytes) != source_length:
        _fail("RPR-PFT-0007", "source byte length changed after import")
    try:
        source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        _fail("RPR-PFT-0008", f"source is not valid UTF-8: {error}")

    generation = _bounded_int(fabric.get("generation"), "fabric.generation", 1)
    topology_generation = _bounded_int(host.get("generation"), "host_evidence.generation", 1)
    if generation != topology_generation:
        _fail("RPR-PFT-0009", "fabric and topology generations are stale or inconsistent")
    if report.get("semantic_admission", {}).get("canonical_ir_emitted") is not False:
        _fail("RPR-PFT-0010", "the producer must not claim to have emitted Reaper typed IR")
    if report.get("execution_performed") is not False or report.get("hardware_access_performed") is not False:
        _fail("RPR-PFT-0011", "import report contains an execution or hardware-access claim")

    nodes_list = fabric.get("nodes")
    edges_list = fabric.get("edges")
    if not isinstance(nodes_list, list) or not isinstance(edges_list, list):
        _fail("RPR-PFT-0012", "full PPF nodes and edges are required for semantic lowering")
    if len(nodes_list) != _bounded_int(fabric.get("node_count"), "fabric.node_count", 1, 4096):
        _fail("RPR-PFT-0013", "fabric node count is inconsistent")
    if len(edges_list) != _bounded_int(fabric.get("edge_count"), "fabric.edge_count", 0, 16384):
        _fail("RPR-PFT-0014", "fabric edge count is inconsistent")

    nodes: dict[int, Mapping[str, Any]] = {}
    process_ids: set[int] = set()
    parent_adjacency: dict[int, list[int]] = {}
    for index, value in enumerate(nodes_list):
        node = _record(value, f"fabric.nodes[{index}]")
        node_id = _bounded_int(node.get("id"), "PPF node id", 1)
        if node_id in nodes:
            _fail("RPR-PFT-0015", f"duplicate PPF node id {node_id}")
        if node.get("generation", generation) != generation:
            _fail("RPR-PFT-0016", f"PPF node {node_id} has a stale generation")
        kind = _text(node.get("kind"), "PPF node kind", 48)
        nodes[node_id] = node
        if kind == "process":
            process_ids.add(node_id)
        parent_id = node.get("parent_id")
        if parent_id is not None:
            parent_id = _bounded_int(parent_id, "PPF parent id", 1)
            parent_adjacency.setdefault(node_id, []).append(parent_id)
    for node_id, dependencies in parent_adjacency.items():
        for dependency in dependencies:
            if dependency not in nodes:
                _fail("RPR-PFT-0017", f"PPF parent {dependency} for node {node_id} is missing")
    _acyclic(parent_adjacency, "PPF parent graph")

    dependency_adjacency: dict[int, list[int]] = {process_id: [] for process_id in process_ids}
    edge_seen: set[tuple[int, int, str]] = set()
    for index, value in enumerate(edges_list):
        edge = _record(value, f"fabric.edges[{index}]")
        from_id = _bounded_int(edge.get("from_id"), "edge from_id", 1)
        to_id = _bounded_int(edge.get("to_id"), "edge to_id", 1)
        kind = _text(edge.get("kind"), "edge kind", 48)
        if from_id not in nodes or to_id not in nodes:
            _fail("RPR-PFT-0018", "PPF edge references a missing node")
        edge_key = (from_id, to_id, kind)
        if edge_key in edge_seen:
            _fail("RPR-PFT-0019", "duplicate PPF edge")
        edge_seen.add(edge_key)
        if kind == "depends-on":
            if from_id not in process_ids or to_id not in process_ids:
                _fail("RPR-PFT-0020", "process dependency must connect two process nodes")
            dependency_adjacency[from_id].append(to_id)
        elif kind == "uses":
            if nodes[from_id].get("kind") != "process":
                _fail("RPR-PFT-0021", "uses edge must originate at a process")
        elif kind not in {"maps-to", "produces"}:
            _fail("RPR-PFT-0022", f"unsupported PPF edge kind {kind}")
    _acyclic(dependency_adjacency, "PPF process dependency graph")

    resources = _record(report.get("resource_contract"), "resource_contract")
    resource_generation = _bounded_int(resources.get("generation"), "resource generation", 1)
    if resource_generation != generation:
        _fail("RPR-PFT-0023", "resource contract generation is stale")
    resource_descriptors: dict[str, Mapping[str, Any]] = {}
    for collection in ("devices", "address_spaces", "memory_regions", "register_banks", "dma_buffers"):
        values = resources.get(collection, [])
        if not isinstance(values, list):
            _fail("RPR-PFT-0024", f"resource collection {collection} must be an array")
        for item in values:
            descriptor = _record(item, collection + " item")
            resource_id = _text(descriptor.get("id"), collection + ".id", 96)
            if resource_id in resource_descriptors:
                _fail("RPR-PFT-0025", f"duplicate resource contract id {resource_id}")
            resource_descriptors[resource_id] = descriptor

    grants = set(granted_effects)
    if any(not isinstance(effect, str) or not effect for effect in grants):
        _fail("RPR-PFT-0026", "granted_effects must contain non-empty effect names")
    resource_nodes: dict[int, SemanticNode] = {}
    for ppf_id, binding in resource_bindings.items():
        _bounded_int(ppf_id, "resource PPF node id", 1)
        if not isinstance(binding, ProcessorResourceBinding):
            _fail("RPR-PFT-0027", f"resource binding for node {ppf_id} is not Reaper-owned")
        node = nodes.get(ppf_id)
        if node is None or node.get("kind") not in {
            "address-space", "memory-region", "register-bank", "device", "register", "dma-buffer"
        }:
            _fail("RPR-PFT-0028", f"resource binding points to a non-resource PPF node {ppf_id}")
        semantic_ref = _text(binding.semantic_ref, "resource semantic_ref", 96)
        if node.get("semantic_ref") != semantic_ref or semantic_ref not in resource_descriptors:
            _fail("RPR-PFT-0029", f"resource binding does not match the validated resource contract for node {ppf_id}")
        if binding.generation != generation:
            _fail("RPR-PFT-0030", f"resource binding for node {ppf_id} has a stale generation")
        if binding.owner not in {"cpu", "device", "shared", "unowned"}:
            _fail("RPR-PFT-0031", f"resource ownership for node {ppf_id} is invalid")
        if binding.kind == "dma-buffer":
            if binding.dma_state not in {"cpu_owned", "prepared_for_device", "device_owned",
                                         "completed_for_cpu", "released"}:
                _fail("RPR-PFT-0032", "DMA ownership state is missing or invalid")
            if binding.dma_state in {"prepared_for_device", "device_owned", "released"}:
                _fail("RPR-PFT-0033", f"DMA resource {ppf_id} is not CPU-readable in state {binding.dma_state}")
            if binding.owner == "device":
                _fail("RPR-PFT-0034", f"DMA resource {ppf_id} is device-owned")
            if binding.coherency not in {"coherent", "non-coherent-explicit-sync"}:
                _fail("RPR-PFT-0035", f"DMA resource {ppf_id} has unknown coherency")
        effects = tuple(binding.effects)
        if set(effects) - grants:
            _fail("RPR-PFT-0036", f"resource {ppf_id} requires ungranted effects: {sorted(set(effects) - grants)}")
        resource_nodes[ppf_id] = SemanticNode.create(
            "hardware-resource:" + binding.kind, (), binding.value_type,
            effects=effects, literal=f"{ppf_id}:{semantic_ref}", label=semantic_ref
        )

    constructs = report.get("constructs")
    if not isinstance(constructs, list) or not constructs:
        _fail("RPR-PFT-0037", "import report has no Hardware AST constructs")
    process_nodes: dict[int, SemanticNode] = {}
    construct_output: list[dict[str, Any]] = []
    process_bindings: dict[int, ProcessorSemanticBinding] = {}
    for index, value in enumerate(constructs):
        construct = _record(value, f"constructs[{index}]")
        process_id = _bounded_int(construct.get("processId"), "construct processId", 1)
        if process_id not in process_ids:
            _fail("RPR-PFT-0038", f"construct process {process_id} is absent from the PPF graph")
        semantic_id = _text(construct.get("semanticId"), "construct semanticId", 128)
        binding = semantic_bindings.get(semantic_id)
        if not isinstance(binding, ProcessorSemanticBinding):
            _fail("RPR-PFT-0039", f"no Reaper semantic binding is available for {semantic_id}")
        if binding.semantic_id != semantic_id:
            _fail("RPR-PFT-0040", "semantic binding key and semantic ID disagree")
        effects = tuple(binding.effects)
        missing = set(effects) - grants
        if missing:
            _fail("RPR-PFT-0041", f"construct {semantic_id} requires ungranted effects: {sorted(missing)}")
        if process_id in process_nodes:
            _fail("RPR-PFT-0042", f"multiple constructs lower to one process id {process_id}")
        process_node = SemanticNode.create(
            binding.operation, binding.input_types, binding.output_type,
            effects=effects, literal=process_id,
            label=f"ppf-process:{process_id}:{semantic_id}"
        )
        process_nodes[process_id] = process_node
        process_bindings[process_id] = binding
        source_span = _record(construct.get("sourceSpan"), "construct.sourceSpan")
        body_span = _record(construct.get("bodySpan"), "construct.bodySpan")
        source_start = _bounded_int(source_span.get("start"), "source span start", 0, len(source_bytes))
        source_size = _bounded_int(source_span.get("length"), "source span length", 0, len(source_bytes))
        body_start = _bounded_int(body_span.get("start"), "body span start", source_start, len(source_bytes))
        body_size = _bounded_int(body_span.get("length"), "body span length", 0, len(source_bytes))
        if source_size > len(source_bytes) - source_start or body_size > len(source_bytes) - body_start:
            _fail("RPR-PFT-0043", "source/body span exceeds source bytes")
        if body_start + body_size > source_start + source_size:
            _fail("RPR-PFT-0044", "body span is not contained by its source span")
        construct_output.append({
            "process_id": process_id,
            "semantic_id": semantic_id,
            "semantic_node_id": process_node.content_id,
            "source_span": {"start": source_start, "length": source_size},
            "body_span": {"start": body_start, "length": body_size},
            "output_type": binding.output_type,
            "effects": list(effects)
        })

    semantic_graph = SemanticGraph()
    for node in sorted((*resource_nodes.values(), *process_nodes.values()),
                       key=lambda item: item.content_id):
        semantic_graph = semantic_graph.add_node(node)
    for process_id, binding in sorted(process_bindings.items()):
        target = process_nodes[process_id]
        claimed_ports: set[int] = set()
        for input_binding in binding.inputs:
            if not isinstance(input_binding, ProcessorInputBinding):
                _fail("RPR-PFT-0045", "process input binding is not a Reaper-owned binding")
            port = _bounded_int(input_binding.target_port, "input target port", 0)
            if port >= len(binding.input_types) or port in claimed_ports:
                _fail("RPR-PFT-0046", f"invalid or duplicate semantic input port {port}")
            claimed_ports.add(port)
            if input_binding.source_kind == "resource":
                source_node = resource_nodes.get(input_binding.source_id)
            elif input_binding.source_kind == "process":
                source_node = process_nodes.get(input_binding.source_id)
            else:
                _fail("RPR-PFT-0047", f"unsupported semantic input source kind {input_binding.source_kind}")
            if source_node is None:
                _fail("RPR-PFT-0048", f"semantic input source {input_binding.source_id} is missing")
            if source_node.output_type != binding.input_types[port]:
                _fail("RPR-PFT-0049", f"semantic input type mismatch at process {process_id} port {port}")
            semantic_graph = semantic_graph.connect(
                source_node.content_id, target.content_id, port
            )
        if len(claimed_ports) != len(binding.input_types):
            _fail("RPR-PFT-0050", f"process {process_id} has unbound typed input ports")

    try:
        semantic_graph.validate(require_complete=True)
    except (TypeError, ValueError) as error:
        _fail("RPR-PFT-0051", f"Reaper SemanticGraph verification failed: {error}")

    control_dependencies = []
    for process_id in sorted(process_ids):
        for dependency_id in sorted(dependency_adjacency.get(process_id, ())):
            control_dependencies.append({
                "process_id": process_id,
                "requires_process_id": dependency_id
            })

    ownership = []
    for ppf_id, binding in sorted(resource_bindings.items()):
        ownership.append({
            "ppf_node_id": ppf_id,
            "semantic_ref": binding.semantic_ref,
            "kind": binding.kind,
            "owner": binding.owner,
            "dma_state": binding.dma_state,
            "coherency": binding.coherency,
            "generation": binding.generation
        })

    return {
        "schema": "reaper.processor-fabric-typed-ir.v1",
        "version": 1,
        "source": {
            "sha256": source_digest,
            "byte_length": len(source_bytes),
            "offset_unit": "utf8-byte"
        },
        "generation": generation,
        "semantic_graph": semantic_graph.to_dict(),
        "constructs": sorted(construct_output, key=lambda item: item["process_id"]),
        "control_dependencies": control_dependencies,
        "resource_ownership": ownership,
        "verification": {
            "source_digest_verified": True,
            "topology_generation_verified": True,
            "fabric_graph_verified": True,
            "types_verified": True,
            "effects_verified": True,
            "ownership_verified": True,
            "semantic_graph_verified": True,
            "canonical_typed_ir_emitted": True,
            "stack_vm_bytecode_emitted": False,
            "execution_performed": False,
            "hardware_access_performed": False
        }
    }
