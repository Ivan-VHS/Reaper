# REAPER toolchain, MOST evolution and IDE foundation

## Patch proposal pipeline

tools/reaper_patch.py creates a reviewable proposal directory containing a
unified patch and JSON manifest. The manifest pins the patch digest, base
content hashes, changed paths, test plan and rollback policy.

    python3 tools/reaper_patch.py --repo . propose --base main --head feature-branch --out .reaper/proposals/example
    python3 tools/reaper_patch.py --repo . verify .reaper/proposals/example
    # After human review only:
    python3 tools/reaper_patch.py --repo . apply .reaper/proposals/example
    python3 tools/reaper_patch.py --repo . rollback .reaper/proposals/example

The tool never executes commands from a proposal manifest. It uses fixed Git
operations, rejects path traversal and .git targets, checks patch integrity,
checks base-file hashes, and runs git apply --check before applying or
reversing. It does not commit, push, merge or silently execute the test plan.
Tests are invoked separately by CI or a reviewer.

## MOST language evolution

language/features.json is the initial machine-readable capability registry.
Stable IDs, explicit statuses, dependency edges and acceptance gates prevent
duplicate proposals and cycles. The validator rejects unknown dependencies,
duplicate IDs, invalid statuses and cyclic graphs.

Statuses: planned (proposal only), specified (contract exists), implemented
(executable implementation and tests exist), verified (feature-specific gates
passed), deprecated (retained for compatibility, not recommended).

Current entries do not claim that syntax, types, effects, regions or standard
library APIs are implemented in the compiler.

## REAPER IDE

editors/vscode supplies file association, brackets, indentation, comments,
strings and syntax highlighting. It is not a full IDE. A language server is
the next boundary: versioned JSON-RPC for diagnostics, completion, hover,
definition, references, rename, document symbols and semantic tokens. It must
consume compiler-owned AST/typed-IR data rather than reimplement semantics.

Debugger and profiler integration must wait for executable generation, source
maps, stable runtime inspection and a target process protocol.

## Bootstrap and self-hosting

scripts/bootstrap_check.py verifies repeatable native compiler version and
lexer-smoke output. This is a bootstrap reproducibility preflight only. The
current compiler cannot compile its own implementation; REAPER is not
self-hosting yet.

A genuine self-hosting acceptance sequence:
1. C17 stage-0 compiler builds the MOST stage-1 compiler.
2. Stage-1 compiles the same MOST compiler sources into stage-2.
3. Stage-1 and stage-2 outputs pass deterministic artifact comparison.
4. Both stages pass parser, semantic, IR, backend and runtime suites.
5. A clean environment repeats bootstrap without generated workspace files.

## Validation

    python3 -m unittest discover -s tests -p 'test_patch_pipeline.py'
    python3 -m unittest discover -s tests -p 'test_feature_registry.py'
    python3 tools/validate_features.py language/features.json
    python3 scripts/bootstrap_check.py --compiler build/reaper-c
    cmake -S . -B build && cmake --build build --parallel && ctest --test-dir build --output-on-failure
