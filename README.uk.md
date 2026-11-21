# Reaper — мова програмування з потоковою композицією

Python 3.10+ · C17 native track · Windows Studio · Apache-2.0 · [CI](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml)

Reaper — мова виразів з явним потоком даних: оператор `::` передає значення наступній операції. Python — поточна еталонна реалізація; C17 — нативний напрям у розробці, ще не повна заміна runtime.

## Живий знімок Studio

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio у Windows" width="100%"></p>
<sub>Знімок запущеного Windows 11 застосунку, 1920×1080.</sub>

| Область | Поточна межа |
|---|---|
| Python runtime | lexer, parser, інтерпретатор, CLI, REPL, модулі, closures, quotas, audit |
| Reaper Studio | Windows editor: check/run/debug, breakpoints, variables, call stack |
| Native C17 | lexer, expression parser, owned AST, checked IR, limited lowering |
| МОСТ | 54 точні аліаси: 21 виконуваний у reference subset, 33 зарезервовані |
| QCS 1.0 | окремий hardware-domain parser та JSON AST; без керування hardware |
| THESIS | граф доказів; твердження не перевіряються автоматично |
| Реєстри | 813 пропозицій; 666 API-контрактів; запис каталогу не дорівнює готовій функції |
| Федерація | OPlague snapshots, VentuSample manifests, optional Pytyliki C ABI |

Запуск: `python -m reaper examples/flow.rpr` · Перевірка: `python -m reaper --check examples/flow.rpr` · VM: `python -m reaper --engine vm examples/flow.rpr` · REPL: `python -m reaper --repl` · Тести: `python -m unittest discover -s tests -v`.

Studio: `python reaper_desktop.py` (Windows). Native: CMake configure → build → CTest.

```reaper
craft double(value) { yield value * 2 }
make result := [1, 2, 3] :: map(double) :: sum()
emit "result = " ++ text(result)
```

[Функції](docs/FEATURES.md) · [Мова](LANGUAGE.md) · [Архітектура](docs/ARCHITECTURE.md) · [Реєстр 813](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [Федерація](docs/PROJECT_FEDERATION_MATRIX.md) · [Індекс](docs/README.md)

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Релізи](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)
