# Mental Wellbeing & Depression Awareness v1 — Code Safety Standard

**Policy ID:** `mental-wellbeing-code-safety.v1`  
**Applies to:** Reaper language, Python reference runtime, native C17 track, Studio, LSP/DAP and plugin services  
**Status:** Engineering guardrails; not a clinical protocol

## Why this exists

This standard translates the non-stigmatizing, help-seeking and self-care themes in the supplied *Mental Wellbeing & Depression Awareness v1* material into engineering safeguards. The supplied transcript includes only opening and closing segments; its missing middle is not reconstructed. Personal stories, the sponsor segment, timestamps and the quoted prevalence figure are not clinical evidence or executable rules.

Reaper is a programming language and developer toolchain, not a mental-health product. It must not diagnose, screen, score, infer or retain a user's psychological state.

## Non-negotiable safeguards

- **No diagnosis or inference:** never infer depression, distress, motivation, disability or psychological traits from code, syntax errors, typing cadence, debugging sessions, editor activity, execution time or plugin usage.
- **No medical advice:** do not recommend medication, treatment, dosage, therapy or clinical decisions. Do not convert language diagnostics or runtime exceptions into mental-health assessments.
- **No sensitive telemetry:** do not transmit source code, LSP/DAP messages, debug locals, stack frames, editor contents, personal logs or wellbeing-related text. Any future optional telemetry requires separate, informed opt-in and documented retention/deletion controls.
- **Untrusted program boundary:** source files, imported modules, plugin manifests, LSP/DAP payloads and FFI arguments are untrusted input. Parsing is not permission to execute.
- **Runtime limits:** preserve execution, heap, file and recursion quotas; deterministic cleanup; bounded parser and protocol inputs; explicit capability checks.
- **Native loading:** FFI libraries remain opt-in and require an explicit trusted path. No implicit library discovery, remote download or manifest-triggered code execution.
- **Honest sandbox boundary:** do not describe the interpreter, debugger or plugin host as an OS security sandbox unless a separately tested OS-level isolation layer exists.
- **Respectful tooling:** diagnostics identify code locations and corrective steps, never characterize the author. Avoid shame-based copy and coercive productivity mechanics.
- **Blameless engineering:** incident reports focus on failure modes and remediation, not a developer's mental state or personal fault.

## Reaper-specific threat model

| Surface | Required protection |
|---|---|
| Lexer / parser / AST / IR / VM | Bound source size, token count, nesting and execution work; reject malformed input safely |
| Runtime / modules | Keep quotas and deterministic cleanup; do not silently execute imports during inspection |
| LSP / DAP | Bound message sizes; avoid logging source text, locals, paths or stack values by default |
| Plugin host / Kora | Metadata discovery is not execution; handlers require explicit registration and lifecycle control |
| Python / C17 / FFI | Preserve explicit trust boundaries; validate arguments and buffer lengths; never claim full native parity prematurely |
| Studio | No keystroke, mood, health or productivity monitoring; keep user-controlled diagnostics and accessible recovery |

## Change acceptance checklist

A change touching execution, parsing, modules, protocols, plugins, FFI, editor telemetry or diagnostics is ready only when:

1. Untrusted input is bounded and rejected safely; inspection does not trigger execution.
2. Quotas, cleanup and explicit native-library trust remain in force.
3. No sensitive content or mental-health inference is collected, logged or transmitted.
4. Diagnostics are factual, actionable and non-stigmatizing.
5. Protocol and runtime tests cover malformed, oversized and boundary input.
6. Python tests and applicable C17/native tests pass; documented capability maturity remains accurate.

## Automated enforcement

`mental-wellbeing-code-safety.v1.json` is the machine-readable policy contract.  
`scripts/check_mental_wellbeing_guardrails.py` validates required prohibitions, Reaper-specific runtime boundaries and this document. The dedicated GitHub Actions workflow runs the validator on pushes and pull requests. The gate checks policy integrity; it does not replace runtime fuzzing, security review or OS-level isolation.

## Scope and limitations

This standard does not create a clinical feature. It is not diagnosis, screening, counselling, crisis response or treatment guidance. Reaper must not present its language services or execution data as a substitute for a qualified healthcare professional.
