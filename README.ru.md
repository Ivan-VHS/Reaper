# Reaper — системный язык и рабочая среда

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **Flow-first-синтаксис. Явные контракты. Диагностика с сохранением контекста исходника.**

**Сведения о проекте:** Alpha · доступна эталонная среда Python · нативная ветка компилятора C17 частичная · Python package 0.1.0 · CMake track 0.2.0 · Apache-2.0 · **Документация проверена:** 2026-11-27 UTC

<p align="center"><img src="assets/reaper-hero.svg" alt="Обзор системного языка и рабочей среды Reaper" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Снимок Reaper Studio" width="100%"></a></p>

## Назначение и границы

Reaper — язык системного программирования и локальная среда разработки. Текущая реализация разделена на два самостоятельных направления: эталонная среда Python и экспериментальная нативная реализация C17. Нативная ветка пока не обладает полным паритетом с эталонной средой. Windows Studio, службы LSP/DAP и внешние адаптеры являются отдельными инструментальными компонентами.

## Пример языка

Язык `.rpr` использует flow-first-выражения и оператор `::`: значение слева передаётся первым аргументом функции справа.

~~~reaper
craft double(value) {
    yield value * 2
}

make values := [1, 2, 3]
make result := values :: map(double) :: sum()
emit "result = " ++ text(result)
~~~

После установки эталонной среды запустите пример из репозитория:

~~~sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

## Реализованные компоненты

- **Эталонная среда языка:** lexer, parser, AST-интерпретатор, CLI/REPL, структурированная диагностика и ограниченное выполнение.
- **Canonical IR и VM:** выбираемая Python bytecode VM поверх Canonical IR; обход дерева остаётся режимом совместимости по умолчанию.
- **Модули:** версионированные импорты/экспорты `.rpr`, изолированные области видимости, кэш экспортов, граф зависимостей и диагностика циклов.
- **Статический анализ:** консервативный вывод типов для поддерживаемых конструкций AST. Неизвестные значения на границах модулей и хоста остаются `Any`; это ещё не полная sound type system.
- **Учёт ресурсов:** квоты heap и открытых файлов, лимиты выполнения и детерминированная очистка. Это ограничения среды выполнения, а не security sandbox для недоверенных программ.
- **Нативная ветка C17:** частичные lexer/parser, собственный AST, проверяемый IR, оптимизатор и ограниченное lowering. Scalar AOT-подмножество генерирует C17 для установленного toolchain GCC/Clang; полного паритета с reference runtime нет.
- **Реестр архитектуры:** 66 стабильных архитектурных концепций в девяти слоях, точный поиск и ограниченная проверка графа зависимостей.
- **Инструменты разработчика:** основа Windows Studio, службы LSP/DAP через stdio, помощники Kora и необязательная интеграция NOO TAH. NOO TAH передаёт выполнение JavaScript официальной среде Node.js.
- **Композиция продуктов:** эталонная среда предоставляет 18 внутрипроцессных продуктовых сервисов. Записи каталога Jora и описания framework не становятся автоматически устанавливаемыми приложениями.

Embedded workbench создаёт и проверяет справочные MCU-проекты и может вызывать установленные пользователем toolchain. Встроенной прошивки устройств и live hardware debugging нет. MMIO-дескрипторы проверяются через bus, предоставленный хостом; физическая память не отображается.

## Сборка и тесты

Требования: Python 3.10+ для эталонной среды; CMake 3.16+ и компилятор C17 для нативной ветки; Node.js 22/24 для необязательных compatibility-проверок; Tkinter для Windows Studio.

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

CTest запускает нативные тесты C и, если найден интерпретатор Python, дополнительные проверки эталонной среды и репозитория.

Запуск REPL или установленной Studio:

~~~sh
python -m reaper --repl
reaper-studio
~~~

## Интеграции и границы доверия

- Снимки устройств OPlague импортируются как версионированный JSON и сравниваются offline.
- Вызовы C ABI Pytyliki требуют явного включения и выбора доверенной ABI-совместимой библиотеки вызывающей стороной.
- Обмен с VentuSample основан на manifest: Reaper читает объявленные метаданные и не изменяет WAV-файлы.
- Федерация OCTA-8 фиксирует peer-контракты; она не создаёт центральную среду выполнения и не выдаёт привилегии.

Эффекты файловой системы, процессов, сети, часов, shell и native-библиотек должны оставаться явными или opt-in. Native FFI выполняет код внутри процесса и должен загружать только доверенные библиотеки.

## Документация

- [Возможности](docs/FEATURES.md) · [Архитектура](docs/ARCHITECTURE.md)
- [Нативный компилятор](docs/NATIVE_COMPILER.md) · [Hardware Language](docs/HARDWARE_LANGUAGE.md)
- [Лимиты runtime](docs/RUNTIME_PLATFORM.md) · [Библиотека Kora](docs/KORA.md)
- [Studio и IDE](docs/REAPER_IDE.md) · [Фабрика Jora](docs/JORA_APPLICATION_FACTORY.md)
- [План реализации](docs/IMPLEMENTATION_ROADMAP.md) · [Индекс документации](docs/README.md)
- [Интеграция HARVEST и Reaper](docs/HARVEST_REAPER_INTEGRATION.md)
- [Общие стандарты экосистемы](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

## Участие и лицензия

Перед изменением семантики языка, стадий компилятора или публичных контрактов прочитайте [CONTRIBUTING.md](CONTRIBUTING.md). Сохраняйте изменения проверяемыми и добавляйте детерминированные тесты. Информация о безопасности — в [SECURITY.md](SECURITY.md).

Лицензия проекта — [Apache-2.0](LICENSE). Названия внешних проектов и товарные знаки принадлежат их правообладателям.

---
<p align="center"><sub>Reaper · проверка README 2026-11-27 UTC</sub></p>
