# Reaper — язык программирования с потоковой композицией

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper — выразительный язык с читаемым синтаксисом и явным потоком данных.** Оператор `::` передаёт значение следующей операции. Репозиторий содержит эталонный интерпретатор Python, развиваемое ядро C17 и Reaper Studio для Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Пример языка

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Предпросмотр Studio

<p align="center"><img src="assets/reaper-terminal-preview.svg" alt="Иллюстративный предпросмотр терминальной сессии Reaper" width="100%"></p>
<sub>Ожидаемый вывод по примерам в репозитории, а не снимок живого терминала или desktop-приложения. Скриншот Reaper Studio пока не добавлен.</sub>

## Реализованные возможности

- **Эталонный runtime:** Python 3.10+, лексер, парсер, tree-walking-интерпретатор, CLI, REPL и тесты на стандартной библиотеке.
- **Ядро языка:** Unicode-идентификаторы, функции и замыкания, рекурсия, неизменяемый `make`, изменяемый `vary` с явным `change`, условия, циклы и композиция потока.
- **Коллекции и метрики:** map/filter/fold/reduce, сортировка, срезы, flatten, UTF-8-утилиты, нормы и расстояния векторов, проекции, квадратичные формы и геометрия.
- **Модули и ресурсы:** импорты/экспорты `.rpr`, граф зависимостей, диагностика циклов, учёт ресурсов, LIFO-регионы, ограниченные файловые дескрипторы и очистка.
- **Исполнение и аудит:** Python bytecode VM, лимиты исполнения, JSON, профилирование и журналы с хеш-цепочкой.
- **Reaper Studio:** Windows-редактор с открытием/сохранением, проверкой и запуском кода, breakpoint, пошаговым управлением, просмотром переменных и стека вызовов.
- **Embedded C и FFI:** шаблоны проектов, профили MCU, бюджет памяти и опциональный C ABI к доверенным библиотекам, включая Pytyliki ABI v1.
- **Дополнительные системы:** локальный Polyglot; 666 зарезервированных лексем; 66 профилей языков/toolchain; 14 архитектур; матрица MOST 20×20 (400 специфицированных проекций) и реализованный валидатор целостности. Это не 400 исполняемых функций языка.

Нативная ветка C17 включает лексер, expression-парсер, AST с владением, проверяемые целочисленные операции IR, ограниченный lowering, тесты оптимизатора и начальный CLI. Это **ещё не полноценный интерпретатор**. Self-hosting lexer/parser — этап bootstrap, а не замена Python frontend.

## Запуск интерпретатора

Требуется Python 3.10+. Сторонние runtime-зависимости не нужны.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

Установка CLI: `python -m pip install -e .`. Запуск Reaper Studio в Windows: `python reaper_desktop.py`.

## Сборка ядра C17

Нужны CMake и компилятор C17.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## Развитие и границы

Языковая основа появилась 17 ноября 2026 года: лексер, парсер, интерпретатор и CLI. Затем main получил модули, лимиты, VM, Studio, Polyglot, Embedded C, частичные C17/self-hosting и валидируемую матрицу MOST 20×20.

Managed heap — учёт поверх аллокатора Python, а не физический аллокатор или лимит RSS. Нативный FFI включается явно и исполняет загруженный код внутри процесса — используйте только доверенные ABI-совместимые библиотеки. Поиск toolchain проверяет `PATH`, но не устанавливает компиляторы. Python остаётся эталоном до подтверждения нативного паритета.

## Документация и загрузки

[Язык](LANGUAGE.md) · [Runtime platform](docs/RUNTIME_PLATFORM.md) · [План self-hosting](docs/SELF_HOSTING_BOOTSTRAP.md) · [Каталог токенов](docs/TOKEN_CATALOG.md) · [Embedded C](docs/EMBEDDED_C_WORKBENCH.md) · [Матрица MOST](docs/MOST_400_COMBINATORIAL_MATRIX.md) · [Инженерный стандарт](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Релизы Windows](https://github.com/Ivan-VHS/Reaper/releases) · [Сборка desktop](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## Лицензия

[Apache License 2.0](LICENSE)