# Repository Security Assurance v2

## Coverage

The federated assurance workflow audits tracked source and configuration files of **Pytyliki, Reaper, OPlague and VentuSample**. It does not execute inspected source during static scanning. Findings contain rule ID, severity, repository-relative path and line number only; secret values and source snippets are never included.

### Automated controls

- **Source audit:** high-confidence private-key/token patterns, hard-coded credential assignments, local developer paths, sensitive-value logging and selected risky APIs.
- **CodeQL:** Python, C/C++ native-track and GitHub Actions source analysis with the extended query suite.
- **Dependency review:** GitHub dependency-review gate on pull requests, Dependabot for Actions and Python packages, and an offline inventory of manifests, lockfiles and exact pins.
- **Fuzz smoke:** the production Reaper tokenize and parse functions receive deterministic bounded malformed, Unicode, nested and valid program samples. Only expected lexical/parser errors are accepted as safe rejection.
- **Privacy regression:** synthetic-token detection, placeholder handling, finding redaction and contract prohibitions are tested.
- **Federation:** all four checkouts are inspected; common policy/tool checksums are compared; actual tracked source and dependency declarations are scanned per repository.

## Run locally

1. Run scripts/security_audit.py and scripts/dependency_audit.py to create reports.
2. Run scripts/test_privacy_regressions.py.
3. Run python -m compileall -q reaper tests scripts.
4. Run scripts/fuzz_smoke.py.
5. Run python -m unittest discover -s tests -v.

The fuzz harness uses a fixed seed and caps every input at 2 KiB and token output at 4096. Runtime behavior, quota tests and native C17 tests remain separate gates in existing CI.

## Shared score

Every repository uses identical 100-point weights:

| Category | Weight |
|---|---:|
| Secret hygiene | 25 |
| Privacy leak prevention | 15 |
| Source-risk review | 15 |
| Fuzz robustness | 15 |
| Dependency pin hygiene | 10 |
| Privacy regressions | 10 |
| Federation consistency | 10 |

The federated report calculates an additional cross-repository score from policy/tool parity, aggregate source findings and dependency pin hygiene. The gate fails on critical secret findings, failed fuzz/privacy/federation checks or a score below 70.

## Boundaries

The pattern scanner is heuristic and does not prove safe execution. CodeQL supplements it with language-aware analysis. Dependency inventory and pin checks are offline; GitHub Dependency Review covers supported PR dependency changes but does not guarantee that every transitive or system package is vulnerability-free. The fixed fuzz corpus is smoke fuzzing, not continuous coverage-guided fuzzing. The Python interpreter and native FFI remain subject to their existing trust boundaries; this workflow does not claim OS sandboxing.
