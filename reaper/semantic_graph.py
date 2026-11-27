"""Typed, content-addressed dataflow graph primitives for Reaper.
The graph is a semantic sidecar to the existing .rpr text/AST/IR toolchain.
It does not execute programs or replace the current source format.
"""
from __future__ import annotations
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, replace
import hashlib
import json
import math
from typing import Any

def _literal_value(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("semantic literals must be finite JSON scalar values")

def _semantic_payload(operation: str, input_types: tuple[str, ...], output_type: str,
                      effects: tuple[str, ...], literal: str | int | float | bool | None) -> dict[str, Any]:
    return {"schema":"reaper.semantic-node/v1","operation":operation,
            "input_types":list(input_types),"output_type":output_type,
            "effects":list(effects),"literal":literal}

def semantic_digest(payload: dict[str, Any]) -> str:
    canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,
                         separators=(",",":"),allow_nan=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

@dataclass(frozen=True, slots=True)
class SemanticNode:
    content_id: str
    operation: str
    input_types: tuple[str, ...]
    output_type: str
    effects: tuple[str, ...] = ()
    literal: str | int | float | bool | None = None
    label: str = ""

    @classmethod
    def create(cls, operation: str, input_types: Iterable[str], output_type: str, *,
               effects: Iterable[str] = (), literal: Any = None, label: str = "") -> "SemanticNode":
        if not isinstance(operation,str) or not operation.strip():
            raise ValueError("operation must be non-empty text")
        if not isinstance(output_type,str) or not output_type.strip():
            raise ValueError("output_type must be non-empty text")
        if isinstance(input_types, (str, bytes)):
            raise TypeError("input_types must be an iterable of type names, not text")
        if isinstance(effects, (str, bytes)):
            raise TypeError("effects must be an iterable of effect names, not text")
        inputs=tuple(input_types); effect_set=tuple(effects)
        if any(not isinstance(x,str) or not x.strip() for x in inputs):
            raise ValueError("input types must be non-empty strings")
        if any(not isinstance(x,str) or not x.strip() for x in effect_set):
            raise ValueError("effects must be non-empty strings")
        if len(set(effect_set)) != len(effect_set):
            raise ValueError("effects must be unique")
        if not isinstance(label,str):
            raise TypeError("label must be text")
        value=_literal_value(literal)
        payload=_semantic_payload(operation.strip(),inputs,output_type.strip(),effect_set,value)
        return cls(semantic_digest(payload),operation.strip(),inputs,output_type.strip(),
                   effect_set,value,label)

    def verify_address(self) -> bool:
        try:
            expected = semantic_digest(
                _semantic_payload(
                    self.operation, self.input_types, self.output_type,
                    self.effects, self.literal
                )
            )
        except (TypeError, ValueError, OverflowError):
            return False
        return self.content_id == expected

    def rename(self, label: str) -> "SemanticNode":
        if not isinstance(label,str):
            raise TypeError("label must be text")
        return replace(self,label=label)

@dataclass(frozen=True, slots=True)
class SemanticEdge:
    source_id: str
    target_id: str
    target_port: int

@dataclass(frozen=True, slots=True)
class SemanticGraph:
    nodes: tuple[SemanticNode, ...] = ()
    edges: tuple[SemanticEdge, ...] = ()

    def add_node(self, node: SemanticNode) -> "SemanticGraph":
        if not isinstance(node,SemanticNode) or not node.verify_address():
            raise ValueError("node must carry a valid semantic content address")
        if any(n.content_id == node.content_id for n in self.nodes):
            raise ValueError(f"semantic node already exists: {node.content_id}")
        result=replace(self,nodes=self.nodes+(node,))
        result.validate()
        return result

    def connect(self, source_id: str, target_id: str, target_port: int) -> "SemanticGraph":
        by_id={n.content_id:n for n in self.nodes}
        if source_id not in by_id or target_id not in by_id:
            raise ValueError("edge endpoints must reference nodes in this graph")
        if isinstance(target_port,bool) or not isinstance(target_port,int) or target_port < 0:
            raise ValueError("target_port must be a non-negative integer")
        source,target=by_id[source_id],by_id[target_id]
        if target_port >= len(target.input_types):
            raise ValueError("target port is outside the node input signature")
        if source.output_type != target.input_types[target_port]:
            raise TypeError(f"port type mismatch: {source.output_type} cannot feed {target.input_types[target_port]}")
        if any(e.target_id == target_id and e.target_port == target_port for e in self.edges):
            raise ValueError("target input port is already connected")
        result=replace(self,edges=self.edges+(SemanticEdge(source_id,target_id,target_port),))
        result.validate()
        return result

    def validate(self, *, require_complete: bool = False) -> None:
        by_id={}
        for node in self.nodes:
            if not isinstance(node, SemanticNode):
                raise ValueError("graph nodes must be SemanticNode instances")
            if (
                not isinstance(node.operation, str) or not node.operation.strip()
                or not isinstance(node.output_type, str) or not node.output_type.strip()
                or not isinstance(node.input_types, tuple)
                or any(not isinstance(item, str) or not item.strip() for item in node.input_types)
                or not isinstance(node.effects, tuple)
                or any(not isinstance(item, str) or not item.strip() for item in node.effects)
                or len(set(node.effects)) != len(node.effects)
                or not isinstance(node.label, str)
            ):
                raise ValueError("semantic node fields violate the immutable signature contract")
            try:
                _literal_value(node.literal)
            except TypeError as error:
                raise ValueError("semantic node literal is invalid") from error
            if not node.verify_address():
                raise ValueError(f"semantic address mismatch: {node.content_id}")
            if node.content_id in by_id:
                raise ValueError(f"duplicate semantic node: {node.content_id}")
            by_id[node.content_id]=node
        incoming=set()
        outgoing={node_id:[] for node_id in by_id}
        indegree={node_id:0 for node_id in by_id}
        for edge in self.edges:
            if not isinstance(edge, SemanticEdge):
                raise ValueError("graph edges must be SemanticEdge instances")
            if (
                not isinstance(edge.source_id, str)
                or not isinstance(edge.target_id, str)
                or isinstance(edge.target_port, bool)
                or not isinstance(edge.target_port, int)
                or edge.target_port < 0
            ):
                raise ValueError("edge fields must use node IDs and a non-negative integer port")
            if edge.source_id not in by_id or edge.target_id not in by_id:
                raise ValueError("edge references a node outside the graph")
            target=by_id[edge.target_id]
            if edge.target_port >= len(target.input_types):
                raise ValueError("edge target port is invalid")
            key=(edge.target_id,edge.target_port)
            if key in incoming:
                raise ValueError("target input port is connected more than once")
            source=by_id[edge.source_id]
            if source.output_type != target.input_types[edge.target_port]:
                raise TypeError("edge connects incompatible semantic types")
            incoming.add(key)
            outgoing[edge.source_id].append(edge.target_id)
            indegree[edge.target_id]+=1
        if require_complete:
            for node in self.nodes:
                for port in range(len(node.input_types)):
                    if (node.content_id,port) not in incoming:
                        raise ValueError(f"unconnected input port {port} on {node.operation}")
        ready=deque(sorted(n for n,d in indegree.items() if d == 0))
        visited=0
        while ready:
            node_id=ready.popleft(); visited+=1
            for target_id in sorted(outgoing[node_id]):
                indegree[target_id]-=1
                if indegree[target_id] == 0:
                    ready.append(target_id)
        if visited != len(by_id):
            raise ValueError("semantic dataflow graph contains a cycle")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema":"reaper.semantic-graph/v1",
            "nodes":[{"id":n.content_id,"operation":n.operation,
                      "input_types":list(n.input_types),"output_type":n.output_type,
                      "effects":list(n.effects),"literal":n.literal,"label":n.label}
                     for n in sorted(self.nodes,key=lambda x:x.content_id)],
            "edges":[{"source":e.source_id,"target":e.target_id,"target_port":e.target_port}
                     for e in sorted(self.edges,key=lambda x:(x.target_id,x.target_port,x.source_id))]
        }
