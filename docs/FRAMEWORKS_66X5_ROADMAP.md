# Reaper Framework Programme — 66 × 5

**Target:** 66 distinct domains × 5 independent frameworks per domain = **330 frameworks**.  
**Profile:** systems programming, compiler/toolchain engineering, runtime architecture and hardware-adjacent development in Reaper.  
**Current repository baseline:** batch 01 contains five Reaper-language validation frameworks; the other 65 batches remain queued.

## Implementation gate

A framework counts as implemented only when it has all of the following:

1. A separate, importable Reaper `.rpr` module with an exported API.
2. A versioned input/output and failure contract.
3. Positive and negative tests executed through the Reaper interpreter.
4. Packaging/discovery integration where applicable.
5. Documentation of its actual boundary and unsupported behavior.
6. A successful required CI run for the exact pull-request head.

A name, table entry, template or proposed API does not count as an implementation. Related frameworks must not be five aliases for the same algorithm. Each one must own a distinct responsibility and acceptance contract.

## Batch tracker

Each numbered row is one independent implementation batch with five framework slots. Batch 01 is described in [Skeleton Frameworks](SKELETON_FRAMEWORKS.md).

| # | Domain | Framework slots | Status |
|---:|---|---:|---|
| 01 | Каркас | 5 | In review |
| 02 | Платформа | 5 | Queued |
| 03 | Среда | 5 | Queued |
| 04 | Инфраструктура | 5 | Queued |
| 05 | Архитектура | 5 | Queued |
| 06 | Базис | 5 | Queued |
| 07 | Основа | 5 | Queued |
| 08 | Фундамент | 5 | Queued |
| 09 | Остов | 5 | Queued |
| 10 | Костяк | 5 | Queued |
| 11 | Структура | 5 | Queued |
| 12 | Конструкция | 5 | Queued |
| 13 | Экосистема | 5 | Queued |
| 14 | Надстройка | 5 | Queued |
| 15 | Оболочка | 5 | Queued |
| 16 | Рантайм | 5 | Queued |
| 17 | Среда выполнения | 5 | Queued |
| 18 | Движок | 5 | Queued |
| 19 | Ядро | 5 | Queued |
| 20 | Библиотека | 5 | Queued |
| 21 | Набор инструментов | 5 | Queued |
| 22 | Инструментарий | 5 | Queued |
| 23 | Тулкит | 5 | Queued |
| 24 | Пакет | 5 | Queued |
| 25 | Стек | 5 | Queued |
| 26 | Технологический стек | 5 | Queued |
| 27 | Шаблон | 5 | Queued |
| 28 | Скелет | 5 | Queued |
| 29 | Бойлерплейт | 5 | Queued |
| 30 | Базовый слой | 5 | Queued |
| 31 | Прослойка | 5 | Queued |
| 32 | Мидлвар | 5 | Queued |
| 33 | Связующее ПО | 5 | Queued |
| 34 | Контейнер | 5 | Queued |
| 35 | Хост | 5 | Queued |
| 36 | Контекст | 5 | Queued |
| 37 | Модель | 5 | Queued |
| 38 | Паттерн | 5 | Queued |
| 39 | Парадигма | 5 | Queued |
| 40 | Концепция | 5 | Queued |
| 41 | Методология | 5 | Queued |
| 42 | Подход | 5 | Queued |
| 43 | Система | 5 | Queued |
| 44 | Подсистема | 5 | Queued |
| 45 | Модуль | 5 | Queued |
| 46 | Компонент | 5 | Queued |
| 47 | Блок | 5 | Queued |
| 48 | Узел | 5 | Queued |
| 49 | Интерфейс | 5 | Queued |
| 50 | Протокол | 5 | Queued |
| 51 | Стандарт | 5 | Queued |
| 52 | Регламент | 5 | Queued |
| 53 | Спецификация | 5 | Queued |
| 54 | Схема | 5 | Queued |
| 55 | Матрица | 5 | Queued |
| 56 | Сетка | 5 | Queued |
| 57 | Контур | 5 | Queued |
| 58 | Периметр | 5 | Queued |
| 59 | Рабочая среда | 5 | Queued |
| 60 | Рабочая область | 5 | Queued |
| 61 | Плацдарм | 5 | Queued |
| 62 | Опорная точка | 5 | Queued |
| 63 | Базовая линия | 5 | Queued |
| 64 | Несущая конструкция | 5 | Queued |
| 65 | Аппаратно-программная база | 5 | Queued |
| 66 | Программный каркас | 5 | Queued |

## Progress

- Implemented source modules in batch 01: 5.
- Queued framework slots in batches 02–66: 325.
- Completed total: 5 / 330, subject to the batch 01 CI gate.

Continue in order, one five-framework batch at a time. Preserve independent contracts and Reaper-language implementations; update this tracker only after the corresponding tests and CI evidence exist.
