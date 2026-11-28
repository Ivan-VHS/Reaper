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
 assert(strstr(b,"\"source_start_byte\":0"));
 assert(strstr(b,"\"source_end_byte\":"));

 fclose(f);reaper_ast_free(&a);
}
int main(void){precedence_test();power_test();bridge_test();legacy_flow_test();literal_test();trailing_test();paren_test();json_test();puts("native parser tests: 8 groups passed");return 0;}
