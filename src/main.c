#include "reaper/lexer.h"
#include "reaper/ast.h"
#include "reaper/evolution.h"
#include "reaper/token_catalog.h"
#include "reaper/capability_suite.h"
#include "reaper/framework_suite.h"
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
      "       reaper-c [--capabilities|--capability MODULE]\n"
      "       reaper-c [--frameworks|--framework NAME|--framework-stats]\n"
      "  --version           Show native runtime version\n"
      "  --evolution-status  Show native evolution gates and safety boundary\n"
      "  --tokens            Print lexical tokens\n"
      "  --ast-json          Parse one expression and print deterministic AST JSON\n"
      "  --capabilities      List the native capability registry\n"
      "  --capability NAME   Inspect one native capability module\n"
      "  --frameworks        List the 20 registered framework namespaces\n"
      "  --framework NAME    Inspect one framework and its stable operation keys\n"
      "  --framework-stats   Print public registry maturity counters as JSON\n",REAPER_VERSION);
}
int main(int argc,char **argv) {
    int dump=0,ast_json=0,catalog_dump=0,capability_dump=0,framework_dump=0,framework_stats=0; const char *catalog_lookup=NULL; const char *capability_lookup=NULL; const char *framework_lookup=NULL; const char *path=NULL;
    for(int i=1;i<argc;++i) {
        if(strcmp(argv[i],"--version")==0){puts("Reaper " REAPER_VERSION " (C17 native core)");return 0;}
        if(strcmp(argv[i],"--evolution-status")==0){reaper_evolution_print_status();return 0;}
        if(strcmp(argv[i],"--tokens")==0){dump=1;continue;}
        if(strcmp(argv[i],"--ast-json")==0){ast_json=1;continue;}
        if(strcmp(argv[i],"--catalog")==0){catalog_dump=1;continue;}
        if(strcmp(argv[i],"--capabilities")==0){capability_dump=1;continue;}
        if(strcmp(argv[i],"--capability")==0){if(i+1>=argc){usage(stderr);return 2;}capability_lookup=argv[++i];continue;}
        if(strcmp(argv[i],"--frameworks")==0){framework_dump=1;continue;}
        if(strcmp(argv[i],"--framework-stats")==0){framework_stats=1;continue;}
        if(strcmp(argv[i],"--framework")==0){if(i+1>=argc){usage(stderr);return 2;}framework_lookup=argv[++i];continue;}
        if(strcmp(argv[i],"--catalog-token")==0){if(i+1>=argc){usage(stderr);return 2;}catalog_lookup=argv[++i];continue;}
        if(argv[i][0]=='-'||(dump&&ast_json)){usage(stderr);return 2;}
        if(path){usage(stderr);return 2;} path=argv[i];
    }

    if(framework_dump||framework_stats||framework_lookup){
        if(path||dump||ast_json||catalog_dump||catalog_lookup||
           capability_dump||capability_lookup||
           (framework_dump&&framework_stats)||(framework_dump&&framework_lookup)||
           (framework_stats&&framework_lookup)){usage(stderr);return 2;}
        if(framework_lookup){
            const ReaperFramework *framework=reaper_framework_find(framework_lookup);
            if(framework==NULL){
                fprintf(stderr,"reaper-c: unknown framework %s\n",framework_lookup);
                return 1;
            }
            printf("%s\t%s\t%s\t%s\t%u operations\n",
                   framework->id,framework->name,framework->domain,
                   framework->maturity,framework->function_count);
            for(uint32_t i=0U;i<framework->function_count;++i){
                const ReaperFrameworkFunction *function=&framework->functions[i];
                printf("  %s\t%s\t%u..%u args\t%s\n",
                       function->key,function->name,function->min_arity,
                       function->max_arity,function->description);
            }
            return 0;
        }
        if(framework_stats){
            ReaperFrameworkRegistryStats stats;
            if(reaper_framework_registry_stats(&stats)!=REAPER_FRAMEWORK_OK){
                fprintf(stderr,"reaper-c: framework statistics unavailable\n");
                return 1;
            }
            printf("{\"schema\":\"reaper.framework-registry-stats/v1\","
                   "\"abi_version\":%u,\"registered_frameworks\":%u,"
                   "\"registered_function_contracts\":%u,"
                   "\"registry_api_functions\":%u,"
                   "\"executable_domain_handlers\":%u,"
                   "\"reaper_source_bindings\":%u}\n",
                   reaper_framework_abi_version(),stats.registered_frameworks,
                   stats.registered_function_contracts,stats.registry_api_functions,
                   stats.executable_domain_handlers,stats.reaper_source_bindings);
            return 0;
        }
        for(uint32_t i=0U;i<reaper_framework_count();++i){
            const ReaperFramework *framework=reaper_framework_at(i);
            printf("%s\t%s\t%s\t%s\t%u operations\n",
                   framework->id,framework->name,framework->domain,
                   framework->maturity,framework->function_count);
        }
        return 0;
    }
    if(capability_dump||capability_lookup){
        if(path||dump||ast_json||catalog_dump||catalog_lookup||
           (capability_dump&&capability_lookup)){usage(stderr);return 2;}
        if(capability_lookup){
            const ReaperCapabilityModule *module =
                reaper_capability_module_find(capability_lookup);
            if(module==NULL){
                fprintf(stderr,"reaper-c: unknown capability module %s\n",capability_lookup);
                return 1;
            }
            printf("%s\t%s\t%s\t%zu operations\n",
                   module->id,module->name,module->domain,module->function_count);
            for(size_t i=0U;i<module->function_count;++i){
                const ReaperCapabilityFunction *function=&module->functions[i];
                if(function->min_arity==function->max_arity)
                    printf("  %s\t%zu args\t%s\n",function->name,
                           function->min_arity,function->description);
                else
                    printf("  %s\t%zu..%zu args\t%s\n",function->name,
                           function->min_arity,function->max_arity,function->description);
            }
            return 0;
        }
        for(size_t i=0U;i<reaper_capability_module_count();++i){
            const ReaperCapabilityModule *module=reaper_capability_module_at(i);
            printf("%s\t%s\t%s\t%zu operations\n",
                   module->id,module->name,module->domain,module->function_count);
        }
        return 0;
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
