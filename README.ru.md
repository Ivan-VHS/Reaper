# Reaper

Reaper — язык системного программирования и локальная среда разработки для embedded-ПО, инструментов компилятора, аппаратно-ориентированных программ и языка с композицией потоков.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg">
  <img src="assets/readme/dashboard-light.svg" alt="Обзор Reaper: язык, frontend компилятора, эталонная среда и инструменты разработчика" width="100%">
</picture>

[![Python CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=Python%20CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Последний коммит](https://img.shields.io/github/last-commit/Ivan-VHS/Reaper?style=flat-square)](https://github.com/Ivan-VHS/Reaper/commits/main) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

[Быстрый старт](#быстрый-старт) · [Скриншоты](#скриншоты) · [Архитектура](#архитектура) · [План развития](#план-развития) · [Документация](docs/README.md) · [Коммиты](https://github.com/Ivan-VHS/Reaper/commits/main)

> **Статус:** активная разработка. Есть Python reference runtime, CLI/REPL, основа Windows Studio, stdio LSP/DAP и частичная нативная ветка C17. Полная native compiler parity и привилегированные аппаратные службы ещё не завершены.
>
> **Платформы:** Python-тесты охватывают 3.10–3.12. Опциональная Node.js-матрица проверяет Node 22/24 в Windows, Linux и macOS. Для Studio в Windows нужен Tkinter. Нативная ветка требует CMake 3.16+ и компилятор C17.

## Быстрый старт

Создайте окружение и установите Python reference runtime:

~~~sh
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

Запустите Studio или REPL:

~~~sh
python reaper_desktop.py
python -m reaper --repl
~~~

Запустите тесты:

~~~sh
python -m compileall -q reaper tests
python -m unittest discover -s tests -v
~~~

## Возможности

| Компонент | Текущее поведение | Граница |
|---|---|---|
| Python runtime | Lexer, parser, interpreter, modules, closures, resource quotas и audit log | Текущая исполняемая реализация языка |
| Статическая проверка | Вывод примитивных/list-типов и диагностика операторов, индексов, mutability и арности вызовов | Частичная система типов |
| Reaper Studio | Основа Windows IDE: дерево проекта, редактор, debugger и системный обзор | Локальный GUI; не управляет устройствами |
| LSP | Диагностика, completion, hover, symbols, lexical navigation и форматирование через stdio JSON-RPC | Только открытый документ, без межфайлового анализа |
| DAP | Точки останова, stepping, stack и locals | Ограниченный отладчик на уровне операторов |
| NOO TAH | Управление процессами официального Node.js, npm/npx и Inspector | JavaScript выполняет upstream Node |
| Нативная ветка C17 | Lexer/parser, AST, checked i64 IR и ограниченное lowering | Экспериментальная частичная реализация |
| QCS и embedded | Разбор аппаратных описаний, AST/диагностика и справочные утилиты | Анализ без доступа к реальному оборудованию |

Запись в каталоге или зарезервированное имя возможности не доказывают наличие готовой функции runtime. Точная зрелость описана в [Features](docs/FEATURES.md), [Hardware Language](docs/HARDWARE_LANGUAGE.md), [Reaper IDE](docs/REAPER_IDE.md), [NOO TAH](docs/NOO_TAH.md) и [Kora](docs/KORA.md).

## Чем отличается Reaper

- Исполняемая реализация `.rpr` уже существует; нативный компилятор выделен в отдельную частичную ветку.
- CLI, Studio, языковые службы и тесты используют одну реализацию языка.
- Квоты ресурсов и опциональный hash-chained audit log позволяют проверять ограничения выполнения.
- Аппаратные функции описываются проверяемыми контрактами и адаптерами, а не обещанием привилегированного доступа.
- NOO TAH использует официальный Node, не заявляя собственную реализацию V8 или libuv.

## Скриншоты

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/workflow-dark.svg">
  <img src="assets/readme/workflow.svg" alt="Поток Reaper от .rpr через lexer/parser к reference runtime и инструментам разработчика" width="100%">
</picture>

<p align="center">
  <a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Настоящий скриншот Reaper Studio в Windows" width="100%"></a>
</p>
<sub>Реальный снимок Windows Studio 1920×1080 из screenshot workflow репозитория. SVG выше — схема архитектуры.</sub>

## Архитектура

~~~mermaid
flowchart LR
    A[.rpr source] --> B[Lexer and parser]
    B --> C[Python reference runtime]
    C --> D[CLI / REPL]
    C --> E[Studio]
    C --> F[LSP / DAP]
    G[Partial native C17] -. separate track .-> B
    H[JavaScript project] --> I[NOO TAH]
    I --> J[Official Node.js]
~~~

| Путь | Назначение |
|---|---|
| `reaper/` | Python runtime, CLI, Studio, language/debug services и NOO TAH |
| `reaper/kora/` | Вспомогательная стандартная библиотека Kora |
| `src/`, `include/` | Частичная реализация C17 |
| `tests/`, `examples/` | Тесты runtime/protocol и локальные `.rpr` программы |
| `docs/`, `editors/` | Язык, IDE, архитектура и поддержка редакторов |
| `.github/workflows/` | CI, native/desktop build, скриншоты и Node compatibility |

## Матрица сборки

| Цель | Требования | Статус |
|---|---|---|
| Python runtime | Python 3.10+ | Исполняемая реализация; CI проверяет 3.10/3.11/3.12 |
| Windows Studio | Python с Tkinter | Цель desktop workflow |
| Native C17 | CMake 3.16+, C17 compiler | Частичная реализация, отдельные тесты |
| NOO TAH | Node.js 22 или 24 по текущей CI-матрице | Опциональная интеграция |
| macOS | Python path / Node compatibility job | Не означает поддержку нативной Reaper Studio |

## Что нового в README Revival

- Первая страница разделяет исполняемый Python runtime и частичный native compiler.
- Команды установки, проверки, запуска и тестирования перемещены вверх.
- Настоящий скриншот Windows Studio отделён от редактируемых схем.
- Точно описаны границы LSP, DAP, аппаратных адаптеров и интеграции Node.

| Было | Стало |
|---|---|
| Широкое обещание языковой платформы | Таблица возможностей и зрелости |
| Статус native compiler можно трактовать слишком широко | Reference и partial ветки разделены |
| Команды нужно искать | Готовые команды в начале |
| Общие заявления об IDE | Ограничения language services по открытому документу |

## План развития

- [x] Python runtime, CLI/REPL и локальные примеры.
- [x] Основа stdio LSP/DAP и Windows Studio.
- [x] Частичные native C17 lexer/parser/IR и тестовые цели.
- [ ] Расширять native type/ownership/effect analysis и code generation вместе с тестами.
- [ ] Добавлять OS-backed MMIO/IRQ/DMA только через проверенные платформенные адаптеры и отдельную валидацию.

## Экосистема

- [DuckOS](https://github.com/Ivan-VHS/DuckOS) — операционная система и пространство Mora.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — анализ процессоров и ограниченные системные утилиты.
- [OPlague](https://github.com/Ivan-VHS/OPlague) — анализ устройств и свидетельств о драйверах.
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — процедурная генерация сэмплов и офлайн DSP.

См. [индекс документации](docs/README.md), [архитектуру](docs/ARCHITECTURE.md), [правила участия](CONTRIBUTING.md) и [описание VS Code syntax support](editors/vscode/README.md). Лицензия: [Apache-2.0](LICENSE).
