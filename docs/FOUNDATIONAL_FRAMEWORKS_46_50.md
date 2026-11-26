# Reaper foundational frameworks 46–50

**Status:** executable Reaper reference contracts; full typed IR, CFG verification and interface lowering remain partial.  
**Source:** `frameworks/foundation_46_50.rpr`  
**Dependency:** `frameworks/foundation_41_45.rpr`  
**Schema:** `reaper.foundation.tenth.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 46 | `foundation.component.v1` | Component | Reusable typed component contract and dependency-first graph | Partial |
| 47 | `foundation.block.v1` | Block | Instruction blocks, effects and block references | Partial |
| 48 | `foundation.node.v1` | Node | Typed graph nodes and interface-compatible edges | Partial |
| 49 | `foundation.interface.v1` | Interface | Versioned interface descriptors and producer/consumer compatibility | Partial |
| 50 | `foundation.protocol.v1` | Protocol | Transport/framing profiles, provenance and explicit opt-in | Partial |

## 46. Component — reusable unit contract

A component descriptor uses:

`[component_id, kind, major, input_contract, output_contract, dependencies, maturity]`

Kinds are frontend, analysis, transform, runtime, host-adapter, tooling and test. IDs and dependencies must be unique; dependency graphs must be supplied in dependency-first order. The catalogue maps the current lexer/parser/semantic/IR/VM boundaries without pretending every stage is complete.

Public functions: `component_kinds()`, `component_catalog()`, `component_validate_descriptor(component)`, `component_validate_catalog()`, `component_validate_graph(components)`, `component_graph_order(components)`.

## 47. Block — bounded instruction region

An instruction is:

`[instruction_id, operation, result_type]`

Operation kinds are load, store, call, branch, return, emit and effect. A block descriptor is:

`[block_id, entry_contract, exit_contract, instructions, value_ids, effects]`

IDs and value IDs must be unique, effects use the established effect catalogue, and `pure` cannot be combined with effects. This is a structural verifier only; it does not execute instructions, prove SSA dominance, compute liveness or lower a CFG.

Public functions: `block_operation_kinds()`, `block_validate_instruction(instruction)`, `block_validate_descriptor(block)`, `block_validate_control_flow(blocks)`, `block_validate_branch(blocks, branch)`.

## 48. Node — typed graph vertex

Node descriptors contain:

`[node_id, kind, label, input_contracts, output_contracts, maturity]`

Edges are:

`[source_node, target_node, interface_id]`

Both endpoints must exist, the source must provide the interface and the target must accept it, and duplicate/self edges are rejected. The topological-order helper returns the supplied node order only after validating the edges; it is not a full cycle-detecting graph sorter yet, so callers must not treat it as a cycle certificate.

Public functions: `node_kinds()`, `node_catalog()`, `node_validate_descriptor(node)`, `node_validate_graph(nodes, edges)`, `node_topological_order(nodes, edges)`.

## 49. Interface — versioned contract

An interface descriptor is:

`[interface_id, major, minor, direction, format, max_bytes]`

Major versions must match; the requested minor cannot exceed the catalogue version; format and payload bound must match the published interface. Compatibility requires producer direction provides/both and consumer direction consumes/both.

Public functions: `interface_directions()`, `interface_catalog()`, `interface_validate_descriptor(descriptor)`, `interface_validate_compatibility(producer, consumer)`.

## 50. Protocol — transport contract

A protocol descriptor is:

`[protocol_id, version, transport, framing, provenance, max_bytes, maturity]`

Known transports are in-process, JSON file, native FFI, DABI64 IPC and none. The registry differentiates implemented, partial, opt-in and planned. Planned protocols are rejected; the native FFI protocol requires an explicit true flag. Payload sizes are checked against per-protocol bounds.

Public functions: `protocol_transports()`, `protocol_catalog()`, `protocol_validate_descriptor(protocol)`, `protocol_validate_selection(id, enabled)`, `protocol_validate_payload(id, size)`.

## Unified catalogue

The module exposes `foundation_all_frameworks_50()` and `foundation_validate_catalog_50()`, extending the first nine groups to fifty unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_46_50.rpr" as graph

emit graph["foundation_validate_catalog_50"]()
emit graph["component_validate_catalog"]()
emit graph["block_validate_descriptor"](["entry", "typed-input.v1", "typed-output.v1", [["load-x", "load", "u32"]], ["x"], ["pure"]])
emit graph["interface_validate_compatibility"](["token-stream.v1", 1, 0, "provides", "token-array", 1024], ["token-stream.v1", 1, 0, "consumes", "token-array", 1024])
emit graph["protocol_validate_selection"]("reaper.pytyliki-ffi.v1", true)
emit graph["protocol_validate_payload"]("reaper.system-runtime.v1", 4096)
```

## Verification and safety

Tests verify component graph ordering, instruction/effect constraints, interface-compatible node edges, version/direction compatibility, protocol maturity and payload bounds. The module does not execute blocks, load modules, open transports, connect networks, grant capabilities or call a host.
