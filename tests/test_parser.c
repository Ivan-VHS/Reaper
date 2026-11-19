#include "reaper/ast.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int parse(const char *s,ReaperAst *a,ReaperParseError *e){ReaperTokenArray t={0};ReaperLexError le={{0},0,0};assert(reaper_lex(s,&t,&le));int ok=reaper_parse_expression(&t,a,e);reaper_tokens_free(&t);return ok;}
static void precedence_test(void){ReaperAst a;ReaperParseError e;assert(parse("1 + 2 * 3",&a,&e));assert(a.length==5);assert(!strcmp(a.items[a.root].text,"+"));assert(!strcmp(a.items[a.items[a.root].right].text,"*"));reaper_ast_free(&a);}
static void power_test(void){ReaperAst a;ReaperParseError e;assert(parse("2 ** 3 ** 4",&a,&e));assert(!strcmp(a.items[a.root].text,"**"));assert(!strcmp(a.items[a.items[a.root].right].text,"**"));reaper_ast_free(&a);}
static void bridge_test(void){ReaperAst a;ReaperParseError e;assert(parse("значение |> обработать ?? 7",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BINARY);reaper_ast_free(&a);}
static void literal_test(void){ReaperAst a;ReaperParseError e;assert(parse("true",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BOOLEAN);reaper_ast_free(&a);assert(parse("\"мост\"",&a,&e));assert(a.items[a.root].kind==REAPER_AST_STRING);reaper_ast_free(&a);}
static void trailing_test(void){ReaperAst a;ReaperParseError e;assert(!parse("1 2",&a,&e));assert(strstr(e.message,"unexpected token"));}
static void paren_test(void){ReaperAst a;ReaperParseError e;assert(!parse("(1 + 2",&a,&e));assert(strstr(e.message,"expected ')'"));}
int main(void){precedence_test();power_test();bridge_test();literal_test();trailing_test();paren_test();puts("native parser tests: 6 groups passed");return 0;}
