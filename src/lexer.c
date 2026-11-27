#include "reaper/lexer.h"
#include "reaper/token_catalog.h"

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *const keywords[] = {
    "make",
    "vary",
    "change",
    "craft",
    "yield",
    "emit",
    "when",
    "otherwise",
    "each",
    "in",
    "loop",
    "while",
    "true",
    "false",
    "nothing",
    "and",
    "or",
    "not",
    "module",
    "import",
    "as",
    "pub",
    "export",
    "fn",
    "struct",
    "enum",
    "trait",
    "impl",
    "type",
    "const",
    "let",
    "mut",
    "return",
    "if",
    "else",
    "match",
    "region",
    "raw",
    "arena",
    "signal",
    "async",
    "await",
    "test",
    "comptime",
    "requires",
    "ensures",
    "unsafe",
    "extern",
    "drop",
    "where",
    "for",
    "break",
    "continue",
    "defer",
    "пусть",
    "переменная",
    "изменить",
    "функция",
    "вернуть",
    "вывести",
    "если",
    "иначе",
    "для",
    "в",
    "цикл",
    "пока",
    "истина",
    "ложь",
    "ничего",
    "и",
    "или",
    "не",
    "импорт",
    "экспорт",
    "как",
    "модуль",
    "публичный",
    "процедура",
    "структура",
    "перечисление",
    "типаж",
    "реализация",
    "тип",
    "константа",
    "связать",
    "изменяемый",
    "возврат",
    "условие",
    "альтернатива",
    "выбор",
    "область",
    "сырой",
    "арена",
    "сигнал",
    "асинхронно",
    "ожидать",
    "тест",
    "вычислить_при_сборке",
    "требует",
    "гарантирует",
    "небезопасно",
    "внешний",
    "где",
    "уничтожить",
    "для_каждого",
    "прервать",
    "продолжить",
    "отложить"
};

typedef struct {
    const char *alias;
    const char *canonical;
} ReaperKeywordAlias;

static const ReaperKeywordAlias russian_aliases[] = {
    {"пусть", "make"},
    {"переменная", "vary"},
    {"изменить", "change"},
    {"функция", "craft"},
    {"вернуть", "yield"},
    {"вывести", "emit"},
    {"если", "when"},
    {"иначе", "otherwise"},
    {"для", "each"},
    {"в", "in"},
    {"цикл", "loop"},
    {"пока", "while"},
    {"истина", "true"},
    {"ложь", "false"},
    {"ничего", "nothing"},
    {"и", "and"},
    {"или", "or"},
    {"не", "not"},
    {"импорт", "import"},
    {"экспорт", "export"},
    {"как", "as"},
    {"модуль", "module"},
    {"публичный", "pub"},
    {"процедура", "fn"},
    {"структура", "struct"},
    {"перечисление", "enum"},
    {"типаж", "trait"},
    {"реализация", "impl"},
    {"тип", "type"},
    {"константа", "const"},
    {"связать", "let"},
    {"изменяемый", "mut"},
    {"возврат", "return"},
    {"условие", "if"},
    {"альтернатива", "else"},
    {"выбор", "match"},
    {"область", "region"},
    {"сырой", "raw"},
    {"арена", "arena"},
    {"сигнал", "signal"},
    {"асинхронно", "async"},
    {"ожидать", "await"},
    {"тест", "test"},
    {"вычислить_при_сборке", "comptime"},
    {"требует", "requires"},
    {"гарантирует", "ensures"},
    {"небезопасно", "unsafe"},
    {"внешний", "extern"},
    {"где", "where"},
    {"уничтожить", "drop"},
    {"для_каждого", "for"},
    {"прервать", "break"},
    {"продолжить", "continue"},
    {"отложить", "defer"}
};

/* Public columns count UTF-8 code points rather than bytes. */
static void advance_column(size_t *column, unsigned char byte)
{
    if ((byte & 0xC0u) != 0x80u) {
        ++*column;
    }
}

static int is_keyword(const char *text)
{
    const size_t keyword_count = sizeof keywords / sizeof keywords[0];

    for (size_t index = 0; index < keyword_count; ++index) {
        if (strcmp(text, keywords[index]) == 0) {
            return 1;
        }
    }

    return 0;
}

const char *reaper_token_canonical_text(const ReaperToken *token)
{
    const size_t alias_count = sizeof russian_aliases / sizeof russian_aliases[0];

    if (token == NULL || token->text == NULL) {
        return "";
    }

    if (token->kind != REAPER_TOK_KEYWORD) {
        return token->text;
    }

    for (size_t index = 0; index < alias_count; ++index) {
        if (strcmp(token->text, russian_aliases[index].alias) == 0) {
            return russian_aliases[index].canonical;
        }
    }

    return token->text;
}

static int append_token(
    ReaperTokenArray *tokens,
    ReaperTokenKind kind,
    const char *source,
    size_t text_length,
    size_t line,
    size_t column,
    int *limit_exceeded
)
{
    if (tokens->length >= REAPER_MAX_TOKENS) {
        if (limit_exceeded != NULL) {
            *limit_exceeded = 1;
        }
        return 0;
    }

    if (tokens->length == tokens->capacity) {
        size_t new_capacity = tokens->capacity == 0u
            ? 32u
            : tokens->capacity * 2u;

        if (new_capacity < tokens->capacity ||
            new_capacity > SIZE_MAX / sizeof *tokens->items) {
            return 0;
        }

        if (new_capacity > REAPER_MAX_TOKENS) {
            new_capacity = REAPER_MAX_TOKENS;
        }

        ReaperToken *new_items = realloc(
            tokens->items,
            new_capacity * sizeof *new_items
        );
        if (new_items == NULL) {
            return 0;
        }

        tokens->items = new_items;
        tokens->capacity = new_capacity;
    }

    char *text = malloc(text_length + 1u);
    if (text == NULL) {
        return 0;
    }

    memcpy(text, source, text_length);
    text[text_length] = '\0';

    tokens->items[tokens->length++] = (ReaperToken) {
        .kind = kind,
        .text = text,
        .line = line,
        .column = column
    };

    return 1;
}

static int fail(
    ReaperLexError *error,
    size_t line,
    size_t column,
    const char *message
)
{
    if (error != NULL) {
        snprintf(error->message, sizeof error->message, "%s", message);
        error->line = line;
        error->column = column;
    }

    return 0;
}

/* Reject overlong encodings, surrogate code points and values beyond U+10FFFF. */
static int validate_utf8_source(
    const unsigned char *source,
    size_t *bad_line,
    size_t *bad_column
)
{
    size_t line = 1u;
    size_t column = 1u;

    for (size_t offset = 0u; source[offset] != '\0';) {
        const unsigned char lead = source[offset];
        size_t width;

        if (lead < 0x80u) {
            width = 1u;
        } else if (lead >= 0xC2u && lead <= 0xDFu) {
            width = 2u;
        } else if (lead >= 0xE0u && lead <= 0xEFu) {
            width = 3u;
        } else if (lead >= 0xF0u && lead <= 0xF4u) {
            width = 4u;
        } else {
            goto invalid;
        }

        for (size_t index = 1u; index < width; ++index) {
            const unsigned char next = source[offset + index];

            if (next == '\0' || (next & 0xC0u) != 0x80u) {
                goto invalid;
            }

            if (index == 1u) {
                if ((lead == 0xE0u && next < 0xA0u) ||
                    (lead == 0xEDu && next > 0x9Fu) ||
                    (lead == 0xF0u && next < 0x90u) ||
                    (lead == 0xF4u && next > 0x8Fu)) {
                    goto invalid;
                }
            }
        }

        if (width == 1u && lead == '\n') {
            ++line;
            column = 1u;
        } else {
            ++column;
        }

        offset += width;
    }

    return 1;

invalid:
    if (bad_line != NULL) {
        *bad_line = line;
    }
    if (bad_column != NULL) {
        *bad_column = column;
    }

    return 0;
}

static int ident_start(unsigned char byte)
{
    return isalpha(byte) || byte == '_' || byte >= 0x80u;
}

static int ident_more(unsigned char byte)
{
    return isalnum(byte) || byte == '_' || byte >= 0x80u;
}

static int one_op(char character)
{
    return strchr("+-*/%<>(){}[],=:;.!?@|~&^", character) != NULL;
}

static int is_pair_operator(const char *source)
{
    static const char *const operators[] = {
        ":=",
        "==",
        "!=",
        "<=",
        ">=",
        "//",
        "**",
        "++",
        "??",
        "+%",
        "+|",
        "->",
        "=>",
        "::",
        "<>",
        "~>",
        "^^",
        "&&",
        "||",
        "<<",
        ">>",
        "&=",
        "|="
    };
    const size_t operator_count = sizeof operators / sizeof operators[0];

    for (size_t index = 0; index < operator_count; ++index) {
        if (source[0] == operators[index][0] &&
            source[1] == operators[index][1]) {
            return 1;
        }
    }

    return 0;
}

int reaper_lex(
    const char *source,
    ReaperTokenArray *out,
    ReaperLexError *error
)
{
    if (source == NULL || out == NULL) {
        return fail(error, 1u, 1u, "source and output are required");
    }

    memset(out, 0, sizeof *out);
    if (error != NULL) {
        memset(error, 0, sizeof *error);
    }

    int token_limit_exceeded = 0;
    size_t source_bytes = 0u;

    while (source_bytes <= REAPER_MAX_SOURCE_BYTES &&
           source[source_bytes] != '\0') {
        ++source_bytes;
    }

    if (source_bytes > REAPER_MAX_SOURCE_BYTES) {
        return fail(
            error,
            1u,
            1u,
            "source exceeds the 16 MiB lexer input limit"
        );
    }

    size_t bad_line = 1u;
    size_t bad_column = 1u;

    if (!validate_utf8_source(
            (const unsigned char *)source,
            &bad_line,
            &bad_column)) {
        return fail(
            error,
            bad_line,
            bad_column,
            "source is not valid UTF-8"
        );
    }

    const char *cursor = source;
    size_t line = 1u;
    size_t column = 1u;

    while (*cursor != '\0') {
        const unsigned char byte = (unsigned char)*cursor;

        if (byte == ' ' || byte == '\t' || byte == '\r') {
            ++cursor;
            ++column;
            continue;
        }

        if (byte == '\n') {
            if (!append_token(
                    out,
                    REAPER_TOK_NEWLINE,
                    cursor,
                    1u,
                    line,
                    column,
                    &token_limit_exceeded)) {
                goto out_of_memory;
            }

            ++cursor;
            ++line;
            column = 1u;
            continue;
        }

        if (byte == '#') {
            while (*cursor != '\0' && *cursor != '\n') {
                advance_column(&column, (unsigned char)*cursor);
                ++cursor;
            }
            continue;
        }

        if (byte == '"') {
            const size_t string_line = line;
            const size_t string_column = column;
            char *decoded;
            size_t decoded_length = 0u;
            int closed = 0;

            ++cursor;
            ++column;

            decoded = malloc(strlen(cursor) + 1u);
            if (decoded == NULL) {
                goto out_of_memory;
            }

            while (*cursor != '\0') {
                if (*cursor == '"') {
                    ++cursor;
                    ++column;
                    closed = 1;
                    break;
                }

                if (*cursor == '\n') {
                    free(decoded);
                    reaper_tokens_free(out);
                    return fail(
                        error,
                        string_line,
                        string_column,
                        "string literal cannot span lines"
                    );
                }

                char value = *cursor++;
                advance_column(&column, (unsigned char)value);

                if (value == '\\') {
                    const char escape = *cursor;

                    if (escape == '\0') {
                        break;
                    }

                    ++cursor;
                    advance_column(&column, (unsigned char)escape);

                    switch (escape) {
                    case 'n':
                        value = '\n';
                        break;
                    case 'r':
                        value = '\r';
                        break;
                    case 't':
                        value = '\t';
                        break;
                    case '"':
                        value = '"';
                        break;
                    case '\\':
                        value = '\\';
                        break;
                    default:
                        free(decoded);
                        reaper_tokens_free(out);
                        return fail(
                            error,
                            line,
                            column - 1u,
                            "unknown string escape"
                        );
                    }
                }

                decoded[decoded_length++] = value;
            }

            if (!closed) {
                free(decoded);
                reaper_tokens_free(out);
                return fail(
                    error,
                    string_line,
                    string_column,
                    "unterminated string literal"
                );
            }

            decoded[decoded_length] = '\0';

            if (!append_token(
                    out,
                    REAPER_TOK_STRING,
                    decoded,
                    decoded_length,
                    string_line,
                    string_column,
                    &token_limit_exceeded)) {
                free(decoded);
                goto out_of_memory;
            }

            free(decoded);
            continue;
        }

        if (isdigit(byte)) {
            const char *number_start = cursor;
            const size_t number_column = column;

            while (isdigit((unsigned char)*cursor)) {
                ++cursor;
                ++column;
            }

            if (*cursor == '.' &&
                isdigit((unsigned char)cursor[1])) {
                ++cursor;
                ++column;

                while (isdigit((unsigned char)*cursor)) {
                    ++cursor;
                    ++column;
                }
            }

            if (!append_token(
                    out,
                    REAPER_TOK_NUMBER,
                    number_start,
                    (size_t)(cursor - number_start),
                    line,
                    number_column,
                    &token_limit_exceeded)) {
                goto out_of_memory;
            }

            continue;
        }

        if (ident_start(byte)) {
            const char *identifier_start = cursor;
            const size_t identifier_column = column;
            char *word;
            size_t identifier_length;
            ReaperTokenKind kind;

            while (ident_more((unsigned char)*cursor)) {
                advance_column(&column, (unsigned char)*cursor);
                ++cursor;
            }

            identifier_length = (size_t)(cursor - identifier_start);
            word = malloc(identifier_length + 1u);
            if (word == NULL) {
                goto out_of_memory;
            }

            memcpy(word, identifier_start, identifier_length);
            word[identifier_length] = '\0';

            kind = is_keyword(word)
                ? REAPER_TOK_KEYWORD
                : REAPER_TOK_IDENTIFIER;
            free(word);

            if (!append_token(
                    out,
                    kind,
                    identifier_start,
                    identifier_length,
                    line,
                    identifier_column,
                    &token_limit_exceeded)) {
                goto out_of_memory;
            }

            continue;
        }

        const size_t operator_column = column;

        if (cursor[0] != '\0' &&
            cursor[1] != '\0' &&
            cursor[2] != '\0') {
            const char candidate[] = {
                cursor[0],
                cursor[1],
                cursor[2],
                '\0'
            };

            if (reaper_token_catalog_lookup(candidate) != NULL) {
                if (!append_token(
                        out,
                        REAPER_TOK_CATALOG_OPERATOR,
                        cursor,
                        3u,
                        line,
                        operator_column,
                        &token_limit_exceeded)) {
                    goto out_of_memory;
                }

                cursor += 3;
                column += 3u;
                continue;
            }
        }

        if (cursor[1] != '\0' && is_pair_operator(cursor)) {
            if (!append_token(
                    out,
                    REAPER_TOK_OPERATOR,
                    cursor,
                    2u,
                    line,
                    operator_column,
                    &token_limit_exceeded)) {
                goto out_of_memory;
            }

            cursor += 2;
            column += 2u;
            continue;
        }

        if (one_op((char)byte)) {
            const ReaperTokenKind kind =
                strchr("(){}[],;.", (char)byte) != NULL
                    ? REAPER_TOK_PUNCTUATION
                    : REAPER_TOK_OPERATOR;

            if (!append_token(
                    out,
                    kind,
                    cursor,
                    1u,
                    line,
                    operator_column,
                    &token_limit_exceeded)) {
                goto out_of_memory;
            }

            ++cursor;
            ++column;
            continue;
        }

        reaper_tokens_free(out);
        return fail(error, line, column, "unexpected character");
    }

    if (!append_token(
            out,
            REAPER_TOK_EOF,
            "",
            0u,
            line,
            column,
            &token_limit_exceeded)) {
        goto out_of_memory;
    }

    return 1;

out_of_memory:
    reaper_tokens_free(out);

    if (token_limit_exceeded) {
        return fail(
            error,
            line,
            column,
            "token count exceeds the 262144-token limit"
        );
    }

    return fail(
        error,
        line,
        column,
        "out of memory while tokenizing source"
    );
}

void reaper_tokens_free(ReaperTokenArray *tokens)
{
    if (tokens == NULL) {
        return;
    }

    for (size_t index = 0; index < tokens->length; ++index) {
        free(tokens->items[index].text);
    }

    free(tokens->items);
    memset(tokens, 0, sizeof *tokens);
}

const char *reaper_token_kind_name(ReaperTokenKind kind)
{
    switch (kind) {
    case REAPER_TOK_EOF:
        return "EOF";
    case REAPER_TOK_NEWLINE:
        return "NEWLINE";
    case REAPER_TOK_IDENTIFIER:
        return "IDENT";
    case REAPER_TOK_KEYWORD:
        return "KEYWORD";
    case REAPER_TOK_NUMBER:
        return "NUMBER";
    case REAPER_TOK_STRING:
        return "STRING";
    case REAPER_TOK_OPERATOR:
        return "OPERATOR";
    case REAPER_TOK_CATALOG_OPERATOR:
        return "CATALOG_OPERATOR";
    case REAPER_TOK_PUNCTUATION:
        return "PUNCTUATION";
    default:
        return "UNKNOWN";
    }
}
