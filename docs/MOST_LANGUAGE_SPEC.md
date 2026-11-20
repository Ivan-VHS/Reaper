# REAPER / МОСТ — спецификация русских псевдонимов

**Статус:** МОСТ — русская запись существующего языка REAPER 0.1. REAPER является единственным источником грамматики, типов значений, операторов, встроенных функций, исполнения, диагностики и совместимости. МОСТ не является отдельным языком или компилятором.

Нормативная спецификация ядра: [LANGUAGE.md](../LANGUAGE.md). Эта страница определяет только таблицу русских написаний и правила их преобразования.

## 1. Архитектурное правило

МОСТ = REAPER + точные русские псевдонимы ключевых слов.

Исходный текст МОСТ преобразуется в те же REAPER-токены, после чего проходит тот же parser, AST, runtime и CLI. Не создаются отдельные:

- грамматика и parser;
- AST, модель типов или семантика;
- name resolver, морфология, stemming или intent resolver;
- стандартная библиотека, runtime, bytecode или ABI;
- компиляторный backend и система пакетов.

Если конструкция отсутствует в REAPER, её нет и в МОСТ. Любое изменение исполнения сначала является изменением REAPER и только затем, при необходимости, получает русский keyword-alias.

## 2. Поддерживаемые точные псевдонимы

| МОСТ | Токен REAPER | Статус |
|---|---|---|
| пусть | make | Python reference: implemented |
| переменная | vary | Python reference: implemented |
| изменить | change | Python reference: implemented |
| функция | craft | Python reference: implemented |
| вернуть | yield | Python reference: implemented |
| вывести | emit | Python reference: implemented |
| если | when | Python reference: implemented |
| иначе | otherwise | Python reference: implemented |
| для | each | Python reference: implemented |
| в | in | Python reference: implemented |
| цикл | loop | Python reference: implemented |
| пока | while | Python reference: implemented |
| истина | true | Python reference: implemented |
| ложь | false | Python reference: implemented |
| ничего | nothing | Python reference: implemented |
| и | and | Python reference: implemented |
| или | or | Python reference: implemented |
| не | not | Python reference: implemented |
| импорт | import | Python reference: implemented |
| экспорт | export | Python reference: implemented |
| как | as | Python reference: implemented |

Таблица является закрытой. Добавлять слова, не имеющие точного соответствия ключевому слову REAPER, запрещено. say, ask, range, map, keep, fold, text, number и остальные встроенные имена REAPER остаются своими существующими именами: они являются функциями/значениями, а не ключевыми словами.

## 3. Исполняемый пример

Следующая программа использует только поддерживаемые конструкции REAPER и работает в его Python reference runtime:

~~~most
функция удвоить(значение) {
    вернуть значение * 2
}

пусть число := 5
переменная сумма := 0

для элемент в range(1, 4) {
    изменить сумма := сумма + удвоить(элемент)
}

если сумма == 12 {
    вывести "готово"
} иначе {
    вывести "ошибка"
}
~~~

Её REAPER-форма:

~~~reaper
craft double(value) {
    yield value * 2
}

make number := 5
vary total := 0

each item in range(1, 4) {
    change total := total + double(item)
}

when total == 12 {
    emit "готово"
} otherwise {
    emit "ошибка"
}
~~~

Разница в русских ключевых словах и выбранных пользователем именах идентификаторов. Все операторы, значения, вызовы, области видимости, вычисления и ограничения остаются правилами REAPER.

## 4. Имена, операторы и встроенные функции

- Имена функций, переменных, параметров и модулей — обычные Unicode-идентификаторы REAPER.
- Имена идентификаторов сравниваются по правилам REAPER; компилятор не выводит склонения и синонимы.
- Пользователь может объявлять функции-обёртки с русскими именами обычными средствами REAPER.
- Оператор потока ::, арифметика, сравнения, логика, вызовы и индексация не переводятся и не переопределяются.
- say() и ask() остаются встроенными функциями REAPER. Русские ключевые слова не создают второй набор I/O-функций.
- Лимиты шагов, глубины вызовов, коллекций и текста наследуются от REAPER.

## 5. Правила нормализации

1. Лексер обнаруживает точное русское написание из таблицы.
2. Псевдоним преобразуется в соответствующий вид токена REAPER.
3. Координаты исходного текста сохраняются для диагностики.
4. Остальные символы и идентификаторы передаются без семантических преобразований.
5. Неизвестные слова обрабатываются обычным lexer/parser/name resolver REAPER.
6. Ошибки, результаты и ограничения обязаны совпадать с эквивалентной программой REAPER.

Не выполняются автоматическое склонение, лемматизация, транслитерация, подбор синонима, исправление смысла или обработка свободной речи.

## 6. Реализация и границы готовности

| Компонент | Фактический статус |
|---|---|
| Python-лексер: точные русские aliases базового подмножества | implemented |
| Python parser/runtime: выполнение русского примера | implemented by shared REAPER grammar/runtime |
| C17 lexer: распознавание русского словаря | implemented lexical recognition |
| C17 lexer: выдача канонического написания токена REAPER | implemented; native tests pending CI |
| Полный C17 parser и runtime REAPER | отдельные этапы развития REAPER |
| Отдельный parser/AST/runtime МОСТ | not applicable — не разрабатывается |
| Морфологический или синонимический resolver МОСТ | not applicable — не разрабатывается |

Сквозная приёмка: для каждого псевдонима сравнить программу МОСТ с программой REAPER после подстановки английского токена. Обе программы должны давать одинаковый token stream, AST, диагностики и результат выполнения.

## 7. Связанные документы

- [REAPER Language 0.1](../LANGUAGE.md) — единственная спецификация языка.
- [66 правил русской записи](MOST_RUSSIAN_66_RULES.md) — рекомендации по читаемости; они не расширяют семантику REAPER.
- [Статус реализации](MOST_IMPLEMENTATION_STATUS.md) — фактические границы кода и тестов.
- [Единая архитектура](REAPER_UNIFIED_ARCHITECTURE.md) — реализация и миграция ядра REAPER.


## MOST Function Registry 666

`language/functions_666.json` is the canonical 666-entry API/feature traceability catalogue (147 existing specifications + 519 proposals). It is distinct from the 66 foundational rules, the 666 lexical-token catalogue, and the 666-rule Constitution profile. Registry membership does not create a callable or imply an implementation.

REAPER remains the semantic core and MOST remains a Russian-language frontend resolving names to canonical REAPER symbols and the shared typed IR. Aliases do not change types, effects, capabilities, ownership, or runtime behavior. Ambiguity remains a diagnostic. See [MOST_FUNCTIONS_666.md](MOST_FUNCTIONS_666.md).
