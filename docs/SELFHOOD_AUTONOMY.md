# Selfhood and autonomy vocabulary

The versioned Reaper catalogue contains 20 exact identity/transformation/outcome triples.

| # | Identity | Transformation | Autonomy outcome |
|---:|---|---|---|
| 1 | Себя | Переформулировать | Самостоятельность |
| 2 | Сам | Переписать | Автономность |
| 3 | Самого | Пересоставить | Независимость |
| 4 | Собственный | Переизложить | Самодостаточность |
| 5 | Личный | Переработать | Самообеспечение |
| 6 | Персональный | Редактировать | Самоуправление |
| 7 | Индивидуальный | Отредактировать | Самоорганизация |
| 8 | Автономный | Скорректировать | Самоконтроль |
| 9 | Самостоятельный | Актуализировать | Саморегуляция |
| 10 | Самобытный | Обновить | Самодисциплина |
| 11 | Самоидентичный | Модифицировать | Инициативность |
| 12 | Самотождественный | Преобразовать | Ответственность |
| 13 | Эго | Трансформировать | Решительность |
| 14 | Личность | Реструктурировать | Независимое мышление |
| 15 | Индивидуальность | Реконструировать | Личная свобода |
| 16 | Самость | Пересмотреть | Автономия |
| 17 | Субъект | Усовершенствовать | Субъектность |
| 18 | Персона | Оптимизировать | Самостоятельное действие |
| 19 | Ипостась | Адаптировать | Независимое функционирование |
| 20 | Я-концепция | Рефакторить | Самоопределение |

## Runtime contract

The table is immutable and available through the native C17 API. Lookups are exact UTF-8 matches; ordinal positions are stable within schema version 1. No fuzzy matching, inferred identity, automatic rewrite or external mutation is performed.

Canonical machine-readable source: [\`language/selfhood.v1.json\`](../language/selfhood.v1.json). Schema: [\`schemas/selfhood-autonomy.v1.schema.json\`](../schemas/selfhood-autonomy.v1.schema.json).

CLI:

\`\`\`sh
reaper-c --selfhood
reaper-c --selfhood-token "Самостоятельный"
\`\`\`
