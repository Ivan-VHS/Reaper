# Reaper — язык программирования с композицией потоков данных

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="Python и native CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Reaper 0.1" src="https://img.shields.io/badge/Reaper-0.1.0-2563EB?style=flat-square">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-111827?style=flat-square">
</p>

<p align="center"><img src="assets/reaper-hero.svg" alt="Язык программирования Reaper с композицией потоков" width="100%"></p>

Reaper — самостоятельный язык программирования с композицией потоков данных, читаемым синтаксисом и ограниченным интерпретатором. В инженерном дереве также есть переносимый фронтенд компилятора, подключаемые host-runtime API и экспериментальное направление native C17. Интерпретатор остаётся эталоном семантики.

**Языки:** [English](README.md) · Русский · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

## Визуальный обзор

<p align="center"><img src="assets/reaper-toolchain-preview.svg" alt="Превью фронтенда компилятора Reaper и пути Quarry IR по исходному коду" width="100%"></p>
<p align="center"><img src="assets/reaper-nine-systems.svg" alt="Архитектура девяти ограниченных host-runtime систем Reaper" width="100%"></p>

<sub>Это SVG-превью, построенные по исходному коду, и схема архитектуры, а не скриншоты реально запущенного терминала. Текст терминала и значения в превью иллюстративные.</sub>

## Язык и runtime

- **Синтаксис потоков:** существующий оператор ~> соединяет преобразования без изменения грамматики Reaper.
- **Интерпретатор:** lexer, parser, AST и ограниченное tree-walking исполнение остаются базовой моделью совместимости.
- **Фронтенд компилятора:** консервативная статическая диагностика, детерминированный Quarry IR с привязкой к исходным позициям, структурная проверка и безопасное сворачивание литералов. Машинный код не генерируется.
- **Host-runtime API:** ограниченные ресурсные области, асинхронные каналы и actors, scoped-capabilities, контрольные снимки состояния приложения, локальная маршрутизация, profiling, capability-gated C ABI и наблюдение за политикой здоровья.
- **Информация о платформе:** команда --target-info сообщает данные хоста, включая определение E2K. Это не означает наличие native backend для MCST.
- **Native C17:** переносимые основы компилятора/runtime и тесты развиваются отдельно от Python-интерпретатора; полная совместимость языковых возможностей не заявляется.

## Запуск примеров

Требуется Python 3.10 или новее. Runtime использует стандартную библиотеку Python.

    git clone https://github.com/Ivan-VHS/Reaper.git
    cd Reaper
    python -m reaper --check examples/flow.rpr
    python -m reaper examples/flow.rpr
    python -m reaper --target-info
    python -m reaper.compiler_cli examples/flow.rpr --optimize

## Сборка и проверка

Запуск тестов Python:

    python -m compileall -q reaper tests
    python -m unittest discover -s tests -v

Сборка и тестирование native C17:

    cmake -S . -B build -DBUILD_TESTING=ON
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

GitHub Actions проверяет Python 3.10, 3.11 и 3.12, запускает примеры интерпретатора, проверяет CLI компилятора и пример архитектуры runtime, а также тестирует native C17-цели. Отдельный HMGA workflow проверяет инженерный контракт репозитория.

## Объединённые инженерные обновления

Ветка интеграции собирает совместимые изменения из открытой истории разработки:

- **Фронтенд компилятора:** Quarry IR с привязкой к исходникам, детерминированные хеши, консервативные статические проверки, структурная валидация и безопасное сворачивание констант.
- **Основы runtime:** ограниченные ресурсы, асинхронные каналы/actors, scoped host-capabilities, контрольные снимки состояния, локальная маршрутизация, profiling, ограниченный C ABI и политика здоровья.
- **E2K-профиль:** только идентификация хоста и явный отчёт о возможностях; генерация native-кода MCST не реализована.
- **Архитектура MOST:** поэтапное отображение системной архитектуры на существующий язык и миграцию C17 без изменения синтаксиса Reaper.
- **HMGA v2/v3:** read-only аудит репозитория и детерминированный каталог из 20 аксиом и 400 операторов native C17 с конечным пределом в 64 раунда.
- **Инженерные проверки:** тесты композиции с учётом сигнатур, проверки Python-версий, native C17 и документированный процесс review/merge.

Исторические прототипы с пересекающимися API actors, effects, ресурсов, relay и health были проверены и дедуплицированы, а не установлены рядом друг с другом. Каноническим остаётся текущий модульный набор host-runtime. Подробности приведены в [аудите интеграции](docs/INTEGRATION_AUDIT_2026-11-19.md).

## Архитектура и документация

- [Справочник языка](LANGUAGE.md)
- [Архитектура платформ](docs/PLATFORM_ARCHITECTURE.md)
- [Справочник девяти runtime-систем](docs/REAPER_SYSTEMS.md)
- [Архитектура циклического runtime](docs/REAPERS_ARCHITECTURE.md)
- [Архитектура MOST](docs/MOST_SYSTEMS_ARCHITECTURE.md)
- [Инженерный стандарт](docs/ENGINEERING_STANDARD.md)
- [Контракт HMGA v2.0](docs/HMGA_V2.0.md)
- [Матрица операторов HMGA v3.0](docs/HMGA_V3.md)
- [Профиль хоста E2K](docs/ELBRUS_E2K.md)
- [Аудит интеграции](docs/INTEGRATION_AUDIT_2026-11-19.md)

## Текущие границы

Reaper 0.1 остаётся языком с приоритетом интерпретатора. Фронтенд компилятора создаёт переносимый IR, а не машинный код. Host API подключаются явно на стороне Python и не становятся скрытыми встроенными возможностями языка или песочницей ОС. Генерация native-кода, JIT, распределённые actors, сетевой транспорт, cloud orchestration и полная поддержка MCST E2K не заявляются.

## Лицензия

Проект распространяется по [Apache License 2.0](LICENSE).
