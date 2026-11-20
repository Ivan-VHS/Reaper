# Reaper — язык программирования с композицией потоков

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Reaper — expression-oriented язык с читаемым синтаксисом и явным потоком данных.** Оператор `::` передаёт значение следующей операции. В репозитории находятся эталонный интерпретатор Python, разрабатываемая нативная реализация C17 и первый компонент self-hosting, написанный на самом Reaper.

## Пример

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Каталог из 666 символических токенов

Reaper включает канонический словарь из 666 уникальных трёхсимвольных лексем без цифр на алфавите `: ; [ { ] } + = _ - *`. Python- и C-лексеры распознают зарезервированные коды; посмотреть их можно командами `reaper --catalog`, `--catalog-group memory` и `reaper --catalog-token ':::'`. Зарезервированные записи пока не являются исполняемыми операциями. См. [каталог токенов](docs/TOKEN_CATALOG.md).

## Что реализовано

- **Эталонная среда Python:** Python 3.10+, tree-walking интерпретатор, lexer, parser, runtime, CLI и тесты на стандартной библиотеке.
- **Ядро языка:** Unicode-идентификаторы, комментарии, строки, функции и closures, рекурсия, неизменяемый `make`, изменяемый `vary` с явным `change`, условия, циклы и композиция потоков.
- **Встроенные операции и диагностика:** конвейеры :: , map/filter/fold/reduce, стабильная сортировка по ключу, chunk/take/drop/flatten/unique, UTF-8-операции над строками, явные преобразования, диагностика с координатами и лимиты исполнения.
- **Метрическая библиотека:** нормы L1/L2/L∞, нормализация, евклидовы/манхэттенские/чебышёвские расстояния, косинусное сходство, угол, проекция и центроид, а также квадратичные формы и неевклидовы модели.
- **CLI:** --lint, постоянный построчный --repl, структурированный --json и замеры --profile.
- **Нативное направление C17:** lexer, expression parser и AST с управлением памятью, проверенный integer Canonical IR, контролируемое свёртывание констант, ограниченный AST-to-IR lowering, начальный CLI и C-тесты.
- **Self-hosting, этап 0 + частичный этап 1:** `selfhost/lexer.rpr` реализует токенизацию, а `selfhost/parser.rpr` — Pratt-парсер выражений на самом Reaper. Он учитывает реальный оператор потока `::`, приоритеты, правоассоциативное `**`, списки, вызовы функций и индексацию. Оба модуля проверяются bootstrap-assertions, Python unit-тестами и CTest. У lexer пока есть ограничение ASCII-идентификаторов; parser ещё не покрывает объявления, блоки и грамматику операторов и не заменяет эталонный frontend. См. [план bootstrap](docs/SELF_HOSTING_BOOTSTRAP.md).
- **MOST:** документированный словарь языка и поэтапный контракт реализации.

Реализация C пока не является полноценным интерпретатором. Полные declarations/blocks, проверка типов, разрешение intent, анализ ownership, генерация native code и WASM ещё не реализованы. Python остаётся эталоном совместимости до подтверждения паритета runtime и CLI.

## Скриншоты

Сейчас это проект языка и runtime, а не графическое приложение. В репозитории нет проверенного скриншота работающего терминала; иллюстративная терминальная графика удалена, чтобы не выдавать её за реальный захват. Фактический вывод можно получить запуском примеров ниже.

## Запуск интерпретатора Python

Требуется Python 3.10 или новее. Сторонние runtime-зависимости отсутствуют.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --repl
python -m reaper --json --profile examples/flow.rpr
python -m unittest discover -s tests -v
```

Установка CLI в editable-режиме:

```bash
python -m pip install -e .
reaper examples/hello.rpr
```

## Сборка нативного ядра C17

Требуются CMake и компилятор с поддержкой C17.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
./build/reaper-c --evolution-status
```

Нативный executable сейчас предоставляет реализованные bring-up и аналитические сценарии; он не является полноценной заменой интерпретатора Python.

## Нативное desktop-приложение

**Reaper Studio** — desktop-среда Windows x64 поверх существующего Python reference runtime: редактирование файлов `.rpr`, открытие и сохранение исходников, синтаксическая проверка, запуск программ и просмотр вывода/ошибок. Разработка ядра C17 продолжается отдельно; полного паритета C runtime пока нет.

- [Релизы Windows x64](https://github.com/Ivan-VHS/Reaper/releases)
- [Сборка приложения и CI-артефакты](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)
- [Последние сборки](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml?query=branch%3Amain)

Успешная сборка публикует `Reaper-Studio-windows-x64.zip`; тег `v*` создаёт GitHub Release. Запуск из исходников (Python 3.10+): `python reaper_desktop.py`.

## Полиглот-система погружения

В Python reference package Reaper добавлена локальная подсистема обучения языкам: несколько языковых профилей, офлайн-библиотека текстов и субтитров, контекстные карточки фраз, интервальное повторение, адаптивный ежедневный план, оценка понятности материалов, журнал занятий и экспорт JSON.

```sh
reaper polyglot init English --native Russian --level A0 --minutes 45
reaper polyglot content add lesson.srt --kind dialogue --level A1
reaper polyglot phrase add "Could you say that again?" --translation "Не могли бы вы повторить?" --context "Вежливая просьба повторить фразу"
reaper polyglot plan
reaper polyglot review
reaper polyglot report
```

Данные хранятся локально в SQLite. Диапазон 70–90% рассчитывается как приближённая доля токенов из уже повторённых карточек, а не как автоматический тест понимания. Воспроизведение медиа, ASR/TTS, автоматический перевод и AI-оценка произношения пока не реализованы. См. [руководство по полиглот-системе](docs/POLYGLOT_IMMERSION.md).

## Дизайн и границы безопасности

Программа проходит токенизацию, парсинг в AST и выполняется ограниченным интерпретатором. Консольные эффекты явные: `emit`, `say`, `ask`. Обычные выражения не получают скрытый доступ к файловой системе, сети, часам, процессам, shell или оборудованию.

Стандартные лимиты включают 1 000 000 шагов, 256 вложенных вызовов, 100 000 элементов коллекции и 1 000 000 символов конкатенации. Это ограничения ресурсов, **а не sandbox безопасности**. Не считайте запуск недоверенного кода изолированным от хост-системы.

## Документация

- [Справочник языка](LANGUAGE.md)
- [Полиглот-система погружения](docs/POLYGLOT_IMMERSION.md)
- [Реализованные расширения runtime и CLI (20.11.2026)](docs/IMPLEMENTATION_UPDATE_2026-11-20.md)
- [Объединённая архитектура REAPER/MOST](docs/REAPER_UNIFIED_ARCHITECTURE.md)
- [План self-hosting bootstrap](docs/SELF_HOSTING_BOOTSTRAP.md)
- [Архитектура](docs/ARCHITECTURE.md)
- [Спецификация MOST](docs/MOST_LANGUAGE_SPEC.md)
- [План миграции на C](docs/C_MIGRATION.md)
- [Примеры](examples/) · [Тесты](tests/)

## CI и лицензия

GitHub Actions тестирует Python 3.10, 3.11 и 3.12, запускает unit-тесты (включая Reaper-written bootstrap lexer и частичный Pratt parser), проверяет пример и выполняет flow-пример. У нативного ядра C есть отдельное покрытие CMake/CTest.

[Apache License 2.0](LICENSE).

> 千里之行，始于足下。 — Путь в тысячу ли начинается с первого шага.


## Execution audit trail

The optional audit mode writes a local hash-chained journal of source fingerprints and run lifecycle events without copying program output. Enable it with --audit-log PATH and verify it with --verify-audit-log PATH. The chain detects record edits but is not a digital signature or remote attestation; see docs/EXECUTION_AUDIT.md. 

## Обновление нативного оптимизатора C17

Проверяемый Canonical IR теперь включает операции целочисленных ADD, SUB, MUL и DIV для типа i64. Оптимизатор сворачивает их, только когда оба операнда являются проверенными константами. Переполнение сложения, вычитания и умножения, деление на ноль и случай INT64_MIN / -1 отклоняются с диагностикой вместо неопределённого поведения.

Итерационный проход остаётся ограниченным бюджетом от 1 до 64 итераций, проверяет IR до и после преобразования и сообщает число итераций и изменённых узлов. Это возможность уровня нативного IR; она не означает полной поддержки всех операций в C-фронтенде или runtime.
