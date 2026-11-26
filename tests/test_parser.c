#include "reaper/ast.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int parse(const char *s,ReaperAst *a,ReaperParseError *e){ReaperTokenArray t={0};ReaperLexError le={{0},0,0};assert(reaper_lex(s,&t,&le));int ok=reaper_parse_expression(&t,a,e);reaper_tokens_free(&t);return ok;}
static void precedence_test(void){ReaperAst a;ReaperParseError e;assert(parse("1 + 2 * 3",&a,&e));assert(a.length==5);assert(!strcmp(a.items[a.root].text,"+"));assert(!strcmp(a.items[a.items[a.root].right].text,"*"));reaper_ast_free(&a);}
static void power_test(void){ReaperAst a;ReaperParseError e;assert(parse("2 ** 3 ** 4",&a,&e));assert(!strcmp(a.items[a.root].text,"**"));assert(!strcmp(a.items[a.items[a.root].right].text,"**"));reaper_ast_free(&a);}
static void bridge_test(void){ReaperAst a;ReaperParseError e;assert(parse("значение :: обработать ?? 7",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BINARY);reaper_ast_free(&a);}
static void legacy_flow_test(void){ReaperAst a;ReaperParseError e;assert(!parse("1 |> f",&a,&e));assert(strstr(e.message,"unexpected token"));}
static void literal_test(void){ReaperAst a;ReaperParseError e;assert(parse("true",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BOOLEAN);reaper_ast_free(&a);assert(parse("\"мост\"",&a,&e));assert(a.items[a.root].kind==REAPER_AST_STRING);reaper_ast_free(&a);}
static void trailing_test(void){ReaperAst a;ReaperParseError e;assert(!parse("1 2",&a,&e));assert(strstr(e.message,"unexpected token"));}
static void paren_test(void){ReaperAst a;ReaperParseError e;assert(!parse("(1 + 2",&a,&e));assert(strstr(e.message,"expected ')'"));}
static void json_test(void){
 ReaperAst a;ReaperParseError e;assert(parse("value + \"a\\\"b\"",&a,&e));
 FILE *f=tmpfile();assert(f);assert(reaper_ast_write_json(&a,f));assert(fflush(f)==0);assert(fseek(f,0,SEEK_SET)==0);
 char b[1024];size_t n=fread(b,1,sizeof b-1,f);b[n]='\0';
 assert(strstr(b,"\"kind\":\"binary\""));assert(strstr(b,"\"text\":\"a\\\"b\""));
 fclose(f);reaper_ast_free(&a);
}

static void source_map_span_test(void)
{
    const char *source = "λ + 2";
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0u, 0u};
    ReaperAst ast;
    ReaperParseError parse_error = {{0}, 0u, 0u};

    assert(reaper_lex(source, &tokens, &lex_error));
    assert(tokens.items[0].byte_start == 0u && tokens.items[0].byte_end == 2u);
    assert(tokens.items[1].byte_start == 3u && tokens.items[1].byte_end == 4u);
    assert(tokens.items[2].byte_start == 5u && tokens.items[2].byte_end == 6u);

    assert(reaper_parse_expression_with_source(&tokens, 17u, &ast, &parse_error));
    const ReaperAstNode *root = &ast.items[ast.root];
    assert(root->kind == REAPER_AST_BINARY);
    assert(root->source_id == 17u);
    assert(root->byte_start == 0u && root->byte_end == 6u);
    assert(root->line == 1u && root->column == 3u);
    assert(ast.items[root->left].byte_start == 0u &&
           ast.items[root->left].byte_end == 2u);
    assert(ast.items[root->right].byte_start == 5u &&
           ast.items[root->right].byte_end == 6u);
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
}

static void grouping_span_covers_parentheses(void)
{
    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0u, 0u};
    ReaperAst ast;
    ReaperParseError parse_error = {{0}, 0u, 0u};
    assert(reaper_lex("(λ + 2)", &tokens, &lex_error));
    assert(reaper_parse_expression_with_source(&tokens, 5u, &ast, &parse_error));
    const ReaperAstNode *root = &ast.items[ast.root];
    assert(root->source_id == 5u);
    assert(root->byte_start == 0u && root->byte_end == 8u);
    assert(root->line == 1u && root->column == 1u);
    reaper_ast_free(&ast);
    reaper_tokens_free(&tokens);
}

int main(void){precedence_test();power_test();bridge_test();legacy_flow_test();literal_test();trailing_test();paren_test();json_test();source_map_span_test();grouping_span_covers_parentheses();puts("native parser tests: 8 groups passed");return 0;}
