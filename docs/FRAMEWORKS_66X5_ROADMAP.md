# Reaper Framework Programme — 66 × 5

**Target:** 66 independent domains × 5 independent frameworks = **330 framework modules**.  
**Implementation language:** Reaper `.rpr`.  
**Runtime:** existing Reaper reference interpreter; native compiler parity is tracked separately.

## What is counted

The programme contains 330 separate `.rpr` source modules:
- Batch 01, Каркас: 5 modules.
- Batches 02–66: 325 domain-specific modules, each indexed by stable ID, source path, exported API and positive/negative fixtures.

A framework is not considered delivered merely because it has a name, file or index row. The delivery gate requires an importable Reaper module, explicit API contract, positive and negative interpreter tests, package inclusion, documentation and a successful required CI run for the exact pull-request head.

## Batch tracker

| # | Domain | Slots | Status |
|---:|---|---:|---|
| 01 | Каркас | 5 | In review |
| 02 | Платформа | 5 | Source added — CI pending |
| 03 | Среда | 5 | Source added — CI pending |
| 04 | Инфраструктура | 5 | Source added — CI pending |
| 05 | Архитектура | 5 | Source added — CI pending |
| 06 | Базис | 5 | Source added — CI pending |
| 07 | Основа | 5 | Source added — CI pending |
| 08 | Фундамент | 5 | Source added — CI pending |
| 09 | Остов | 5 | Source added — CI pending |
| 10 | Костяк | 5 | Source added — CI pending |
| 11 | Структура | 5 | Source added — CI pending |
| 12 | Конструкция | 5 | Source added — CI pending |
| 13 | Экосистема | 5 | Source added — CI pending |
| 14 | Надстройка | 5 | Source added — CI pending |
| 15 | Оболочка | 5 | Source added — CI pending |
| 16 | Рантайм | 5 | Source added — CI pending |
| 17 | Среда выполнения | 5 | Source added — CI pending |
| 18 | Движок | 5 | Source added — CI pending |
| 19 | Ядро | 5 | Source added — CI pending |
| 20 | Библиотека | 5 | Source added — CI pending |
| 21 | Набор инструментов | 5 | Source added — CI pending |
| 22 | Инструментарий | 5 | Source added — CI pending |
| 23 | Тулкит | 5 | Source added — CI pending |
| 24 | Пакет | 5 | Source added — CI pending |
| 25 | Стек | 5 | Source added — CI pending |
| 26 | Технологический стек | 5 | Source added — CI pending |
| 27 | Шаблон | 5 | Source added — CI pending |
| 28 | Скелет | 5 | Source added — CI pending |
| 29 | Бойлерплейт | 5 | Source added — CI pending |
| 30 | Базовый слой | 5 | Source added — CI pending |
| 31 | Прослойка | 5 | Source added — CI pending |
| 32 | Мидлвар | 5 | Source added — CI pending |
| 33 | Связующее ПО | 5 | Source added — CI pending |
| 34 | Контейнер | 5 | Source added — CI pending |
| 35 | Хост | 5 | Source added — CI pending |
| 36 | Контекст | 5 | Source added — CI pending |
| 37 | Модель | 5 | Source added — CI pending |
| 38 | Паттерн | 5 | Source added — CI pending |
| 39 | Парадигма | 5 | Source added — CI pending |
| 40 | Концепция | 5 | Source added — CI pending |
| 41 | Методология | 5 | Source added — CI pending |
| 42 | Подход | 5 | Source added — CI pending |
| 43 | Система | 5 | Source added — CI pending |
| 44 | Подсистема | 5 | Source added — CI pending |
| 45 | Модуль | 5 | Source added — CI pending |
| 46 | Компонент | 5 | Source added — CI pending |
| 47 | Блок | 5 | Source added — CI pending |
| 48 | Узел | 5 | Source added — CI pending |
| 49 | Интерфейс | 5 | Source added — CI pending |
| 50 | Протокол | 5 | Source added — CI pending |
| 51 | Стандарт | 5 | Source added — CI pending |
| 52 | Регламент | 5 | Source added — CI pending |
| 53 | Спецификация | 5 | Source added — CI pending |
| 54 | Схема | 5 | Source added — CI pending |
| 55 | Матрица | 5 | Source added — CI pending |
| 56 | Сетка | 5 | Source added — CI pending |
| 57 | Контур | 5 | Source added — CI pending |
| 58 | Периметр | 5 | Source added — CI pending |
| 59 | Рабочая среда | 5 | Source added — CI pending |
| 60 | Рабочая область | 5 | Source added — CI pending |
| 61 | Плацдарм | 5 | Source added — CI pending |
| 62 | Опорная точка | 5 | Source added — CI pending |
| 63 | Базовая линия | 5 | Source added — CI pending |
| 64 | Несущая конструкция | 5 | Source added — CI pending |
| 65 | Аппаратно-программная база | 5 | Source added — CI pending |
| 66 | Программный каркас | 5 | Source added — CI pending |

## Current inventory

- Target modules: **330**.
- Batch 01 modules: **5**.
- New modules in the index: **325**.
- Total source slots represented: **330**.
- Unindexed slots: **0**.
- CI acceptance remains pending for the active implementation branch; no batch is marked delivered until exact-head tests pass.

## Module index

The machine-readable contract registry is [`reaper/frameworks/framework-index.v1.json`](../reaper/frameworks/framework-index.v1.json). Each entry records the domain number, stable ID, module path, API function, purpose, positive fixture and negative fixture. The focused programme test imports each module through the Reaper interpreter and compares its actual output.

## Implementation and safety boundaries

All framework behavior is written in Reaper. The Python test harness only invokes the existing interpreter and checks the public contract. Modules in this programme are deterministic local algorithms and validators; they do not implicitly read files, access the network, launch processes, load native libraries, install drivers, map physical memory or flash hardware.

In particular, a hardware-oriented contract validates supplied metadata only. It is not a privileged hardware runtime. A policy validator is not an OS security boundary. A lifecycle validator does not supervise live services. Such operational capabilities require dedicated runtime/host adapters and separate security review.

## Verification commands

```sh
python -m unittest tests.test_framework_programme -v
python -m unittest tests.test_skeleton_frameworks -v
python -m unittest discover -s tests -v
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The authoritative maturity state is the combination of source, tests, package inventory and exact-head GitHub Actions results.