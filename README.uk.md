<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>⚙️ Reaper — системна мова та робоче середовище</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **Явні контракти. Типізовані потоки. Діагностика з прив’язкою до вихідного коду.**

**Стан:** Alpha · еталонне середовище доступне · нативна гілка C17 часткова · **Версія:** Python package 0.1.0 · Native CMake track 0.2.0 · **License:** [Apache-2.0](LICENSE) · **Стандарт README:** Psychoporter 666 v1.0 · **Дата перевірки:** 2026-11-25 · UTC · **Source:** [Ivan-VHS/Reaper](https://github.com/Ivan-VHS/Reaper)

<p align="center"><img src="assets/reaper-hero.svg" alt="Reaper — системна мова та робоче середовище — project overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper — системна мова та робоче середовище — application screenshot" width="100%"></a></p>

## Швидка навігація

[🚀 Demo: Studio screenshot](assets/screenshots/reaper-studio.png) · [Documentation](docs/README.md) · [Source repository](https://github.com/Ivan-VHS/Reaper) · [Issues](https://github.com/Ivan-VHS/Reaper/issues)

## Призначення та межі

Reaper — мова системного програмування та локальне середовище розробки. Еталонне середовище Python, CLI/REPL, служби LSP/DAP та основа Windows Studio відокремлені від експериментальної нативної гілки компілятора C17. Паритет нативної реалізації й привілейовані апаратні служби ще не завершені.

## Можливості

- Вихідна мова .rpr, lexer/parser, еталонний інтерпретатор і структурована діагностика.
- CLI, REPL, основа Windows Studio та служби LSP/DAP через stdio.
- Статичні перевірки й ліміти ресурсів в еталонному середовищі; режим перевірки не виконує вихідний код.
- Нативна гілка C17: lexer, parser, owned AST, перевірний IR, згортання констант і обмежений lowering.
- Перевірні MMIO-дескриптори й ABI-контракти — це інтерфейси, а не фізичний mapper чи драйвер.
- Каркаси Jora, помічники Kora та необов’язкові інтеграції з явними межами довіри.

## Архітектура та потік даних

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

## Вимоги

Python 3.10+ для еталонного середовища й пакетних інструментів; CMake 3.16+ і компілятор C17 для нативної гілки; Node.js 22/24 для необов’язкових compatibility-перевірок; Tkinter для Windows Studio.

## Збирання

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

## Перші перевірки

~~~sh
python -m reaper --check examples/flow.rpr
python -m reaper --repl
~~~

Команда --check виконує статичну перевірку до запуску. У Windows PowerShell активуйте середовище через .venv\Scripts\Activate.ps1.

## Запуск

After installation, the package exposes the reaper-studio GUI script when Tkinter is installed; language and debug services are separate stdio processes.

## Інтерфейси

| Surface | Contract / entry point | Boundary |
|---|---|---|
| CLI / REPL | `reaper` | Source checking, execution and interactive mode. |
| Language service | `reaper-lsp / stdio` | Document-local diagnostics, completion and navigation subset. |
| Debug adapter | `reaper-dap / stdio` | Implemented breakpoint and step subset. |
| Native ABI | `reaper_ffi / reaper_system / reaper_dabi64_desktop` | Versioned C interfaces; native compiler parity remains partial. |

REST/GraphQL, WebSocket, OAuth, хмарний deployment і cookie-механізми не описуються як можливості, якщо в репозиторії немає версіонованої реалізації та тестів.

## Безпека та межі довіри

Еталонне середовище застосовує ліміти ресурсів і явні capability-контракти. MMIO API перевіряє дескриптори та політику доступу, але не відображає фізичні пристрої. LSP/DAP використовують локальний stdio; розміщений REST-сервіс, OAuth-провайдер або хмарна площина керування не є частиною документованого середовища.

Security reporting: [SECURITY.md](SECURITY.md). Do not publish secrets, device identifiers or private logs in public issues.

## Перевірка якості

~~~sh
python -m unittest discover -s tests -v

cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

Склад тестів визначається зареєстрованими CTest/unittest цілями та workflow. Відсоток покриття, fuzz-результат і звіт навантаження не заявляються без опублікованого артефакту.

## Докази продуктивності

Для еталонного середовища й часткової нативної гілки не опубліковано стабільних міжмашинних показників затримки чи пам’яті. Порівнюйте відтворювані прогони з фіксацією компілятора, цілі, режиму збирання та вхідних даних.

## Сумісність

Еталонний пакет підтримує Python 3.10+; нативна гілка C17 використовує CMake і системний компілятор C17. Windows Studio потребує Tkinter. Паритет платформ і компіляторів перевіряється для кожної цілі окремо.

## Документація та екосистема

- [Features and maturity](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Hardware language](docs/HARDWARE_LANGUAGE.md)
- [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [Studio and IDE](docs/REAPER_IDE.md)
- [Psychoporter 666](docs/PSYCHOPORTER_666.md)
- [Documentation index](docs/README.md)

Матриця можливостей і план реалізації відокремлюють готову поведінку еталонного середовища від часткової нативної роботи та майбутніх апаратних можливостей.

Cross-project integrations use documented versioned interfaces and explicit adapters. An optional adapter does not grant another project runtime or hardware privileges.

## Участь у розробці

Ознайомтеся з CONTRIBUTING.md перед зміною коду або контрактів. Робіть зміни невеликими й перевірними, додавайте детерміновані тести та використовуйте Conventional Commits, якщо цього вимагає посібник.

## Ліцензія та правові умови

Поширюється за ліцензією [Apache-2.0](LICENSE). Програмне забезпечення надається «ЯК Є» в межах умов ліцензії. Назви сторонніх проєктів і торговельні марки належать їхнім правовласникам.

This repository documents local software interfaces. Hosted-service terms, cookie consent, OAuth and CORS are not applicable to the runtime surfaces described above unless a separate hosted component is introduced and documented.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 · UTC</sub></p>