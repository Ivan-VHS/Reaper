# Reaper Processor Intelligence

**Status:** Reaper source module and deterministic conformance fixture added  
**Source API:** \`stdlib/processor_intelligence.rpr\`  
**Fixture:** \`examples/processor_intelligence.rpr\`  
**Scope:** bounded processor observations, action-state accounting and export models

Reaper Processor Intelligence is a language-level model for describing processor activity, validating event streams and preparing bounded reports. It complements the native processor discovery and measurement work in Pytyliki; it does not replace the platform-specific C11 measurement path.

## Capabilities

| Requested capability | Reaper API | Contract |
|---|---|---|
| Embedded C planning | \`processor_embedded_budget\` | FLASH/SRAM byte budgets; no firmware flashing |
| State programmer | \`processor_state_make\`, \`processor_state_append\` | Immutable state transitions with monotonic sequence and tick checks |
| Reliable action counter | \`processor_action_count\`, \`processor_action_counter\` | Accepted/rejected totals and successful-action ratio |
| Processor slow-motion | \`processor_slowmo_plan\` | Produces a scaled replay schedule; does not slow or throttle the physical CPU |
| Processor source chunks | \`processor_source_unpack\` | Ordered, unique, size-bounded source-fragment reconstruction |
| Operation expansion | \`processor_operation_expand\` | Converts compact action records into explicit interval rows |
| Code pulse | \`processor_pulse_analyze\` | Bounded interval mean, maximum relative deviation and consistency flag |
| System tray model | \`processor_tray_snapshot\` | Small human-readable status record for a host UI to render |
| Humanization | \`processor_humanize_status\` | Stable status vocabulary |
| Memory control | \`processor_memory_budget\` | Whole-byte capacity, use, reservation and headroom validation |
| Hardware policy | \`processor_hardware_policy\` | Read-only observation; simulated writes produce plans only |
| Deterministic processor control | \`processor_state_valid\`, \`processor_checkpoint_valid\` | Stable event sequence, nondecreasing ticks and checkpoint matching |
| Table export | \`processor_table_export\` | Fixed header and expanded rows for CSV/JSON host adapters |
| Design guide | This document | Input schemas, safe boundaries and expected data provenance |
| Processor logic | \`processor_action_valid\`, \`processor_state_valid\` | Structural and semantic validation |
| Graph reduction | \`processor_graph_reduce\` | Bounded counts, average degree and simple directed graph density |
| Processor “stone” / package | \`processor_chip_snapshot_valid\` | Package/core/thread/NUMA counts with ISA and provenance |
| State caching | \`processor_checkpoint_make\`, \`processor_cache_store\` | Versioned checkpoints and bounded FIFO retention |

“Confidence” from \`processor_action_counter\` is deliberately only the ratio of accepted actions to all recorded actions. It is not a hardware health score, probability of correctness or certification.

## Data contracts

An action is a fixed nine-field record:

\`\`\`text
["processor.action.v1", sequence, operation, target,
 start_tick, duration_ticks, cycles, outcome, source_chunk]
\`\`\`

A processor state is a seven-field record:

\`\`\`text
["processor.state.v1", next_sequence, last_tick, actions,
 checkpoints, accepted_actions, rejected_actions]
\`\`\`

The module validates the complete history when a transition occurs. Sequence values begin at one; action start ticks cannot move behind the previous committed end tick; durations and cycle counts are non-negative integers. Outcomes are \`ok\` or \`err\`. A malformed transition returns an \`ERR\` value and does not produce a replacement state.

Processor package snapshots are caller-supplied observations with an explicit source classification: \`observed\`, \`reference\` or \`simulated\`. A reference profile or simulated fixture must not be presented as live hardware telemetry.

## Usage

\`\`\`rpr
import "../stdlib/processor_intelligence.rpr" as processor

make state := processor.processor_state_make()
make action := [
    "processor.action.v1", 1, "decode", "core0",
    0, 5, 12, "ok", "chunk-001"
]
make committed := processor.processor_state_append(state, action)
assert(committed[0] == "OK", "invalid processor transition")
make table := processor.processor_table_export(committed[1])
\`\`\`

Run the conformance fixture using the existing Reaper runtime:

\`\`\`sh
python -m reaper --check examples/processor_intelligence.rpr
python -m reaper examples/processor_intelligence.rpr
\`\`\`

The fixture is also part of the existing self-hosting regression suite. It checks rejected transitions, invalid budgets, hardware policy denial, chunk ordering, graph edge cases, checkpoint staleness and export shape.

## Safety and integration boundaries

- The module has no direct CPU instruction, scheduler, affinity, voltage, frequency, firmware, BIOS/UEFI, driver or device-register operation.
- A \`read_only\` hardware mode describes permission to observe. The module itself does not acquire a physical sensor or bus.
- \`simulated\` writes create a plan-only result; no bus adapter is invoked.
- Slow-motion scales logical ticks for replay and analysis. It does not sleep, alter execution speed or manipulate processor frequency.
- Memory and Embedded C functions validate numeric budgets supplied by the caller; they do not allocate process memory or map MCU memory.
- The source unpacker reconstructs validated text chunks only. It does not compile or execute the reconstructed source.
- The tray snapshot is UI-ready data, not a resident system-tray process.
- Real CPU topology, ISA state, hardware measurements, trace samples, and MCU profile discovery remain owned by Pytyliki's native C11 implementation. Existing Pytyliki-to-Reaper C ABI v1 calls remain explicit and opt-in.
- The state ledger is an accounting model. It is not a replacement for the runtime's ownership, memory-region or hardware-bus contracts.

## Limits

State history is bounded by the Reaper runtime's configured collection limits. Source reconstruction accepts at most 256 chunks and 2 MB total text. Pulse analysis accepts 2 to 1,000,000 intervals. Graph reduction accepts at most 10,000 nodes and 1,000,000 edges. State cache capacity is 1 to 32 checkpoints. Slow-motion factor is an integer from 1 to 16.

The module is an executable reference-language feature. Equivalent native compiler syntax, lowering and backend parity should be marked separately until implemented and tested.
