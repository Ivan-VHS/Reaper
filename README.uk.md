# Reaper

Reaper — мова системного програмування та локальне середовище розробника для embedded-ПЗ, інструментів компілятора, апаратно-орієнтованих програм і власної мови з композицією потоків.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg">
  <img src="assets/readme/dashboard-light.svg" alt="Огляд Reaper: мова програмування, frontend компілятора, еталонне середовище та інструменти розробника" width="100%">
</picture>

[![Python CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=Python%20CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Останній коміт](https://img.shields.io/github/last-commit/Ivan-VHS/Reaper?style=flat-square)](https://github.com/Ivan-VHS/Reaper/commits/main) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

[Швидкий старт](#швидкий-старт) · [Знімки екрана](#знімки-екрана) · [Архітектура](#архітектура) · [План розвитку](#план-розвитку) · [Документація](docs/README.md) · [Коміти](https://github.com/Ivan-VHS/Reaper/commits/main)

> **Статус:** активна розробка. Наявні еталонне середовище Python, CLI/REPL, основа Windows Studio, сервіси LSP/DAP через stdio та часткова нативна гілка C17. Повна відповідність нативного компілятора й привілейовані апаратні служби ще не завершені.
>
> **Платформи:** середовище Python тестується на 3.10–3.12. Опційна сумісність Node.js перевіряє Node 22/24 у Windows, Linux та macOS. Для Windows Studio потрібен Tkinter. Нативна гілка C17 потребує CMake 3.16+ і компілятора C17.

### Фабрика застосунків Jora

[DuckOS Jora](https://github.com/Ivan-VHS/DuckOS) інтегрується як платформа та магазин застосунків Jora. Кожен створений застосунок отримує власну незалежну назву, яка не повинна містити слово Jora. Із вибраних модулів можливостей, наприклад текстового редактора, аудіоредактора та перекладача, формується окремий продукт, наприклад Sonaris, після чого створюється каркас проєкту Reaper і словники інтерфейсу EN/RU/UK/MOST. Запропоновані назви визначаються можливостями застосунку й не використовують бренд платформи. Варіанти графа можна оптимізувати за збалансованістю, затримкою, модульністю, розширюваністю або мінімальною складністю; вони експортуються в JSON і Mermaid. Докладніше: [фабрика застосунків Jora](docs/JORA_APPLICATION_FACTORY.md). Перші пакети поки є специфікаціями, а не готовими редакторами; створений проєкт проходить статичну перевірку, але не є придатним до встановлення застосунком. У цій версії Reaper — єдиний підключений генератор вихідного коду; додаткові компіляторні адаптери ще очікують реалізації.

## Швидкий старт

Створіть середовище та встановіть еталонне середовище Python:

~~~sh
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

Запустіть Studio або інтерактивну консоль:

~~~sh
python reaper_desktop.py
python -m reaper --repl
~~~

Перевірте Python-тести:

~~~sh
python -m compileall -q reaper tests
python -m unittest discover -s tests -v
~~~

## Можливості

| Компонент | Поточна поведінка | Межа |
|---|---|---|
| Python runtime | Лексер, парсер, інтерпретатор, модулі, замикання, квоти ресурсів та журнал аудиту | Поточна виконувана мовна реалізація |
| Статична перевірка | Виведення примітивних/list-типів і діагностика операторів, індексів, змінності та арності викликів | Часткова система типів |
| Reaper Studio | Основа Windows IDE: дерево проєкту, редактор, налагоджувач і системний огляд | Локальний GUI; не керує пристроями наживо |
| LSP | Діагностика, completion, hover, symbols, лексична навігація й форматування через stdio JSON-RPC | Відкритий документ; без міжфайлового семантичного аналізу |
| DAP | Точки зупину за рядками, покрокове виконання, стек і локальні змінні | Обмеження на рівні операторів |
| NOO TAH | Інтеграція процесів з офіційним Node.js, npm/npx та Inspector | Виконання JavaScript делегується Node |
| Нативна гілка C17 | Лексер/парсер, AST, перевірений i64 IR і часткове lowering | Експериментальна частина, не повна сумісність |
| QCS та embedded | Розбір апаратного опису, AST/діагностика та обмежені довідкові утиліти | Аналіз і довідка, не доступ до фізичного обладнання |

Запис у каталозі чи зарезервована назва можливості не означають, що функція реалізована в runtime. Зрілість і межі описані в [Features](docs/FEATURES.md), [Hardware Language](docs/HARDWARE_LANGUAGE.md), [Reaper IDE](docs/REAPER_IDE.md), [NOO TAH](docs/NOO_TAH.md) та [Kora](docs/KORA.md).

## Чим відрізняється Reaper

- Виконувана реалізація `.rpr` існує сьогодні; нативний компілятор відокремлено як часткову гілку.
- CLI, Studio, мовні сервіси й тести використовують спільну реалізацію мови.
- Квоти ресурсів та опційний hash-chained журнал аудиту роблять межі виконання видимими.
- Апаратні концепції оформлені як перевірювані контракти й адаптери, а не як обіцянка привілейованого доступу.
- NOO TAH використовує upstream Node, а не заявляє про власну реалізацію V8 або libuv.

## Знімки екрана

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/workflow-dark.svg">
  <img src="assets/readme/workflow.svg" alt="Потік Reaper від .rpr через лексер і парсер до еталонного середовища та інструментів розробника" width="100%">
</picture>

<p align="center">
  <a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Справжній знімок Reaper Studio у Windows" width="100%"></a>
</p>
<sub>Реальний знімок Windows Studio 1920×1080 зі screenshot workflow репозиторію. SVG вище — архітектурна схема.</sub>

## Архітектура

~~~mermaid
flowchart LR
    A[.rpr source] --> B[Лексер і парсер]
    B --> C[Python reference runtime]
    C --> D[CLI / REPL]
    C --> E[Studio]
    C --> F[LSP / DAP]
    G[Неповна гілка C17] -. окрема часткова реалізація .-> B
    H[JavaScript-проєкт] --> I[NOO TAH]
    I --> J[Офіційний Node.js]
~~~

| Шлях | Призначення |
|---|---|
| `reaper/` | Python runtime, CLI, Studio, мовні/налагоджувальні сервіси та NOO TAH |
| `reaper/kora/` | Допоміжна стандартна бібліотека Kora |
| `src/`, `include/` | Часткова реалізація на C17 |
| `tests/`, `examples/` | Тести runtime/protocol і локальні `.rpr` приклади |
| `docs/`, `editors/` | Мова, IDE, архітектура та підтримка редакторів |
| `.github/workflows/` | CI, native/desktop build, скриншоти й Node compatibility |

## Матриця збирання

| Ціль | Вимоги | Стан |
|---|---|---|
| Python runtime | Python 3.10+ | Виконувана реалізація; CI 3.10/3.11/3.12 |
| Windows Studio | Python із Tkinter | Ціль desktop workflow |
| Нативна гілка C17 | CMake 3.16+, компілятор C17 | Часткова, тестується окремо |
| NOO TAH | Node.js 22 або 24 у поточній CI-матриці | Опційна інтеграція; не потрібна для `.rpr` |
| macOS | Python / Node compatibility job | Не означає підтримку нативної Studio |

## Що змінилося в README Revival

- Перша сторінка розділяє виконуване Python-середовище та неповний нативний компілятор.
- Команди встановлення, перевірки, запуску й тестування розміщені на початку.
- Реальний знімок Windows Studio відокремлено від редагованих схем.
- Точно описано межі LSP, DAP, апаратних адаптерів і Node-інтеграції.

| Було | Стало |
|---|---|
| Загальна обіцянка мовної платформи | Таблиця можливостей і зрілості |
| Статус нативного компілятора можна трактувати широко | Еталонна та часткова гілки розділені |
| Команди потрібно шукати в тексті | Готові команди на початку |
| Загальні заяви про IDE | Межі мовних сервісів за відкритим документом |

## План розвитку

- [x] Python runtime, CLI/REPL та локальні приклади.
- [x] Основа stdio LSP/DAP і Windows Studio.
- [x] Часткові нативні C17 lexer/parser/IR та тестові цілі.
- [ ] Розширення native type/ownership/effect analysis і code generation разом із тестами.
- [ ] Додавати OS-backed MMIO/IRQ/DMA лише через перевірені платформні адаптери та окрему цільову валідацію.

## Екосистема

- [DuckOS](https://github.com/Ivan-VHS/DuckOS) — операційна система та робочий простір Mora.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — дослідження процесорів і обмежені системні утиліти.
- [OPlague](https://github.com/Ivan-VHS/OPlague) — робоча станція доказів щодо пристроїв і драйверів.
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — процедурна генерація семплів та офлайн DSP.

Дивіться [індекс документації](docs/README.md), [архітектуру](docs/ARCHITECTURE.md), [правила внеску](CONTRIBUTING.md) та [опис VS Code syntax support](editors/vscode/README.md). Ліцензія: [Apache-2.0](LICENSE).
