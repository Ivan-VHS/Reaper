#include "reaper/ast.h"
#include "reaper/capability_suite.h"
#include "reaper/codegen.h"
#include "reaper/evolution.h"
#include "reaper/ir.h"
#include "reaper/lexer.h"
#include "reaper/lower.h"
#include "reaper/token_catalog.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REAPER_VERSION "0.2.0-dev"

static char *read_file(const char *path) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) return NULL;
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }

    long size = ftell(file);
    if (size < 0 || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return NULL;
    }

    char *buffer = malloc((size_t)size + 1U);
    if (buffer == NULL) {
        fclose(file);
        return NULL;
    }

    size_t count = fread(buffer, 1U, (size_t)size, file);
    if (count != (size_t)size || ferror(file)) {
        free(buffer);
        fclose(file);
        return NULL;
    }

    buffer[count] = '\0';
    fclose(file);
    return buffer;
}

static void usage(FILE *stream) {
    fprintf(stream,
        "Reaper %s — native C17 compiler development track\n"
        "Usage: reaper-c [--version] [--evolution-status]\n"
        "       reaper-c [--tokens|--ast-json] <source.rpr>\n"
        "       reaper-c --emit-asm <expression.rpr> [-o output.s]\n"
        "       reaper-c [--catalog|--catalog-token TOKEN]\n"
        "       reaper-c [--capabilities|--capability MODULE]\n"
        "  --version           Show native compiler version\n"
        "  --evolution-status  Show native development gates and safety boundary\n"
        "  --tokens            Print lexical tokens\n"
        "  --ast-json          Parse one expression and print deterministic AST JSON\n"
        "  --emit-asm          Emit checked x86-64 System V ELF assembly for an i64 expression\n"
        "  -o PATH             Write generated assembly to PATH instead of stdout\n"
        "  --catalog           List the native token catalogue\n"
        "  --catalog-token     Inspect one token catalogue entry\n"
        "  --capabilities      List the native capability registry\n"
        "  --capability NAME   Inspect one native capability module\n",
        REAPER_VERSION
    );
}

static int emit_native_assembly(
    const ReaperTokenArray *tokens,
    const char *source_path,
    FILE *output
) {
    ReaperAst ast;
    ReaperParseError parse_error = {{0}, 0U, 0U};
    if (!reaper_parse_expression(tokens, &ast, &parse_error)) {
        fprintf(stderr, "%s:%zu:%zu: parser error: %s\n",
            source_path, parse_error.line, parse_error.column,
            parse_error.message);
        return 1;
    }

    if (ast.length > (REAPER_CODEGEN_X86_64_MAX_NODES - 1U) / 2U) {
        fprintf(stderr, "%s: expression is too large for the bounded native backend\n",
            source_path);
        reaper_ast_free(&ast);
        return 1;
    }

    size_t capacity = ast.length * 2U + 1U;
    ReaperIrNode *nodes = calloc(capacity, sizeof *nodes);
    if (nodes == NULL) {
        fprintf(stderr, "%s: cannot allocate native IR storage\n", source_path);
        reaper_ast_free(&ast);
        return 1;
    }

    size_t length = 0U;
    ReaperIrError ir_error;
    if (!reaper_lower_ast_to_ir(&ast, nodes, capacity, &length, &ir_error)) {
        fprintf(stderr, "%s: native lowering error at AST node %zu: %s\n",
            source_path, ir_error.node_index, ir_error.message);
        free(nodes);
        reaper_ast_free(&ast);
        return 1;
    }

    ReaperIrModule module = { nodes, length };
    ReaperCodegenError codegen_error;
    int success = reaper_codegen_x86_64_sysv_elf(&module, output, &codegen_error);
    if (!success) {
        fprintf(stderr, "%s: native codegen error at IR node %zu: %s\n",
            source_path, codegen_error.node_index, codegen_error.message);
    }

    free(nodes);
    reaper_ast_free(&ast);
    return success ? 0 : 1;
}

int main(int argc, char **argv) {
    int dump_tokens = 0;
    int dump_ast = 0;
    int dump_catalog = 0;
    int dump_capabilities = 0;
    int emit_assembly = 0;
    const char *catalog_lookup = NULL;
    const char *capability_lookup = NULL;
    const char *output_path = NULL;
    const char *source_path = NULL;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--version") == 0) {
            puts("Reaper " REAPER_VERSION " (C17 native core)");
            return 0;
        }
        if (strcmp(argv[i], "--evolution-status") == 0) {
            reaper_evolution_print_status();
            return 0;
        }
        if (strcmp(argv[i], "--tokens") == 0) {
            dump_tokens = 1;
            continue;
        }
        if (strcmp(argv[i], "--ast-json") == 0) {
            dump_ast = 1;
            continue;
        }
        if (strcmp(argv[i], "--emit-asm") == 0) {
            emit_assembly = 1;
            continue;
        }
        if (strcmp(argv[i], "-o") == 0) {
            if (i + 1 >= argc || output_path != NULL) {
                usage(stderr);
                return 2;
            }
            output_path = argv[++i];
            continue;
        }
        if (strcmp(argv[i], "--catalog") == 0) {
            dump_catalog = 1;
            continue;
        }
        if (strcmp(argv[i], "--capabilities") == 0) {
            dump_capabilities = 1;
            continue;
        }
        if (strcmp(argv[i], "--capability") == 0) {
            if (i + 1 >= argc) {
                usage(stderr);
                return 2;
            }
            capability_lookup = argv[++i];
            continue;
        }
        if (strcmp(argv[i], "--catalog-token") == 0) {
            if (i + 1 >= argc) {
                usage(stderr);
                return 2;
            }
            catalog_lookup = argv[++i];
            continue;
        }
        if (argv[i][0] == '-') {
            usage(stderr);
            return 2;
        }
        if (source_path != NULL) {
            usage(stderr);
            return 2;
        }
        source_path = argv[i];
    }

    if (dump_capabilities || capability_lookup != NULL) {
        if (source_path != NULL || dump_tokens || dump_ast || emit_assembly ||
            dump_catalog || catalog_lookup != NULL || output_path != NULL ||
            (dump_capabilities && capability_lookup != NULL)) {
            usage(stderr);
            return 2;
        }

        if (capability_lookup != NULL) {
            const ReaperCapabilityModule *module =
                reaper_capability_module_find(capability_lookup);
            if (module == NULL) {
                fprintf(stderr, "reaper-c: unknown capability module %s\n", capability_lookup);
                return 1;
            }

            printf("%s\t%s\t%s\t%zu operations\n",
                module->id, module->name, module->domain, module->function_count);
            for (size_t i = 0U; i < module->function_count; ++i) {
                const ReaperCapabilityFunction *function = &module->functions[i];
                if (function->min_arity == function->max_arity) {
                    printf("  %s\t%zu args\t%s\n",
                        function->name, function->min_arity, function->description);
                } else {
                    printf("  %s\t%zu..%zu args\t%s\n",
                        function->name, function->min_arity,
                        function->max_arity, function->description);
                }
            }
            return 0;
        }

        for (size_t i = 0U; i < reaper_capability_module_count(); ++i) {
            const ReaperCapabilityModule *module = reaper_capability_module_at(i);
            printf("%s\t%s\t%s\t%zu operations\n",
                module->id, module->name, module->domain, module->function_count);
        }
        return 0;
    }

    if (dump_catalog || catalog_lookup != NULL) {
        if (source_path != NULL || dump_tokens || dump_ast || emit_assembly ||
            output_path != NULL || (dump_catalog && catalog_lookup != NULL)) {
            usage(stderr);
            return 2;
        }
        if (!reaper_token_catalog_validate()) {
            fprintf(stderr, "reaper-c: token catalogue integrity failure\n");
            return 1;
        }

        if (catalog_lookup != NULL) {
            const ReaperCatalogEntry *entry = reaper_token_catalog_lookup(catalog_lookup);
            if (entry == NULL) {
                fprintf(stderr, "reaper-c: unknown catalogue token %s\n", catalog_lookup);
                return 1;
            }
            printf("%03zu\t%s\t%s\t%s\n",
                entry->ordinal, entry->lexeme, entry->group, entry->name);
            return 0;
        }

        for (size_t i = 0U; i < reaper_token_catalog_count(); ++i) {
            const ReaperCatalogEntry *entry = reaper_token_catalog_at(i);
            printf("%03zu\t%s\t%s\t%s\n",
                entry->ordinal, entry->lexeme, entry->group, entry->name);
        }
        return 0;
    }

    if (source_path == NULL ||
        (dump_tokens && dump_ast) ||
        (emit_assembly && (dump_tokens || dump_ast)) ||
        (output_path != NULL && !emit_assembly)) {
        usage(stderr);
        return 2;
    }

    char *source = read_file(source_path);
    if (source == NULL) {
        fprintf(stderr, "reaper-c: cannot read %s\n", source_path);
        return 2;
    }

    ReaperTokenArray tokens = {0};
    ReaperLexError lex_error = {{0}, 0U, 0U};
    if (!reaper_lex(source, &tokens, &lex_error)) {
        fprintf(stderr, "%s:%zu:%zu: lexer error: %s\n",
            source_path, lex_error.line, lex_error.column, lex_error.message);
        free(source);
        return 1;
    }

    int result = 0;
    if (dump_tokens) {
        for (size_t i = 0U; i < tokens.length; ++i) {
            printf("%zu:%zu %-12s %s\n",
                tokens.items[i].line, tokens.items[i].column,
                reaper_token_kind_name(tokens.items[i].kind),
                tokens.items[i].text);
        }
    } else if (dump_ast) {
        ReaperAst ast;
        ReaperParseError parse_error = {{0}, 0U, 0U};
        if (!reaper_parse_expression(&tokens, &ast, &parse_error)) {
            fprintf(stderr, "%s:%zu:%zu: parser error: %s\n",
                source_path, parse_error.line, parse_error.column,
                parse_error.message);
            result = 1;
        } else {
            if (!reaper_ast_write_json(&ast, stdout)) {
                fprintf(stderr, "reaper-c: cannot serialize AST\n");
                result = 1;
            }
            reaper_ast_free(&ast);
        }
    } else if (emit_assembly) {
        FILE *output = stdout;
        if (output_path != NULL) {
            output = fopen(output_path, "wb");
            if (output == NULL) {
                fprintf(stderr, "reaper-c: cannot write %s\n", output_path);
                reaper_tokens_free(&tokens);
                free(source);
                return 2;
            }
        }

        result = emit_native_assembly(&tokens, source_path, output);
        if (output_path != NULL && fclose(output) != 0 && result == 0) {
            fprintf(stderr, "reaper-c: failed to finish %s\n", output_path);
            result = 1;
        }
    } else {
        printf("Reaper native lexer: %s — %zu tokens; parser/runtime migration is in progress.\n",
            source_path, tokens.length - 1U);
    }

    reaper_tokens_free(&tokens);
    free(source);
    return result;
}
