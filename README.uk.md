# Reaper — мова програмування з потоковою композицією

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper — виразна мова з читабельним синтаксисом і явним потоком даних.** Оператор `::` передає значення наступній операції. Репозиторій містить еталонний інтерпретатор Python, нативне ядро C17 у розробці та Reaper Studio для Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Приклад мови

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Попередній перегляд Studio

<p align="center"><img src="assets/reaper-terminal-preview.svg" alt="Ілюстративний попередній перегляд термінальної сесії Reaper" width="100%"></p>
<sub>Очікуваний вивід за прикладами репозиторію, а не знімок живого термінала чи desktop-програми. Скриншот Reaper Studio поки не додано.</sub>

## Реалізовані можливості

- **Еталонний runtime:** Python 3.10+, лексер, парсер, tree-walking-інтерпретатор, CLI, REPL і тести на стандартній бібліотеці.
- **Ядро мови:** Unicode-ідентифікатори, функції та замикання, рекурсія, незмінний `make`, змінний `vary` з явним `change`, умови, цикли й композиція потоку.
- **Колекції та метрики:** map/filter/fold/reduce, сортування, зрізи, flatten, UTF-8-утиліти, векторні норми/відстані, проєкції, квадратичні форми та геометрія.
- **Модулі й ресурси:** імпорт/експорт `.rpr`, граф залежностей, діагностика циклів, облік ресурсів, LIFO-регіони, обмежені файлові дескриптори та очищення.
- **Виконання й аудит:** Python bytecode VM, ліміти виконання, JSON, профілювання та журнали з хеш-ланцюгом.
- **Reaper Studio:** редактор Windows з відкриттям/збереженням, перевіркою й запуском, breakpoint, покроковим керуванням, переглядом змінних і стека викликів.
- **Embedded C та FFI:** шаблони проєктів, профілі MCU, бюджет пам’яті й опційний C ABI до довірених бібліотек, зокрема Pytyliki ABI v1.
- **Додаткові системи:** локальний Polyglot; 666 зарезервованих лексем; 66 профілів мов/toolchain; 14 архітектур; матриця MOST 20×20 (400 специфікованих проєкцій) і реалізований валідатор цілісності. Це не 400 виконуваних функцій мови.
- **МОСТ:** точні російські псевдоніми ключових слів REAPER 0.1. Використовуються ті самі parser, AST і runtime; Python-еталон виконує обмежену підмножину, а C17-лексер повертає канонічні написання токенів REAPER. Окремої граматики, морфології, системи типів чи runtime немає.

Нативний напрям C17 містить лексер, expression-парсер, AST з володінням, перевірені цілочисельні операції IR, обмежений lowering, тести оптимізатора та початковий CLI. Це **ще не повноцінний інтерпретатор**. Self-hosting lexer/parser — етап bootstrap, а не заміна Python frontend.

## Запуск інтерпретатора

Потрібен Python 3.10+. Сторонні runtime-залежності не потрібні.

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

Інсталяція CLI: `python -m pip install -e .`. Запуск Reaper Studio у Windows: `python reaper_desktop.py`.

## Збирання ядра C17

Потрібні CMake і компілятор C17.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## Розвиток і межі

Основа мови з’явилася 17 листопада 2026 року: лексер, парсер, інтерпретатор і CLI. Далі main отримав модулі, ліміти, VM, Studio, Polyglot, Embedded C, часткові C17/self-hosting і валідовану матрицю MOST 20×20.

Managed heap — облік поверх алокатора Python, а не фізичний алокатор чи ліміт RSS. Нативний FFI вмикається явно та виконує завантажений код у процесі — використовуйте лише довірені ABI-сумісні бібліотеки. Пошук toolchain перевіряє `PATH`, але не встановлює компілятори. Python залишається еталоном до підтвердження нативного паритету.

## Документація та завантаження

[Мова](LANGUAGE.md) · [Runtime platform](docs/RUNTIME_PLATFORM.md) · [План self-hosting](docs/SELF_HOSTING_BOOTSTRAP.md) · [Каталог токенів](docs/TOKEN_CATALOG.md) · [Embedded C](docs/EMBEDDED_C_WORKBENCH.md) · [Матриця MOST](docs/MOST_400_COMBINATORIAL_MATRIX.md) · [Інженерний стандарт](docs/UNIFIED_ENGINEERING_STANDARD.md) · [Псевдоніми МОСТ](docs/MOST_LANGUAGE_SPEC.md) · [66 правил російського запису](docs/MOST_RUSSIAN_66_RULES.md)

[Релізи Windows](https://github.com/Ivan-VHS/Reaper/releases) · [Збирання desktop](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## Ліцензія

[Apache License 2.0](LICENSE)