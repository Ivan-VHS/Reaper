# Documentation control

**Baseline date:** 2026-11-26 · **Scope:** root README locales, language reference, docs library, schemas, toolchain, ABI and federation material.

The [shared documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md) points to the canonical DAK policy and publication checklist.

## Repository-specific publication gates

| Gate | Acceptance |
|---|---|
| Language identity | Name Reaper, `.rpr` files, `::` composition and supported syntax consistently. |
| Runtime truth | Separate Python reference runtime, selectable IR/VM path, partial C17 implementation and self-hosting subset. |
| Toolchain | State exact Python/CMake/compiler/Node prerequisites per command. |
| Platform | Distinguish cross-platform CLI/runtime from Windows-only Studio. |
| Effects | Document filesystem, process, network, clock, shell and native FFI boundaries. |
| Resource safety | State quotas, but never call them a security sandbox. |
| Native hardware | MMIO adapter contracts are not physical memory mapping or device control. |
| Interop | Version JSON/schema/ABI interfaces and require explicit trusted native library paths. |
| Maturity | Distinguish specified, planned, partial, implemented and verified behavior. |
| Release | Keep Python package and CMake project versions separate; no unified version claim without evidence. |
| Navigation | Catalog all docs pages, link clusters and verify relative paths. |
| Localization | Keep EN/RU/UK/ZH-CN headings and technical facts aligned. |

## Required README review

1. Exact repository identity, concise positioning and compact metadata table.
2. Diagram or actual UI capture with truthful context.
3. Purpose, architecture, data flow, trade-offs and supported workflow.
4. Table of contents for long or multi-subsystem content.
5. Version and release history based on Git tags, manifests or published artifacts; do not merge package versions into one product version.
6. Stable/nightly/experimental/deprecated/EOL labels only when backed by repository evidence.
7. Explicit API/ABI/schema compatibility and migration notes.
8. Implemented, partial, specified and planned functionality shown separately.
9. Known limitations, unsupported environments and host/toolchain requirements.
10. Security boundaries for untrusted source, native libraries, MMIO and explicit effects.
11. Performance measurements with reproducible workload and environment; otherwise state no universal metric is claimed.
12. Separate navigation to API, architecture, examples, RFC/design docs and external standards.
13. Working internal/external links, dated citations and exact standard versions.
14. Contribution, issue, vulnerability disclosure and license references.
15. Third-party attribution and upstream license preservation.
16. Same-change documentation updates when syntax, flags, configuration, contracts or build commands change.
17. Clean-environment verification of onboarding commands.
18. Section-order and terminology parity across all supported README languages.

## Evidence and terminology

- **Specified:** contract exists, runtime behavior not claimed.
- **Planned:** accepted future work not implemented.
- **Partial:** tested subset exists; missing behavior is stated.
- **Implemented:** source behavior is connected to an executable workflow.
- **Verified:** acceptance criteria passed on a named platform/revision with recorded evidence.

A registry count is inventory, not completion. A passing reference-runtime test does not prove native C17 parity. A checked MMIO descriptor does not prove physical mapping. An execution quota does not isolate arbitrary code.

## Maintainer checklist

- [ ] Check code, tests, schemas, CMake and packaging manifests.
- [ ] Verify every changed command and local link.
- [ ] Keep all four README locales aligned.
- [ ] Update the information map and topic hub in the same pull request.
- [ ] Record breaking changes, compatibility effects and migration steps.
- [ ] Preserve license, author and third-party notices.
- [ ] Do not claim CI, benchmarks, audits or stable releases without artifacts.
