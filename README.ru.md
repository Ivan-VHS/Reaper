# Reaper — язык программирования с потоковой композицией

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper — выразительный язык с читаемым синтаксисом и явным потоком данных.** Оператор `::` передаёт значение следующей операции. Репозиторий содержит эталонный интерпретатор Python, развиваемое ядро C17 и Reaper Studio для Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Пример

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Возможности

- **Python runtime:** лексер, парсер, интерпретатор, CLI, REPL, модули, замыкания, коллекции, учёт ресурсов, квоты, bytecode VM, профилирование и аудит с хеш-цепочкой; host-инъектируемые grants поддерживают HMAC-аутентификацию, проверку scope, конечный TTL и отзыв.
- **Reaper Studio:** Windows-редактор с проверкой, запуском, отладкой, breakpoint, просмотром переменных и стека вызовов.
- **Нативный C17:** лексер, expression-парсер, AST с владением, проверяемые integer IR-операции и ограниченный lowering. Это ещё не полный интерпретатор; Python остаётся эталоном.
- **МОСТ:** точные русские псевдонимы ключевых слов REAPER 0.1 над тем же parser/runtime; отдельной семантики или runtime нет.
- **QCS 1.0:** самостоятельный frontend аппаратного синтаксиса: позиции исходника, frame parser, Pratt expressions и JSON AST. Не заменяет `.rpr` и не исполняет аппаратные операции. Команда: `reaper-qcs check examples/qcs_irq.qcs`.
- **Граф утверждений ТЕЗИС:** версионируемые тезисы, связанные с источниками свидетельства, проверка сопоставимости периода и области, статусы ревью и добавляемая история исправлений. Автоматического признания тезиса истинным нет ([описание](docs/THESIS_ASSERTION_GRAPH.md)).
- **Реестр MOST 666:** 666 контрактов API (147 существующих спецификаций + 519 предложений), source inventory и валидатор. Это каталог спецификаций, а не 666 готовых функций.
- **Системы и interop:** Embedded C, профили MCU и бюджеты памяти; opt-in Pytyliki C ABI v1; 66 языков/toolchain, 14 архитектурных профилей и проверяемая матрица MOST 20×20.

## Запуск

Нужен Python 3.10+, сторонние runtime-зависимости отсутствуют.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m pip install -e .
python -m unittest discover -s tests -v
```

Reaper Studio в Windows: `python reaper_desktop.py`.

## Сборка C17

Нужны CMake и компилятор C17.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## Архитектура и ограничения

Python остаётся исполняемым эталоном до подтверждения нативного паритета. Managed heap — учёт поверх аллокатора Python, не физический аллокатор и не лимит RSS. Нативный FFI исполняет доверенный ABI-совместимый код внутри процесса. Поиск toolchain проверяет `PATH`, но не устанавливает компиляторы. МОСТ разрешает имена в канонические символы REAPER; QCS-разбор не доказывает аппаратные контракты.

## Документация

[Граф происхождения утверждений ТЕЗИС](docs/THESIS_ASSERTION_GRAPH.md)

[Anatidae UI/UX](docs/UI_UX_SYSTEM.md) · [12 принципов анимации](docs/DISNEY_MOTION_SYSTEM.md) · [Язык](LANGUAGE.md) · [QCS frontend](docs/QCS_FRONTEND.md) · [Реестр MOST 666](docs/MOST_FUNCTIONS_666.md) · [Спецификация МОСТ](docs/MOST_LANGUAGE_SPEC.md) · [Runtime](docs/RUNTIME_PLATFORM.md) · [Инженерный стандарт](docs/UNIFIED_ENGINEERING_STANDARD.md)


[Управление и согласие](docs/HUMAN_FIRST_GOVERNANCE.md) · [Конституция Anatidae](docs/ANATIDAE_CONSTITUTION.md) · [Дизайн-система](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) · [Архитектура UI/UX](docs/UI_UX_ARCHITECTURE.md) · [12 принципов анимации](docs/DISNEY_MOTION_SYSTEM.md) · [Надёжность клинических систем CSR-120](docs/CLINICAL_SYSTEMS_CSR120.md) · [Статус реализации MOST](docs/MOST_IMPLEMENTATION_STATUS.md) · [Контракт проекта](docs/UNIFIED_PROJECT_CONTRACT.md)
[Релизы Windows](https://github.com/Ivan-VHS/Reaper/releases) · [Сборка desktop](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## Доктрина Anatidae и гарантии языка

- **Согласие и ответственность:** grants от хоста проходят HMAC-аутентификацию и проверку областей действия, имеют ограниченный срок и могут быть отозваны; аудит позволяет проверять решения выполнения.
- **Ограниченное выполнение:** квоты, учёт ресурсов и проверка входных данных задают границы runtime. Интерпретатор Python остаётся эталоном совместимости, пока паритет нативного C17 не подтверждён.
- **Единый контракт языка:** псевдонимы МОСТ используют канонические символы, parser и runtime REAPER; QCS — отдельный frontend проверки, а не исполнитель аппаратных команд.
- **Честный статус реализации:** реестр MOST 666 содержит 147 существующих спецификаций и 519 предложений; это не означает, что реализовано 666 функций. Нативный C17 lowering остаётся частичным.
- **Граница доверенного кода:** нативный FFI выполняет доверенный ABI-совместимый код внутри процесса и не является песочницей для недоверенных расширений.
- **Доступные инструменты и осмысленная анимация:** Studio и редакторские интеграции должны обеспечивать понятное управление с клавиатуры, видимый фокус, читаемую диагностику, локализацию и поддержку уменьшения движения. Анимация проясняет обратную связь, а не скрывает состояние.

Доктрина направляет инженерные решения, но не превращает пункты дорожной карты в реализованные функции runtime.

## Лицензия

[Apache License 2.0](LICENSE)
