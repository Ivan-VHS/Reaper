#include "reaper/compiler_ir.h"

#include <float.h>
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int fail(ReaperCompilerIrError *error, size_t index, const char *message) {
    if (error != NULL) {
        memset(error, 0, sizeof *error);
        error->node_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int bounded_text(const char *value, size_t capacity, int allow_empty) {
    size_t index;
    if (value == NULL) return 0;
    for (index = 0u; index < capacity; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        if (ch == 0u) return allow_empty || index > 0u;
        if (ch < 0x20u || ch == 0x7fu) return 0;
    }
    return 0;
}

/* Text payloads may contain decoded newline/tab/return bytes. The C17
 * emitter encodes all non-ASCII and control bytes with fixed-width octal
 * escapes, so they are safe to carry in a bounded, NUL-terminated field. */
static int bounded_payload(const char *value, size_t capacity, int allow_empty) {
    size_t index;
    if (value == NULL) return 0;
    for (index = 0u; index < capacity; ++index) {
        if (value[index] == '\\0') return allow_empty || index > 0u;
    }
    return 0;
}

static int valid_key(const char *value) {
    size_t index;
    if (!bounded_text(value, REAPER_COMPILER_IR_KEY_MAX, 0)) return 0;
    for (index = 0u; value[index] != '\0'; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        if (!((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
              (ch >= '0' && ch <= '9') || ch == '_' || ch == '-' ||
              ch == '.' || ch == '/')) return 0;
    }
    return 1;
}

static int valid_operator(const char *value, int unary) {
    if (value == NULL) return 0;
    if (unary)
        return strcmp(value, "+") == 0 || strcmp(value, "-") == 0;
    return strcmp(value, "+") == 0 || strcmp(value, "-") == 0 ||
           strcmp(value, "*") == 0 || strcmp(value, "/") == 0;
}

static int valid_color(const char *value) {
    size_t index;
    if (value == NULL || strlen(value) != 7u || value[0] != '#') return 0;
    for (index = 1u; index < 7u; ++index) {
        const char ch = value[index];
        if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f') ||
              (ch >= 'A' && ch <= 'F'))) return 0;
    }
    return 1;
}

static int is_text_type(ReaperCompilerIrType type) {
    return type == REAPER_COMPILER_IR_TYPE_TEXT ||
           type == REAPER_COMPILER_IR_TYPE_COLOR ||
           type == REAPER_COMPILER_IR_TYPE_FONT;
}

static int is_numeric_type(ReaperCompilerIrType type) {
    return type == REAPER_COMPILER_IR_TYPE_I64 ||
           type == REAPER_COMPILER_IR_TYPE_F64;
}

static int native_binary64_supported(void) {
    return sizeof(double) == sizeof(uint64_t) &&
           DBL_MANT_DIG == 53 && DBL_MAX_EXP == 1024;
}

static int valid_value(const ReaperCompilerIrNode *node) {
    if (node->type <= REAPER_COMPILER_IR_TYPE_INVALID ||
        node->type > REAPER_COMPILER_IR_TYPE_RATIO) return 0;
    if (is_text_type(node->type)) {
        if (!bounded_payload(node->text, REAPER_COMPILER_IR_TEXT_MAX,
                node->type == REAPER_COMPILER_IR_TYPE_TEXT)) return 0;
        if (node->type == REAPER_COMPILER_IR_TYPE_COLOR && !valid_color(node->text)) return 0;
    } else if (node->type == REAPER_COMPILER_IR_TYPE_F64 ||
               node->type == REAPER_COMPILER_IR_TYPE_LENGTH ||
               node->type == REAPER_COMPILER_IR_TYPE_RATIO) {
        if (!native_binary64_supported() || !isfinite(node->number)) return 0;
        if (node->type == REAPER_COMPILER_IR_TYPE_RATIO &&
            (node->number < 0.0 || node->number > 16.0)) return 0;
    } else if (node->type == REAPER_COMPILER_IR_TYPE_BOOL) {
        if (node->integer != 0 && node->integer != 1) return 0;
    } else if (node->type == REAPER_COMPILER_IR_TYPE_DURATION) {
        if (node->integer < 0 || node->integer > 60000) return 0;
    }
    return 1;
}

static int earlier_ref(uint32_t ref, size_t index) {
    return ref != REAPER_COMPILER_IR_NO_VALUE && (size_t)ref < index;
}

static int valid_span(const ReaperCompilerSourceSpan *span) {
    if (span->source[0] == '\0')
        return span->line == 0u && span->column == 0u;
    return bounded_text(span->source, REAPER_COMPILER_IR_SOURCE_MAX, 0) &&
           span->line > 0u && span->column > 0u;
}

static int valid_node(const ReaperCompilerIrNode *node,
                      ReaperCompilerIrStage stage, size_t index,
                      const ReaperCompilerIrNode *nodes) {
    if (node == NULL || !valid_span(&node->span) ||
        !bounded_payload(node->key, sizeof node->key, 1) ||
        !bounded_payload(node->text, sizeof node->text, 1)) return 0;
    switch (stage) {
    case REAPER_COMPILER_IR_HIR:
        switch (node->opcode) {
        case REAPER_COMPILER_IR_HIR_VALUE:
            return node->key[0] == '\0' &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE && valid_value(node);
        case REAPER_COMPILER_IR_HIR_NAME:
            return valid_key(node->key) &&
                node->type > REAPER_COMPILER_IR_TYPE_INVALID &&
                node->type <= REAPER_COMPILER_IR_TYPE_RATIO &&
                (!is_text_type(node->type) ||
                 bounded_payload(node->text, REAPER_COMPILER_IR_TEXT_MAX, 1)) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_HIR_UNARY:
            return valid_operator(node->key, 1) &&
                earlier_ref(node->lhs, index) &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE &&
                is_numeric_type(nodes[node->lhs].type) &&
                node->type == nodes[node->lhs].type;
        case REAPER_COMPILER_IR_HIR_BINARY:
            return valid_operator(node->key, 0) &&
                earlier_ref(node->lhs, index) && earlier_ref(node->rhs, index) &&
                is_numeric_type(nodes[node->lhs].type) &&
                nodes[node->rhs].type == nodes[node->lhs].type &&
                node->type == nodes[node->lhs].type;
        case REAPER_COMPILER_IR_HIR_CALL:
            return valid_key(node->key) &&
                (node->lhs == REAPER_COMPILER_IR_NO_VALUE || earlier_ref(node->lhs, index)) &&
                (node->rhs == REAPER_COMPILER_IR_NO_VALUE || earlier_ref(node->rhs, index)) &&
                valid_value(node);
        case REAPER_COMPILER_IR_HIR_COLOR_ROLE:
            return valid_key(node->key) && node->type == REAPER_COMPILER_IR_TYPE_COLOR &&
                valid_color(node->text) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_HIR_FONT_ROLE:
            return valid_key(node->key) &&
                (node->type == REAPER_COMPILER_IR_TYPE_FONT ||
                 node->type == REAPER_COMPILER_IR_TYPE_TEXT) && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_HIR_METRIC_ROLE:
            return valid_key(node->key) &&
                (node->type == REAPER_COMPILER_IR_TYPE_I64 ||
                 node->type == REAPER_COMPILER_IR_TYPE_F64 ||
                 node->type == REAPER_COMPILER_IR_TYPE_LENGTH ||
                 node->type == REAPER_COMPILER_IR_TYPE_RATIO) && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_HIR_MOTION_ROLE:
            return valid_key(node->key) &&
                (node->type == REAPER_COMPILER_IR_TYPE_DURATION ||
                 node->type == REAPER_COMPILER_IR_TYPE_TEXT ||
                 node->type == REAPER_COMPILER_IR_TYPE_BOOL) && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE:
            return valid_key(node->key) &&
                (node->type == REAPER_COMPILER_IR_TYPE_BOOL ||
                 node->type == REAPER_COMPILER_IR_TYPE_RATIO) && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        default:
            return 0;
        }
    case REAPER_COMPILER_IR_MIR:
        switch (node->opcode) {
        case REAPER_COMPILER_IR_MIR_CONSTANT:
            return node->key[0] == '\0' && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_MIR_NAME:
            return valid_key(node->key) &&
                node->type > REAPER_COMPILER_IR_TYPE_INVALID &&
                node->type <= REAPER_COMPILER_IR_TYPE_RATIO &&
                (!is_text_type(node->type) ||
                 bounded_payload(node->text, REAPER_COMPILER_IR_TEXT_MAX, 1)) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_MIR_UNARY:
            return valid_operator(node->key, 1) && earlier_ref(node->lhs, index) &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE &&
                is_numeric_type(nodes[node->lhs].type) &&
                node->type == nodes[node->lhs].type;
        case REAPER_COMPILER_IR_MIR_ARITHMETIC:
            return valid_operator(node->key, 0) &&
                earlier_ref(node->lhs, index) && earlier_ref(node->rhs, index) &&
                is_numeric_type(nodes[node->lhs].type) &&
                nodes[node->rhs].type == nodes[node->lhs].type &&
                node->type == nodes[node->lhs].type;
        case REAPER_COMPILER_IR_MIR_CALL:
            return valid_key(node->key) && valid_value(node) &&
                (node->lhs == REAPER_COMPILER_IR_NO_VALUE || earlier_ref(node->lhs, index)) &&
                (node->rhs == REAPER_COMPILER_IR_NO_VALUE || earlier_ref(node->rhs, index));
        case REAPER_COMPILER_IR_MIR_SET_PROPERTY:
            return valid_key(node->key) && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        default:
            return 0;
        }
    case REAPER_COMPILER_IR_LIR:
        switch (node->opcode) {
        case REAPER_COMPILER_IR_LIR_NATIVE_CONSTANT:
            return node->key[0] == '\0' && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_LIR_NATIVE_NAME:
            return valid_key(node->key) &&
                node->type > REAPER_COMPILER_IR_TYPE_INVALID &&
                node->type <= REAPER_COMPILER_IR_TYPE_RATIO &&
                (!is_text_type(node->type) ||
                 bounded_payload(node->text, REAPER_COMPILER_IR_TEXT_MAX, 1)) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        case REAPER_COMPILER_IR_LIR_NATIVE_UNARY:
            return valid_operator(node->key, 1) && earlier_ref(node->lhs, index) &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE &&
                is_numeric_type(nodes[node->lhs].type) &&
                node->type == nodes[node->lhs].type;
        case REAPER_COMPILER_IR_LIR_NATIVE_ARITHMETIC:
            return valid_operator(node->key, 0) &&
                earlier_ref(node->lhs, index) && earlier_ref(node->rhs, index) &&
                is_numeric_type(nodes[node->lhs].type) &&
                nodes[node->rhs].type == nodes[node->lhs].type &&
                node->type == nodes[node->lhs].type;
        case REAPER_COMPILER_IR_LIR_NATIVE_CALL:
            return valid_key(node->key) && valid_value(node) &&
                (node->lhs == REAPER_COMPILER_IR_NO_VALUE || earlier_ref(node->lhs, index)) &&
                (node->rhs == REAPER_COMPILER_IR_NO_VALUE || earlier_ref(node->rhs, index));
        case REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY:
            return valid_key(node->key) && valid_value(node) &&
                node->lhs == REAPER_COMPILER_IR_NO_VALUE &&
                node->rhs == REAPER_COMPILER_IR_NO_VALUE;
        default:
            return 0;
        }
    default:
        return 0;
    }
}

int reaper_compiler_ir_verify(const ReaperCompilerIrModule *module,
                              ReaperCompilerIrStage expected_stage,
                              ReaperCompilerIrError *error) {
    size_t index;
    if (error != NULL) { error->node_index = 0u; error->message[0] = '\0'; }
    if (module == NULL || module->version != REAPER_COMPILER_IR_VERSION ||
        module->stage != expected_stage ||
        module->length > REAPER_COMPILER_IR_MAX_NODES ||
        (module->length > 0u && module->nodes == NULL))
        return fail(error, 0u, "invalid compiler IR module header or storage");
    if ((module->flags & ~REAPER_COMPILER_IR_FLAG_REDUCED_MOTION) != 0u)
        return fail(error, 0u, "unknown compiler IR module flags");
    if (module->stage == REAPER_COMPILER_IR_LIR &&
        !bounded_text(module->target, sizeof module->target, 0))
        return fail(error, 0u, "LIR target must be non-empty bounded text");
    for (index = 0u; index < module->length; ++index) {
        if (!valid_node(&module->nodes[index], module->stage, index, module->nodes)) {
            (void)fail(error, index, "IR node has invalid opcode, key, type, value, operand or source span");
            if (error != NULL) {
                error->span = module->nodes[index].span;
            }
            return 0;
        }
    }
    return 1;
}

int reaper_compiler_ir_lower_hir_to_mir(const ReaperCompilerIrModule *hir,
                                        ReaperCompilerIrNode *output,
                                        size_t output_capacity,
                                        ReaperCompilerIrModule *mir,
                                        ReaperCompilerIrError *error) {
    size_t index;
    int reduced_motion = (hir != NULL &&
        (hir->flags & REAPER_COMPILER_IR_FLAG_REDUCED_MOTION) != 0u);
    if (mir != NULL) memset(mir, 0, sizeof *mir);
    if (!reaper_compiler_ir_verify(hir, REAPER_COMPILER_IR_HIR, error)) return 0;
    if (mir == NULL || (hir->length > 0u && output == NULL) ||
        output_capacity < hir->length)
        return fail(error, 0u, "MIR output storage is missing or too small");
    for (index = 0u; index < hir->length; ++index) {
        if (strcmp(hir->nodes[index].key, "a11y.reduced_motion") == 0 &&
            hir->nodes[index].type == REAPER_COMPILER_IR_TYPE_BOOL &&
            hir->nodes[index].integer == 1) reduced_motion = 1;
    }
    for (index = 0u; index < hir->length; ++index) {
        output[index] = hir->nodes[index];
        switch (hir->nodes[index].opcode) {
        case REAPER_COMPILER_IR_HIR_VALUE:
            output[index].opcode = REAPER_COMPILER_IR_MIR_CONSTANT;
            break;
        case REAPER_COMPILER_IR_HIR_NAME:
            output[index].opcode = REAPER_COMPILER_IR_MIR_NAME;
            break;
        case REAPER_COMPILER_IR_HIR_UNARY:
            output[index].opcode = REAPER_COMPILER_IR_MIR_UNARY;
            break;
        case REAPER_COMPILER_IR_HIR_BINARY:
            output[index].opcode = REAPER_COMPILER_IR_MIR_ARITHMETIC;
            break;
        case REAPER_COMPILER_IR_HIR_CALL:
            output[index].opcode = REAPER_COMPILER_IR_MIR_CALL;
            break;
        default:
            output[index].opcode = REAPER_COMPILER_IR_MIR_SET_PROPERTY;
            break;
        }
        if (reduced_motion && output[index].type == REAPER_COMPILER_IR_TYPE_DURATION)
            output[index].integer = 0;
        if (reduced_motion && strcmp(output[index].key, "motion.easing") == 0 &&
            is_text_type(output[index].type))
            (void)snprintf(output[index].text, sizeof output[index].text, "%s", "linear");
    }
    mir->version = REAPER_COMPILER_IR_VERSION;
    mir->stage = REAPER_COMPILER_IR_MIR;
    mir->flags = hir->flags | (reduced_motion ? REAPER_COMPILER_IR_FLAG_REDUCED_MOTION : 0u);
    mir->nodes = output;
    mir->length = hir->length;
    return reaper_compiler_ir_verify(mir, REAPER_COMPILER_IR_MIR, error);
}

int reaper_compiler_ir_lower_mir_to_lir(const ReaperCompilerIrModule *mir,
                                        const char *target,
                                        ReaperCompilerIrNode *output,
                                        size_t output_capacity,
                                        ReaperCompilerIrModule *lir,
                                        ReaperCompilerIrError *error) {
    size_t index;
    if (lir != NULL) memset(lir, 0, sizeof *lir);
    if (!reaper_compiler_ir_verify(mir, REAPER_COMPILER_IR_MIR, error)) return 0;
    if (lir == NULL || target == NULL ||
        !bounded_text(target, REAPER_COMPILER_IR_KEY_MAX, 0) ||
        (mir->length > 0u && output == NULL) || output_capacity < mir->length)
        return fail(error, 0u, "LIR target or output storage is invalid");
    for (index = 0u; index < mir->length; ++index) {
        output[index] = mir->nodes[index];
        switch (mir->nodes[index].opcode) {
        case REAPER_COMPILER_IR_MIR_CONSTANT:
            output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_CONSTANT;
            break;
        case REAPER_COMPILER_IR_MIR_NAME:
            output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_NAME;
            break;
        case REAPER_COMPILER_IR_MIR_UNARY:
            output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_UNARY;
            break;
        case REAPER_COMPILER_IR_MIR_ARITHMETIC:
            output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_ARITHMETIC;
            break;
        case REAPER_COMPILER_IR_MIR_CALL:
            output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_CALL;
            break;
        default:
            output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY;
            break;
        }
    }
    lir->version = REAPER_COMPILER_IR_VERSION;
    lir->stage = REAPER_COMPILER_IR_LIR;
    lir->flags = mir->flags;
    (void)snprintf(lir->target, sizeof lir->target, "%s", target);
    lir->nodes = output;
    lir->length = mir->length;
    return reaper_compiler_ir_verify(lir, REAPER_COMPILER_IR_LIR, error);
}

static int appendf(char *output, size_t capacity, size_t *length,
                   ReaperCompilerIrError *error, const char *format, ...) {
    int written;
    va_list args;
    if (*length >= capacity) return fail(error, 0u, "generated C17 output capacity exceeded");
    va_start(args, format);
    written = vsnprintf(output + *length, capacity - *length, format, args);
    va_end(args);
    if (written < 0 || (size_t)written >= capacity - *length)
        return fail(error, 0u, "generated C17 output capacity exceeded");
    *length += (size_t)written;
    return 1;
}

static int append_c_string(char *output, size_t capacity, size_t *length,
                           ReaperCompilerIrError *error, const char *value) {
    size_t index;
    if (!appendf(output, capacity, length, error, "\"")) return 0;
    for (index = 0u; value[index] != '\0'; ++index) {
        const unsigned char ch = (unsigned char)value[index];
        if (ch == '"' || ch == '\\') {
            if (!appendf(output, capacity, length, error, "\\%c", (char)ch)) return 0;
        } else if (ch < 0x20u || ch >= 0x7fu) {
            if (!appendf(output, capacity, length, error, "\\%03o", (unsigned int)ch)) return 0;
        } else if (!appendf(output, capacity, length, error, "%c", (char)ch)) return 0;
    }
    return appendf(output, capacity, length, error, "\"") ? 1 : 0;
}

int reaper_compiler_ir_emit_c17(const ReaperCompilerIrModule *lir,
                                char *output, size_t output_capacity,
                                size_t *output_length, ReaperCompilerIrError *error) {
    size_t index, length = 0u;
    if (output_length != NULL) *output_length = 0u;
    if (output == NULL || output_capacity == 0u || output_length == NULL)
        return fail(error, 0u, "C17 output buffer and output length are required");
    if (!reaper_compiler_ir_verify(lir, REAPER_COMPILER_IR_LIR, error)) return 0;
    output[0] = '\0';
    if (!appendf(output, output_capacity, &length, error,
        "/* Generated by Reaper's typed compiler IR. */\n"
        "#include <stddef.h>\n"
        "#include <stdint.h>\n"
        "typedef struct { const char *opcode; const char *key; const char *type; "
        "const char *text; unsigned lhs; unsigned rhs; long long integer; "
        "uint64_t number_bits; } ReaperGeneratedInstruction;\n"
        "static const char reaper_generated_target[] = ")) return 0;
    if (!append_c_string(output, output_capacity, &length, error, lir->target)) return 0;
    if (!appendf(output, output_capacity, &length, error,
        ";\nstatic const ReaperGeneratedInstruction reaper_generated_instructions[%zu] = {\n",
        lir->length > 0u ? lir->length : 1u)) return 0;
    if (lir->length == 0u &&
        !appendf(output, output_capacity, &length, error,
            "    { \"invalid\", \"\", \"invalid\", \"\", %u, %u, 0, UINT64_C(0) },\n",
            REAPER_COMPILER_IR_NO_VALUE, REAPER_COMPILER_IR_NO_VALUE)) return 0;
    for (index = 0u; index < lir->length; ++index) {
        const ReaperCompilerIrNode *node = &lir->nodes[index];
        uint64_t number_bits = UINT64_C(0);
        if (sizeof node->number == sizeof number_bits)
            memcpy(&number_bits, &node->number, sizeof number_bits);
        if (!appendf(output, output_capacity, &length, error, "    {")) return 0;
        if (!append_c_string(output, output_capacity, &length, error,
                             reaper_compiler_ir_opcode_name(node->opcode)) ||
            !appendf(output, output_capacity, &length, error, ", ")) return 0;
        if (!append_c_string(output, output_capacity, &length, error, node->key) ||
            !appendf(output, output_capacity, &length, error, ", ")) return 0;
        if (!append_c_string(output, output_capacity, &length, error,
                             reaper_compiler_ir_type_name(node->type)) ||
            !appendf(output, output_capacity, &length, error, ", ")) return 0;
        if (!append_c_string(output, output_capacity, &length, error,
                              is_text_type(node->type) ? node->text : "") ||
            !appendf(output, output_capacity, &length, error,
                      ", %u, %u, %lld, UINT64_C(0x%016llx) },\\n",
                      node->lhs, node->rhs, (long long)node->integer,
                      (unsigned long long)number_bits)) return 0;    }
    if (!appendf(output, output_capacity, &length, error,
        "};\n"
        "const ReaperGeneratedInstruction *reaper_generated_instructions_get(size_t *count) {\n"
        "    if (count != NULL) *count = %zu;\n"
        "    return reaper_generated_instructions;\n"
        "}\n"
        "const char *reaper_generated_target_get(void) { return reaper_generated_target; }\n",
        lir->length)) return 0;
    *output_length = length;
    return 1;
}

const char *reaper_compiler_ir_stage_name(ReaperCompilerIrStage stage) {
    switch (stage) {
    case REAPER_COMPILER_IR_HIR: return "HIR";
    case REAPER_COMPILER_IR_MIR: return "MIR";
    case REAPER_COMPILER_IR_LIR: return "LIR";
    default: return "invalid";
    }
}

const char *reaper_compiler_ir_type_name(ReaperCompilerIrType type) {
    switch (type) {
    case REAPER_COMPILER_IR_TYPE_I64: return "i64";
    case REAPER_COMPILER_IR_TYPE_F64: return "f64";
    case REAPER_COMPILER_IR_TYPE_BOOL: return "bool";
    case REAPER_COMPILER_IR_TYPE_TEXT: return "text";
    case REAPER_COMPILER_IR_TYPE_COLOR: return "color";
    case REAPER_COMPILER_IR_TYPE_LENGTH: return "length";
    case REAPER_COMPILER_IR_TYPE_DURATION: return "duration";
    case REAPER_COMPILER_IR_TYPE_FONT: return "font";
    case REAPER_COMPILER_IR_TYPE_RATIO: return "ratio";
    default: return "invalid";
    }
}

const char *reaper_compiler_ir_opcode_name(ReaperCompilerIrOpcode opcode) {
    switch (opcode) {
    case REAPER_COMPILER_IR_HIR_VALUE: return "hir.value";
    case REAPER_COMPILER_IR_HIR_NAME: return "hir.name";
    case REAPER_COMPILER_IR_HIR_UNARY: return "hir.unary";
    case REAPER_COMPILER_IR_HIR_BINARY: return "hir.binary";
    case REAPER_COMPILER_IR_HIR_CALL: return "hir.call";
    case REAPER_COMPILER_IR_HIR_COLOR_ROLE: return "hir.color";
    case REAPER_COMPILER_IR_HIR_FONT_ROLE: return "hir.font";
    case REAPER_COMPILER_IR_HIR_METRIC_ROLE: return "hir.metric";
    case REAPER_COMPILER_IR_HIR_MOTION_ROLE: return "hir.motion";
    case REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE: return "hir.accessibility";
    case REAPER_COMPILER_IR_MIR_CONSTANT: return "mir.constant";
    case REAPER_COMPILER_IR_MIR_NAME: return "mir.name";
    case REAPER_COMPILER_IR_MIR_UNARY: return "mir.unary";
    case REAPER_COMPILER_IR_MIR_ARITHMETIC: return "mir.arithmetic";
    case REAPER_COMPILER_IR_MIR_CALL: return "mir.call";
    case REAPER_COMPILER_IR_MIR_SET_PROPERTY: return "mir.set_property";
    case REAPER_COMPILER_IR_LIR_NATIVE_CONSTANT: return "lir.native_constant";
    case REAPER_COMPILER_IR_LIR_NATIVE_NAME: return "lir.native_name";
    case REAPER_COMPILER_IR_LIR_NATIVE_UNARY: return "lir.native_unary";
    case REAPER_COMPILER_IR_LIR_NATIVE_ARITHMETIC: return "lir.native_arithmetic";
    case REAPER_COMPILER_IR_LIR_NATIVE_CALL: return "lir.native_call";
    case REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY: return "lir.native_property";
    default: return "invalid";
    }
}
