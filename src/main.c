#include "reaper/lexer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define REAPER_VERSION "0.2.0-dev"
static char *read_file(const char *path){FILE *f=fopen(path,"rb");if(!f)return NULL;if(fseek(f,0,SEEK_END)!=0){fclose(f);return NULL;}long n=ftell(f);if(n<0||fseek(f,0,SEEK_SET)!=0){fclose(f);return NULL;}char *b=malloc((size_t)n+1);if(!b){fclose(f);return NULL;}size_t got=fread(b,1,(size_t)n,f);if(got!=(size_t)n||ferror(f)){free(b);fclose(f);return NULL;}b[got]='\0';fclose(f);return b;}
static void usage(FILE *f){fprintf(f,"Reaper %s — native C development runtime\nUsage: reaper-c [--version] [--tokens] <source.rpr>\n  --version  Show native runtime version\n  --tokens   Print lexical tokens (native lexer bring-up mode)\n",REAPER_VERSION);}
int main(int argc,char **argv){int dump=0;const char *path=NULL;for(int i=1;i<argc;++i){if(!strcmp(argv[i],"--version")){puts("Reaper " REAPER_VERSION " (C17 native core)");return 0;}if(!strcmp(argv[i],"--tokens")){dump=1;continue;}if(argv[i][0]=='-'){usage(stderr);return 2;}if(path){usage(stderr);return 2;}path=argv[i];}if(!path){usage(stderr);return 2;}
 char *source=read_file(path);if(!source){fprintf(stderr,"reaper-c: cannot read %s\n",path);return 2;}ReaperTokenArray ts={0};ReaperLexError e={{0},0,0};if(!reaper_lex(source,&ts,&e)){fprintf(stderr,"%s:%zu:%zu: lexer error: %s\n",path,e.line,e.column,e.message);free(source);return 1;}
 if(dump){for(size_t i=0;i<ts.length;++i)printf("%zu:%zu %-12s %s\n",ts.items[i].line,ts.items[i].column,reaper_token_kind_name(ts.items[i].kind),ts.items[i].text);}else printf("Reaper native lexer: %s — %zu tokens; parser/runtime migration is in progress.\n",path,ts.length-1);
 reaper_tokens_free(&ts);free(source);return 0;}
