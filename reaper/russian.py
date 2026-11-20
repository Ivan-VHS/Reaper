"""Russian keyword aliases for the Reaper reference language.

Aliases map to existing token kinds; they do not introduce new runtime semantics.
"""

RUSSIAN_KEYWORD_ALIASES: dict[str, str] = {
    # Bindings and assignment
    "пусть": "MAKE",
    "создать": "MAKE",
    "неизменяемое": "MAKE",
    "неизменяемая": "MAKE",
    "изменяемая": "VARY",
    "изменяемый": "VARY",
    "переменная": "VARY",
    "изменить": "CHANGE",
    "присвоить": "CHANGE",
    "переприсвоить": "CHANGE",
    # Functions and output
    "функция": "CRAFT",
    "процедура": "CRAFT",
    "вернуть": "YIELD",
    "возвратить": "YIELD",
    "вывести": "EMIT",
    "показать": "EMIT",
    "напечатать": "EMIT",
    # Control flow
    "если": "WHEN",
    "когда": "WHEN",
    "иначе": "OTHERWISE",
    "каждый": "EACH",
    "для": "EACH",
    "в": "IN",
    "среди": "IN",
    "цикл": "LOOP",
    "пока": "WHILE",
    # Literals and logic
    "истина": "TRUE",
    "ложь": "FALSE",
    "ничего": "NOTHING",
    "пусто": "NOTHING",
    "и": "AND",
    "или": "OR",
    "не": "NOT",
    # Module declarations
    "импорт": "IMPORT",
    "экспорт": "EXPORT",
    "как": "AS",
}

__all__ = ["RUSSIAN_KEYWORD_ALIASES"]
