#include "reaper/lexer.h"
#include "reaper/token_catalog.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_catalog_contract(void) {
    assert(reaper_token_catalog_count() == 666u);
    assert(reaper_token_catalog_validate());
    const ReaperCatalogEntry *first = reaper_token_catalog_at(0u);
    const ReaperCatalogEntry *last = reaper_token_catalog_at(665u);
    assert(first && first->ordinal == 1u && strlen(first->lexeme) == 3u);
    assert(last && last->ordinal == 666u && strlen(last->lexeme) == 3u);
    assert(reaper_token_catalog_at(666u) == NULL);
    assert(reaper_token_catalog_lookup(first->lexeme) == first);
    assert(reaper_token_catalog_lookup("not-a-token") == NULL);
}
static void test_native_lexer_catalogue_tokens(void) {
    const char *a = reaper_token_catalog_at(0u)->lexeme;
    const char *b = reaper_token_catalog_at(359u)->lexeme;
    const char *c = reaper_token_catalog_at(665u)->lexeme;
    char source[32];
    (void)snprintf(source, sizeof source, "%s %s %s", a, b, c);
    ReaperTokenArray tokens = {0};
    ReaperLexError error = {{0}, 0, 0};
    assert(reaper_lex(source, &tokens, &error));
    size_t found = 0;
    for (size_t i = 0; i < tokens.length; ++i)
        if (tokens.items[i].kind == REAPER_TOK_CATALOG_OPERATOR) ++found;
    assert(found == 3u);
    reaper_tokens_free(&tokens);
}
int main(void) {
    test_catalog_contract();
    test_native_lexer_catalogue_tokens();
    puts("native token catalogue tests: 2 groups passed");
    return 0;
}
