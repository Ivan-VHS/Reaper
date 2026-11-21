#include "reaper/lexer.h"
#include "reaper/ast.h"
#include "reaper/evolution.h"
#include "reaper/token_catalog.h"
#include "reaper/selfhood.h"
#include "reaper/ffi.h"
#include <inttypes.h>
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
      "       reaper-c --eval <integer-expression> | --run <expression.rpr>\n"
      "       reaper-c --selfhood | --selfhood-token <identity>\n"
      "  --version           Show native runtime version\n"
      "  --evolution-status  Show native evolution gates and safety boundary\n"
      "  --tokens            Print lexical tokens\n"
      "  --ast-json          Parse one expression and print deterministic AST JSON\n"
      "  --eval              Evaluate an integer expression in the native C17 pipeline\n"
      "  --run               Evaluate one integer-expression source file natively\n"
      "  --selfhood          Print the 20-entry identity/autonomy vocabulary\n"
      "  --selfhood-token    Look up one exact identity term\n",REAPER_VERSION);
}

static int run_expression(const char *source, size_t length, const char *label) {
    char error[256] = {0};
    int64_t result = 0;
    int32_t status = reaper_v1_eval_i64(source, (uint64_t)length,
                                        &result, error, sizeof error);
    if (status != REAPER_ABI_OK) {
        fprintf(stderr, "%s: native evaluation failed (%d): %s\n",
                label, (int)status, error);
        return 1;
    }
    printf("%" PRId64 "\n", result);
    return 0;
}

int main(int argc,char **argv) {
    int dump=0,ast_json=0,catalog_dump=0,run_mode=0,selfhood_dump=0;\n    const char *catalog_lookup=NULL,*selfhood_lookup=NULL,*eval_expression=NULL,*path=NULL;
    for(int i=1;i<argc;++i) {
        if(strcmp(argv[i],"--version")==0){puts("Reaper " REAPER_VERSION " (C17 native core)");return 0;}
        if(strcmp(argv[i],"--evolution-status")==0){reaper_evolution_print_status();return 0;}
        if(strcmp(argv[i],"--tokens")==0){dump=1;continue;}
        if(strcmp(argv[i],"--ast-json")==0){ast_json=1;continue;}
        if(strcmp(argv[i],"--catalog")==0){catalog_dump=1;continue;}\n        if(strcmp(argv[i],"--run")==0){run_mode=1;continue;}\n        if(strcmp(argv[i],"--selfhood")==0){selfhood_dump=1;continue;}\n        if(strcmp(argv[i],"--eval")==0){if(i+1>=argc){usage(stderr);return 2;}eval_expression=argv[++i];continue;}\n        if(strcmp(argv[i],"--selfhood-token")==0){if(i+1>=argc){usage(stderr);return 2;}selfhood_lookup=argv[++i];continue;}
        if(strcmp(argv[i],"--catalog-token")==0){if(i+1>=argc){usage(stderr);return 2;}catalog_lookup=argv[++i];continue;}
        if(argv[i][0]=='-'||(dump&&ast_json)){usage(stderr);return 2;}
        if(path){usage(stderr);return 2;} path=argv[i];
    }

    if(selfhood_dump||selfhood_lookup){
        if(path||dump||ast_json||catalog_dump||catalog_lookup||
           (selfhood_dump&&selfhood_lookup)||eval_expression||run_mode){usage(stderr);return 2;}
        if(selfhood_lookup){
            const ReaperSelfhoodEntry *entry=reaper_selfhood_find(selfhood_lookup);
            if(!entry){fprintf(stderr,"reaper-c: unknown selfhood identity %s\\n",selfhood_lookup);return 1;}
            printf("%02u\\t%s\\t%s\\t%s\\n",entry->ordinal,entry->identity,entry->transformation,entry->autonomy);
            return 0;
        }
        for(size_t i=0;i<reaper_selfhood_count();++i){
            const ReaperSelfhoodEntry *entry=reaper_selfhood_at(i);
            printf("%02u\\t%s\\t%s\\t%s\\n",entry->ordinal,entry->identity,entry->transformation,entry->autonomy);
        }
        return 0;
    }
    if(eval_expression){
        if(path||run_mode||dump||ast_json||catalog_dump||catalog_lookup){usage(stderr);return 2;}
        return run_expression(eval_expression,strlen(eval_expression),"<argument>");
    }
    if(catalog_dump||catalog_lookup){
        if(path||dump||ast_json||(catalog_dump&&catalog_lookup)){usage(stderr);return 2;}
        if(!reaper_token_catalog_validate()){fprintf(stderr,"reaper-c: token catalogue integrity failure\\n");return 1;}
        if(catalog_lookup){
            const ReaperCatalogEntry *entry=reaper_token_catalog_lookup(catalog_lookup);
            if(!entry){fprintf(stderr,"reaper-c: unknown catalogue token %s\\n",catalog_lookup);return 1;}
            printf("%03zu\\t%s\\t%s\\t%s\\n",entry->ordinal,entry->lexeme,entry->group,entry->name);
            return 0;
        }
        for(size_t i=0;i<reaper_token_catalog_count();++i){
            const ReaperCatalogEntry *entry=reaper_token_catalog_at(i);
            printf("%03zu\\t%s\\t%s\\t%s\\n",entry->ordinal,entry->lexeme,entry->group,entry->name);
        }
        return 0;
    }
    if(!path||(dump&&ast_json)||(run_mode&&(dump||ast_json))){usage(stderr);return 2;}
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
