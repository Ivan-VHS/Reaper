#include "reaper/lexer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int has(const ReaperTokenArray *t,const char *s,ReaperTokenKind k){for(size_t i=0;i<t->length;++i)if(t->items[i].kind==k&&!strcmp(t->items[i].text,s))return 1;return 0;}
static void test_most_surface(void){
 const char *s="module counter\nstruct State { value: signal<i32> = 0 }\nfn increment(@: ~State, step: i32) -> i32 { @.value = @.value +| step }\n";
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));
 assert(has(&t,"module",REAPER_TOK_KEYWORD));assert(has(&t,"struct",REAPER_TOK_KEYWORD));assert(has(&t,"signal",REAPER_TOK_KEYWORD));assert(has(&t,"fn",REAPER_TOK_KEYWORD));assert(has(&t,"+|",REAPER_TOK_OPERATOR));assert(has(&t,"@",REAPER_TOK_OPERATOR));assert(has(&t,":",REAPER_TOK_OPERATOR));assert(has(&t,"->",REAPER_TOK_OPERATOR));assert(has(&t,".",REAPER_TOK_PUNCTUATION));reaper_tokens_free(&t);
}
static void test_most_operator_family(void){
 const char *s="x := a |> f ?? b +% c +| d raw { p + 4 }";
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));
 assert(has(&t,":=",REAPER_TOK_OPERATOR));assert(has(&t,"|>",REAPER_TOK_OPERATOR));assert(has(&t,"??",REAPER_TOK_OPERATOR));assert(has(&t,"+%",REAPER_TOK_OPERATOR));assert(has(&t,"+|",REAPER_TOK_OPERATOR));assert(has(&t,"raw",REAPER_TOK_KEYWORD));reaper_tokens_free(&t);
}
static void test_program(void){const char *s="make value := [1, 2] ~> map(double)\nemit \"ok\"\n";ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));assert(t.length>10);assert(t.items[0].kind==REAPER_TOK_KEYWORD);assert(!strcmp(t.items[0].text,"make"));int flow=0,str=0;for(size_t i=0;i<t.length;++i){if(!strcmp(t.items[i].text,"~>"))flow=1;if(t.items[i].kind==REAPER_TOK_STRING&&!strcmp(t.items[i].text,"ok"))str=1;}assert(flow&&str);reaper_tokens_free(&t);}
static void test_escape(void){ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex("emit \"a\\nb\"\n",&t,&e));assert(!strcmp(t.items[1].text,"a\nb"));reaper_tokens_free(&t);}
static void test_bad_escape(void){ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(!reaper_lex("emit \"bad\\q\"\n",&t,&e));assert(strstr(e.message,"escape"));assert(t.length==0);}
static void test_unterminated(void){ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(!reaper_lex("emit \"unfinished",&t,&e));assert(e.line==1&&e.column==6);}
int main(void){test_program();test_escape();test_bad_escape();test_unterminated();test_most_surface();test_most_operator_family();puts("native lexer tests: 6 groups passed");return 0;}
