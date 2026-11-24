#include "reaper/lexer.h"
#include "reaper/token_catalog.h"
#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const char *const keywords[]={
 "make","vary","change","craft","yield","emit","when","otherwise","each","in","loop","while","true","false","nothing","and","or","not","module","import","as","pub","export","fn","struct","enum","trait","impl","type","const","let","mut","return","if","else","match","region","raw","arena","signal","async","await","test","comptime","requires","ensures","unsafe","extern","drop","where","for","break","continue","defer","пусть","переменная","изменить","функция","вернуть","вывести","если","иначе","для","в","цикл","пока","истина","ложь","ничего","и","или","не","импорт","экспорт","как","модуль","публичный","процедура","структура","перечисление","типаж","реализация","тип","константа","связать","изменяемый","возврат","условие","альтернатива","выбор","область","сырой","арена","сигнал","асинхронно","ожидать","тест","вычислить_при_сборке","требует","гарантирует","небезопасно","внешний","где","уничтожить","для_каждого","прервать","продолжить","отложить"
};
static int is_keyword(const char *s){for(size_t i=0;i<sizeof keywords/sizeof keywords[0];++i)if(strcmp(s,keywords[i])==0)return 1;return 0;}
/* Count UTF-8 code points, not bytes, in the public 1-based source column. */
static void advance_column(size_t *column,unsigned char byte){if((byte&0xC0u)!=0x80u)++*column;}

typedef struct { const char *alias; const char *canonical; } ReaperKeywordAlias;
static const ReaperKeywordAlias russian_aliases[] = {
 {"пусть","make"},
 {"переменная","vary"},
 {"изменить","change"},
 {"функция","craft"},
 {"вернуть","yield"},
 {"вывести","emit"},
 {"если","when"},
 {"иначе","otherwise"},
 {"для","each"},
 {"в","in"},
 {"цикл","loop"},
 {"пока","while"},
 {"истина","true"},
 {"ложь","false"},
 {"ничего","nothing"},
 {"и","and"},
 {"или","or"},
 {"не","not"},
 {"импорт","import"},
 {"экспорт","export"},
 {"как","as"},
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
const char *reaper_token_canonical_text(const ReaperToken *token){
 if(!token||!token->text)return "";
 if(token->kind!=REAPER_TOK_KEYWORD)return token->text;
 for(size_t i=0;i<sizeof russian_aliases/sizeof russian_aliases[0];++i)
  if(strcmp(token->text,russian_aliases[i].alias)==0)return russian_aliases[i].canonical;
 return token->text;
}
static int append_token(ReaperTokenArray *o,ReaperTokenKind k,const char *s,size_t n,
                         size_t l,size_t c,int *limit_exceeded){
 if(o->length>=REAPER_MAX_TOKENS){if(limit_exceeded)*limit_exceeded=1;return 0;}
 if(o->length==o->capacity){size_t z=o->capacity?o->capacity*2:32;
  if(z<o->capacity||z>SIZE_MAX/sizeof *o->items)return 0;
  if(z>REAPER_MAX_TOKENS)z=REAPER_MAX_TOKENS;
  ReaperToken *p=realloc(o->items,z*sizeof *p);if(!p)return 0;o->items=p;o->capacity=z;
 }
 char *v=malloc(n+1);if(!v)return 0;memcpy(v,s,n);v[n]='\0';
 o->items[o->length++]=(ReaperToken){k,v,l,c};return 1;
}
static int fail(ReaperLexError *e,size_t l,size_t c,const char *m){if(e){snprintf(e->message,sizeof e->message,"%s",m);e->line=l;e->column=c;}return 0;}

/* Reject overlong encodings, surrogate code points and values beyond U+10FFFF. */
static int validate_utf8_source(const unsigned char *source, size_t *bad_line, size_t *bad_column) {
 size_t line=1u,column=1u;
 for(size_t i=0u;source[i]!='\0';){
  const unsigned char lead=source[i];
  size_t width=0u;
  if(lead<0x80u) width=1u;
  else if(lead>=0xC2u&&lead<=0xDFu) width=2u;
  else if(lead>=0xE0u&&lead<=0xEFu) width=3u;
  else if(lead>=0xF0u&&lead<=0xF4u) width=4u;
  else goto invalid;
  for(size_t j=1u;j<width;++j){
   const unsigned char next=source[i+j];
   if(next=='\0'||(next&0xC0u)!=0x80u) goto invalid;
   if(j==1u){
    if(lead==0xE0u&&next<0xA0u) goto invalid;
    if(lead==0xEDu&&next>0x9Fu) goto invalid;
    if(lead==0xF0u&&next<0x90u) goto invalid;
    if(lead==0xF4u&&next>0x8Fu) goto invalid;
   }
  }
  if(width==1u&&lead=='\n'){++line;column=1u;}
  else ++column;
  i+=width;
  continue;
invalid:
  if(bad_line)*bad_line=line;
  if(bad_column)*bad_column=column;
  return 0;
 }
 return 1;
}
static int ident_start(unsigned char c){return isalpha(c)||c=='_'||c>=0x80;}
static int ident_more(unsigned char c){return isalnum(c)||c=='_'||c>=0x80;}
static int one_op(char c){return strchr("+-*/%<>(){}[],=:;.!?@|~&^",c)!=NULL;}
static int is_pair_operator(const char *p){
 static const char *const ops[]={":=","==","!=","<=",">=","//","**","++","??","+%","+|","->","=>","::","&&","||","<<",">>","&=","|="};
 for(size_t i=0;i<sizeof ops/sizeof ops[0];++i)if(p[0]==ops[i][0]&&p[1]==ops[i][1])return 1;
 return 0;
}
int reaper_lex(const char *source,ReaperTokenArray *out,ReaperLexError *error){
 if(!source||!out)return fail(error,1,1,"source and output are required");memset(out,0,sizeof *out);if(error)memset(error,0,sizeof *error);
 int token_limit_exceeded=0;
 size_t source_bytes=0u;
 while(source_bytes<=REAPER_MAX_SOURCE_BYTES && source[source_bytes]!='\0')++source_bytes;
 if(source_bytes>REAPER_MAX_SOURCE_BYTES)
  return fail(error,1,1,"source exceeds the 16 MiB lexer input limit");
 size_t bad_line=1u,bad_column=1u;
 if(!validate_utf8_source((const unsigned char *)source,&bad_line,&bad_column))
  return fail(error,bad_line,bad_column,"source is not valid UTF-8");
 const char *p=source;size_t line=1,col=1;
 while(*p){unsigned char c=(unsigned char)*p;
  if(c==' '||c=='\t'||c=='\r'){++p;++col;continue;}
  if(c=='\n'){if(!append_token(out, REAPER_TOK_NEWLINE,p,1,line,col, &token_limit_exceeded))goto oom;++p;++line;col=1;continue;}
  if(c=='#'){while(*p&&*p!='\n'){advance_column(&col,(unsigned char)*p);++p;}continue;}
  if(c=='"'){size_t sl=line,sc=col++;++p;char *decoded=malloc(strlen(p)+1);if(!decoded)goto oom;size_t used=0;int closed=0;
   while(*p){if(*p=='"'){++p;++col;closed=1;break;}if(*p=='\n'){free(decoded);reaper_tokens_free(out);return fail(error,sl,sc,"string literal cannot span lines");}
    char v=*p++;advance_column(&col,(unsigned char)v);if(v=='\\'){char e=*p;if(!e)break;++p;advance_column(&col,(unsigned char)e);switch(e){case 'n':v='\n';break;case 'r':v='\r';break;case 't':v='\t';break;case '"':v='"';break;case '\\':v='\\';break;default:free(decoded);reaper_tokens_free(out);return fail(error,line,col-1,"unknown string escape");}}
    decoded[used++]=v;
   }
   if(!closed){free(decoded);reaper_tokens_free(out);return fail(error,sl,sc,"unterminated string literal");}
   decoded[used]='\0';if(!append_token(out, REAPER_TOK_STRING,decoded,used,sl,sc, &token_limit_exceeded)){free(decoded);goto oom;}free(decoded);continue;
  }
  if(isdigit(c)){const char *s=p;size_t sc=col;while(isdigit((unsigned char)*p)){++p;++col;}if(*p=='.'&&isdigit((unsigned char)p[1])){++p;++col;while(isdigit((unsigned char)*p)){++p;++col;}}if(!append_token(out,REAPER_TOK_NUMBER,s,(size_t)(p-s),line,sc,&token_limit_exceeded))goto oom;continue;}
  if(ident_start(c)){const char *s=p;size_t sc=col;while(ident_more((unsigned char)*p)){advance_column(&col,(unsigned char)*p);++p;}size_t n=(size_t)(p-s);char *w=malloc(n+1);if(!w)goto oom;memcpy(w,s,n);w[n]='\0';ReaperTokenKind k=is_keyword(w)?REAPER_TOK_KEYWORD:REAPER_TOK_IDENTIFIER;free(w);if(!append_token(out, k,s,n,line,sc, &token_limit_exceeded))goto oom;continue;}
  size_t sc=col;
  if(p[0]&&p[1]&&p[2]){
   char candidate[4]={p[0],p[1],p[2],'\0'};
   if(reaper_token_catalog_lookup(candidate)){
    if(!append_token(out, REAPER_TOK_CATALOG_OPERATOR,p,3,line,sc, &token_limit_exceeded))goto oom;
    p+=3;col+=3;continue;
   }
  }
  if(p[1]&&is_pair_operator(p)){if(!append_token(out, REAPER_TOK_OPERATOR,p,2,line,sc, &token_limit_exceeded))goto oom;p+=2;col+=2;continue;}
  if(one_op((char)c)){ReaperTokenKind k=strchr("(){}[],;.",(char)c)?REAPER_TOK_PUNCTUATION:REAPER_TOK_OPERATOR;if(!append_token(out, k,p,1,line,sc, &token_limit_exceeded))goto oom;++p;++col;continue;}
  reaper_tokens_free(out);return fail(error,line,col,"unexpected character");
 }
 if(!append_token(out, REAPER_TOK_EOF,"",0,line,col, &token_limit_exceeded))goto oom;return 1;
oom: reaper_tokens_free(out);
 if(token_limit_exceeded)return fail(error,line,col,"token count exceeds the 262144-token limit");
 return fail(error,line,col,"out of memory while tokenizing source");
}
void reaper_tokens_free(ReaperTokenArray *t){if(!t)return;for(size_t i=0;i<t->length;++i)free(t->items[i].text);free(t->items);memset(t,0,sizeof *t);}
const char *reaper_token_kind_name(ReaperTokenKind k){switch(k){case REAPER_TOK_EOF:return "EOF";case REAPER_TOK_NEWLINE:return "NEWLINE";case REAPER_TOK_IDENTIFIER:return "IDENT";case REAPER_TOK_KEYWORD:return "KEYWORD";case REAPER_TOK_NUMBER:return "NUMBER";case REAPER_TOK_STRING:return "STRING";case REAPER_TOK_OPERATOR:return "OPERATOR";case REAPER_TOK_CATALOG_OPERATOR:return "CATALOG_OPERATOR";case REAPER_TOK_PUNCTUATION:return "PUNCTUATION";default:return "UNKNOWN";}}
