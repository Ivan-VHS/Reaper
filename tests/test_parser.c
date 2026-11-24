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
static void nesting_limit_test(void){
 char accepted[2u*255u+2u];
 char rejected[2u*256u+2u];
 size_t accepted_size=255u,rejected_size=256u;
 ReaperAst ast;ReaperParseError error;
 for(size_t i=0u;i<accepted_size;i++)accepted[i]='(';
 accepted[accepted_size]='1';
 for(size_t i=0u;i<accepted_size;i++)accepted[accepted_size+1u+i]=')';
 accepted[2u*accepted_size+1u]='\0';
 assert(parse(accepted,&ast,&error));
 reaper_ast_free(&ast);

 for(size_t i=0u;i<rejected_size;i++)rejected[i]='(';
 rejected[rejected_size]='1';
 for(size_t i=0u;i<rejected_size;i++)rejected[rejected_size+1u+i]=')';
 rejected[2u*rejected_size+1u]='\0';
 assert(!parse(rejected,&ast,&error));
 assert(strstr(error.message,"nesting limit")!=NULL);
 assert(ast.items==NULL&&ast.length==0u);
}
static void json_test(void){
 ReaperAst a;ReaperParseError e;assert(parse("value + \"a\\\"b\"",&a,&e));
 FILE *f=tmpfile();assert(f);assert(reaper_ast_write_json(&a,f));assert(fflush(f)==0);assert(fseek(f,0,SEEK_SET)==0);
 char b[1024];size_t n=fread(b,1,sizeof b-1,f);b[n]='\0';
 assert(strstr(b,"\"kind\":\"binary\""));assert(strstr(b,"\"text\":\"a\\\"b\""));
 fclose(f);reaper_ast_free(&a);
}
int main(void){precedence_test();power_test();bridge_test();legacy_flow_test();literal_test();trailing_test();paren_test();nesting_limit_test();json_test();puts("native parser tests: 9 groups passed");return 0;}
