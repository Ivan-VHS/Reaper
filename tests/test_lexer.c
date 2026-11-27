#include "reaper/lexer.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int has(
    const ReaperTokenArray *tokens,
    const char *text,
    ReaperTokenKind kind
)
{
    for (size_t index = 0; index < tokens->length; ++index) {
        if (tokens->items[index].kind == kind &&
            strcmp(tokens->items[index].text, text) == 0) {
            return 1;
        }
    }

    return 0;
}

static int has_canonical(const ReaperTokenArray *tokens, const char *text)
{
    for (size_t index = 0; index < tokens->length; ++index) {
        if (strcmp(reaper_token_canonical_text(&tokens->items[index]), text) == 0) {
            return 1;
        }
    }

    return 0;
}

static void test_most_surface(void)
{
    const char *source =
        "module counter\n"
        "struct State { value: signal<i32> = 0 }\n"
        "fn increment(@: ~State, step: i32) -> i32 { "
        "@.value = @.value +| step }\n";

    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(reaper_lex(source, &tokens, &error));
    assert(has(&tokens, "module", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "struct", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "signal", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "fn", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "+|", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "@", REAPER_TOK_OPERATOR));
    assert(has(&tokens, ":", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "->", REAPER_TOK_OPERATOR));
    assert(has(&tokens, ".", REAPER_TOK_PUNCTUATION));

    reaper_tokens_free(&tokens);
}

static void test_most_operator_family(void)
{
    const char *source = "x := a :: f ?? b +% c +| d raw { p + 4 }";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(reaper_lex(source, &tokens, &error));
    assert(has(&tokens, ":=", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "::", REAPER_TOK_OPERATOR));
    assert(!has(&tokens, "|>", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "??", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "+%", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "+|", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "raw", REAPER_TOK_KEYWORD));

    reaper_tokens_free(&tokens);
}

static void test_program(void)
{
    const char *source =
        "make value := [1, 2] :: map(double)\n"
        "emit \"ok\"\n";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};
    int found_flow = 0;
    int found_string = 0;

    assert(reaper_lex(source, &tokens, &error));
    assert(tokens.length > 10u);
    assert(tokens.items[0].kind == REAPER_TOK_KEYWORD);
    assert(strcmp(tokens.items[0].text, "make") == 0);

    for (size_t index = 0; index < tokens.length; ++index) {
        if (strcmp(tokens.items[index].text, "::") == 0) {
            found_flow = 1;
        }

        if (tokens.items[index].kind == REAPER_TOK_STRING &&
            strcmp(tokens.items[index].text, "ok") == 0) {
            found_string = 1;
        }
    }

    assert(found_flow && found_string);
    reaper_tokens_free(&tokens);
}

static void test_escape(void)
{
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(reaper_lex("emit \"a\\nb\"\n", &tokens, &error));
    assert(strcmp(tokens.items[1].text, "a\nb") == 0);

    reaper_tokens_free(&tokens);
}

static void test_bad_escape(void)
{
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(!reaper_lex("emit \"bad\\q\"\n", &tokens, &error));
    assert(strstr(error.message, "escape") != NULL);
    assert(tokens.length == 0u);
}

static void test_unterminated(void)
{
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(!reaper_lex("emit \"unfinished", &tokens, &error));
    assert(error.line == 1u);
    assert(error.column == 6u);
}

static void test_most_russian_vocabulary(void)
{
    const char *source =
        "функция удвоить(значение) { вернуть значение * 2 }\n"
        "пусть число := истина\n"
        "переменная сумма := 0\n"
        "изменить сумма := сумма + 1\n"
        "для элемент в range(1, 4) { "
        "если не ложь и элемент > 0 или ложь { вывести сумма } "
        "иначе { вывести ничего } }\n"
        "цикл пока сумма < 5 { изменить сумма := сумма + 1 }\n"
        "импорт модуль как имя\n"
        "экспорт имя\n";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(reaper_lex(source, &tokens, &error));

    assert(has(&tokens, "функция", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "вернуть", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "пусть", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "переменная", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "изменить", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "вывести", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "если", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "иначе", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "для", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "в", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "цикл", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "пока", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "истина", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "ложь", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "ничего", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "и", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "или", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "не", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "импорт", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "экспорт", REAPER_TOK_KEYWORD));
    assert(has(&tokens, "как", REAPER_TOK_KEYWORD));

    assert(has_canonical(&tokens, "craft"));
    assert(has_canonical(&tokens, "yield"));
    assert(has_canonical(&tokens, "make"));
    assert(has_canonical(&tokens, "vary"));
    assert(has_canonical(&tokens, "change"));
    assert(has_canonical(&tokens, "when"));
    assert(has_canonical(&tokens, "otherwise"));
    assert(has_canonical(&tokens, "each"));
    assert(has_canonical(&tokens, "in"));
    assert(has_canonical(&tokens, "emit"));
    assert(has_canonical(&tokens, "loop"));
    assert(has_canonical(&tokens, "while"));
    assert(has_canonical(&tokens, "true"));
    assert(has_canonical(&tokens, "false"));
    assert(has_canonical(&tokens, "nothing"));
    assert(has_canonical(&tokens, "and"));
    assert(has_canonical(&tokens, "or"));
    assert(has_canonical(&tokens, "not"));
    assert(has_canonical(&tokens, "import"));
    assert(has_canonical(&tokens, "export"));
    assert(has_canonical(&tokens, "as"));

    assert(has(&tokens, "удвоить", REAPER_TOK_IDENTIFIER));
    assert(has(&tokens, "значение", REAPER_TOK_IDENTIFIER));
    assert(has(&tokens, "модуль", REAPER_TOK_KEYWORD));

    reaper_tokens_free(&tokens);
}

typedef struct {
    const char *alias;
    const char *canonical;
} AliasExpectation;

static void test_most_extended_aliases(void)
{
    static const AliasExpectation cases[] = {
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
    const char *source =
        "модуль "
        "публичный "
        "процедура "
        "структура "
        "перечисление "
        "типаж "
        "реализация "
        "тип "
        "константа "
        "связать "
        "изменяемый "
        "возврат "
        "условие "
        "альтернатива "
        "выбор "
        "область "
        "сырой "
        "арена "
        "сигнал "
        "асинхронно "
        "ожидать "
        "тест "
        "вычислить_при_сборке "
        "требует "
        "гарантирует "
        "небезопасно "
        "внешний "
        "где "
        "уничтожить "
        "для_каждого "
        "прервать "
        "продолжить "
        "отложить ";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};
    const size_t case_count = sizeof cases / sizeof cases[0];

    assert(reaper_lex(source, &tokens, &error));

    for (size_t index = 0; index < case_count; ++index) {
        assert(has(&tokens, cases[index].alias, REAPER_TOK_KEYWORD));
        assert(has_canonical(&tokens, cases[index].canonical));
    }

    reaper_tokens_free(&tokens);

    ReaperTokenArray unknown = {0};
    assert(reaper_lex("структуры", &unknown, &error));
    assert(has(&unknown, "структуры", REAPER_TOK_IDENTIFIER));

    reaper_tokens_free(&unknown);
}

static void test_source_size_limit_is_enforced(void)
{
    char *source = malloc((size_t)REAPER_MAX_SOURCE_BYTES + 2u);
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(source != NULL);
    memset(source, 'a', (size_t)REAPER_MAX_SOURCE_BYTES + 1u);
    source[(size_t)REAPER_MAX_SOURCE_BYTES + 1u] = '\0';

    assert(!reaper_lex(source, &tokens, &error));
    assert(tokens.length == 0u);
    assert(strstr(error.message, "16 MiB") != NULL);

    free(source);
}

static void test_token_count_limit_is_enforced(void)
{
    const size_t count = (size_t)REAPER_MAX_TOKENS;
    char *source = malloc(count * 2u + 1u);
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(source != NULL);

    for (size_t index = 0u; index < count; ++index) {
        source[index * 2u] = 'x';
        source[index * 2u + 1u] = ' ';
    }

    source[count * 2u] = '\0';

    assert(!reaper_lex(source, &tokens, &error));
    assert(tokens.length == 0u);
    assert(strstr(error.message, "262144-token limit") != NULL);

    free(source);
}

static void test_invalid_utf8_is_rejected(void)
{
    const char invalid[] = "emit \xC0\xAF";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(!reaper_lex(invalid, &tokens, &error));
    assert(tokens.length == 0u);
    assert(error.line == 1u);
    assert(error.column == 6u);
    assert(strstr(error.message, "UTF-8") != NULL);
}

static void test_invalid_utf8_reports_line_and_column(void)
{
    const char invalid[] = "emit 1\n\xF5";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(!reaper_lex(invalid, &tokens, &error));
    assert(tokens.length == 0u);
    assert(error.line == 2u);
    assert(error.column == 1u);
}

static void test_utf8_columns_count_codepoints(void)
{
    const char *source = "вывести утка + 1";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};
    int found_operator = 0;

    assert(reaper_lex(source, &tokens, &error));

    for (size_t index = 0; index < tokens.length; ++index) {
        if (strcmp(tokens.items[index].text, "+") == 0) {
            assert(tokens.items[index].column == 14u);
            found_operator = 1;
        }
    }

    assert(found_operator);
    reaper_tokens_free(&tokens);
}


static void test_rfs01_operator_lexing(void)
{
    const char *source = "node <> State flow a ~> b flow a >> b flow a << b contrast a || b contrast a ^^ b recover a <-root recover a ^core";
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0u, 0u};

    assert(reaper_lex(source, &tokens, &error));
    assert(has(&tokens, "<>", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "~>", REAPER_TOK_OPERATOR));
    assert(has(&tokens, ">>", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "<<", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "||", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "^^", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "<-root", REAPER_TOK_OPERATOR));
    assert(has(&tokens, "^core", REAPER_TOK_OPERATOR));
    reaper_tokens_free(&tokens);
}

int main(void)
{
    test_program();
    test_escape();
    test_bad_escape();
    test_unterminated();
    test_most_surface();
    test_most_operator_family();
    test_rfs01_operator_lexing();
    test_most_russian_vocabulary();
    test_most_extended_aliases();
    test_utf8_columns_count_codepoints();
    test_invalid_utf8_is_rejected();
    test_invalid_utf8_reports_line_and_column();
    test_source_size_limit_is_enforced();
    test_token_count_limit_is_enforced();

    puts("native lexer tests: 14 groups passed");
    return 0;
}
