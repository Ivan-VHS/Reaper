# Reaper

Reaper — мова системного програмування та локальне середовище розробки для інструментів компілятора, embedded-ПЗ й апаратно-орієнтованих програм.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="Мова Reaper та інструменти розробника" width="100%"></picture>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

**Стан:** доступні еталонне середовище Python, CLI/REPL, основа Windows Studio, служби LSP/DAP через stdio та часткова нативна гілка C17. Паритет нативного компілятора й привілейовані апаратні служби ще не завершені.

## Склад

- Мова Reaper, lexer/parser, еталонне середовище та діагностика.
- CLI, REPL, основа Windows Studio, служби LSP і DAP.
- Експериментальна реалізація на C17; вона ще не має повного паритету з еталонним середовищем.
- NOO TAH делегує виконання JavaScript офіційному Node.js.
- Генерація каркасів Jora та композиція можливостей; пакети каталогу поки є специфікаціями, а не встановлюваними редакторами.

Документи: [Можливості](docs/FEATURES.md) · [MAZA — живі основи](docs/MAZA.md) · [Архітектура](docs/ARCHITECTURE.md) · [Hardware Language](docs/HARDWARE_LANGUAGE.md) · [Фабрика Jora](docs/JORA_APPLICATION_FACTORY.md) · [Studio](docs/REAPER_IDE.md) · [NOO TAH](docs/NOO_TAH.md).

## Швидкий старт

Вимоги: Python 3.10–3.12 для еталонного середовища; Node.js 22/24 для необов’язкових compatibility-тестів; Tkinter для Windows Studio; CMake 3.16+ і компілятор C17 для нативної гілки.

```sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
```

Studio та REPL:

```sh
python reaper_desktop.py
python -m reaper --repl
```

Тести еталонного середовища:

```sh
python -m unittest discover -s tests -v
```

## Архітектура та стан

Еталонне середовище .rpr, часткова нативна реалізація C17, інструменти розробника й зовнішні runtime-адаптери — окремі напрями. Запис у каталозі або план не доводять наявності реалізації.

- [План реалізації](docs/IMPLEMENTATION_ROADMAP.md)
- [Бібліотека Kora](docs/KORA.md)
- [Індекс документації](docs/README.md)
- [Спільні стандарти екосистеми](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/SHARED_STANDARDS.md)

[Внесок у проєкт](CONTRIBUTING.md) · [Безпека](SECURITY.md) · [Apache-2.0](LICENSE)
