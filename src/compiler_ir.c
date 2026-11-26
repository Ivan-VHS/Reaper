#include "reaper/compiler_ir.h"

#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

static int fail(ReaperCompilerIrError *error, size_t index, const char *message) {
    if (error != NULL) {
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

static int valid_node(const ReaperCompilerIrNode *node, ReaperCompilerIrStage stage) {
    if (node == NULL || !valid_key(node->key)) return 0;
    if (node->span.source[0] != '\0' &&
        (!bounded_text(node->span.source, REAPER_COMPILER_IR_SOURCE_MAX, 0) ||
         node->span.line == 0u || node->span.column == 0u)) return 0;
    if (node->span.source[0] == '\0' &&
        (node->span.line != 0u || node->span.column != 0u)) return 0;
    if (node->type <= REAPER_COMPILER_IR_TYPE_INVALID ||
        node->type > REAPER_COMPILER_IR_TYPE_RATIO) return 0;

    if (is_text_type(node->type)) {
        if (!bounded_text(node->text, REAPER_COMPILER_IR_TEXT_MAX, 0)) return 0;
        if (node->type == REAPER_COMPILER_IR_TYPE_COLOR && !valid_color(node->text)) return 0;
    } else if (node->type == REAPER_COMPILER_IR_TYPE_F64 ||
               node->type == REAPER_COMPILER_IR_TYPE_LENGTH ||
               node->type == REAPER_COMPILER_IR_TYPE_RATIO) {
        if (!isfinite(node->number)) return 0;
        if (node->type == REAPER_COMPILER_IR_TYPE_RATIO &&
            (node->number < 0.0 || node->number > 16.0)) return 0;
    } else if (node->type == REAPER_COMPILER_IR_TYPE_BOOL) {
        if (node->integer != 0 && node->integer != 1) return 0;
    } else if (node->type == REAPER_COMPILER_IR_TYPE_DURATION) {
        if (node->integer < 0 || node->integer > 60000) return 0;
    }

    if (stage == REAPER_COMPILER_IR_HIR) {
        switch (node->opcode) {
        case REAPER_COMPILER_IR_HIR_COLOR_ROLE:
            return node->type == REAPER_COMPILER_IR_TYPE_COLOR;
        case REAPER_COMPILER_IR_HIR_FONT_ROLE:
            return node->type == REAPER_COMPILER_IR_TYPE_FONT ||
                   node->type == REAPER_COMPILER_IR_TYPE_TEXT;
        case REAPER_COMPILER_IR_HIR_METRIC_ROLE:
            return node->type == REAPER_COMPILER_IR_TYPE_I64 ||
                   node->type == REAPER_COMPILER_IR_TYPE_F64 ||
                   node->type == REAPER_COMPILER_IR_TYPE_LENGTH ||
                   node->type == REAPER_COMPILER_IR_TYPE_RATIO;
        case REAPER_COMPILER_IR_HIR_MOTION_ROLE:
            return node->type == REAPER_COMPILER_IR_TYPE_DURATION ||
                   node->type == REAPER_COMPILER_IR_TYPE_TEXT ||
                   node->type == REAPER_COMPILER_IR_TYPE_BOOL;
        case REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE:
            return node->type == REAPER_COMPILER_IR_TYPE_BOOL ||
                   node->type == REAPER_COMPILER_IR_TYPE_RATIO;
        default:
            return 0;
        }
    }
    if (stage == REAPER_COMPILER_IR_MIR)
        return node->opcode == REAPER_COMPILER_IR_MIR_SET_PROPERTY;
    if (stage == REAPER_COMPILER_IR_LIR)
        return node->opcode == REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY;
    return 0;
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
        if (!valid_node(&module->nodes[index], module->stage))
            return fail(error, index, "IR node has invalid opcode, key, type, value or source span");
    }
    return 1;
}

int reaper_compiler_ir_lower_hir_to_mir(const ReaperCompilerIrModule *hir,
                                        ReaperCompilerIrNode *output,
                                        size_t output_capacity,
                                        ReaperCompilerIrModule *mir,
                                        ReaperCompilerIrError *error) {
    size_t index;
    int reduced_motion = 0;
    if (mir != NULL) memset(mir, 0, sizeof *mir);
    if (!reaper_compiler_ir_verify(hir, REAPER_COMPILER_IR_HIR, error)) return 0;
    if (mir == NULL || (hir->length > 0u && output == NULL) ||
        output_capacity < hir->length)
        return fail(error, 0u, "MIR output storage is missing or too small");
    for (index = 0u; index < hir->length; ++index) {
        const ReaperCompilerIrNode *node = &hir->nodes[index];
        if (strcmp(node->key, "a11y.reduced_motion") == 0 &&
            node->type == REAPER_COMPILER_IR_TYPE_BOOL && node->integer == 1)
            reduced_motion = 1;
    }
    for (index = 0u; index < hir->length; ++index) {
        output[index] = hir->nodes[index];
        output[index].opcode = REAPER_COMPILER_IR_MIR_SET_PROPERTY;
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
        output[index].opcode = REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY;
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
        "typedef struct { const char *key; const char *type; const char *text; "
        "long long integer; double number; } ReaperGeneratedProperty;\n"
        "static const char reaper_generated_target[] = ")) return 0;
    if (!append_c_string(output, output_capacity, &length, error, lir->target)) return 0;
    if (!appendf(output, output_capacity, &length, error,
        ";\nstatic const ReaperGeneratedProperty reaper_generated_properties[] = {\n")) return 0;
    for (index = 0u; index < lir->length; ++index) {
        const ReaperCompilerIrNode *node = &lir->nodes[index];
        if (!appendf(output, output_capacity, &length, error, "    {")) return 0;
        if (!append_c_string(output, output_capacity, &length, error, node->key) ||
            !appendf(output, output_capacity, &length, error, ", ")) return 0;
        if (!append_c_string(output, output_capacity, &length, error,
                             reaper_compiler_ir_type_name(node->type)) ||
            !appendf(output, output_capacity, &length, error, ", ")) return 0;
        if (!append_c_string(output, output_capacity, &length, error,
                             is_text_type(node->type) ? node->text : "") ||
            !appendf(output, output_capacity, &length, error, ", %lld, %.17g},\n",
                     (long long)node->integer, node->number)) return 0;
    }
    if (!appendf(output, output_capacity, &length, error,
        "};\n"
        "const ReaperGeneratedProperty *reaper_generated_properties_get(size_t *count) {\n"
        "    if (count != NULL) *count = sizeof reaper_generated_properties / "
        "sizeof reaper_generated_properties[0];\n"
        "    return reaper_generated_properties;\n"
        "}\n"
        "const char *reaper_generated_target_get(void) { return reaper_generated_target; }\n"))
        return 0;
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
    case REAPER_COMPILER_IR_HIR_COLOR_ROLE: return "hir.color";
    case REAPER_COMPILER_IR_HIR_FONT_ROLE: return "hir.font";
    case REAPER_COMPILER_IR_HIR_METRIC_ROLE: return "hir.metric";
    case REAPER_COMPILER_IR_HIR_MOTION_ROLE: return "hir.motion";
    case REAPER_COMPILER_IR_HIR_ACCESSIBILITY_ROLE: return "hir.accessibility";
    case REAPER_COMPILER_IR_MIR_SET_PROPERTY: return "mir.set_property";
    case REAPER_COMPILER_IR_LIR_NATIVE_PROPERTY: return "lir.native_property";
    default: return "invalid";
    }
}
