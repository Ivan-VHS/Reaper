# Experimental Language Workbench

## Execution model
1. Keystroke path: versioned document snapshots, incremental LSP edits and a tolerant structural scanner.
2. Background path: cancellable indexing; results publish only while their document version is current.
3. Execution path: compiler, test runner and debugger remain separate processes. A compiler failure cannot block editor input.

## Implemented foundation
- Lazy extension-to-plugin activation.
- UTF-16-aware incremental document edits and stale-version rejection.
- Error-tolerant delimiter diagnostics for unfinished buffers.
- Symbol index, fuzzy completion ranking, definition, references and identifier-validated rename edits.
- Minimal stdio JSON-RPC language server: initialize, open/change/close, completion, definition, references, rename and document symbols.
- DAP adapter backed by the existing RuntimeDebugger: launch, line breakpoints, continue/next/step-in, stack frames and local-variable snapshots.

## IDE integration
Launch the language server with python -m reaper.lsp and the debug adapter with python -m reaper.dap as separate subprocesses. Use UTF-8 Content-Length framing; stdout is protocol-only and logs belong on stderr. Register .rpr as language id reaper. Send monotonically increasing document versions. Compiler/type diagnostics are a slower separate phase.

## Explicit scope
This is a working integration foundation, not a full semantic compiler. Current indexing is per open document: no cross-file import graph, Git-branch workspace index, type inference, full AST selection, code actions, test discovery, or hot reload is claimed. Rename is limited to identifier tokens in the open document. DAP currently supports statement-boundary breakpoints and stepping, stack/local inspection and termination; conditional breakpoints, expression evaluation, step-out and pause-anywhere are not implemented. Native compiler interfaces remain unchanged.

## Validation
Run python -m unittest tests.test_language_service and the existing test suite.
