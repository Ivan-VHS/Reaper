# Reaper — язык программирования с потоковой композицией

[CI](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) · [Сборка Windows Studio](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml) · Python 3.10+ reference runtime · нативная ветка C17 · Windows Studio · Apache-2.0
**Разработчик:** [Ivan-VHS](https://github.com/Ivan-VHS)

Reaper — язык выражений с явным потоком данных: оператор `::` передаёт значение следующей операции. Python runtime остаётся текущей исполняемой эталонной реализацией. Реализация на C17 развивается отдельно и пока не заменяет runtime полностью.

## Реальный снимок Reaper Studio

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio под Windows 11" width="100%"></p>
<sub>Реальный снимок Windows 11 из сборки Studio с Node.js, 1920×1080.</sub>

## Актуальная матрица возможностей

| Область | Реализованные функции и границы |
|---|---|
| Python runtime | lexer, parser, интерпретатор, CLI, REPL, модули, closures, quotas и audit |
| Reaper Studio | основа Windows IDE: дерево проекта, редактор, подсветка, номера строк, поиск, check/run и отладчик |
| LSP | stdio-сервис: инкрементальные UTF-16-документы, диагностика parser/structure, completion, hover, symbols и лексическая навигация; анализ в пределах открытого файла |
| DAP | stdio debug adapter: запуск, построчные breakpoints, пошаговое выполнение операторов, stack и локальные переменные |
| Деление и распределение | проверенное деление Евклида, сбалансированное разбиение работ и пропорциональное распределение |
| NOO TAH | интеграция официального Node.js: V8/libuv, ESM/CommonJS, core APIs, streams, workers, npm/npx, N-API и Inspector; JS Run/Check/Debug/Stop в Studio |
| Внутренние плагины | 18 встроенных сервисов с lifecycle-состоянием и ограниченным dispatch; Python reference runtime |
| Kora | 66 стандартных utility-функций в семи модулях с манифестами; три Lua ReaScript для Cockos REAPER |
| Native C17 | lexer, expression parser, owned AST, checked IR и ограниченный lowering; без полного паритета с Python runtime |
| МОСТ | 54 точных алиаса: 21 исполняется в текущем reference subset, 33 зарезервированы лексически |
| QCS 1.0 | отдельный hardware-domain parser и JSON AST; без управления оборудованием |
| THESIS | типизированный граф доказательств; утверждения автоматически не подтверждаются |
| Реестры | 813 предложений функций, 666 API-контрактов и 666 зарезервированных лексем; запись реестра не означает готовую реализацию |
| Федерация | snapshots OPlague, manifests VentuSample и опциональный Pytyliki C ABI |

## Движение интерфейса и доступность

Reaper Studio сохраняет настройки **Reduce Motion** и **Eco / Low-CPU Visuals** отдельно от темы оформления. При включении переходы ограничиваются 80 мс, а пространственные и необязательные эффекты отключаются. **Sync to Transport / BPM** недоступен: Studio пока не предоставляет аудиотранспорт и источник темпа. См. [контракт движения интерфейса](docs/UI_MOTION.md).

## Сервисы языка и отладки

Инструменты редактора предоставляют stdio-протоколы:

```sh
python -m reaper lsp
python -m reaper dap
```

Установленные entry points: `reaper-lsp` и `reaper-dap`. LSP обеспечивает инкрементальные функции языка на уровне документа. DAP отлаживает программы Reaper. Сервисы используют канонический Python parser/runtime и не означают полного паритета C17, межфайлового семантического анализа или наличия готового VS Code-клиента.

Подробности и ограничения: [архитектура REAPER IDE](docs/REAPER_IDE.md).

## NOO TAH — среда Node.js

NOO TAH управляет официальной кроссплатформенной сборкой Node.js, а не имитирует её движок. V8, libuv, системные модули, ESM/CommonJS, streams, workers, child processes, npm/npx, N-API и Inspector предоставляются выбранным дистрибутивом Node.

Reaper Studio распознаёт проекты `.js`, `.mjs` и `.cjs`; доступны JS Run, JS Check, JS Debug через Node Inspector, JS Stop, npm-команды и диагностика runtime. Node Inspector пока не преобразуется в панели нативного DAP-отладчика.

```sh
reaper-noo-tah version
reaper-noo-tah doctor
reaper-noo-tah run app.mjs
reaper-noo-tah check app.js
reaper-noo-tah npm run build
node --test tests/noo_tah/conformance.test.mjs
```

Тесты совместимости проверяют метаданные runtime, ESM/CommonJS, файловый ввод-вывод, crypto, streams/backpressure, loopback HTTP/TCP, workers, child processes, DNS и порядок event loop. CI-матрица использует Node 22 и 24 на Windows, Linux и macOS. См. [архитектуру NOO TAH](docs/NOO_TAH.md).

## Kora и приложения для Cockos REAPER

Kora содержит 66 стандартных utility-функций в модулях ZDORO, DILLY, BAPLAP, KALI, PYEMONT, LIUR и SRETUO. Также доступны три Lua ReaScript:

- **Track Health Dashboard** — диагностика проекта и дорожек без изменений.
- **Prefix Selected Tracks** — переименование выбранных дорожек одной undoable-операцией.
- **Marker and Region Report** — список маркеров и регионов в ReaScript console.

В Cockos REAPER откройте **Actions → Show action list → ReaScript → Load** и выберите скрипт из `reaper_scripts/kora/`. Это скрипты для встроенного хоста REAPER, а не скомпилированные VST/AU/CLAP-эффекты. Отдельный процесс Node.js для них не нужен. См. [Kora для REAPER](docs/KORA_REAPER.md).

## Запуск, тесты и сборка

```sh
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

Windows Studio: `python reaper_desktop.py`.

Нативная ветка C17:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Пример:

```reaper
craft double(value) { yield value * 2 }
make result := [1, 2, 3] :: map(double) :: sum()
emit "result = " ++ text(result)
```

[Контракт IDE 666](docs/IDE_666_IMPLEMENTATION.md) · [LSP/DAP](docs/REAPER_IDE.md) · [Node.js](docs/NOO_TAH.md) · [Kora для REAPER](docs/KORA_REAPER.md) · [Плагины](docs/PLUGINS.md) · [Внутренние продукты](docs/INTERNAL_PRODUCTS.md) · [Функции](docs/FEATURES.md) · [Язык](LANGUAGE.md) · [Архитектура](docs/ARCHITECTURE.md) · [Реестр 813](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [Федерация](docs/PROJECT_FEDERATION_MATRIX.md) · [Индекс](docs/README.md)

[English](README.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md) · [Релизы](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)
