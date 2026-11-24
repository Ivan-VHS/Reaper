#include "reaper/command_palette.h"

#include <limits.h>
#include <string.h>

static size_t bounded_length(const char *text, size_t maximum) {
    size_t length = 0;
    if (text == NULL) return maximum + 1u;
    while (length <= maximum && text[length] != '\0') ++length;
    return length;
}

static unsigned char fold_ascii(unsigned char value) {
    if (value >= (unsigned char)'A' && value <= (unsigned char)'Z')
        return (unsigned char)(value + ((unsigned char)'a' - (unsigned char)'A'));
    return value;
}

static int equal_ascii(const char *left, size_t left_size,
                       const char *right, size_t right_size) {
    size_t i;
    if (left_size != right_size) return 0;
    for (i = 0; i < left_size; ++i) {
        if (fold_ascii((unsigned char)left[i]) != fold_ascii((unsigned char)right[i]))
            return 0;
    }
    return 1;
}

static uint32_t field_score(const char *field, size_t field_size,
                            const char *token, size_t token_size) {
    size_t i, cursor = 0, gaps = 0;
    int matched = 1;
    if (token_size == 0u || field_size == 0u) return UINT32_MAX;
    if (equal_ascii(field, field_size, token, token_size)) return 0u;
    if (field_size >= token_size &&
        equal_ascii(field, token_size, token, token_size))
        return 10u + (uint32_t)(field_size - token_size);
    for (i = 0; i + token_size <= field_size; ++i) {
        if (equal_ascii(field + i, token_size, token, token_size))
            return 100u + (uint32_t)i;
    }
    for (i = 0; i < token_size; ++i) {
        while (cursor < field_size &&
               fold_ascii((unsigned char)field[cursor]) !=
               fold_ascii((unsigned char)token[i])) {
            ++cursor;
            if (i > 0u) ++gaps;
        }
        if (cursor == field_size) {
            matched = 0;
            break;
        }
        ++cursor;
    }
    if (!matched) return UINT32_MAX;
    if (gaps > UINT32_MAX - 200u) return UINT32_MAX;
    return 200u + (uint32_t)gaps;
}

static uint32_t command_score(const ReaperPaletteCommand *command,
                              const char *query, size_t query_size) {
    size_t start = 0;
    uint32_t total = 0u;
    const size_t label_size = bounded_length(command->label, REAPER_PALETTE_FIELD_MAX);
    const size_t keywords_size = bounded_length(command->keywords, REAPER_PALETTE_FIELD_MAX);
    if (label_size > REAPER_PALETTE_FIELD_MAX ||
        keywords_size > REAPER_PALETTE_FIELD_MAX) return UINT32_MAX;
    while (start < query_size) {
        size_t end = start;
        uint32_t label_score, keyword_score, best;
        while (start < query_size && (query[start] == ' ' || query[start] == '\t' ||
                                      query[start] == '\n' || query[start] == '\r'))
            ++start;
        if (start == query_size) break;
        end = start;
        while (end < query_size && query[end] != ' ' && query[end] != '\t' &&
               query[end] != '\n' && query[end] != '\r') ++end;
        label_score = field_score(command->label, label_size, query + start, end - start);
        keyword_score = field_score(command->keywords, keywords_size, query + start, end - start);
        best = label_score < keyword_score ? label_score : keyword_score;
        if (best == UINT32_MAX || total > UINT32_MAX - best) return UINT32_MAX;
        total += best;
        start = end;
    }
    return total;
}

static int comes_before(const ReaperPaletteMatch *left,
                        const ReaperPaletteMatch *right,
                        const ReaperPaletteCommand *commands) {
    if (left->score != right->score) return left->score < right->score;
    return strcmp(commands[left->command_index].id,
                  commands[right->command_index].id) < 0;
}

size_t reaper_palette_rank(const ReaperPaletteCommand *commands,
                           size_t command_count, const char *query,
                           ReaperPaletteMatch *matches, size_t capacity) {
    size_t query_size, written = 0u, index;
    if (commands == NULL || query == NULL || matches == NULL ||
        capacity == 0u || command_count == 0u) return 0u;
    query_size = bounded_length(query, REAPER_PALETTE_QUERY_MAX);
    if (query_size == 0u || query_size > REAPER_PALETTE_QUERY_MAX) return 0u;
    for (index = 0u; index < command_count; ++index) {
        const size_t id_size = bounded_length(commands[index].id, 96u);
        const size_t label_size = bounded_length(commands[index].label, REAPER_PALETTE_FIELD_MAX);
        const size_t keyword_size = bounded_length(commands[index].keywords, REAPER_PALETTE_FIELD_MAX);
        ReaperPaletteMatch candidate;
        size_t position;
        if (id_size == 0u || id_size > 96u || label_size == 0u ||
            label_size > REAPER_PALETTE_FIELD_MAX ||
            keyword_size > REAPER_PALETTE_FIELD_MAX) continue;
        candidate.command_index = index;
        candidate.score = command_score(&commands[index], query, query_size);
        if (candidate.score == UINT32_MAX) continue;
        if (written < capacity) {
            position = written++;
            matches[position] = candidate;
        } else {
            if (!comes_before(&candidate, &matches[written - 1u], commands)) continue;
            position = written - 1u;
            matches[position] = candidate;
        }
        while (position > 0u &&
               comes_before(&matches[position], &matches[position - 1u], commands)) {
            const ReaperPaletteMatch temporary = matches[position - 1u];
            matches[position - 1u] = matches[position];
            matches[position] = temporary;
            --position;
        }
    }
    return written;
}
