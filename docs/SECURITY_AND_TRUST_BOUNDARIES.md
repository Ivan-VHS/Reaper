# Security and trust boundaries — Reaper

## Scope and current runtime status

Reaper is an expression-oriented language and development environment. The Python runtime remains the current executable compatibility reference; the C17 track is partial and must not be described as full parity. Interpreter quotas constrain language-level work but are not an operating-system sandbox.

## Assets and trust boundaries

| Boundary | Untrusted material | Required handling |
|---|---|---|
| Lexer / parser | source text, tokens, nesting | bounded input, explicit diagnostics, no implicit evaluation during parsing |
| AST / modules | imported module content and names | validate identifiers and module resolution; avoid path escape |
| Interpreter | expressions, recursion, loops | deterministic quotas, cancellation and bounded diagnostics |
| Host effects | filesystem, console, network, shell and subprocess requests | explicit capability/effect API; deny absent grants |
| FFI / native adapters | library path, ABI, native calls | explicit trusted path and ABI checks; document host-process privileges |
| LSP / DAP | editor protocol messages and document contents | validate framing, sizes, IDs and state transitions |
| Node.js bridge | JS project and runtime commands | use official runtime selection; keep process launch explicit and observable |

## Effect and privilege policy

Filesystem, network, shell, subprocess and native-code operations are privileged host effects. They must not become available merely because a program can name an API. Each effect needs an explicit host-side grant, bounded arguments, auditable result and deterministic denial path.

FFI executes with the permissions of the Reaper host process unless a separately configured OS sandbox is demonstrated. Do not call interpreter quotas, a plugin lifecycle state or a UI warning a sandbox.

## Failure behavior

Malformed source and protocol input must produce bounded errors, not interpreter crashes or unbounded memory growth. Quota exhaustion and cancellation must stop the active evaluation predictably. An unavailable host capability must return a typed denial; it must not silently fall back to shell, network or a broader filesystem scope.

## Verification evidence

For changes to language or host boundaries, add:
1. parser tests for malformed, deeply nested and oversized source;
2. interpreter tests for recursion, instruction/time quotas and cancellation;
3. effect tests proving denied operations have no side effect;
4. protocol tests for malformed LSP/DAP messages and document lifecycle;
5. FFI tests for ABI mismatch and explicit library selection;
6. differential tests before claiming Python/C17 semantic parity.

Run the AppGuard catalog checks:

```sh
python scripts/validate_beelzebul_appguard.py
python -m unittest discover -s tests -p "test_beelzebul_appguard.py" -v
```

These validate the AppGuard inventory only. They do not establish OS isolation, full C17 parity or security of arbitrary native libraries.

## AppGuard status vocabulary

- **planned** — catalogued; no executable enforcement claim.
- **partial** — a named subset is implemented and evidenced.
- **implemented** — enforcement code and focused tests exist.
- **verified** — implementation, tests and review evidence are linked.

The current AppGuard change adds a catalog, schema, validator, tests and CI. It does not activate all 666 controls.

## Change and release checklist

- Update syntax, runtime, effect and compatibility docs when semantics change.
- Mark Python reference behavior and C17 parity separately.
- Include exact quota defaults and protocol limits in docs and tests.
- Keep examples runnable on the documented runtime.
- Never imply that IDE completion, static analysis or quotas provide OS-level containment.
