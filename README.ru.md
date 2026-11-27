# Reaper

Reaper — язык системного программирования и локальная среда разработки для компиляторных инструментов, embedded-ПО и аппаратно-ориентированных программ.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="Язык Reaper и инструменты разработчика" width="100%"></picture>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

**Состояние:** доступны эталонная среда Python, CLI/REPL, основа Windows Studio, службы LSP/DAP через stdio и частичная нативная ветка C17. Паритет нативного компилятора и привилегированные аппаратные службы ещё не завершены.

## Состав

- Исходный язык Reaper, lexer/parser, эталонная среда и диагностика.
- CLI, REPL, основа Windows Studio, службы LSP и DAP.
- Экспериментальная реализация на C17; она пока не равна по возможностям эталонной среде.
- NOO TAH передаёт выполнение JavaScript официальному Node.js.
- Генерация каркасов Jora и композиция возможностей; пакеты каталога пока являются спецификациями, а не устанавливаемыми редакторами.

Документы: [Возможности](docs/FEATURES.md) · [Архитектура](docs/ARCHITECTURE.md) · [Hardware Language](docs/HARDWARE_LANGUAGE.md) · [Фабрика Jora](docs/JORA_APPLICATION_FACTORY.md) · [Studio](docs/REAPER_IDE.md) · [NOO TAH](docs/NOO_TAH.md).

## Быстрый старт

Требования: Python 3.10–3.12 для эталонной среды; Node.js 22/24 для необязательных compatibility-тестов; Tkinter для Windows Studio; CMake 3.16+ и компилятор C17 для нативной ветки.

```sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
```

Studio и REPL:

```sh
python reaper_desktop.py
python -m reaper --repl
```

Тесты эталонной среды:

```sh
python -m unittest discover -s tests -v
```

## Архитектура и статус

Эталонная среда .rpr, частичная нативная реализация C17, инструменты разработчика и внешние runtime-адаптеры — отдельные направления. Запись в каталоге или план не подтверждают наличие реализации.

- [План реализации](docs/IMPLEMENTATION_ROADMAP.md)
- [Библиотека Kora](docs/KORA.md)
- [Индекс документации](docs/README.md)
- [Общие стандарты экосистемы](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/SHARED_STANDARDS.md)
- [Лестница эволюции проекта](docs/PROJECT_LADDER.md) · [Текущий уровень](.github/project-ladder.v1.json)

[Вклад в проект](CONTRIBUTING.md) · [Безопасность](SECURITY.md) · [Apache-2.0](LICENSE)
