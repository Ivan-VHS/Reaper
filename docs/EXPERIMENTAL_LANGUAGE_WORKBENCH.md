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

## IDE integration
Launch with python -m reaper.lsp as a subprocess. Use UTF-8 Content-Length framing; stdout is protocol-only and logs belong on stderr. Register .rpr as language id reaper. Send monotonically increasing document versions. Compiler/type diagnostics are a slower separate phase.

## Explicit scope
This is a working integration foundation, not a full semantic compiler. Current indexing is per open document: no cross-file import graph, Git-branch workspace index, type inference, full AST selection, code actions, DAP, test discovery, or hot reload is claimed. Rename is limited to identifier tokens in the open document. DAP must later map VM source spans to the same zero-based UTF-16 positions. Native compiler interfaces remain unchanged.

## Validation
Run python -m unittest tests.test_language_service and the existing test suite.
