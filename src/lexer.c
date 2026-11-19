#include "reaper/lexer.h"
#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const char *const keywords[]={"make","vary","change","craft","yield","emit","when","otherwise","each","in","loop","while","true","false","nothing","and","or","not"};
static int is_keyword(const char *s){for(size_t i=0;i<sizeof keywords/sizeof keywords[0];++i)if(strcmp(s,keywords[i])==0)return 1;return 0;}
static int append_token(ReaperTokenArray *o,ReaperTokenKind k,const char *s,size_t n,size_t l,size_t c){
 if(o->length==o->capacity){size_t z=o->capacity?o->capacity*2:32;if(z<o->capacity||z>SIZE_MAX/sizeof *o->items)return 0;ReaperToken *p=realloc(o->items,z*sizeof *p);if(!p)return 0;o->items=p;o->capacity=z;}
 char *v=malloc(n+1);if(!v)return 0;memcpy(v,s,n);v[n]='\\0';o->items[o->length++]=(ReaperToken){k,v,l,c};return 1;
}
static int fail(ReaperLexError *e,size_t l,size_t c,const char *m){if(e){snprintf(e->message,sizeof e->message,"%s",m);e->line=l;e->column=c;}return 0;}
static int ident_start(unsigned char c){return isalpha(c)||c=='_'||c>=0x80;}
static int ident_more(unsigned char c){return isalnum(c)||c=='_'||c>=0x80;}
static int one_op(char c){return strchr("+-*/%<>(){}[],=",c)!=NULL;}
int reaper_lex(const char *source,ReaperTokenArray *out,ReaperLexError *error){
 if(!source||!out)return fail(error,1,1,"source and output are required");memset(out,0,sizeof *out);if(error)memset(error,0,sizeof *error);
 const char *p=source;size_t line=1,col=1;
 while(*p){unsigned char c=(unsigned char)*p;
  if(c==' '||c=='\\t'||c=='\\r'){++p;++col;continue;}
  if(c=='\\n'){if(!append_token(out,REAPER_TOK_NEWLINE,p,1,line,col))goto oom;++p;++line;col=1;continue;}
  if(c=='#'){while(*p&&*p!='\\n'){++p;++col;}continue;}
  if(c=='"'){size_t sl=line,sc=col++;++p;char *decoded=malloc(strlen(p)+1);if(!decoded)goto oom;size_t used=0;int closed=0;
   while(*p){if(*p=='"'){++p;++col;closed=1;break;}if(*p=='\\n'){free(decoded);reaper_tokens_free(out);return fail(error,sl,sc,"string literal cannot span lines");}
    char v=*p++;++col;if(v=='\\\\'){char e=*p;if(!e)break;++p;++col;switch(e){case 'n':v='\\n';break;case 'r':v='\\r';break;case 't':v='\\t';break;case '"':v='"';break;case '\\\\':v='\\\\';break;default:free(decoded);reaper_tokens_free(out);return fail(error,line,col-1,"unknown string escape");}}
    decoded[used++]=v;
   }
   if(!closed){free(decoded);reaper_tokens_free(out);return fail(error,sl,sc,"unterminated string literal");}
   decoded[used]='\\0';if(!append_token(out,REAPER_TOK_STRING,decoded,used,sl,sc)){free(decoded);goto oom;}free(decoded);continue;
  }
  if(isdigit(c)){const char *s=p;size_t sc=col;while(isdigit((unsigned char)*p)){++p;++col;}if(*p=='.'&&isdigit((unsigned char)p[1])){++p;++col;while(isdigit((unsigned char)*p)){++p;++col;}}if(!append_token(out,REAPER_TOK_NUMBER,s,(size_t)(p-s),line,sc))goto oom;continue;}
  if(ident_start(c)){const char *s=p;size_t sc=col;while(ident_more((unsigned char)*p)){++p;++col;}size_t n=(size_t)(p-s);char *w=malloc(n+1);if(!w)goto oom;memcpy(w,s,n);w[n]='\\0';ReaperTokenKind k=is_keyword(w)?REAPER_TOK_KEYWORD:REAPER_TOK_IDENTIFIER;free(w);if(!append_token(out,k,s,n,line,sc))goto oom;continue;}
  size_t sc=col;if(p[1]){char pair[3]={p[0],p[1],'\\0'};if(!strcmp(pair,":=")||!strcmp(pair,"==")||!strcmp(pair,"!=")||!strcmp(pair,"<=")||!strcmp(pair,">=")||!strcmp(pair,"//")||!strcmp(pair,"**")||!strcmp(pair,"++")||!strcmp(pair,"~>")){if(!append_token(out,REAPER_TOK_OPERATOR,p,2,line,sc))goto oom;p+=2;col+=2;continue;}}
  if(one_op((char)c)){ReaperTokenKind k=strchr("(){}[],",(char)c)?REAPER_TOK_PUNCTUATION:REAPER_TOK_OPERATOR;if(!append_token(out,k,p,1,line,sc))goto oom;++p;++col;continue;}
  reaper_tokens_free(out);return fail(error,line,col,"unexpected character");
 }
 if(!append_token(out,REAPER_TOK_EOF,"",0,line,col))goto oom;return 1;
oom: reaper_tokens_free(out);return fail(error,line,col,"out of memory while tokenizing source");
}
void reaper_tokens_free(ReaperTokenArray *t){if(!t)return;for(size_t i=0;i<t->length;++i)free(t->items[i].text);free(t->items);memset(t,0,sizeof *t);}
const char *reaper_token_kind_name(ReaperTokenKind k){switch(k){case REAPER_TOK_EOF:return "EOF";case REAPER_TOK_NEWLINE:return "NEWLINE";case REAPER_TOK_IDENTIFIER:return "IDENT";case REAPER_TOK_KEYWORD:return "KEYWORD";case REAPER_TOK_NUMBER:return "NUMBER";case REAPER_TOK_STRING:return "STRING";case REAPER_TOK_OPERATOR:return "OPERATOR";case REAPER_TOK_PUNCTUATION:return "PUNCTUATION";default:return "UNKNOWN";}}
