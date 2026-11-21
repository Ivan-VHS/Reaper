#include "reaper/selfhood.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    static const char *const identities[] = {
        "Себя", "Сам", "Самого", "Собственный", "Личный", "Персональный",
        "Индивидуальный", "Автономный", "Самостоятельный", "Самобытный",
        "Самоидентичный", "Самотождественный", "Эго", "Личность",
        "Индивидуальность", "Самость", "Субъект", "Персона", "Ипостась",
        "Я-концепция"
    };
    static const char *const transformations[] = {
        "Переформулировать", "Переписать", "Пересоставить", "Переизложить",
        "Переработать", "Редактировать", "Отредактировать", "Скорректировать",
        "Актуализировать", "Обновить", "Модифицировать", "Преобразовать",
        "Трансформировать", "Реструктурировать", "Реконструировать",
        "Пересмотреть", "Усовершенствовать", "Оптимизировать", "Адаптировать",
        "Рефакторить"
    };
    static const char *const autonomy[] = {
        "Самостоятельность", "Автономность", "Независимость", "Самодостаточность",
        "Самообеспечение", "Самоуправление", "Самоорганизация", "Самоконтроль",
        "Саморегуляция", "Самодисциплина", "Инициативность", "Ответственность",
        "Решительность", "Независимое мышление", "Личная свобода", "Автономия",
        "Субъектность", "Самостоятельное действие",
        "Независимое функционирование", "Самоопределение"
    };

    assert(reaper_selfhood_count() == 20u);
    for (size_t i = 0u; i < 20u; ++i) {
        const ReaperSelfhoodEntry *entry = reaper_selfhood_at(i);
        assert(entry != NULL && entry->ordinal == (uint32_t)(i + 1u));
        assert(strcmp(entry->identity, identities[i]) == 0);
        assert(strcmp(entry->transformation, transformations[i]) == 0);
        assert(strcmp(entry->autonomy, autonomy[i]) == 0);
        assert(reaper_selfhood_find(identities[i]) == entry);
        for (size_t j = i + 1u; j < 20u; ++j)
            assert(strcmp(identities[i], identities[j]) != 0);
    }
    assert(reaper_selfhood_at(20u) == NULL);
    assert(reaper_selfhood_find(NULL) == NULL);
    assert(reaper_selfhood_find("несуществующий") == NULL);
    puts("native selfhood vocabulary tests: 20 entries passed");
    return 0;
}
