# Fundamental, Spine, Backbone and Structure Frameworks — batches 08–11

## Fundamental (08)

| Framework | API | Contract |
|---|---|---|
| Primitive Registry | `valid_fundamental_primitives(types)` | Closed, duplicate-free primitive type vocabulary |
| Unit Scale | `fundamental_bytes(value, unit)` | B/KiB/MiB/GiB conversion with 64-bit bounds |
| Invariant | `valid_fundamental_invariant(value, lower, upper)` | Inclusive scalar interval |
| Result Envelope | `valid_fundamental_result_envelope(envelope)` | Tagged ok/err value contract |
| Diagnostic Severity | `fundamental_diagnostic_severity(code)` | Stable RPR-E/W/I prefix classification |

## Spine (09)

| Framework | API | Contract |
|---|---|---|
| Chain | `valid_spine_chain(nodes)` | Unique ordered node sequence |
| Index | `spine_node_index(nodes, target)` | Deterministic lookup, -1 when absent |
| Tree | `valid_spine_tree(node_count, root, edges)` | Rooted tree, one parent per non-root node, full reachability |
| Cycle | `spine_graph_has_cycle(node_count, edges)` | Directed cycle detection by Kahn reduction |
| Path | `compact_spine_path(nodes)` | Collapse adjacent duplicate nodes |

## Backbone (10)

| Framework | API | Contract |
|---|---|---|
| Retry Schedule | `backbone_retry_delays(base, factor, attempts, cap)` | Bounded exponential retry schedule |
| Queue Admission | `backbone_queue_admission(depth, incoming, capacity)` | Queue capacity admission |
| Route Selection | `backbone_select_route(topic, routes)` | Longest-prefix route selection |
| Topic Fanout | `backbone_topic_subscribers(topic, subscriptions)` | Exact-topic subscriber fanout |
| Message Envelope | `valid_backbone_envelope(envelope)` | Versioned, bounded message envelope |

## Structure (11)

| Framework | API | Contract |
|---|---|---|
| Record Layout | `valid_structure_record_layout(total_size, fields)` | Bounded non-overlapping record fields |
| Hierarchy | `valid_structure_hierarchy(node_count, parents)` | Single-root parent vector without cycles |
| Matrix Shape | `structure_matrix_shape(matrix)` | Rectangular matrix dimensions |
| Field Alignment | `valid_structure_field_alignment(fields)` | Power-of-two field alignment and non-overlap |
| Coverage | `structure_missing_slots(required, provided)` | Missing structural slot report |

These modules are Reaper implementations and process caller-supplied values only. They do not start services, send messages, access physical memory, schedule jobs or mutate source trees.
