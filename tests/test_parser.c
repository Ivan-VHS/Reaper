#include "reaper/ast.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int parse(const char *s,ReaperAst *a,ReaperParseError *e){ReaperTokenArray t={0};ReaperLexError le={{0},0,0};assert(reaper_lex(s,&t,&le));int ok=reaper_parse_expression(&t,a,e);reaper_tokens_free(&t);return ok;}
static void precedence_test(void){ReaperAst a;ReaperParseError e;assert(parse("1 + 2 * 3",&a,&e));assert(a.length==5);assert(!strcmp(a.items[a.root].text,"+"));assert(!strcmp(a.items[a.items[a.root].right].text,"*"));reaper_ast_free(&a);}
static void power_test(void){ReaperAst a;ReaperParseError e;assert(parse("2 ** 3 ** 4",&a,&e));assert(!strcmp(a.items[a.root].text,"**"));assert(!strcmp(a.items[a.items[a.root].right].text,"**"));reaper_ast_free(&a);}
static void bridge_test(void){ReaperAst a;ReaperParseError e;assert(parse("значение :: обработать ?? 7",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BINARY);reaper_ast_free(&a);}
static void legacy_flow_test(void){ReaperAst a;ReaperParseError e;assert(!parse("1 |> f",&a,&e));assert(strstr(e.message,"unexpected token"));}
static void literal_test(void){ReaperAst a;ReaperParseError e;assert(parse("true",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BOOLEAN);assert(!strcmp(a.items[a.root].text,"true"));reaper_ast_free(&a);assert(parse("истина",&a,&e));assert(a.items[a.root].kind==REAPER_AST_BOOLEAN);assert(!strcmp(a.items[a.root].text,"true"));reaper_ast_free(&a);assert(parse("ничего",&a,&e));assert(a.items[a.root].kind==REAPER_AST_NULL);assert(!strcmp(a.items[a.root].text,"nothing"));reaper_ast_free(&a);assert(parse("\"мост\"",&a,&e));assert(a.items[a.root].kind==REAPER_AST_STRING);reaper_ast_free(&a);}
static void most_boolean_operator_test(void){
 ReaperAst english,russian;ReaperParseError e;
 assert(parse("true and not false",&english,&e));
 assert(parse("истина и не ложь",&russian,&e));
 const ReaperAstNode *en=&english.items[english.root],*ru=&russian.items[russian.root];
 assert(en->kind==REAPER_AST_BINARY&&ru->kind==REAPER_AST_BINARY);
 assert(!strcmp(en->text,"and")&&!strcmp(ru->text,"and"));
 assert(english.items[en->left].kind==REAPER_AST_BOOLEAN);
 assert(russian.items[ru->left].kind==REAPER_AST_BOOLEAN);
 assert(!strcmp(english.items[en->left].text,russian.items[ru->left].text));
 assert(english.items[en->right].kind==REAPER_AST_UNARY);
 assert(russian.items[ru->right].kind==REAPER_AST_UNARY);
 assert(!strcmp(english.items[en->right].text,"not"));
 assert(!strcmp(russian.items[ru->right].text,"not"));
 assert(!strcmp(english.items[english.items[en->right].left].text,
                russian.items[russian.items[ru->right].left].text));
 reaper_ast_free(&english);reaper_ast_free(&russian);
}
static void trailing_test(void){ReaperAst a;ReaperParseError e;assert(!parse("1 2",&a,&e));assert(strstr(e.message,"unexpected token"));}
static void paren_test(void){ReaperAst a;ReaperParseError e;assert(!parse("(1 + 2",&a,&e));assert(strstr(e.message,"expected ')'"));}
static void json_test(void){
 ReaperAst a;ReaperParseError e;assert(parse("value + \"a\\\"b\"",&a,&e));
 FILE *f=tmpfile();assert(f);assert(reaper_ast_write_json(&a,f));assert(fflush(f)==0);assert(fseek(f,0,SEEK_SET)==0);
 char b[1024];size_t n=fread(b,1,sizeof b-1,f);b[n]='\0';
 assert(strstr(b,"\"kind\":\"binary\""));assert(strstr(b,"\"text\":\"a\\\"b\""));
 fclose(f);reaper_ast_free(&a);
}
int main(void){precedence_test();power_test();bridge_test();legacy_flow_test();literal_test();most_boolean_operator_test();trailing_test();paren_test();json_test();puts("native parser tests: 9 groups passed");return 0;}
