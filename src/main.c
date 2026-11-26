#include "reaper/lexer.h"
#include "reaper/ast.h"
#include "reaper/evolution.h"
#include "reaper/token_catalog.h"
#include "reaper/capability_suite.h"
#include "reaper/framework.h"
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
      "       reaper-c [--frameworks|--framework NAME]\n"
      "  --version           Show native runtime version\n"
      "  --evolution-status  Show native evolution gates and safety boundary\n"
      "  --tokens            Print lexical tokens\n"
      "  --ast-json          Parse one expression and print deterministic AST JSON\n"
      "  --capabilities      List the native capability registry\n"
      "  --capability NAME   Inspect one native capability module\n"
      "  --frameworks        List built-in framework extension profiles\n"
      "  --framework NAME    Inspect a built-in framework extension profile\n",REAPER_VERSION);
}
static void print_framework(const ReaperFrameworkManifest *manifest) {
    printf("%s\t%s\t%u.%u.%u\t%s\n",manifest->id,manifest->name,
           manifest->version.major,manifest->version.minor,manifest->version.patch,
           (manifest->flags & REAPER_FRAMEWORK_DECLARATIVE_ONLY) != 0U
               ? "declarative-only" : "host-extension");
    printf("  %s\n",manifest->description);
    printf("  ABI: %u.%u; required capabilities: 0x%016llx\n",
           manifest->abi_major,manifest->abi_minor,
           (unsigned long long)manifest->required_capabilities);
    for(size_t i=0U;i<manifest->dependency_count;++i) {
        const ReaperFrameworkDependency *dependency=&manifest->dependencies[i];
        printf("  requires: %s >= %u.%u.%u",dependency->id,
               dependency->minimum_version.major,
               dependency->minimum_version.minor,
               dependency->minimum_version.patch);
        if(dependency->maximum_version_exclusive.major != 0U ||
           dependency->maximum_version_exclusive.minor != 0U ||
           dependency->maximum_version_exclusive.patch != 0U)
            printf(" < %u.%u.%u",dependency->maximum_version_exclusive.major,
                   dependency->maximum_version_exclusive.minor,
                   dependency->maximum_version_exclusive.patch);
        putchar('\n');
    }
    for(size_t i=0U;i<manifest->provides_count;++i)
        printf("  provides: %s\n",manifest->provides[i]);
    for(size_t i=0U;i<manifest->extension_point_count;++i)
        printf("  extension-point: %s\n",manifest->extension_points[i]);
}
int main(int argc,char **argv) {
    int dump=0,ast_json=0,catalog_dump=0,capability_dump=0,framework_dump=0;
    const char *catalog_lookup=NULL;
    const char *capability_lookup=NULL;
    const char *framework_lookup=NULL;
    const char *path=NULL;
    for(int i=1;i<argc;++i) {
        if(strcmp(argv[i],"--version")==0){puts("Reaper " REAPER_VERSION " (C17 native core)");return 0;}
        if(strcmp(argv[i],"--evolution-status")==0){reaper_evolution_print_status();return 0;}
        if(strcmp(argv[i],"--tokens")==0){dump=1;continue;}
        if(strcmp(argv[i],"--ast-json")==0){ast_json=1;continue;}
        if(strcmp(argv[i],"--catalog")==0){catalog_dump=1;continue;}
        if(strcmp(argv[i],"--capabilities")==0){capability_dump=1;continue;}
        if(strcmp(argv[i],"--capability")==0){if(i+1>=argc){usage(stderr);return 2;}capability_lookup=argv[++i];continue;}
        if(strcmp(argv[i],"--frameworks")==0){framework_dump=1;continue;}
        if(strcmp(argv[i],"--framework")==0){if(i+1>=argc){usage(stderr);return 2;}framework_lookup=argv[++i];continue;}
        if(strcmp(argv[i],"--catalog-token")==0){if(i+1>=argc){usage(stderr);return 2;}catalog_lookup=argv[++i];continue;}
        if(argv[i][0]=='-'||(dump&&ast_json)){usage(stderr);return 2;}
        if(path){usage(stderr);return 2;} path=argv[i];
    }
    if(framework_dump||framework_lookup){
        if(path||dump||ast_json||catalog_dump||catalog_lookup||capability_dump||
           capability_lookup||(framework_dump&&framework_lookup)){usage(stderr);return 2;}
        if(framework_lookup){
            const ReaperFrameworkManifest *manifest =
                reaper_framework_builtin_find(framework_lookup);
            if(manifest==NULL){
                fprintf(stderr,"reaper-c: unknown framework profile %s\n",framework_lookup);
                return 1;
            }
            print_framework(manifest);
            return 0;
        }
        for(size_t i=0U;i<reaper_framework_builtin_count();++i)
            print_framework(reaper_framework_builtin_at(i));
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
        if(!reaper_token_catalog_validate()){fprintf(stderr,"reaper-c: token catalogue integrity failure\n");return 1;}
        if(catalog_lookup){
            const ReaperCatalogEntry *entry=reaper_token_catalog_lookup(catalog_lookup);
            if(!entry){fprintf(stderr,"reaper-c: unknown catalogue token %s\n",catalog_lookup);return 1;}
            printf("%03zu\t%s\t%s\t%s\n",entry->ordinal,entry->lexeme,entry->group,entry->name);
            return 0;
        }
        for(size_t i=0;i<reaper_token_catalog_count();++i){
            const ReaperCatalogEntry *entry=reaper_token_catalog_at(i);
            printf("%03zu\t%s\t%s\t%s\n",entry->ordinal,entry->lexeme,entry->group,entry->name);
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
