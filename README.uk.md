# Reaper — системна мова та робоче середовище

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **Flow-first-синтаксис. Явні контракти. Діагностика зі збереженням контексту вихідного коду.**

**Відомості про проєкт:** Alpha · доступне еталонне середовище Python · нативна гілка компілятора C17 часткова · Python package 0.1.0 · CMake track 0.2.0 · Apache-2.0 · **Документацію перевірено:** 2026-11-27 UTC

<p align="center"><img src="assets/reaper-hero.svg" alt="Огляд системної мови та робочого середовища Reaper" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Знімок Reaper Studio" width="100%"></a></p>

## Призначення та межі

Reaper — мова системного програмування та локальне середовище розробки. Поточна реалізація розділена на два окремі напрями: еталонне середовище Python та експериментальна нативна реалізація C17. Нативна гілка ще не має повного паритету з еталонним середовищем. Windows Studio, служби LSP/DAP і зовнішні адаптери є окремими інструментальними компонентами.

## Приклад мови

Мова `.rpr` використовує flow-first-вирази й оператор `::`: значення ліворуч передається першим аргументом функції праворуч.

~~~reaper
craft double(value) {
    yield value * 2
}

make values := [1, 2, 3]
make result := values :: map(double) :: sum()
emit "result = " ++ text(result)
~~~

Після встановлення еталонного середовища запустіть приклад із репозиторію:

~~~sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

## Реалізовані компоненти

- **Еталонне середовище мови:** lexer, parser, AST-інтерпретатор, CLI/REPL, структурована діагностика та обмежене виконання.
- **Canonical IR і VM:** доступна для вибору Python bytecode VM поверх Canonical IR; обхід дерева залишається режимом сумісності за замовчуванням.
- **Модулі:** версіоновані імпорти/експорти `.rpr`, ізольовані області видимості, кеш експортів, граф залежностей і діагностика циклів.
- **Статичний аналіз:** консервативне виведення типів для підтримуваних конструкцій AST. Невідомі значення на межах модулів і хоста залишаються `Any`; це ще не повна sound type system.
- **Облік ресурсів:** квоти heap і відкритих файлів, обмеження виконання та детерміноване очищення. Це запобіжники runtime, а не security sandbox для недовірених програм.
- **Нативна гілка C17:** часткові lexer/parser, власний AST, перевірюваний IR, оптимізатор і обмежене lowering. Scalar AOT-підмножина генерує C17 для встановленого toolchain GCC/Clang; повного паритету з reference runtime немає.
- **Реєстр архітектури:** 66 стабільних архітектурних концепцій у дев’яти шарах, точний пошук і обмежена перевірка графа залежностей.
- **Інструменти розробника:** основа Windows Studio, служби LSP/DAP через stdio, помічники Kora та необов’язкова інтеграція NOO TAH. NOO TAH делегує виконання JavaScript офіційному середовищу Node.js.
- **Композиція продуктів:** еталонне середовище надає 18 внутрішньопроцесних продуктових сервісів. Записи каталогу Jora й описи framework не стають автоматично встановлюваними застосунками.

Embedded workbench створює та перевіряє довідкові MCU-проєкти й може викликати встановлені користувачем toolchain. Вбудованого прошивання пристроїв і live hardware debugging немає. MMIO-дескриптори перевіряються через bus, наданий хостом; фізична пам’ять не відображається.

## Збирання та тести

Вимоги: Python 3.10+ для еталонного середовища; CMake 3.16+ і компілятор C17 для нативної гілки; Node.js 22/24 для необов’язкових compatibility-перевірок; Tkinter для Windows Studio.

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

CTest запускає нативні тести C і, якщо знайдено інтерпретатор Python, додаткові перевірки еталонного середовища та репозиторію.

Запуск REPL або встановленої Studio:

~~~sh
python -m reaper --repl
reaper-studio
~~~

## Інтеграції та межі довіри

- Знімки пристроїв OPlague імпортуються як версіонований JSON і порівнюються offline.
- Виклики C ABI Pytyliki потребують явного ввімкнення та вибору довіреної ABI-сумісної бібліотеки стороною-викликом.
- Обмін із VentuSample використовує manifest: Reaper читає оголошені метадані й не змінює WAV-файли.
- Федерація OCTA-8 фіксує peer-контракти; вона не створює центрального середовища виконання й не надає привілеїв.

Ефекти файлової системи, процесів, мережі, годинника, shell і native-бібліотек мають залишатися явними або opt-in. Native FFI виконує код усередині процесу й повинен завантажувати лише довірені бібліотеки.

## Документація

- [Можливості](docs/FEATURES.md) · [Архітектура](docs/ARCHITECTURE.md)
- [Нативний компілятор](docs/NATIVE_COMPILER.md) · [Hardware Language](docs/HARDWARE_LANGUAGE.md)
- [Ліміти runtime](docs/RUNTIME_PLATFORM.md) · [Бібліотека Kora](docs/KORA.md)
- [Studio та IDE](docs/REAPER_IDE.md) · [Фабрика Jora](docs/JORA_APPLICATION_FACTORY.md)
- [План реалізації](docs/IMPLEMENTATION_ROADMAP.md) · [Індекс документації](docs/README.md)
- [NOO TAH JavaScript boundary](docs/NOO_TAH.md)
- [Shared ecosystem standards](https://github.com/Ivan-VHS/DAK/blob/main/docs/UNIFIED_DOCUMENTATION_STANDARD.md)

## Участь і ліцензія

Перед зміною семантики мови, стадій компілятора або публічних контрактів прочитайте [CONTRIBUTING.md](CONTRIBUTING.md). Зберігайте зміни перевірюваними й додавайте детерміновані тести. Інформація про безпеку — у [SECURITY.md](SECURITY.md).

Ліцензія проєкту — [Apache-2.0](LICENSE). Назви зовнішніх проєктів і торговельні марки належать їхнім правовласникам.

---
<p align="center"><sub>Reaper · перевірка README 2026-11-27 UTC</sub></p>
