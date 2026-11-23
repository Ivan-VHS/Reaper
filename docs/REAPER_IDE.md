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
| Definition / references | Workspace lexical | Across currently open documents; not semantic resolution |
| Rename | Basic | Current-document lexical edits after client confirmation |
| Workspace symbols | Implemented | Bounded search across open buffers only |
| Document symbols | Basic | Indexed make, vary, craft and supported type declarations |
| DAP transport | Implemented | Framed request/response/events |
| Breakpoints and stepping | Implemented | Statement-boundary debugger; next and step-in share granularity |
| Stack and locals | Implemented | Existing runtime debugger snapshots |
| Conditional breakpoints / evaluate / step-out | Not implemented | Not advertised as supported |
| Type inference, semantic graph, incremental AST | Planned | Requires canonical type/IR APIs |
| Native C17 language service | Planned | Python remains the compatibility reference |
| Coverage, profiler UI, test explorer, integrated Git UI | Planned | Requires stable data contracts |

## Reaper Studio editor integration

The Windows Studio editor also reuses the canonical `LanguageService` directly:

- **Ctrl+Space** opens local completion for REAPER keywords, built-ins and symbols in the current document.
- **F12** navigates to a declaration in that document.
- **Find references** highlights lexical occurrences and lists their line/column positions.
- **Ctrl+Shift+R** renames lexical occurrences in the current document after a confirmation prompt.
- **Ctrl+K** opens the existing command palette; **Ctrl+Alt+K** opens the CODEX-66 capability browser.

F12, Find references and workspace-symbol search can inspect all currently open buffers (up to 512 documents and 8 million characters). Results remain lexical: they do not provide cross-file type resolution, disk crawling, AST-safe refactoring, cloud AI generation, or an automatic code execution step. Rename remains limited to the current document. JavaScript files continue to use NOO TAH rather than the REAPER language completion service. The CODEX-66 catalogue labels each feature as implemented, partial, planned or unsupported and exports a versioned JSON snapshot; exporting does not activate any feature.

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

LSP advertises only implemented handlers. Document edits use UTF-16 positions and monotonically increasing versions; stale edits are rejected. A cancellable background index publishes only results for the current snapshot. The index is per open document and lexical. Workspace symbol lookup and navigation aggregate those open-document indexes under explicit document/character limits; disk crawling, cross-file semantic resolution, type inference, semantic tokens and AST refactoring remain future work. DAP does not evaluate arbitrary host-language expressions or create an OS sandbox. Launch only trusted local programs.

## Design constraints

- REAPER owns syntax and semantics; MOST aliases come from the canonical lexer.
- Python is the compatibility oracle. Native C17 parity is not implied.
- IDE features grant no hidden filesystem, network, shell, FFI or hardware permission.
- Protocol stdout is machine-only; logs belong on stderr.
- A capability is shipped only when its handler and regression tests exist.


## Systems and hardware workspace roadmap

Reaper Studio is being reoriented around firmware and systems projects. The existing editor, command palette, LSP and DAP remain the current desktop foundation; the hardware panels below are roadmap capabilities unless explicitly marked otherwise.

| Workspace area | Intended behavior | Maturity |
|---|---|---|
| Target and board profiles | target triple, CPU features, ABI, memory regions, linker script and toolchain fingerprint | planned |
| Hardware manifest | typed peripheral/register metadata, address space, width, endian, reset value and access policy | planned |
| Memory map | Flash/SRAM/ROM/MMIO/reserved ranges, section placement and overlap diagnostics | planned |
| Compiler inspector | typed IR, CFG, ownership/effect view, assembly/object output and source mapping | planned |
| Resource budgets | stack, heap, static sections, interrupt stack and DMA region budgets | planned |
| Simulator and debugger | QEMU/vendor simulator launch, register views, memory inspection and probe-specific debug adapters | planned |
| Hardware authorization | explicit per-project capabilities, adapter identity, privilege boundary and auditable actions | planned |
| MMIO descriptor API | checked C descriptors and callback dispatch with fake-bus tests | implemented native C API; no physical mapping |

Do not present target selection, live register inspection, firmware flashing, or physical-device debugging as shipped Studio features until each has a working adapter and automated/manual qualification evidence. The desktop must show when a feature is simulated, delegated to a platform tool, experimental or unavailable.
