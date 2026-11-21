# Reaper — язык программирования с потоковой композицией

Python 3.10+ · C17 native track · Windows Studio · Apache-2.0 · [CI](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml)

Reaper — язык выражений с явным потоком данных: оператор `::` передаёт значение следующей операции. Python — текущая исполняемая эталонная реализация; C17 — развиваемый нативный путь, пока не полная замена runtime.

## Живой снимок Studio

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio под Windows" width="100%"></p>
<sub>Снимок работающего приложения Windows 11, 1920×1080.</sub>

| Область | Текущая граница |
|---|---|
| Python runtime | lexer, parser, интерпретатор, CLI, REPL, модули, closures, quotas, audit |
| NOO TAH | интеграция официального Node.js: V8/libuv, ESM/CommonJS, системные API, streams, workers, npm/npx, N-API и Inspector; JS run/check/stop в Studio |
| Reaper Studio | Основа Windows IDE: дерево проекта, подсветка, номера строк, поиск, проверка/запуск и отладчик; LSP уже поддерживает диагностику и навигацию по открытым файлам, межфайловая семантика и Git UI пока в плане |
| Native C17 | lexer, expression parser, owned AST, checked IR, limited lowering |
| МОСТ | 54 точных алиаса: 21 исполняемый в reference subset, 33 зарезервированы |
| QCS 1.0 | отдельный hardware-domain parser и JSON AST; без управления hardware |
| THESIS | граф доказательств; утверждения не проверяются автоматически |
| Реестры | 813 предложений; 666 API-контрактов; запись каталога не равна готовой функции |
| Внутренние продукты | 18 встроенных сервисов; Operandu + Dropaul; Python reference runtime |
| Федерация | OPlague snapshots, VentuSample manifests, optional Pytyliki C ABI |

Запуск: `python -m reaper examples/flow.rpr` · Проверка: `python -m reaper --check examples/flow.rpr` · VM: `python -m reaper --engine vm examples/flow.rpr` · REPL: `python -m reaper --repl` · Продукты: `python -m reaper --products` · Dropaul: `python -m reaper --product-info Dropaul` · Тесты: `python -m unittest discover -s tests -v`.

NOO TAH интегрирует официальный кроссплатформенный Node.js: V8, libuv, системные API, ESM/CommonJS, streams, workers, child processes, npm/npx, N-API и Inspector. В Reaper Studio добавлены запуск, проверка и остановка JavaScript, а также диагностика runtime. Команды: `reaper-noo-tah doctor`, `reaper-noo-tah run app.mjs`, `reaper-noo-tah npm run build`. См. [архитектуру NOO TAH](docs/NOO_TAH.md).

Studio: `python reaper_desktop.py` (Windows). Native: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`, затем build и CTest.

```reaper
craft double(value) { yield value * 2 }
make result := [1, 2, 3] :: map(double) :: sum()
emit "result = " ++ text(result)
```

[Контракт IDE 666](docs/IDE_666_IMPLEMENTATION.md) · [Внутренние продукты](docs/INTERNAL_PRODUCTS.md) · [Функции](docs/FEATURES.md) · [Язык](LANGUAGE.md) · [Архитектура](docs/ARCHITECTURE.md) · [Реестр 813](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [Федерация](docs/PROJECT_FEDERATION_MATRIX.md) · [Индекс](docs/README.md)

[English](README.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md) · [Релизы](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)
