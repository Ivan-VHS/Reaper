# Reaper — flow-first язык программирования и Studio

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Обзор проекта Reaper" width="100%"></p>

[Исходный код](https://github.com/Ivan-VHS/Reaper) · [Python CI](.github/workflows/ci.yml) · [Сборка Windows Studio](.github/workflows/desktop-build.yml) · [Совместимость Node.js](.github/workflows/noo-tah.yml) · [Индекс документации](docs/README.md) · [Apache-2.0](LICENSE)

## Реальный снимок Studio

<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Реальный снимок Reaper в Windows" width="100%"></a></p>
<p align="center"><sub>1920×1080 · Нажмите на изображение, чтобы открыть исходный PNG.</sub></p>

Настоящий снимок запущенного окна Reaper Studio в Windows, созданный screenshot workflow этого репозитория. Баннер и схема потока — авторские SVG-иллюстрации, а не скриншоты.

### Архитектура с первого взгляда

<p align="center"><img src="assets/readme/workflow.svg" alt="Reaper implemented data flow" width="100%"></p>

Рабочие пути: `.rpr` → Python reference runtime → CLI, Studio, LSP и DAP; отдельно — ограниченные i64-выражения → проверяемый native IR → assembly x86-64 System V ELF.


[![Python CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=Python%20CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml)  [![Live Studio capture](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/readme-screenshots.yml?branch=main&label=Live%20Studio%20capture)](https://github.com/Ivan-VHS/Reaper/actions/workflows/readme-screenshots.yml)  [![License](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)


> **Назначение:** Reaper — локальный язык программирования, интерпретатор, набор инструментов разработчика и desktop IDE для Windows. Это не hosted web demo и не production web service. Python runtime — текущая исполняемая эталонная реализация совместимости; нативный C17-трек уже генерирует проверяемый assembly x86-64 System V ELF для ограниченной подмножины i64-выражений. Документация сверена с `main` **22.11.2026**.

## Назначение и состояние реализации

Reaper — expression-oriented язык, в котором оператор `::` передаёт значение следующей операции. В состав входят Python reference runtime, CLI/REPL, Windows Studio, LSP/DAP через stdio и необязательная интеграция с официальным Node.js через NOO TAH.

Проект предназначен для разработчиков языков и tooling, инженеров приложений, QA, преподавателей и ревьюеров, которым нужно экспериментировать с файлами Reaper и проверять контракты языковых сервисов.

### Что реализовано

| Компонент | Текущий объём | Граница |
|---|---|---|
| Python runtime | lexer, parser, interpreter, CLI, REPL, модули, closures, quotas и audit log | текущая исполняемая эталонная реализация |
| Reaper Studio | основа Windows IDE: дерево проекта, редактор, подсветка синтаксиса, поиск, check/run и debugger | локальное desktop-приложение |
| LSP | stdio JSON-RPC, diagnostics, completion, hover, symbols и лексическая навигация | открытый документ; без межфайлового type inference |
| DAP | stdio debug adapter, line breakpoints, stepping, stack и locals | отладка на границах операторов; только доверенные локальные программы |
| NOO TAH | управление проектами/процессами вокруг официального Node.js, npm/npx и Inspector | Node/V8/libuv предоставляет upstream Node |
| Native C17 | UTF-8 lexer, Pratt expression parser, owned AST, проверяемый i64 IR, checked lowering и backend assembly x86-64 System V ELF | только целочисленные выражения; не полный compiler и не parity с Python runtime |
| QCS / embedded tools | отдельный parser аппаратной области, JSON AST и ограниченные embedded-инструменты | справочный/аналитический инструментарий, не выполнение на оборудовании |
| Kora | необязательные вспомогательные функции стандартной библиотеки в семи модулях | отдельно от runtime языка Reaper |

Каталоги и реестры могут содержать предложенные или зарезервированные записи. Наличие записи в каталоге не означает, что функция реализована в runtime. Уровни зрелости и границы описаны в [Features](docs/FEATURES.md), [REAPER IDE](docs/REAPER_IDE.md), [NOO TAH](docs/NOO_TAH.md) и [Kora helpers](docs/KORA.md).

Изображение ниже — снимок Windows Studio, а не браузерный playground.


## Быстрый старт

### Требования

- Python **3.10 или новее**. CI проверяет Python 3.10, 3.11 и 3.12.
- Tkinter для графического Studio (обычно входит в стандартный Python; в некоторых минимальных Linux-пакетах устанавливается отдельно).
- Git.
- CMake **3.16+** и компилятор C17 только для сборки частичного native track.
- Node.js необязателен для NOO TAH. Compatibility workflow тестирует Node.js **22 и 24**; он не нужен для запуска программ Reaper `.rpr`.

Python package объявляет `setuptools>=68` как build-system requirement и не содержит списка сторонних runtime-зависимостей в `pyproject.toml`.

### Установка Python reference runtime

```sh
python -m venv .venv
# Активируйте окружение:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux / macOS:       source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

### Запуск программы и Studio

```sh
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
python -m reaper --repl
python reaper_desktop.py
```

После editable installation доступны соответствующие entry points `reaper` и `reaper-studio`.

### Запуск тестов

```sh
python -m compileall -q reaper tests
python -m unittest discover -s tests -v
```

При первой установке может скачиваться объявленный build backend из package index; дальнейший запуск программ локальный. Нет HTTP-порта приложения, браузерного URL, шага seed базы данных или отдельного mock-сервера.

### Необязательный native C17 track

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Эта сборка проверяет нативную подмножину compiler и её тесты. Она не заменяет Python runtime и не подтверждает полную языковую parity.

На Linux x86-64 можно сгенерировать нативный assembly и объектный файл:

```sh
./build/reaper-c --emit-asm examples/native/arithmetic.rpr -o build/arithmetic.s
cc -c build/arithmetic.s -o build/arithmetic.o
```

Генерируемый assembly экспортирует `int reaper_program(int64_t *result)`. Грамматика подмножества и ABI описаны в [документации native compiler](docs/NATIVE_COMPILER.md). Это backend выражений, а не компиляция полноценных `.rpr`-программ.

### Необязательные проверки NOO TAH / Node.js

Установите Node.js из официального дистрибутива и добавьте `node` в `PATH`, затем выполните:

```sh
reaper-noo-tah version
reaper-noo-tah doctor
reaper-noo-tah check app.mjs
reaper-noo-tah run app.mjs
reaper-noo-tah npm run build
```

Команды работают с выбранным локальным Node-проектом. Если сам проект запускает HTTP-сервер, его порт определяется этим проектом; Reaper не предоставляет собственного web-preview URL.

## Воспроизводимые сценарии, примеры и данные

Примеры в репозитории — локальные программы, а не ответы живого API:

- `examples/flow.rpr` — базовый smoke-пример языка.
- `examples/native/` — i64-выражения для проверки генерации native assembly, включая переполнение и деление на ноль.
- `examples/device_audit.rpr` — пример read-only аудита, который после запуска создаёт версионированный JSON-отчёт.
- `tests/` содержит тесты parser, runtime, language service, debugger, реестров и интеграций.
- NOO TAH conformance suite проверяет Node built-ins, ESM/CommonJS, streams, workers, child processes и loopback HTTP/TCP. Публичный тестовый сервис не используется.

Основные сценарии:

1. **Только синтаксис:** `python -m reaper --check examples/flow.rpr`; команда проверяет синтаксис без запуска программы.
2. **Запуск примера:** `python -m reaper examples/flow.rpr`; проверьте вывод результата.
3. **Альтернативный execution engine:** `python -m reaper --engine vm examples/flow.rpr`; сравните с tree-walk engine по умолчанию.
4. **Интерактивный prompt:** `python -m reaper --repl`; выход завершает текущую сессию в памяти.
5. **LSP:** `python -m reaper lsp`; читает framed JSON-RPC из stdin и пишет протокольные сообщения в stdout.
6. **DAP:** `python -m reaper dap`; используйте доверенную локальную программу для запуска и пошаговой отладки.
7. **Node compatibility:** `node --test tests/noo_tah/conformance.test.mjs`; тесты используют loopback networking и Node built-ins.

CLI применяет явные resource limits: по умолчанию один миллион шагов выполнения, 100 000 элементов коллекции, один миллион символов текста, managed heap 64 MiB и 64 одновременно открытых managed files. Значения можно менять документированными CLI-параметрами. Это ограничения интерпретатора, а не OS-level sandbox.

Состояние runtime существует в процессе и в файлах, выбранных оператором. Необязательный `--audit-log PATH` дописывает локальный hash-chained журнал выполнения; `--verify-audit-log PATH` проверяет его. Закрытие процесса завершает активную memory-сессию, но не удаляет исходники или журналы. Browser localStorage, sessionStorage, IndexedDB и cookies отсутствуют.

## Конфигурация, окружение и доверие

Корневого `.env.example`, Docker Compose web stack, hosted-аккаунтов, demo login, CORS policy или настройки HTTPS самого приложения нет. Python runtime работает без Node.js. У NOO TAH есть три документированных environment override:

| Переменная | Назначение | Значение по умолчанию / поведение |
|---|---|---|
| `NOO_TAH_NODE` | путь к исполняемому Node | иначе поиск `node` в `PATH` |
| `NOO_TAH_NPM_CLI` | явный путь к `npm-cli.js` | иначе поиск в типовых путях рядом с выбранным Node |
| `NOO_TAH_NPX_CLI` | явный путь к `npx-cli.js` | иначе поиск в типовых путях рядом с выбранным Node |

Это пути к исполняемым файлам, а не секреты. Не храните credentials в source control. Если Node отсутствует, выводится понятная ошибка `Node.js not found`; если отсутствует npm/npx CLI, сообщение указывает нужный override.

Другие важные переключатели:

- `--check` / `--lint` разбирает программу без запуска.
- `--engine treewalk|vm` выбирает runtime engine.
- `--allow-native-ffi` явно разрешает загрузку native C ABI; используйте только доверенную библиотеку.
- `--steps`, `--items`, `--text-length`, `--heap-bytes` и `--open-resources` задают resource limits.

Интерпретатор языка не является OS sandbox. DAP запускает доверенные локальные файлы; FFI допускает native code; установка npm-пакетов и lifecycle scripts запускают сторонний код с правами текущего пользователя. Не запускайте неизвестные программы или пакеты только потому, что они приведены в примере.

LSP и DAP используют Content-Length framed JSON-RPC через standard input/output, а не hosted HTTP API. Node Inspector может открыть локальную debugging endpoint по явному запросу; она принадлежит выбранному Node-процессу, а не публичному web stand Reaper.

## Работа со Studio и сочетания клавиш

Редактор Windows Studio использует канонический language service для локальной навигации:

| Комбинация / действие | Поведение |
|---|---|
| `Ctrl+Space` | локальное дополнение ключевых слов Reaper, built-ins и символов текущего документа |
| `F12` | переход к декларации в текущем документе |
| Find references | поиск лексических вхождений идентификатора в текущем документе |
| `Ctrl+Shift+R` | переименование лексических вхождений в текущем документе после подтверждения |
| `Ctrl+K` | открытие command palette |
| `Ctrl+Alt+K` | открытие каталога возможностей CODEX-66 |

Эти действия ограничены текущим документом и не выполняют межфайловый semantic refactoring. Conditional breakpoints, evaluate, step-out, полный type inference и cloud AI assistant не заявлены как реализованные возможности.

## Архитектура и структура репозитория

```text
Reaper source (.rpr)
  -> Python lexer / parser / runtime
  -> CLI, REPL или Studio
  -> optional LSP / DAP stdio services

JavaScript project
  -> NOO TAH process manager
  -> official Node.js (V8, libuv, npm, Inspector)

Native C17 track
  -> UTF-8 lexer / Pratt parser / owned AST
  -> verified i64 IR / checked lowering / x86-64 ELF assembly (только integer expressions)
```

| Путь | Содержимое |
|---|---|
| `reaper/` | Python reference runtime, CLI, Studio, language/debug services и NOO TAH |
| `reaper/kora/` | вспомогательные функции стандартной библиотеки Kora |
| `src/`, `include/` | native C17 frontend, проверяемый i64 IR и backend x86-64 assembly |
| `tests/` | Python, protocol, runtime и native тесты |
| `examples/` | локальные программы-примеры `.rpr` |
| `docs/` | язык, IDE, архитектура и границы возможностей |
| `editors/` | поддержка редакторов и protocol notes |
| `.github/workflows/` | CI, native/desktop build и Node compatibility |

Проект не разделён на развёрнутые frontend, backend и mock API. Browser compatibility, browser storage, публичные порты, CORS и HTTPS неприменимы к самому runtime Reaper.

## CI, desktop-артефакты и откат

- [Reaper CI](.github/workflows/ci.yml) запускает тесты Python 3.10/3.11/3.12 и проверяет примеры и контракты.
- [NOO TAH compatibility](.github/workflows/noo-tah.yml) проверяет Node 22 и 24 на Windows, Linux и macOS.
- Native C17 track собирается и тестируется отдельно.
- [Desktop build](.github/workflows/desktop-build.yml) упаковывает Windows Studio в `Reaper-Studio-windows-x64.zip`. Git-тег формата `v*` запускает публикацию релиза.

Workflow artifacts — это скачиваемые результаты сборки, а не live hosted IDE. Для отката распространяемой desktop-версии используйте предыдущий GitHub Release с тегом. Онлайн web service для отката нет. Логи сборки и тестов доступны в GitHub Actions.

## Устранение проблем

| Симптом | Что проверить |
|---|---|
| `python -m reaper` не найден | активируйте virtual environment или запускайте из корня репозитория |
| Studio не открывается | проверьте, что установленный Python содержит Tkinter |
| Node не найден | установите Node.js или задайте путь через `NOO_TAH_NODE` |
| Не найден npm/npx | задайте `NOO_TAH_NPM_CLI` или `NOO_TAH_NPX_CLI` |
| Node project build завершается ошибкой | выполните `reaper-noo-tah doctor` и изучите вывод Node/npm; lifecycle scripts могут запускать сторонний код |
| Native C тесты падают | проверьте CMake 3.16+, компилятор C17 и полный вывод CTest |
| Неверный вывод LSP/DAP | оставляйте stdout для protocol frames; application logs направляйте в stderr |

## Известные ограничения, вклад и лицензия

Python остаётся исполняемой эталонной реализацией. Native C17 backend пока компилирует только signed i64-выражения с `+`, `-`, `*` и `/` в assembly x86-64 System V ELF; объявления, функции, ветвления и полноценные программы ещё не компилируются. LSP symbols/references/rename являются лексическими и ограничены текущим документом; DAP stepping выполняется на уровне операторов; IDE не является OS sandbox. NOO TAH делегирует JavaScript официальному Node, а не реализует собственную версию V8.

Правила разработки, проверки изменений и оформления Pull Request описаны в [CONTRIBUTING.md](CONTRIBUTING.md). Предлагайте изменения через [GitHub Issues](https://github.com/Ivan-VHS/Reaper/issues) или Pull Request. Добавляйте воспроизводимый пример `.rpr`, версии Python/Node/compiler и точную команду с результатом. Запускайте Python tests, а при изменении native track — CMake/CTest. Архитектура и ограничения native backend описаны в [docs/NATIVE_COMPILER.md](docs/NATIVE_COMPILER.md).

Лицензия: [Apache-2.0](LICENSE).

## Соответствие 66 правилам README

Правила вебстенда отражены с учётом реального продукта — локального инструментария разработчика:

| Правила | Покрытие в README |
|---|---|
| 1–11 · назначение и границы | описаны язык/IDE, аудитория, исполняемое и частичное направления, локальная область и отсутствие hosted demo |
| 12–22 · быстрый старт | точная установка Python, CLI, Studio, тесты, native C17 и необязательные Node-команды |
| 23–33 · конфигурация и доступ | документированы три реальные NOO TAH path overrides, CLI-переключатели и границы доверия; фиктивных credentials и `.env` нет |
| 34–44 · данные и поведение | локальные примеры, сценарии, execution quotas, срок хранения audit log, loopback-only tests и ограничения debug |
| 45–55 · архитектура и сборка | описаны пакеты, native sources, примеры, тесты, сервисы и CI-артефакты |
| 56–66 · эксплуатация и поддержка | приведены build/release workflow, откат артефакта, диагностика, известные ограничения, вклад и лицензия |

**Публичного URL Reaper web-playground нет.** Скриншоты Studio и скачиваемые Windows artifacts не являются live web stand.

## Единая оболочка отчёта

JSON-вывод можно обернуть в общий формат метаданных ivan-vhs.report.v1, сохранив исходный результат Reaper:

    python tools/report_envelope.py --tool reaper --version VERSION < result.json

См. docs/REPORT_ENVELOPE.md и schemas/ivan-vhs.report.v1.schema.json. Оболочка сохраняет данные инструмента и фиксирует ограничения результата.
