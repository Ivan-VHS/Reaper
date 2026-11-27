# RFS-01 — Rhythm-Field Syntax

**Status:** reference-runtime v1.0; native C frontend lexical parity is a follow-up gate  
**Canonical owner:** Reaper  
**Consumers:** Duck OS and Pytyliki  
**Contract family:** `rfs-01.*.v1`

RFS-01 is a typed, deterministic graph-and-phase sublanguage hosted by Reaper. It models computation as state nodes, directed flows, phase gates, contrast pairs, and explicit root recovery. It does not replace Reaper's ordinary expression grammar.

## 1. Compatibility boundary

The existing Reaper `::` operator remains left-to-right function application in the base language. RFS-01's `::` is a type-introducing declaration marker **only inside an RFS-01 source unit**. The RFS-01 parser is selected explicitly; there is no global lexer or precedence change.

The alternative `<>` marker declares a state-shaped node. RFS-01 does not reinterpret `::` or `<>` in ordinary `.rpr` units.

## 2. Source grammar

The v1.0 reference grammar is line-insensitive; commas separate fields.

```ebnf
program      = "module", identifier, "version", string, "{", { statement }, "}" ;
statement    = node | state | link | phase | flow | contrast | recover | cycles | emit ;
node         = "node", identifier, "::", "Node", fields ;
state        = "state", identifier, "<>", "State", fields ;
link         = "link", identifier, "::", "Link", fields ;
fields       = "{", [ field, { ",", field }, [ "," ] ], "}" ;
field        = identifier, ":", scalar ;
phase        = "phase", identifier, "on", identifier, "[",
               metric, comparator, number, ":", metric, comparator, number, "]" ;
flow         = "flow", identifier, flow_operator, identifier ;
flow_operator= "~>" | ">>" | "<<" ;
contrast     = "contrast", identifier, contrast_operator, identifier ;
contrast_operator = "||" | "^^" ;
recover      = "recover", identifier, ("<-root" | "^core") ;
cycles       = "cycles", integer ;
emit         = "emit", string ;
scalar       = identifier | number | string | "true" | "false" ;
metric       = "pressure" | "integrity" | "noise_db" ;
comparator   = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
```

The parser rejects unknown fields, duplicate IDs, unknown references, unsupported operators, malformed UTF-8, non-finite numbers, and values outside the v1.0 domain.

## 3. Typed state model

- `Node`: stable non-empty ID; layer in `Basement | Corridor | Gate | Skyline | Horizon`; finite pressure `>= 0`; finite load limit `> 0`; integrity ratio in `[0,1]`; noise level in `[-160,24]` dBFS; non-empty core seed.
- `Link`: origin and target node IDs; channel in `Wire | Rail | Beat | Current | Bridge`; blocked flag; finite non-negative weight.
- `Phase`: two bounded comparisons over one node. All gates declared for a node must pass before that node forwards a flow.
- `SignalFrame`: monotonic non-negative sequence, origin ID, bounded payload, trusted flag, manufactured flag.
- `Contrast`: references two nodes and yields a normalized reserve relation.
- `Recovery`: `<-root` restores the immutable load-time node snapshot; `^core` restores only the original core seed.

Pressure is dimensionless relative to a node's explicit load limit. The runtime does not silently increase integrity when pressure rises. Its reserve measure is:

```text
load_ratio = min(pressure / load_limit, 1)
reserve    = integrity * (1 - load_ratio)
```

It is a diagnostic index, not a claim about physical material strength.

## 4. Operator semantics

| Operator | Meaning | Deterministic effect |
|---|---|---|
| `::` | Typed node/link declaration | Binds a declaration to a v1 type |
| `<>` | State-node declaration | Declares a node in the state form |
| `~>` | Signal flow | Activates the destination and attenuates destination noise by the configured amplitude ratio |
| `>>` | Forward pressure flow | Adds source pressure × link weight if the destination load limit is not exceeded |
| `<<` | Reverse feedback flow | Transfers target pressure × link weight back to the source |
| `[a : b]` | Phase gate | Both comparisons must pass |
| `||` | Complementary contrast | `1 - abs(reserve(left)-reserve(right))` |
| `^^` | Differential contrast | `abs(reserve(left)-reserve(right))` |
| `<-root` | Full root restore | Restores layer, pressure, load limit, integrity, noise, and core seed |
| `^core` | Core restore | Restores only the original core seed |

Noise attenuation uses an amplitude ratio `r` and the standard dB relation `20 × log10(r)`; the reference runtime uses `r = 0.6` and clamps the floor to `-160 dBFS`.

## 5. Execution and safety limits

The reference runtime is deterministic and single-threaded. Nodes and links are processed in declaration order; signal frames are filtered by provenance; all iteration is bounded.

| Resource | v1.0 limit |
|---|---:|
| Source bytes | 1 MiB |
| Nodes | 4,096 |
| Links | 16,384 |
| Signal frames | 65,536 |
| Signal payload | 4 KiB |
| Cycles | 108 |
| Emitted messages | 256 |

The engine is local and side-effect-free: it does not open files, spawn processes, access hardware, use the network, or mutate caller-owned inputs. A blocked link never forwards. Over-pressure never changes integrity and never silently clamps a physical quantity; the attempted transfer is rejected and recorded.

## 6. Diagnostics

- `RFS-E001`: invalid token or malformed source.
- `RFS-E101`: invalid declaration or field type.
- `RFS-E201`: unresolved node/link reference.
- `RFS-E301`: invalid phase or unsupported comparison.
- `RFS-E401`: resource limit exceeded.
- `RFS-E501`: runtime invariant violated.

Diagnostics carry source line and column where applicable. Runtime events have stable sequence numbers and no wall-clock timestamps.

## 7. Cross-repository contracts

- **Reaper** owns grammar, semantics, typed IR, and the reference implementation.
- **Duck OS** consumes the bounded node/flow/recovery policy through Reaper-native modules. It may schedule processes and events only through existing OS services; RFS itself grants no privilege.
- **Pytyliki** consumes versioned state/signal records and provides read-only C11 validation and reserve metrics. Its adapter never changes scheduling, affinity, voltage, firmware, device registers, or process state.

The cross-repository ABI is opt-in and versioned. No consumer may infer that a documented or catalogued operation is implemented unless its source, test, and CI evidence are present.
