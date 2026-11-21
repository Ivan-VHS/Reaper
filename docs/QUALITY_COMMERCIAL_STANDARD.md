# Quality, execution and commercial readiness

## Scope

Reaper is a flow-first programming language and developer workstation with a Python reference runtime, a developing native C17 implementation, explicit integrations and Windows Studio. This 20 × 3 matrix applies the supplied vocabulary to correctness, operational cohesion and commercial governance without overstating implementation status.

## Axis interpretation

- **Quality** covers language correctness, bounded behavior, diagnostics, security boundaries and verifiable implementation evidence.
- **Execution** covers operational cohesion: consistent semantics, stable interfaces, controlled builds, repeatable workflows and aligned documentation. “Monolithic” means one coherent user journey and contract, not one large source module.
- **Commercial** covers product positioning, licensing, packaging, support, user validation, costs and any future pricing decision. Commercial words in the matrix are control themes, not claims that revenue, profit or market demand already exist.

## 20 × 3 control matrix

| # | Quality | Execution | Commercial | Acceptance intent |
|---:|---|---|---|---|
| 1 | Качественность | Качество | Коммерческий | Every implemented language capability has an explicit acceptance condition and source/test evidence. |
| 2 | Добротность | Добротность | Торговый | Runtime resource accounting and deterministic cleanup bound program execution. |
| 3 | Безупречность | Безупречность | Предпринимательский | Invalid language inputs and denied effects fail with controlled diagnostics. |
| 4 | Совершенство | Совершенство | Рыночный | Release claims reflect the tested reference runtime and explicitly bounded native implementation. |
| 5 | Цельность | Мастерство | Деловой | Lexer, parser, runtime, modules and developer tools form one coherent language workflow. |
| 6 | Целостность | Профессионализм | Финансовый | Federated inputs and trusted native-library calls preserve explicit evidence and trust boundaries. |
| 7 | Монолитность | Надёжность | Прибыльный | Execution quotas, resource tracking and diagnostics keep supported workloads bounded. |
| 8 | Согласованность | Основательность | Доходный | Runtime decisions and integrations remain traceable to documented language and project contracts. |
| 9 | Последовательность | Гармоничность | Экономический | The same program, engine selection and inputs have deterministic documented behavior within the runtime contract. |
| 10 | Системность | Согласованность | Хозяйственный | FFI, process and filesystem boundaries are explicit and are not presented as an untrusted-code sandbox. |
| 11 | Структурированность | Цельность | Бизнесовый | Public modules and developer workflows have clear ownership and integration surfaces. |
| 12 | Упорядоченность | Целостность | Маркетинговый | Public documentation explains the language audience, supported workflow and current implementation limits. |
| 13 | Непротиворечивость | Монолитность | Клиентский | Language specification, examples, runtime and diagnostics share one canonical semantic contract. |
| 14 | Однородность | Нераздельность | Сбытовой | Installation, CLI execution, checks and Studio entry point form a consistent first-run path. |
| 15 | Унификация | Единство | Промышленный | Cross-project exchange uses versioned JSON and explicit FFI contracts, not private runtime layouts. |
| 16 | Стандартизация | Слаженность | Корпоративный | Source, Windows desktop packaging and CI use documented build and verification steps. |
| 17 | Полнота | Ритмичность | Инвестиционный | Capability status distinguishes implemented features, partial native work and future proposals. |
| 18 | Точность | Размеренность | Монетизируемый | Runtime limits and toolchain requirements are published without unsupported performance or cost promises. |
| 19 | Выверенность | Синхронность | Рентабельный | Specification, tests, packaging metadata and release documentation are updated consistently. |
| 20 | Профессионализм | Упорядоченность | Капитализированный | License, package metadata, source contents and release assets have an identifiable distribution boundary. |

## Evaluation

The root profile **quality-commercial.v1.json** records all 60 axis controls and links each control to repository-local evidence. Run:

```bash
python tools/quality_commercial.py
python tools/quality_commercial.py --format json
python -m unittest discover -s tests -p test_quality_commercial.py -v
```

The evaluator checks profile shape and referenced file presence; the regression tests check missing evidence, path traversal, vocabulary preservation and action-plan ordering. Evidence-file presence is not proof that a linked test has executed successfully.

Maturity is declared per control: **implemented** = evidence-backed implementation; **planned** = proposed and weighted at 25%; **not_assessed** = zero credit pending evidence; **not_applicable** = excluded from the denominator. These are transparent bookkeeping weights, not a certification score.

## Commercial action gates

The evaluator converts open commercial fields into a prioritized next-step list:

- **P0 — Licensing:** review the Apache-2.0 distribution obligations, bundled dependencies, notices and third-party materials before making commercial redistribution claims.
- **P1 — Support and delivery:** define maintenance ownership, supported versions, issue intake, release artifacts and reproducible installation. No response-time SLA is implied.
- **P2 — Demand and economics:** gather actual developer workflow feedback and measure build, distribution, dependency and maintenance costs.
- **P3 — Pricing:** make no pricing claim until user value, rights, operating costs and support scope have been assessed.

The current public posture is open-source distribution under the checked-in Apache License 2.0. Pricing is not set; paid support is not offered; market validation and unit economics are not assessed. This profile does not imply revenue, profit, investment readiness or customer adoption.

## Product and safety boundaries

- Python remains the compatibility reference until native C17 parity is demonstrated.
- The native C17 track is not yet a complete interpreter.
- Runtime quotas and resource accounting are guardrails, not a security sandbox for arbitrary untrusted programs.
- Native FFI runs trusted ABI-compatible code in-process; loading is explicit and must not be represented as sandboxed execution.
- Filesystem, process, network, clock, shell and external-tool effects remain subject to their documented opt-in boundaries.
- MOST registry proposals and reserved keywords are not counted as implemented language functionality.

Commercial copy and release notes MUST preserve these limits. Market, revenue, margin and willingness-to-pay statements require independent evidence.
