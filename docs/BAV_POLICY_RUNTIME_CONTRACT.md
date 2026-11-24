# Reaper policy runtime contract for DuckOS BAV

**Contract ID:** `reaper.bav-red-sparrow-policy.v1`  
**Canonical policy:** [DuckOS BAV Red Sparrow doctrine](https://github.com/Ivan-VHS/DuckOS/blob/main/security/bav/defender-doctrine.v1.json)  
**Status:** `specified` — no BAV evaluator, malware scanner, containment service or kernel enforcement is claimed.

## 1. Responsibility

Reaper is the intended deterministic/native policy-validation and evaluation path for DuckOS BAV. It may validate the canonical policy, normalize local text evidence, classify sensitive topic/context combinations and emit an auditable review record.

It must not become a weapon-system interface. BAV and Reaper do not design, construct, calculate, target, guide, launch, intercept or control weapons; do not connect to military networks or hardware; and do not make operational or use-of-force decisions.

## 2. Canonical input and compatibility

The DuckOS policy is the single source of truth:

- `security/bav/defender-doctrine.v1.json`
- `schemas/bav-defender-doctrine.v1.schema.json`

Consumers must validate the exact schema version and policy identifier before evaluation. OPlague may carry a byte-identical consumer copy for its local repository guard. Reaper must not maintain an independent, drifting term list.

Unknown schema versions, duplicate JSON keys, invalid UTF-8, malformed terms, unsupported decision values or violated hard-boundary constants produce a typed policy error. They do not trigger file deletion, process termination or automatic quarantine.

## 3. Evaluation semantics

For each bounded local text input, the evaluator may emit:

- `clear` — no actionable sensitive-topic combination was observed;
- `review` — a sensitive topic and non-negated actionable operational language occur together, so a human reviewer must inspect context;
- `error` — the policy or input could not be validated.

The evaluator must preserve these invariants:

1. A nuclear, military-equipment or air-defence term alone is not a finding.
2. A country, nationality or platform category alone is not a risk signal.
3. Historical, legal, humanitarian, safety, arms-control and non-proliferation context is not harmful intent by itself.
4. Sensitive topic plus non-negated operational construction/use/targeting/control language is a review candidate, not an automatic guilt verdict.
5. Defensive wording does not silently waive review when actionable operational instructions are present.
6. Negation and quoted prohibition language are recognized conservatively; ambiguous scope stays reviewable.
7. Automatic blocking and automatic quarantine remain disabled by this policy version.

No probabilistic author-intent inference is permitted. A classifier score may order review queues, but it must not be used as an autonomous verdict.

## 4. Data model target

The future native API should use typed, versioned records equivalent to:

| Record | Required meaning |
|---|---|
| `PolicyRef` | policy ID, semantic version, schema ID and canonical content hash |
| `LocalTextEvidence` | caller-provided path/label, bounded bytes, encoding and content hash |
| `TopicMatch` | category ID and normalized span location; no copied source text |
| `ContextEvidence` | matched intent/context/negation classes and line location |
| `ReviewRecord` | rule ID, severity, review state, path/line, policy hash and remediation |
| `DecisionRecord` | deterministic outcome, input hash, policy hash, evaluator version and request ID |

The eventual ABI must define integer widths, string encoding, ownership/lifetimes, buffer limits, error codes and forward/backward compatibility before implementation. Do not expose an unstable native ABI as production-ready.

## 5. Required runtime boundaries

- Local-only evaluation by default; no remote upload, background network lookup or third-party model call.
- Read-only input access; no source rewriting, command execution or dynamic plugin loading.
- Bounded file count, per-file size, total bytes, line length, recursion and execution time.
- Deterministic Unicode normalization and matching rules, versioned with the policy.
- Reports must not include entire source lines, secrets, credentials or unnecessary personal data.
- Audit records are append-only at the owning service boundary and include a request ID; they must not contain source payloads.
- Repeated evaluation of the same bytes, policy and evaluator version must produce the same semantic findings.
- Errors must preserve safe diagnostics without exposing internal secrets or untrusted control sequences.

The current Python reference runtime and partial native C17 compiler are not equivalent to a native BAV runtime. A Reaper implementation must be authored in Reaper for the DuckOS-native path, with native output parity tested against explicit contract fixtures; a Python prototype must not be presented as native integration.

## 6. Layered architecture target

1. **Policy validator:** schema/version validation, duplicate-key rejection and hard-boundary checks.
2. **Normalizer:** bounded UTF-8 processing and deterministic Unicode normalization.
3. **Topic classifier:** category IDs only; no weapon specifications or capability inference.
4. **Context evaluator:** operational-language, defensive-context, negation and quotation evidence.
5. **Evidence ledger:** hashes, paths, line numbers, policy/evaluator versions and request IDs.
6. **Review broker:** returns a review record to the authorized local BAV UI; it does not take destructive action.
7. **Future containment broker:** separate native DuckOS capability, disabled until a distinct threat policy, consent/authority model, audit and reversible recovery are independently specified and verified.

## 7. Acceptance tests before implementation can be promoted

- Valid canonical policy loads; malformed, duplicate-key, wrong-version and hard-boundary-violating policies fail closed without side effects.
- All policy categories are covered by fixtures in Russian and English.
- Topic-only, nationality-only, history-only and humanitarian examples produce `clear`.
- Sensitive topic plus actionable non-negated phrasing produces `review`.
- Negative/quoted prohibition examples do not become false accusations.
- A defensive marker does not suppress a co-occurring actionable instruction.
- Reports contain hashes and locations but no original source text or secrets.
- Limits are enforced before full buffering; symlink/path escape is rejected by the caller's file boundary.
- Repeated runs are deterministic and produce stable structured output.
- Native Reaper behavior is tested from Reaper-authored source and verified native build artifacts.
- No networking, shell execution, weapon-system control, targeting, launch or interception interfaces exist.

## 8. Maturity

This document specifies a future capability only. The Reaper repository currently has a Python reference runtime and a partial native C17 track. Neither is evidence of a completed native BAV policy engine. Promotion to `implemented` requires source, tests, a supported build target, registered contracts and a real DuckOS adapter. Promotion to `verified` requires reproducible acceptance evidence on the declared target.

