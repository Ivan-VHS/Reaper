# BAV — unified Java/Reaper security system

**Product name:** BAV (Beelzebul Antivirus for Reaper)  
**Report contract:** `bav.security.report.v1`  
**Java baseline:** JDK 17  
**Canonical policy:** `security/beelzebul.v1.json`

BAV combines the repository's existing 66-rule Beelzebul policy engine with a new Java Guard and a first-party Reaper command. It produces one deterministic report and one final verdict while retaining the origin of each finding.

## Architecture

```text
reaper security scan
        |
        v
Reaper BAV adapter (reaper/bav.py)
        |
        +-------------------------------+
        |                               |
        v                               v
Beelzebul policy engine             BAV Java Guard
tools/beelzebul.py                  JDK-only static scanner
66 canonical rules                  Java + text integrity checks
        |                               |
        +---------------+---------------+
                        |
                        v
             deterministic report merge
             schemas/bav.security.report.v1
                        |
                        v
               blocked / review / clear
```

### 1. Canonical Beelzebul policy

The existing `security/beelzebul.v1.json` remains the single source of truth for 66 repository rules (15 + 15 + 15 + 15 + 6). Its policy schema, severity, enforcement, exceptions and limits are not copied into a second mutable Java catalogue.

The existing scanner remains responsible for repository-wide checks such as secrets, path metadata, unsafe dynamic execution, dependency changes, workflow isolation, CI policy, change correlation, rule coherence and governance signals.

### 2. Java Guard

The Java component is implemented using the JDK standard library only. It has no third-party runtime dependency, does not load classes from the inspected project and does not execute application code. Its source is shipped inside the `reaper` Python package at `reaper/java/src/main/java/org/ivanvhs/bav/Bav.java`, so the guard remains available from an installed wheel rather than only from a source checkout. It walks without following symbolic links, applies deterministic ordering, enforces bounded file/byte limits, decodes UTF-8 strictly, redacts credential values and emits JSON.

Supplementary Java checks:

| Rule | Coverage | Default action |
|---|---|---|
| `BAV-J-001` | Credential prefixes, private-key markers and secret-like assignments | Critical block |
| `BAV-J-002` | `Runtime.exec` and `ProcessBuilder` use | High review |
| `BAV-J-003` | Java native object deserialization | High review |
| `BAV-J-004` | XML parser factory use without visible external-entity hardening | High review |
| `BAV-J-005` | Trust-all or empty TLS peer verification | High review |
| `BAV-J-006` | Weak digest and unauthenticated/weak cipher selection | High review |
| `BAV-J-007` | SQL statement construction with string concatenation | High review |
| `BAV-J-008` | Path integrity, unsafe archive-entry resolution and source-format anomalies | High review |

These are conservative static heuristics, not proofs of exploitability. A finding requires human review where the rule says `review`; it is not silently promoted to a critical verdict.

### 3. Reaper integration

The Reaper CLI exposes the complete system as one command:

```sh
python -m reaper security scan --root . --policy security/beelzebul.v1.json
```

Machine-readable report, written atomically:

```sh
python -m reaper security scan --root . --policy security/beelzebul.v1.json \
  --json --output bav-report.json
```

Review of changes relative to a base commit:

```sh
python -m reaper security scan --root . --base-ref origin/main --json
```

Exit status:

- `0`: `clear`, or `review` in normal mode.
- `1`: `review` when `--strict-review` is enabled.
- `2`: `blocked`, invalid policy, unavailable engine or execution failure.

The adapter compiles the Java scanner into a temporary directory and removes it after execution. It uses argument vectors (never a shell), a minimalized child-process environment, bounded timeouts and no stdin. It then runs the canonical Beelzebul scanner and merges both reports. A failed/missing engine is an error, not a partial green scan.

### 4. Reaper Capability Forge

The Reaper extension host now uses `reaper/capabilities.py` for application-level object capabilities:

- Raw request mappings are parsed into immutable `CapabilityRequest` objects; principal, resource and action values pass explicit taint/refinement parsing before they reach the authority.
- Grants are HMAC-SHA-256 authenticated, bound to one authority, one principal, one canonical resource subtree and a finite action set. Tokens are opaque, signatures are redacted from representations, and tokens deliberately cannot be serialized.
- Every grant has a bounded lifetime (15 minutes by default for an individual request, one hour for built-in plugin grants by host policy), and the authority enforces a configurable active-token ceiling.
- The authority supports token revocation, principal-wide revocation and global revocation. Expiry is purged during verification and active-count inspection.
- Authorization checks use constant-time signature comparison and segment-bounded resource matching. A plugin cannot access a sibling resource by exploiting a textual prefix such as `plugins/app` versus `plugins/application`.
- `PluginManager` issues each built-in plugin a separate principal/resource grant, requires both `invoke` and the plugin's registered primary operation, and revokes the grant when the plugin is disabled. Expired or externally revoked grants fail closed.
- A protected plugin operation and revocation are serialized by the authority lock: once a revocation call returns, that grant cannot authorize a later operation. Plugin host state is also protected by a reentrant lock.

This is a real Reaper host authorization boundary for the built-in plugin dispatch path. It is **not** an OS process sandbox: it does not confine arbitrary Python code, other direct in-process calls, filesystem access outside the plugin host, native FFI, network sockets or child processes. The signing key is ephemeral and process-local by default; durable cross-process tokens and managed key rotation are not part of this increment.

### 5. Unified report semantics

The report schema is versioned at `schemas/bav.security.report.v1.schema.json`. Each finding preserves `rule_id`, `severity`, `enforcement`, `path`, `line`, `message` and `remediation`, plus a `component` field identifying its scanner.

Verdict precedence is monotonic:

1. Any component reporting `blocked` makes BAV `blocked`.
2. Otherwise any finding or component reporting `review` makes BAV `review`.
3. Only two clear components with no findings produce `clear`.

The unified risk score is the maximum of the component scores, not a sum; this avoids double-counting the same underlying exposure when both scanners observe it. All distinct findings remain in the report.

### 6. Safety and maturity boundaries

BAV is a repository/source security scanner and CI gate. It is **not yet** a general-purpose endpoint antivirus, kernel anti-malware driver, firewall, runtime EDR, process monitor, malware-signature cloud, disk quarantine service or operating-system sandbox. It does not claim to deliver those capabilities.

The existing Reaper C capability registry and its `Kali` module are not re-labelled as an OS sandbox. OS-level process isolation, kernel enforcement, native FFI confinement, secure secret storage, durable managed key rotation, filesystem encryption and native process containment still require separate runtime/OS implementations and dedicated integration tests. The application-level plugin grants do not replace those controls.

The scanner itself is read-only with respect to inspected source. The optional `--output` path is the only intentional report write. CI runs with read-only repository permissions and does not grant scanned pull-request code access to secrets.

## Verification

The BAV workflow validates the existing policy contract, runs the original Beelzebul regression suite, compiles and executes the Java self-test under JDK 17, runs the capability-authority, plugin-host and Reaper adapter tests, and finally executes the unified scan. The self-test verifies Java-specific detections, secret redaction and non-mutation of inspected files.
