#include "reaper/lexer.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    const char *russian;
    const char *canonical;
} AliasCase;

static const AliasCase cases[] = {
    {"объявить", "make"},
    {"создать", "make"},
    {"присвоить", "change"},
    {"перезаписать", "change"},
    {"напечатать", "emit"},
    {"показать", "emit"},
    {"когда", "when"},
    {"каждый", "each"},
    {"среди", "in"},
    {"повторять", "loop"},
    {"верно", "true"},
    {"неверно", "false"},
    {"пусто", "nothing"},
    {"либо", "or"},
    {"подключить", "import"},
    {"опубликовать", "export"},
    {"под_именем", "as"},
    {"пакет", "module"},
    {"открытый", "pub"},
    {"ритуал", "fn"},
    {"каркас", "struct"},
    {"вариант", "enum"},
    {"контракт", "trait"},
    {"воплощение", "impl"},
    {"объявление_типа", "type"},
    {"неизменная", "const"},
    {"связка", "let"},
    {"изменяемая", "mut"},
    {"вернуть_из", "return"},
    {"сопоставление", "match"},
    {"контур", "region"},
    {"необработанный", "raw"},
    {"память_арены", "arena"},
    {"сигнальный_поток", "signal"},
    {"асинхронный", "async"},
    {"дождаться", "await"},
    {"испытание", "test"},
    {"сборочно", "comptime"},
    {"предусловие", "requires"},
    {"постусловие", "ensures"},
    {"опасный", "unsafe"},
    {"внешний_модуль", "extern"},
    {"ограничение", "where"},
    {"освободить", "drop"},
    {"для_каждого_элемента", "for"},
    {"выйти_из_цикла", "break"},
    {"следующий_элемент", "continue"},
    {"отложенное_действие", "defer"}
};

int main(void)
{
    const size_t count = sizeof cases / sizeof cases[0];
    for (size_t index = 0; index < count; ++index) {
        ReaperTokenArray tokens = {0};
        ReaperLexError error = {{0}, 0u, 0u};
        assert(reaper_lex(cases[index].russian, &tokens, &error));
        assert(tokens.length == 2u);
        assert(tokens.items[0].kind == REAPER_TOK_KEYWORD);
        assert(strcmp(tokens.items[0].text, cases[index].russian) == 0);
        assert(strcmp(reaper_token_canonical_text(&tokens.items[0]), cases[index].canonical) == 0);
        assert(tokens.items[1].kind == REAPER_TOK_EOF);
        reaper_tokens_free(&tokens);
    }
    printf("native MOST LITHOS aliases: %zu cases passed\n", count);
    return 0;
}
