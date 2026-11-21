#include "reaper/lexer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int has(const ReaperTokenArray *t,const char *s,ReaperTokenKind k){for(size_t i=0;i<t->length;++i)if(t->items[i].kind==k&&!strcmp(t->items[i].text,s))return 1;return 0;}
static int has_canonical(const ReaperTokenArray *t,const char *s){for(size_t i=0;i<t->length;++i)if(!strcmp(reaper_token_canonical_text(&t->items[i]),s))return 1;return 0;}
static void test_most_surface(void){
 const char *s="module counter\nstruct State { value: signal<i32> = 0 }\nfn increment(@: ~State, step: i32) -> i32 { @.value = @.value +| step }\n";
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));
 assert(has(&t,"module",REAPER_TOK_KEYWORD));assert(has(&t,"struct",REAPER_TOK_KEYWORD));assert(has(&t,"signal",REAPER_TOK_KEYWORD));assert(has(&t,"fn",REAPER_TOK_KEYWORD));assert(has(&t,"+|",REAPER_TOK_OPERATOR));assert(has(&t,"@",REAPER_TOK_OPERATOR));assert(has(&t,":",REAPER_TOK_OPERATOR));assert(has(&t,"->",REAPER_TOK_OPERATOR));assert(has(&t,".",REAPER_TOK_PUNCTUATION));reaper_tokens_free(&t);
}
static void test_most_operator_family(void){
 const char *s="x := a :: f ?? b +% c +| d raw { p + 4 }";
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));
 assert(has(&t,":=",REAPER_TOK_OPERATOR));assert(has(&t,"::",REAPER_TOK_OPERATOR));assert(!has(&t,"|>",REAPER_TOK_OPERATOR));assert(has(&t,"??",REAPER_TOK_OPERATOR));assert(has(&t,"+%",REAPER_TOK_OPERATOR));assert(has(&t,"+|",REAPER_TOK_OPERATOR));assert(has(&t,"raw",REAPER_TOK_KEYWORD));reaper_tokens_free(&t);
}
static void test_program(void){const char *s="make value := [1, 2] :: map(double)\nemit \"ok\"\n";ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));assert(t.length>10);assert(t.items[0].kind==REAPER_TOK_KEYWORD);assert(!strcmp(t.items[0].text,"make"));int flow=0,str=0;for(size_t i=0;i<t.length;++i){if(!strcmp(t.items[i].text,"::"))flow=1;if(t.items[i].kind==REAPER_TOK_STRING&&!strcmp(t.items[i].text,"ok"))str=1;}assert(flow&&str);reaper_tokens_free(&t);}
static void test_escape(void){ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex("emit \"a\\nb\"\n",&t,&e));assert(!strcmp(t.items[1].text,"a\nb"));reaper_tokens_free(&t);}
static void test_bad_escape(void){ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(!reaper_lex("emit \"bad\\q\"\n",&t,&e));assert(strstr(e.message,"escape"));assert(t.length==0);}
static void test_unterminated(void){ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(!reaper_lex("emit \"unfinished",&t,&e));assert(e.line==1&&e.column==6);}
static void test_most_russian_vocabulary(void){
 const char *s="функция удвоить(значение) { вернуть значение * 2 }\nпусть число := истина\nпеременная сумма := 0\nизменить сумма := сумма + 1\nдля элемент в range(1, 4) { если не ложь и элемент > 0 или ложь { вывести сумма } иначе { вывести ничего } }\nцикл пока сумма < 5 { изменить сумма := сумма + 1 }\nимпорт модуль как имя\nэкспорт имя\n";
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(s,&t,&e));
 assert(has(&t,"функция",REAPER_TOK_KEYWORD));assert(has(&t,"вернуть",REAPER_TOK_KEYWORD));assert(has(&t,"пусть",REAPER_TOK_KEYWORD));
 assert(has(&t,"переменная",REAPER_TOK_KEYWORD));assert(has(&t,"изменить",REAPER_TOK_KEYWORD));assert(has(&t,"вывести",REAPER_TOK_KEYWORD));
 assert(has(&t,"если",REAPER_TOK_KEYWORD));assert(has(&t,"иначе",REAPER_TOK_KEYWORD));assert(has(&t,"для",REAPER_TOK_KEYWORD));assert(has(&t,"в",REAPER_TOK_KEYWORD));
 assert(has(&t,"цикл",REAPER_TOK_KEYWORD));assert(has(&t,"пока",REAPER_TOK_KEYWORD));assert(has(&t,"истина",REAPER_TOK_KEYWORD));assert(has(&t,"ложь",REAPER_TOK_KEYWORD));
 assert(has(&t,"ничего",REAPER_TOK_KEYWORD));assert(has(&t,"и",REAPER_TOK_KEYWORD));assert(has(&t,"или",REAPER_TOK_KEYWORD));assert(has(&t,"не",REAPER_TOK_KEYWORD));
 assert(has(&t,"импорт",REAPER_TOK_KEYWORD));assert(has(&t,"экспорт",REAPER_TOK_KEYWORD));assert(has(&t,"как",REAPER_TOK_KEYWORD));
 assert(has_canonical(&t,"craft"));assert(has_canonical(&t,"yield"));assert(has_canonical(&t,"make"));assert(has_canonical(&t,"vary"));assert(has_canonical(&t,"change"));
 assert(has_canonical(&t,"when"));assert(has_canonical(&t,"otherwise"));assert(has_canonical(&t,"each"));assert(has_canonical(&t,"in"));assert(has_canonical(&t,"emit"));
 assert(has_canonical(&t,"loop"));assert(has_canonical(&t,"while"));assert(has_canonical(&t,"true"));assert(has_canonical(&t,"false"));assert(has_canonical(&t,"nothing"));
 assert(has_canonical(&t,"and"));assert(has_canonical(&t,"or"));assert(has_canonical(&t,"not"));assert(has_canonical(&t,"import"));assert(has_canonical(&t,"export"));assert(has_canonical(&t,"as"));
 assert(has(&t,"удвоить",REAPER_TOK_IDENTIFIER));assert(has(&t,"значение",REAPER_TOK_IDENTIFIER));assert(has(&t,"модуль",REAPER_TOK_KEYWORD));
 reaper_tokens_free(&t);
}

typedef struct {const char *alias;const char *canonical;} AliasExpectation;
static void test_most_extended_aliases(void){
 static const AliasExpectation cases[]={
   {"модуль","module"},
   {"публичный","pub"},
   {"процедура","fn"},
   {"структура","struct"},
   {"перечисление","enum"},
   {"типаж","trait"},
   {"реализация","impl"},
   {"тип","type"},
   {"константа","const"},
   {"связать","let"},
   {"изменяемый","mut"},
   {"возврат","return"},
   {"условие","if"},
   {"альтернатива","else"},
   {"выбор","match"},
   {"область","region"},
   {"сырой","raw"},
   {"арена","arena"},
   {"сигнал","signal"},
   {"асинхронно","async"},
   {"ожидать","await"},
   {"тест","test"},
   {"вычислить_при_сборке","comptime"},
   {"требует","requires"},
   {"гарантирует","ensures"},
   {"небезопасно","unsafe"},
   {"внешний","extern"},
   {"где","where"},
   {"уничтожить","drop"},
   {"для_каждого","for"},
   {"прервать","break"},
   {"продолжить","continue"},
   {"отложить","defer"}
 };
 const char *source=
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
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(source,&t,&e));
 for(size_t i=0;i<sizeof cases/sizeof cases[0];++i){
  assert(has(&t,cases[i].alias,REAPER_TOK_KEYWORD));
  assert(has_canonical(&t,cases[i].canonical));
 }
 reaper_tokens_free(&t);
 ReaperTokenArray unknown={0};
 assert(reaper_lex("структуры", &unknown, &e));
 assert(has(&unknown,"структуры",REAPER_TOK_IDENTIFIER));
 reaper_tokens_free(&unknown);
}
static void test_utf8_columns_count_codepoints(void){
 const char *source="вывести утка + 1";
 ReaperTokenArray t={0};ReaperLexError e={{0},0,0};assert(reaper_lex(source,&t,&e));
 int found=0;
 for(size_t i=0;i<t.length;++i)if(!strcmp(t.items[i].text,"+")){
  assert(t.items[i].column==14);found=1;
 }
 assert(found);reaper_tokens_free(&t);
}
int main(void){test_program();test_escape();test_bad_escape();test_unterminated();test_most_surface();test_most_operator_family();test_most_russian_vocabulary();test_most_extended_aliases();test_utf8_columns_count_codepoints();puts("native lexer tests: 9 groups passed");return 0;}
