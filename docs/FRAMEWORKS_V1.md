# Reaper framework set v1

The framework set adds eight executable modules in Reaper source. Each module
exports ordinary Reaper crafts and can be imported from another .rpr file. It
uses the existing module loader and reference runtime; it does not add another
parser, execution engine or hidden host capability.

## Modules and contracts

| Framework | Executable responsibility | Stable data contract |
|---|---|---|
| GalHero | validates dependency graphs, produces stable topological order, reports cycles, expands transitive dependencies | nodes are a list; each edge is [node, prerequisite] |
| Call-and-Back | registers callbacks, dispatches matching events by ascending priority, removes one-shot handlers, composes callback results | handler is [event, priority, once, callback] |
| Stacked Options | merges configuration layers, upserts keys, supplies defaults and checks required values and runtime kinds | option is [key, value]; rule is [key, kind, required, default] |
| PerenosiMOST | maps exact Russian МОСТ spellings to canonical Reaper names and reports runtime/reserved/unknown status | alias row is [source, canonical, support] |
| MOST | exposes a stable public facade over PerenosiMOST and checks executable aliases | one Reaper grammar and runtime remain authoritative |
| Blau | returns immutable key/value snapshots, increments versions, performs compare-and-set and calculates diffs | snapshot is [version, entries] |
| Shashio | validates finite-state transitions, applies event sequences and provides all-or-nothing batch behavior | transition is [from_state, event, to_state] |
| Showel Fleppery CODE | builds validated transform pipelines, renders exact placeholders and returns an audit trail | step is [name, transform, validator] |

## Usage

The full integration exercise is in examples/frameworks_smoke.rpr. Run it from
the repository root:

    python -m reaper examples/frameworks_smoke.rpr

The automated test suite executes the same Reaper source through the reference
interpreter:

    python -m unittest tests.test_frameworks -v

## Per-framework behavior

### GalHero

A graph edge points from a node to a prerequisite. The order operation uses a
stable Kahn-style pass: a node is emitted only when all its prerequisites have
already been emitted. Invalid endpoints, self-dependencies and duplicate node
names are rejected. If no node can progress, the remaining nodes are returned
as a cycle report. Transitive dependency expansion is breadth-first and keeps
first-seen order.

### Call-and-Back

Registration is immutable: subscribe returns a new registry and an explicit
success/error tuple. Dispatch sorts matching handlers by ascending numeric
priority. The callback receives the same payload; its return value is collected.
A one-shot handler is omitted from the returned registry after dispatch.
call_chain passes each callback's return value into the next callback.
Execution is synchronous; no promise, thread or event-loop semantics are implied.

### Stacked Options

resolve merges defaults, profile, workspace and request layers in that order.
The right-most value wins. validate applies defaults from rules, checks required
keys and compares values using the runtime kind names: nothing, boolean, number,
text, list, map and craft. The no-default sentinel is nothing; an explicit null
value therefore cannot be distinguished from an omitted default in this v1
contract.

### PerenosiMOST and MOST

The alias table mirrors the repository's existing exact МОСТ manifest: 21
runtime aliases and 33 lexically reserved aliases. Unknown words are returned
unchanged. There is no stemming, inflection guessing, transliteration,
synonym lookup or identifier translation. Reserved aliases are reported as
reserved and are not presented as executable syntax.

MOST is a facade over the same table. It does not define a second language,
grammar, AST, runtime or backend.

### Blau

A snapshot contains a monotonically increasing version and a list of unique
key/value entries. write and apply return new snapshots. compare_and_set
commits only when the supplied version matches; otherwise it returns the
original snapshot and version-conflict. diff reports additions, changes and
removals. This module is a value-level local state primitive, not a durable
database or a thread-safe shared-memory service.

### Shashio

The state machine accepts explicit state and transition tables. Duplicate
source/event pairs are ambiguous and rejected during validation. run reports
the last successful state and event history when a transition fails.
apply_atomic returns the original initial state and an empty committed history
on failure, so callers never mistake a partial sequence for a committed batch.

### Showel Fleppery CODE

add_step accepts only Reaper crafts for both transform and validator. run
executes stages in their declared order and records [step, before, after]
entries. A rejected stage restores its input; the overall result reports the
original source as the rollback value. render replaces exact {{KEY}}
placeholders in the supplied order. The module does not write files, invoke a
shell, download dependencies or execute generated source.

## Scope and maturity

These are implemented source modules with an integration smoke example and an
automated reference-runtime test. They are not yet native C17 modules and do
not establish native compiler parity. Asynchronous callbacks, persistent
storage, concurrent state mutation, source-map-aware rewriting, filesystem
patch application and privileged capabilities remain outside this v1 scope.
