# REAPER toolchain, MOST evolution and IDE foundation

## Patch proposal pipeline

tools/reaper_patch.py creates reviewable patch proposals with a manifest,
base-file hashes, test plan and rollback metadata. It rejects unsafe paths,
checks integrity and requires explicit human review before apply or rollback.

## MOST language evolution

language/features.json is the machine-readable capability registry. Stable
IDs, explicit statuses, dependency edges and acceptance gates prevent
duplicate proposals and dependency cycles. Planned and specified entries are
not represented as implemented compiler features.

## REAPER IDE and AST inspection

The native CLI now supports --ast-json for one expression. It emits
deterministic JSON with node IDs, kinds, text, child references and source
locations. The serializer validates the complete AST before output, escapes
JSON control characters and rejects invalid child references. This is a
compiler-owned inspection interface for editor tooling, not a replacement
parser or language server.

The VS Code starter provides file association, indentation, comments and
syntax highlighting. A semantic language server is the next boundary and
must consume compiler-owned AST/typed-IR data rather than reimplement rules.

Debugger and profiler integration must wait for executable generation,
source maps, stable runtime inspection and a target process protocol.

## Bootstrap and self-hosting

scripts/bootstrap_check.py verifies repeatable native compiler version and
lexer-smoke output. This is a reproducibility preflight only. The compiler
cannot yet compile its own implementation; self-hosting is not claimed.

A genuine self-hosting gate requires stage-0 to build stage-1, stage-1 to
build stage-2, deterministic artifact comparison, full semantic/backend tests
and a clean-environment bootstrap.

## Validation

    cmake -S . -B build && cmake --build build --parallel
    ctest --test-dir build --output-on-failure


## Verified pull-request automation

.github/workflows/reaper-verified-pr.yml is a manual, review-gated PR creation
workflow. It accepts only an existing feat/*, fix/* or docs/* candidate branch,
requires the candidate to contain the current main commit, and rejects empty
changes or an already-open PR for that head. It then runs the Python tests,
language-example checks, native C17 build and native test suite before opening
a **draft** pull request. The workflow has read-only contents permission and
pull-request creation permission only; it never pushes code, enables auto-merge
or merges a pull request.
