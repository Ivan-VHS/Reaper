# REAPER IDE and language tooling

## Implemented protocol slice

Two dependency-free stdio services are included:

- **LSP:** initialize/shutdown, UTF-16 incremental document changes, version checks, parser and tolerant-structure diagnostics, background symbol indexing, fuzzy completion, hover, definition/reference lookup, rename edits and document symbols.
- **DAP:** launch a trusted local .rpr file, line breakpoints, continue/next/step-in, stack frame, local-variable inspection and termination. It reuses the existing RuntimeDebugger statement-boundary hook.

Run from the repository root:

```sh
python -m reaper lsp
python -m reaper dap
python -m unittest tests.test_ide_protocols -v
```

Both services use Content-Length framed JSON-RPC over stdin/stdout. Stdout is reserved for protocol frames.

## Capability and maturity

| Capability | State | Contract |
|---|---|---|
| LSP transport | Implemented | JSON-RPC 2.0, Content-Length framing |
| Parser diagnostics | Implemented | Existing REAPER lexer/parser; no second grammar |
| Completion / hover | Implemented | Canonical keywords, aliases and bounded built-ins |
| Definition / references / rename | Basic | Lexical identifier matching, not semantic resolution |
| Document symbols | Basic | Indexed make, vary, craft and supported type declarations |
| DAP transport | Implemented | Framed request/response/events |
| Breakpoints and stepping | Implemented | Statement-boundary debugger; next and step-in share granularity |
| Stack and locals | Implemented | Existing runtime debugger snapshots |
| Conditional breakpoints / evaluate / step-out | Not implemented | Not advertised as supported |
| Type inference, semantic graph, incremental AST | Planned | Requires canonical type/IR APIs |
| Native C17 language service | Planned | Python remains the compatibility reference |
| Coverage, profiler UI, test explorer, integrated Git UI | Planned | Requires stable data contracts |

## Architecture

```text
VS Code / REAPER Studio
   | LSP JSON-RPC                    | DAP JSON-RPC
   v                                 v
reaper.lsp                        reaper.dap
   |                                 |
lexer + parser                    RuntimeDebugger
   |                                 |
parser diagnostics                Interpreter
   +---------------+-----------------+
                   |
             REAPER language core
```

LSP advertises only implemented handlers. Document edits use UTF-16 positions and monotonically increasing versions; stale edits are rejected. A cancellable background index publishes only results for the current snapshot. The index is per open document and lexical: cross-file semantic resolution, type inference, semantic tokens and AST refactoring remain future work. DAP does not evaluate arbitrary host-language expressions or create an OS sandbox. Launch only trusted local programs.

## Design constraints

- REAPER owns syntax and semantics; MOST aliases come from the canonical lexer.
- Python is the compatibility oracle. Native C17 parity is not implied.
- IDE features grant no hidden filesystem, network, shell, FFI or hardware permission.
- Protocol stdout is machine-only; logs belong on stderr.
- A capability is shipped only when its handler and regression tests exist.
