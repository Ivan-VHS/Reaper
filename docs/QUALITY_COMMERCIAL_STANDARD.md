# Quality, execution and commercial readiness

## Scope

Reaper is a flow-first language with a Python reference runtime, developing native C17 core, editor integration and developer tools. This matrix turns the supplied term triplets into testable engineering and product-governance controls.

## 20 × 3 control matrix

| # | Quality | Execution | Commercial | Acceptance intent |
|---:|---|---|---|---|
| 1 | Качественность | Качество | Коммерческий | Приёмка каждой языковой функции опирается на критерии и проверяемые результаты. |
| 2 | Добротность | Добротность | Торговый | Долговечность обеспечивается квотами, управлением ресурсами и безопасным отказом. |
| 3 | Безупречность | Безупречность | Предпринимательский | Опасные и неоднозначные действия ограничиваются явными полномочиями и контрактами. |
| 4 | Совершенство | Совершенство | Рыночный | Изменения воспроизводимы, регрессионно проверяемы и пригодны к выпуску. |
| 5 | Цельность | Мастерство | Деловой | Парсер, IR, runtime, VM и инструменты образуют цельную систему. |
| 6 | Целостность | Профессионализм | Финансовый | Доверие обеспечивают аудит, provenance, управление полномочиями и границы FFI. |
| 7 | Монолитность | Надёжность | Прибыльный | Исполнение остаётся предсказуемым в заявленных лимитах. |
| 8 | Согласованность | Основательность | Доходный | Диагностика и отчёты опираются на источники, версии и проверяемые факты. |
| 9 | Последовательность | Гармоничность | Экономический | Повторяемые сборки и проверки имеют единый порядок. |
| 10 | Системность | Согласованность | Хозяйственный | Политики языка, runtime, toolchain и модулей согласованы. |
| 11 | Структурированность | Цельность | Бизнесовый | Схемы, API и контракты позволяют независимую интеграцию. |
| 12 | Упорядоченность | Целостность | Маркетинговый | Документация и редактор ясно объясняют назначение и ограничения языка. |
| 13 | Непротиворечивость | Монолитность | Клиентский | Синтаксис, спецификация, runtime и тесты не расходятся. |
| 14 | Однородность | Нераздельность | Сбытовой | Путь разработчика от диагностики к исправлению остаётся последовательным. |
| 15 | Унификация | Единство | Промышленный | Алиасы, IR и интерфейсы используют стабильные канонические контракты. |
| 16 | Стандартизация | Слаженность | Корпоративный | Релизы, миграции и управление изменениями проходят повторяемые проверки. |
| 17 | Полнота | Ритмичность | Инвестиционный | Доказательств достаточно для независимого технического и финансового due diligence. |
| 18 | Точность | Размеренность | Монетизируемый | Монетизация требует отдельного подтверждения ценности, прав и затрат. |
| 19 | Выверенность | Синхронность | Рентабельный | Рентабельность требует измерения сопровождения, поддержки и стоимости поставки. |
| 20 | Профессионализм | Упорядоченность | Капитализированный | Языковые спецификации, код, документация и лицензии сохраняют прослеживаемость. |

## Evaluation

The root profile **quality-commercial.v1.json** records all 60 controls. Run **python tools/quality_commercial.py** for a text report or add **--format json** for machine-readable output. The workflow runs the evaluator and regression tests.

Maturity is explicitly declared per control: **implemented** = linked implementation evidence; **planned** = planned and receives 25% credit; **not_assessed** = no evidence and receives no credit; **not_applicable** = excluded from the denominator. The evaluator checks profile structure and repository-relative file presence only. It does not execute the linked tests or certify language/runtime parity.

## Commercial gates

- Market validation: not assessed; require real developer workflows and feedback.
- Pricing: not set; do not infer willingness-to-pay from downloads or stars.
- Unit economics: not assessed; measure maintenance, support and release costs.
- Licensing: manual review required for dependencies, runtime distribution and editor assets.
- Support: planned; document compatibility windows and maintenance ownership.
- Distribution: build/release workflow artifacts exist; they do not prove adoption or sales.

## Project-specific boundaries

Python remains the executable compatibility reference until native C17 parity is demonstrated. The MOST registry distinguishes existing specifications from proposals; reserved contracts are not presented as implemented functions. Native FFI is for trusted ABI-compatible code and is not a sandbox for untrusted extensions. Toolchain discovery does not install compilers.

Controls advance to **implemented** only when source, tests and supporting contracts exist. Market, financial and licensing states require separate evidence; source-code completeness is not a profitability claim.
