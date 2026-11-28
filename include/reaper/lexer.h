#ifndef REAPER_LEXER_H
#define REAPER_LEXER_H

#include <stddef.h>

#define REAPER_MAX_SOURCE_BYTES (16u * 1024u * 1024u)
#define REAPER_MAX_TOKENS 262144u

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    REAPER_TOK_EOF = 0,
    REAPER_TOK_NEWLINE,
    REAPER_TOK_IDENTIFIER,
    REAPER_TOK_KEYWORD,
    REAPER_TOK_NUMBER,
    REAPER_TOK_STRING,
    REAPER_TOK_OPERATOR,
    REAPER_TOK_CATALOG_OPERATOR,
    REAPER_TOK_PUNCTUATION
} ReaperTokenKind;

typedef struct {
    ReaperTokenKind kind;
    char *text;
    size_t line;
    size_t column;
    size_t source_start_byte;
    size_t source_end_byte;
} ReaperToken;

typedef struct {
    ReaperToken *items;
    size_t length;
    size_t capacity;
} ReaperTokenArray;

typedef struct {
    char message[256];
    size_t line;
    size_t column;
} ReaperLexError;

int reaper_lex(
    const char *source,
    ReaperTokenArray *out,
    ReaperLexError *error
);

void reaper_tokens_free(ReaperTokenArray *tokens);
const char *reaper_token_kind_name(ReaperTokenKind kind);

/* Return the canonical REAPER spelling for an alias token. */
const char *reaper_token_canonical_text(const ReaperToken *token);

#ifdef __cplusplus
}
#endif

#endif
