<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>⚙️ Reaper — системный язык и рабочая среда</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **Явные контракты. Типизированные потоки. Диагностика с привязкой к исходникам.**

**Состояние:** Alpha · эталонная среда доступна · нативная ветка C17 частичная · **Версия:** Python package 0.1.0 · Native CMake track 0.2.0 · **License:** [Apache-2.0](LICENSE) · **Стандарт README:** Psychoporter 666 v1.0 · **Дата проверки:** 2026-11-25 · UTC · **Source:** [Ivan-VHS/Reaper](https://github.com/Ivan-VHS/Reaper)

<p align="center"><img src="assets/reaper-hero.svg" alt="Reaper — системный язык и рабочая среда — project overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper — системный язык и рабочая среда — application screenshot" width="100%"></a></p>

## Быстрая навигация

[🚀 Demo: Studio screenshot](assets/screenshots/reaper-studio.png) · [Documentation](docs/README.md) · [Source repository](https://github.com/Ivan-VHS/Reaper) · [Issues](https://github.com/Ivan-VHS/Reaper/issues)

## Назначение и границы

Reaper — язык системного программирования и локальная среда разработки. Эталонная среда Python, CLI/REPL, службы LSP/DAP и основа Windows Studio отделены от экспериментальной нативной ветки компилятора C17. Паритет нативной реализации и привилегированные аппаратные службы ещё не завершены.

## Возможности

- Исходный язык .rpr, lexer/parser, эталонный интерпретатор и структурированная диагностика.
- CLI, REPL, основа Windows Studio и службы LSP/DAP через stdio.
- Статические проверки и лимиты ресурсов в эталонной среде; режим проверки не исполняет исходный код.
- Нативная ветка C17: lexer, parser, owned AST, проверяемый IR, свёртка констант и ограниченный lowering.
- Проверяемые MMIO-дескрипторы и ABI-контракты — это интерфейсы, а не физический mapper или драйвер.
- Каркасы Jora, помощники Kora и необязательные интеграции с явными границами доверия.

## Архитектура и поток данных

~~~mermaid
flowchart TB
  S[".rpr source"] --> P["Lexer / parser"]
  P --> V["Reference runtime"]
  V --> C["CLI / REPL"]
  V --> L["stdio LSP / DAP"]
  S --> N["Native C17 track — partial"]
  N --> I["Checked IR / limited lowering"]
  H["Hardware contracts"] --> A["Checked ABI descriptors"]
  A -.-> X["No implicit device access"]
~~~

Source code, schemas, build files, tests and CI are the evidence for implemented behavior. Roadmap entries and catalogue records describe plans or inventories, not shipped functionality.

## Требования

Python 3.10+ для эталонной среды и пакетных инструментов; CMake 3.16+ и компилятор C17 для нативной ветки; Node.js 22/24 для необязательных compatibility-проверок; Tkinter для Windows Studio.

## Сборка

~~~sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

### Native C17 track

~~~sh
cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

The Python reference runtime and native C17 track are separate implementation tracks; passing tests in one does not establish feature parity in the other.

## Первые проверки

~~~sh
python -m reaper --check examples/flow.rpr
python -m reaper --repl
~~~

Команда --check выполняет статическую проверку до запуска. В Windows PowerShell активируйте окружение через .venv\Scripts\Activate.ps1.

## Запуск

After installation, the package exposes the reaper-studio GUI script when Tkinter is installed; language and debug services are separate stdio processes.

## Интерфейсы

| Surface | Contract / entry point | Boundary |
|---|---|---|
| CLI / REPL | `reaper` | Source checking, execution and interactive mode. |
| Language service | `reaper-lsp / stdio` | Document-local diagnostics, completion and navigation subset. |
| Debug adapter | `reaper-dap / stdio` | Implemented breakpoint and step subset. |
| Native ABI | `reaper_ffi / reaper_system / reaper_dabi64_desktop` | Versioned C interfaces; native compiler parity remains partial. |

REST/GraphQL, WebSocket, OAuth, облачный deployment и cookie-механизмы не описываются как возможности, если в репозитории нет версионированной реализации и тестов.

## Безопасность и границы доверия

Эталонная среда применяет лимиты ресурсов и явные capability-контракты. MMIO API проверяет дескрипторы и политику доступа, но не отображает физические устройства. LSP/DAP используют локальный stdio; размещённый REST-сервис, OAuth-провайдер или облачная плоскость управления не входят в документированную среду.

Security reporting: [SECURITY.md](SECURITY.md). Do not publish secrets, device identifiers or private logs in public issues.

## Проверка качества

~~~sh
python -m unittest discover -s tests -v

cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

Состав тестов определяется зарегистрированными CTest/unittest целями и workflow. Процент покрытия, fuzz-результат и нагрузочный отчёт не заявляются без опубликованного артефакта.

## Доказательства производительности

对于 эталонной среды и частичной нативной ветки не опубликованы стабильные межмашинные показатели задержки или памяти. Сравнивайте воспроизводимые прогоны с фиксацией компилятора, цели, режима сборки и входных данных.

## Совместимость

Эталонный пакет поддерживает Python 3.10+; нативная ветка C17 использует CMake и системный компилятор C17. Windows Studio требует Tkinter. Паритет платформ и компиляторов проверяется для каждой цели отдельно.

## Документация и экосистема

- [Features and maturity](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Hardware language](docs/HARDWARE_LANGUAGE.md)
- [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [Studio and IDE](docs/REAPER_IDE.md)
- [Psychoporter 666](docs/PSYCHOPORTER_666.md)
- [Documentation index](docs/README.md)

Матрица возможностей и план реализации отделяют готовое поведение эталонной среды от частичной нативной работы и будущих аппаратных возможностей.

Cross-project integrations use documented versioned interfaces and explicit adapters. An optional adapter does not grant another project runtime or hardware privileges.

## Участие в разработке

Изучите CONTRIBUTING.md перед изменением кода или контрактов. Сохраняйте изменения небольшими и проверяемыми, добавляйте детерминированные тесты, используйте Conventional Commits, если это требуется руководством.

## Лицензия и правовые условия

Распространяется по лицензии [Apache-2.0](LICENSE). Программное обеспечение предоставляется «КАК ЕСТЬ» в пределах условий лицензии. Названия сторонних проектов и товарные знаки принадлежат их правообладателям.

This repository documents local software interfaces. Hosted-service terms, cookie consent, OAuth and CORS are not applicable to the runtime surfaces described above unless a separate hosted component is introduced and documented.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 · UTC</sub></p>