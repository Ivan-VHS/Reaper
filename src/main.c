#include "reaper/lexer.h"
#include "reaper/ast.h"
#include "reaper/evolution.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define REAPER_VERSION "0.2.0-dev"
static char *read_file(const char *path) {
    FILE *f=fopen(path,"rb"); if(!f)return NULL;
    if(fseek(f,0,SEEK_END)!=0){fclose(f);return NULL;}
    long n=ftell(f); if(n<0||fseek(f,0,SEEK_SET)!=0){fclose(f);return NULL;}
    char *b=malloc((size_t)n+1U); if(!b){fclose(f);return NULL;}
    size_t got=fread(b,1U,(size_t)n,f);
    if(got!=(size_t)n||ferror(f)){free(b);fclose(f);return NULL;}
    b[got]='\0'; fclose(f); return b;
}
static void usage(FILE *f) {
    fprintf(f,"Reaper %s — native C17 development runtime\n"
      "Usage: reaper-c [--version] [--evolution-status] [--tokens|--ast-json] <source.rpr>\n"
      "  --version           Show native runtime version\n"
      "  --evolution-status  Show native evolution gates and safety boundary\n"
      "  --tokens            Print lexical tokens\n"
      "  --ast-json          Parse one expression and print deterministic AST JSON\n",REAPER_VERSION);
}
int main(int argc,char **argv) {
    int dump=0,ast_json=0; const char *path=NULL;
    for(int i=1;i<argc;++i) {
        if(strcmp(argv[i],"--version")==0){puts("Reaper " REAPER_VERSION " (C17 native core)");return 0;}
        if(strcmp(argv[i],"--evolution-status")==0){reaper_evolution_print_status();return 0;}
        if(strcmp(argv[i],"--tokens")==0){dump=1;continue;}
        if(strcmp(argv[i],"--ast-json")==0){ast_json=1;continue;}
        if(argv[i][0]=='-'||(dump&&ast_json)){usage(stderr);return 2;}
        if(path){usage(stderr);return 2;} path=argv[i];
    }
    if(!path||(dump&&ast_json)){usage(stderr);return 2;}
    char *source=read_file(path);
    if(!source){fprintf(stderr,"reaper-c: cannot read %s\n",path);return 2;}
    ReaperTokenArray tokens={0}; ReaperLexError error={{0},0,0};
    if(!reaper_lex(source,&tokens,&error)){
        fprintf(stderr,"%s:%zu:%zu: lexer error: %s\n",path,error.line,error.column,error.message);
        free(source);return 1;
    }
    int result=0;
    if(dump) {
        for(size_t i=0;i<tokens.length;++i)
            printf("%zu:%zu %-12s %s\n",tokens.items[i].line,tokens.items[i].column,
                   reaper_token_kind_name(tokens.items[i].kind),tokens.items[i].text);
    } else if(ast_json) {
        ReaperAst ast; ReaperParseError pe={{0},0,0};
        if(!reaper_parse_expression(&tokens,&ast,&pe)){
            fprintf(stderr,"%s:%zu:%zu: parser error: %s\n",path,pe.line,pe.column,pe.message);result=1;
        } else {
            if(!reaper_ast_write_json(&ast,stdout)){fprintf(stderr,"reaper-c: cannot serialize AST\n");result=1;}
            reaper_ast_free(&ast);
        }
    } else {
        printf("Reaper native lexer: %s — %zu tokens; parser/runtime migration is in progress.\n",path,tokens.length-1U);
    }
    reaper_tokens_free(&tokens);free(source);return result;
}
