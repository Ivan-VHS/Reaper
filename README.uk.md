# Reaper — мова програмування з композицією потоків

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Reaper — expression-oriented мова з читабельним синтаксисом і явним потоком даних.** Оператор `::` передає значення наступній операції. Репозиторій містить еталонний інтерпретатор Python і розроблювану нативну реалізацію C17.

## Приклад

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Каталог із 666 символічних токенів

Reaper містить канонічний словник із 666 унікальних трисимвольних лексем без цифр на алфавіті `: ; [ { ] } + = _ - *`. Python- і C-лексери розпізнають зарезервовані коди; переглянути їх можна командами `reaper --catalog`, `reaper --catalog-group memory` та `reaper --catalog-token ':::'`. Зарезервовані записи поки не є виконуваними операціями. Див. [каталог токенів](docs/TOKEN_CATALOG.md).

## Що реалізовано

- **Еталонне середовище Python:** Python 3.10+, tree-walking інтерпретатор, lexer, parser, runtime, CLI та тести на стандартній бібліотеці.
- **Ядро мови:** Unicode-ідентифікатори, коментарі, рядки, функції й closures, рекурсія, незмінний `make`, змінний `vary` з явним `change`, умови, цикли та композиція потоків.
- **Вбудовані операції й діагностика:** операції над колекціями, явні перетворення, помилки lexer/parser/runtime з прив’язкою до джерела та ліміти виконання.
- **Нативний напрям C17:** lexer, expression parser і AST з керуванням пам’яттю, перевірений integer Canonical IR, контрольоване згортання ADD/SUB/MUL/DIV для signed i64 з відхиленням переповнення й ділення на нуль, обмежений AST-to-IR lowering, початковий CLI та C-тести.
- **MOST:** документований словник мови й поетапний контракт реалізації.

Реалізація C поки не є повним інтерпретатором. Повні declarations/blocks, перевірка типів, розв’язання intent, аналіз ownership, генерація native code та WASM ще не реалізовані. Python залишається еталоном сумісності до підтвердження паритету runtime і CLI.

## Скріншоти

Зараз це проєкт мови та runtime, а не графічний застосунок. У репозиторії немає перевіреного скриншота живого термінала; ілюстративну графіку термінала прибрано, щоб не видавати її за справжнє захоплення. Реальний вивід можна отримати запуском прикладів нижче.

## Запуск інтерпретатора Python

Потрібен Python 3.10 або новіший. Сторонні runtime-залежності відсутні.

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m unittest discover -s tests -v
```

Встановлення CLI в editable-режимі:

```bash
python -m pip install -e .
reaper examples/hello.rpr
```

## Збирання нативного ядра C17

Потрібні CMake та компілятор із підтримкою C17.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
./build/reaper-c --evolution-status
```

Нативний executable наразі надає реалізовані bring-up та аналізувальні сценарії; він не замінює інтерпретатор Python.

## Нативний desktop-застосунок

**Reaper Studio** — desktop-середовище Windows x64 на базі наявного Python reference runtime: редагування файлів `.rpr`, відкриття та збереження коду, перевірка синтаксису, запуск програм і перегляд виводу/помилок. Розробка ядра C17 триває окремо; повної паритетності C runtime ще немає.

- [Релізи Windows x64](https://github.com/Ivan-VHS/Reaper/releases)
- [Збирання застосунку та CI-артефакти](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)
- [Останні збирання](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml?query=branch%3Amain)

Успішна збірка публікує `Reaper-Studio-windows-x64.zip`; тег `v*` створює GitHub Release. Запуск із вихідного коду (Python 3.10+): `python reaper_desktop.py`.

## Поліглот-система занурення

У Python reference package Reaper додано локальну підсистему вивчення мов: кілька мовних профілів, офлайн-бібліотеку текстів і субтитрів, контекстні картки фраз, інтервальне повторення, адаптивний щоденний план, оцінку зрозумілості матеріалів, журнал занять та експорт JSON.

```sh
reaper polyglot init English --native Ukrainian --level A0 --minutes 45
reaper polyglot content add lesson.srt --kind dialogue --level A1
reaper polyglot phrase add "Could you say that again?" --translation "Не могли б ви повторити?" --context "Ввічливе прохання повторити фразу"
reaper polyglot plan
reaper polyglot review
reaper polyglot report
```

Дані зберігаються локально в SQLite.

Профілі також зберігають тип письма, тональність, фонетичний фокус і тимчасовий міст транслітерації. Картки підтримують особисті приклади й необов’язковий частотний ранг від користувача; звіт показує приблизний етап за накопиченими годинами практики. Це навчальні орієнтири, а не прогноз рівня володіння мовою. Діапазон 70–90% є приблизною часткою токенів із повторених карток, а не автоматичним тестом розуміння. Відтворення медіа, ASR/TTS, автоматичний переклад та AI-оцінювання вимови ще не реалізовані. Див. [посібник із поліглот-системи](docs/POLYGLOT_IMMERSION.md).

## Дизайн і межі безпеки

Програма проходить токенізацію, парсинг в AST і виконується обмеженим інтерпретатором. Консольні ефекти явні: `emit`, `say`, `ask`. Звичайні вирази не отримують прихованого доступу до файлової системи, мережі, годинника, процесів, shell чи обладнання.

Стандартні ліміти включають 1 000 000 кроків, 256 вкладених викликів, 100 000 елементів колекції та 1 000 000 символів конкатенації. Це обмеження ресурсів, **а не sandbox безпеки**. Не вважайте запуск недовіреного коду ізольованим від хост-системи.

## Self-hosting frontend: перевірена часткова реалізація

Reaper уже виконує частину логіки frontend власною мовою, але **ще не є self-hosting-компілятором**.

- **Stage 0 — lexer:** selfhost/lexer.rpr сканує підтримувану ASCII-орієнтовану підмножину токенів і створює записи з координатами у вихідному коді. Сумісність Unicode-ідентифікаторів із Python lexer ще не завершена.
- **Stage 1 — Pratt expression parser:** selfhost/parser.rpr розбирає літерали, імена, унарні та згруповані вирази, списки, виклики функцій, індексацію й інфіксні оператори. Таблиця пріоритетів містить потоковий оператор :: і правоасоціативне піднесення до степеня (**).
- **Еталонна реалізація:** Python parser та AST залишаються oracle сумісності. Парсер на Reaper повертає проміжне подання-масив; граматика оголошень і операторів та відповідність канонічному AST ще не реалізовані.

Запуск цільових bootstrap-тестів:

~~~bash
python -m unittest discover -s tests -p 'test_self_hosting.py' -v
~~~

Див. [контракт етапів self-hosting](docs/SELF_HOSTING_BOOTSTRAP.md), [парсер на Reaper](selfhost/parser.rpr) і [lexer на Reaper](selfhost/lexer.rpr). Етап вважається реалізованим лише в межах, підтверджених тестами; самої наявності файла недостатньо.

## Документація

- [Довідник мови](LANGUAGE.md)
- [Поліглот-система занурення](docs/POLYGLOT_IMMERSION.md)
- [Об’єднана архітектура REAPER/MOST](docs/REAPER_UNIFIED_ARCHITECTURE.md)
- [Архітектура](docs/ARCHITECTURE.md)
- [Специфікація MOST](docs/MOST_LANGUAGE_SPEC.md)
- [План переходу на C](docs/C_MIGRATION.md)
- [Приклади](examples/) · [Тести](tests/)

## CI та ліцензія

GitHub Actions тестує Python 3.10, 3.11 і 3.12, запускає unit-тести, перевіряє приклад і виконує flow-приклад. Нативне ядро C має окреме покриття CMake/CTest.

[Apache License 2.0](LICENSE).

> 千里之行，始于足下。 — Подорож у тисячу миль починається з першого кроку.


## Перевірювана цілочисельна арифметика Canonical IR

Нативний IR підтримує додавання, віднімання, множення й ділення i64. Згортання виконується лише для двох констант; переповнення signed i64, ділення на нуль і INT64_MIN / -1 повертають діагностику. Fixed-point pipeline обмежений бюджетом 1–64 ітерації з перевіркою IR до та після кожного проходу. Це гарантія рівня IR, а не твердження про повний паритет C-фронтенду чи runtime.
