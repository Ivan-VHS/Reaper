
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="Язык системного программирования и среда разработки Reaper" width="880"></picture></p>
<h1 align="center">Reaper — системный язык программирования и среда разработки</h1>
<p align="center"><strong>Flow-first язык с Python reference runtime, CLI, Windows Studio, локальными stdio LSP/DAP и отдельно развиваемой частичной веткой native C17.</strong></p>
<p align="center"><a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="Python CI" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=Python%20CI"></a> <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml"><img alt="Windows Studio" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/desktop-build.yml?branch=main&style=flat-square&label=Windows%20Studio"></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square"></a></p>

[Быстрый старт](#быстрый-старт) · [Revival](#обновление-документации-revival) · [Визуальный обзор](#визуальный-обзор) · [Архитектура](#архитектура) · [Документация](docs/README.md)

> **Граница реализации:** Python runtime — исполняемая reference-реализация совместимости. Native C17 lexer/parser/IR/lowering реализованы частично и не являются полным компилятором или универсальным backend машинного кода. Studio работает только в Windows. LSP/DAP — локальные stdio-сервисы, а не hosted API.

## Быстрый старт

**Требования:** Python 3.10+, Git. Для Studio нужен Tkinter. CMake 3.16+ и компилятор C17 нужны только для частичной native-ветки. Node.js необязателен для NOO TAH.

~~~sh
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

Запуск Windows Studio:

~~~sh
python reaper_desktop.py
~~~

Тесты:

~~~sh
python -m unittest discover -s tests -v
~~~

## Обновление документации Revival

| Было | Стало |
|---|---|
| Один статичный баннер | Парные SVG-баннеры для светлой и тёмной тем |
| Сложно отличить Python runtime от native compiler | Явно разделены Python reference и частичный native C17 |
| Скриншот Studio смешан со схемой данных | Реальный снимок Windows Studio и отдельно обозначенная схема |
| Обобщённые описания функций | Конкретные ограничения сервисов, платформ и language tooling |
| Длинная навигация | Тематические хабы, карта документации и стандарт публикации |

Это обновление документации, **не новая версия языка и не выпуск Reaper**. Статусы сверяются с кодом, тестами и [FEATURES.md](docs/FEATURES.md).

## Текущая реализация

| Компонент | Доступные функции | Граница |
|---|---|---|
| Python reference runtime | Lexer, parser, interpreter, scopes, values, quotas, CLI/REPL | Эталонная совместимая реализация |
| Статический анализ | Консервативные AST/type diagnostics в check, Studio и LSP | Не исполняет исходный код |
| Studio | Windows editor/debugger, command palette, MCU-профили | Без live device inspector |
| LSP | stdio, UTF-16 positions, локальная диагностика, completion, hover, symbols | Только открытый документ; без межфайлового type inference |
| DAP | Launch, line breakpoints, statement-boundary stepping, stack и locals | Только документированное подмножество runtime |
| Native C17 | Lexer, expression parser, owned AST, checked i64 IR, ограниченный lowering | Частично; не полная паритетность языка |
| QCS / hardware contracts | Проверка синтаксиса и checked MMIO descriptor API | Без физического mapping и полного device runtime |
| NOO TAH | Необязательная интеграция с официальным Node.js | Node.js не нужен для .rpr |

## Визуальный обзор

<table><tr><td width="50%"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Снимок работающего Reaper Studio в Windows" width="100%"></a><p><sub><strong>Реальный снимок Studio</strong> — Windows desktop, 1920×1080.</sub></p></td><td width="50%"><img src="assets/readme/workflow.svg" alt="Поток Reaper от исходного кода через parser и Python runtime к инструментам" width="100%"><p><sub><strong>Архитектурная иллюстрация</strong> — реализованный поток, не скриншот интерфейса.</sub></p></td></tr></table>

## Архитектура

~~~mermaid
flowchart LR
  A[.rpr source] --> B[Lexer и parser]
  B --> C[AST и source spans]
  C --> D[Python reference runtime]
  D --> E[CLI / REPL]
  D --> F[Windows Studio]
  D --> G[stdio LSP / DAP]
  C -. частичная ветка .-> H[Native C17 IR и limited lowering]
  I[Необязательный Node.js] --> J[NOO TAH adapter]
~~~

Native C17 показан отдельной частичной веткой и не приравнивается к Python reference runtime.

## Конфигурация и доверие

Hosted web service, аккаунта или корневого .env нет. Для NOO TAH доступны необязательные переменные путей:

| Переменная | Назначение |
|---|---|
| NOO_TAH_NODE | Явный путь к Node executable |
| NOO_TAH_NPM_CLI | Явный путь к npm-cli.js |
| NOO_TAH_NPX_CLI | Явный путь к npx-cli.js |

Полезные флаги: --check / --lint, --engine treewalk|vm, --allow-native-ffi и лимиты --steps, --items, --text-length, --heap-bytes, --open-resources. FFI выключен, пока пользователь явно его не разрешит. Интерпретатор не является OS sandbox; запускайте только доверенные программы и библиотеки.

## Структура репозитория

| Путь | Назначение |
|---|---|
| reaper/ | Python frontend языка, runtime и command services |
| native/ / src/ | Частичная реализация C17 и native contracts |
| examples/ | Исполняемые программы .rpr |
| tests/ | Runtime, parser, diagnostics и интеграционные тесты |
| editors/vscode/ | Только синтаксическая поддержка VS Code |
| docs/ | Контракты языка, compiler, runtime, IDE и hardware |
| assets/readme/ | Адаптивный баннер и схема потока |
| .github/workflows/ | Python CI, Windows Studio и интеграции |

## Проверка и дорожная карта

~~~sh
python -m unittest discover -s tests -v
python -m reaper --check examples/flow.rpr
git diff --check
~~~

При изменениях native-ветки также запустите CMake/CTest. Текущие статусы и этапы: [архитектура](docs/ARCHITECTURE.md), [матрица функций](docs/FEATURES.md), [Hardware Language](docs/HARDWARE_LANGUAGE.md), [IDE contract](docs/REAPER_IDE.md) и [карта документации](docs/INFORMATION_ARCHITECTURE.md).

## Разработка

См. [CONTRIBUTING.md](CONTRIBUTING.md), [README Visual Standard](docs/README_VISUAL_STANDARD.md) и [SECURITY.md](SECURITY.md). Изменения grammar, diagnostics, runtime quotas, LSP/DAP и native contracts должны сопровождаться regression-тестами.

## Лицензия

[Apache-2.0](LICENSE).
