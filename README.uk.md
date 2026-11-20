# Reaper — мова програмування з потоковою композицією

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper — виразна мова з читабельним синтаксисом і явним потоком даних.** Оператор `::` передає значення наступній операції. Репозиторій містить еталонний інтерпретатор Python, нативне ядро C17 у розробці та Reaper Studio для Windows.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Приклад

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Можливості

- **Python runtime:** лексер, парсер, інтерпретатор, CLI, REPL, модулі, замикання, колекції, облік ресурсів, квоти, bytecode VM, профілювання й аудит із хеш-ланцюгом.
- **Reaper Studio:** редактор Windows із перевіркою, запуском, налагодженням, breakpoint, переглядом змінних і стека викликів.
- **Нативний C17:** лексер, expression-парсер, AST із володінням, перевірені integer IR-операції та обмежений lowering. Це ще не повний інтерпретатор; Python лишається еталоном.
- **МОСТ:** точні російські псевдоніми ключових слів REAPER 0.1 над тим самим parser/runtime; окремої семантики чи runtime немає.
- **QCS 1.0:** окремий frontend апаратного синтаксису: позиції джерела, frame parser, Pratt expressions і JSON AST. Не замінює `.rpr` та не виконує апаратні операції. Команда: `reaper-qcs check examples/qcs_irq.qcs`.
- **Реєстр MOST 666:** 666 API-контрактів (147 наявних специфікацій + 519 пропозицій), source inventory і валідатор. Це каталог специфікацій, а не 666 готових функцій.
- **Системи й interop:** Embedded C, профілі MCU та бюджети пам’яті; opt-in Pytyliki C ABI v1; 66 мов/toolchain, 14 архітектурних профілів і перевірена матриця MOST 20×20.

## Запуск

Потрібен Python 3.10+, сторонніх runtime-залежностей немає.

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

Reaper Studio у Windows: `python reaper_desktop.py`.

## Збирання C17

Потрібні CMake і компілятор C17.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## Архітектура та межі

Python залишається виконуваним еталоном до підтвердження нативного паритету. Managed heap — облік поверх алокатора Python, а не фізичний алокатор чи ліміт RSS. Нативний FFI виконує довірений ABI-сумісний код у процесі. Пошук toolchain перевіряє `PATH`, але не встановлює компілятори. МОСТ зіставляє імена з канонічними символами REAPER; QCS не доводить апаратні контракти.

## Документація

[Anatidae UI/UX](docs/UI_UX_SYSTEM.md) · [12 принципів анімації](docs/DISNEY_MOTION_SYSTEM.md) · [Мова](LANGUAGE.md) · [QCS frontend](docs/QCS_FRONTEND.md) · [Реєстр MOST 666](docs/MOST_FUNCTIONS_666.md) · [Специфікація МОСТ](docs/MOST_LANGUAGE_SPEC.md) · [Runtime](docs/RUNTIME_PLATFORM.md) · [Інженерний стандарт](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Релізи Windows](https://github.com/Ivan-VHS/Reaper/releases) · [Збирання desktop](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## Ліцензія

[Apache License 2.0](LICENSE)
