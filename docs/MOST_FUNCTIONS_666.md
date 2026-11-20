# MOST Function Registry 666

**Дата:** 20 ноября 2026 г.  
**Машинный каталог:** [`language/functions_666.json`](../language/functions_666.json)  
**Проверка:** `python tools/validate_most_functions.py`

## Назначение и терминология

Реестр объединяет **147 прежних контрактов возможностей MOST** и **519 новых API-предложений** — всего ровно **666 стабильных записей**. Это спецификация и карта прослеживаемости, а не 666 готовых callable-функций.

- **66** — архитектурные правила ядра, не API-каталог.
- **147** — существующий реестр системных возможностей.
- **666** — новый реестр API/возможностей: 147 + 519.
- **666 токенов** в лексическом каталоге — другое число и другой объект.
- **666-rule Constitution profile** — профиль приёмки/принципов, а не список реализованных функций.

## Диапазоны

| ID | Диапазон | Кол-во | Область |
|---|---:|---:|---|
| MOST-MEM-BASE | 1–21 | 21 | Память, регионы, аппаратные контракты |
| MOST-TYPE-BASE | 22–41 | 20 | Типы и контракты |
| MOST-UI-BASE | 42–63 | 22 | Web, UI, WASM |
| MOST-NET-BASE | 64–84 | 21 | Сеть и распределённые системы |
| MOST-COMP-BASE | 85–105 | 21 | Компилятор и статический анализ |
| MOST-DATA-BASE | 106–126 | 21 | Данные, текст, бинарные форматы |
| MOST-ECOSYS-BASE | 127–147 | 21 | Экосистема и инструменты |
| MOST-BRIDGE | 148–220 | 73 | Русский frontend, морфология, словари, intent, source maps |
| MOST-TYPES | 221–310 | 90 | Типы, доказуемые контракты, математика |
| MOST-EXEC | 311–410 | 100 | Память, владение, задачи и конкурентность |
| MOST-DATA | 411–510 | 100 | Схемы, кодеки, текст и потоки |
| MOST-SEC | 511–610 | 100 | Capabilities, аудит, границы, устойчивость |
| MOST-TOOL | 611–666 | 56 | Сборка, тесты, fuzz, диагностика, профилирование |

## Семантическая модель

REAPER — семантическое ядро; MOST — русскоязычный frontend. Оба обязаны приходить к одной typed IR:

`source → lexer/parser → MOST intent resolver → canonical AST → type/effect/ownership checks → typed IR → verifier/optimizer → backend`

Морфология, синонимы и доменные словари используются только для разрешения исходного имени. После разрешения остаётся один канонический символ. Они не меняют типы, эффекты, capabilities, ownership или runtime-поведение. Неоднозначность — ошибка, а не эвристический выбор.

Новые имена 148–666 — предварительные ASCII API-символы. Они не добавлены в lexer как ключевые слова, не экспортированы из runtime и не утверждают конкретный пользовательский синтаксис. Русские псевдонимы оставлены неутверждёнными до реализации MOST resolver (M2).

Каждая запись имеет контракт и критерии приёмки. Перед статусом implemented дополнительно требуются сигнатура, ошибки/эффекты, права/capabilities, владение и lifetime, квоты, ограничения target, тесты, документация и source mapping.

## Что найдено в исходниках

| Проект | Проверенные подсистемы | Реальная граница |
|---|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Python reference runtime, коллекции/строки, metrics, modules, heap accounting, resources, FFI, Pytyliki adapter, Canonical IR/VM, debugger; native C17 lexer, expression parser, owned AST, narrow integer lowering, IR verifier/optimizer | Python runtime отдельно от native C17; полноценные MOST declaration grammar, intent resolver, type/effect/ownership checker и native backend не заявлены |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | C11 memory views/arenas/pools, 30 metric operations, metric registry, systems acceleration lab, embedded profiles/budget, processor profiling, DSP, versioned ABI v1 | Самостоятельная native library; для MOST нужны типизированные bindings, error/effect contracts, capability checks и conformance tests |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Read-only PnP snapshots, UDRV package inspection, INF target classification, exact-ID compatibility graph/dry-run, metric analysis, QCS parser utility, report composition | Python tooling и JSON interchange; driver install/remove/enable/disable не входят в federation bridge; QCS не объявляется MOST parser |

Подробный список путей и реальных экспортированных/обнаруженных символов записан в `source_inventory` JSON. `source_refs` конкретной функции ссылается только на символы из этого inventory. Совпадение назначения или частичное покрытие не означает, что API доступен из MOST.

## Межпроектная интеграция

**REAPER ↔ Pytyliki.** В Python reference runtime есть opt-in C ABI v1 adapter: явный абсолютный путь к доверенной библиотеке, проверка ABI и обязательных exports, синхронные bounded float64 buffers. Native library выполняется с правами процесса REAPER — это не sandbox. Мост не превращает все C API в native MOST functions.

**REAPER ↔ OPlague.** Контракт — `oplage.device-snapshot.v1`. Reaper читает и проверяет JSON, извлекает normalized metrics и строит read-only comparison. Snapshot — телеметрия, а не доказательство подписи, доверия или совместимости драйвера. Установка и изменение состояния устройств не выполняются.

**OPlague ↔ Pytyliki.** Есть необязательная численная cross-check distance через явно заданную ABI v1 библиотеку; Python расчёт OPlague остаётся самостоятельным.

## Реализационный статус на 20.11.2026

В native C17 ветке Reaper есть token lexer с частью MOST-лексики, bounded Pratt expression parser, owned AST/source locations, узкий integer AST-to-IR lowerer, structural IR verifier и checked i64 constant-folding. Это только фундамент frontend/toolchain, не завершённый MOST compiler.

Значительная часть прикладной функциональности Reaper живёт в Python reference runtime. Pytyliki — отдельная C11 библиотека, OPlague — Python tooling. Их функции не становятся встроенными функциями MOST без bindings и conformance acceptance.

Поэтому для всех 666 строк `most_native=false`. Первые 147 имеют статус specification; часть помечена `partial_outside_most` с точными внешними source references. Для 519 расширений состояние — `planned`. Поле `status` говорит о наличии контракта; `implementation_state` описывает код отдельно.

## Критерий implemented

1. Утверждены каноническая сигнатура, типы параметров/результата и ownership.
2. Зафиксированы ошибки, эффекты, capabilities, квоты, таймауты и target gates.
3. Есть parser/resolver/type checker/IR/backend путь для выбранной платформы.
4. Есть positive, negative, boundary, fuzz/property и differential tests по применимости.
5. Документация и source maps обновлены; CI/conformance suite проходит.
6. Для внешнего API утверждены ABI/version, trust boundary, lifecycle и поведение отказа.

До выполнения этих требований строка остаётся спецификацией/предложением и не регистрируется автоматически как runtime builtin.

## Проверка

```sh
python tools/validate_most_functions.py
```

Валидатор проверяет точный размер 666, последовательность IDs, уникальность имён, диапазоны без дыр/пересечений, контракты, acceptance criteria и совпадение source references с зафиксированным source inventory.
