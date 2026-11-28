#include "reaper/backend.h"

#include <inttypes.h>
#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#define REAPER_BACKEND_OP_BIT(opcode) (UINT32_C(1) << (unsigned)(opcode))
#define REAPER_BACKEND_EFFECT_MASK (REAPER_EFFECT_PURE | REAPER_EFFECT_CONTROL)

static const ReaperBackendManifest host_manifest = {
    REAPER_HOST_C17_BACKEND_ID,
    REAPER_HOST_C17_ABI_ID,
    REAPER_IMPORT_ABI_VERSION,
    REAPER_BACKEND_OP_BIT(REAPER_IR_OP_CONST_I64) |
    REAPER_BACKEND_OP_BIT(REAPER_IR_OP_ADD_I64) |
    REAPER_BACKEND_OP_BIT(REAPER_IR_OP_SUB_I64) |
    REAPER_BACKEND_OP_BIT(REAPER_IR_OP_MUL_I64) |
    REAPER_BACKEND_OP_BIT(REAPER_IR_OP_DIV_I64) |
    REAPER_BACKEND_OP_BIT(REAPER_IR_OP_RETURN),
    REAPER_BACKEND_EFFECT_MASK,
    1u
};

static ReaperImportStatus backend_fail(ReaperImportError *error,
                                       ReaperImportStatus status,
                                       size_t index, const char *message) {
    if (error != NULL) {
        error->status = status;
        error->instruction_index = index;
        (void)snprintf(error->message, sizeof(error->message), "%s", message);
    }
    return status;
}

static int append_text(char *output, size_t capacity, size_t *used,
                       const char *text) {
    size_t length = strlen(text);
    if (length >= capacity - *used) return 0;
    memcpy(output + *used, text, length);
    *used += length;
    output[*used] = '\0';
    return 1;
}

static int append_format(char *output, size_t capacity, size_t *used,
                         const char *format, ...) {
    va_list args;
    int written;
    if (*used >= capacity) return 0;
    va_start(args, format);
    written = vsnprintf(output + *used, capacity - *used, format, args);
    va_end(args);
    if (written < 0 || (size_t)written >= capacity - *used) return 0;
    *used += (size_t)written;
    return 1;
}

static int format_i64(int64_t value, char *output, size_t capacity) {
    if (value == INT64_MIN)
        return snprintf(output, capacity, "INT64_MIN") > 0;
    if (value < 0) {
        uint64_t magnitude = (uint64_t)(-(value + 1)) + UINT64_C(1);
        int written = snprintf(output, capacity, "(-INT64_C(%" PRIu64 "))", magnitude);
        return written > 0 && (size_t)written < capacity;
    }
    {
        int written = snprintf(output, capacity, "INT64_C(%" PRIu64 ")",
                               (uint64_t)value);
        return written > 0 && (size_t)written < capacity;
    }
}

static const char *helper_for_opcode(ReaperIrOpcode opcode) {
    switch (opcode) {
    case REAPER_IR_OP_ADD_I64: return "reaper_add_i64";
    case REAPER_IR_OP_SUB_I64: return "reaper_sub_i64";
    case REAPER_IR_OP_MUL_I64: return "reaper_mul_i64";
    case REAPER_IR_OP_DIV_I64: return "reaper_div_i64";
    default: return NULL;
    }
}

const ReaperBackendManifest *reaper_backend_host_c17_manifest(void) {
    return &host_manifest;
}

ReaperImportStatus reaper_backend_host_c17_emit(
    const ReaperCanonicalTypedModule *module,
    char *output, size_t output_capacity, size_t *output_bytes,
    ReaperImportError *error) {
    size_t used = 0u, return_count = 0u, return_index = 0u, i;
    ReaperImportStatus status;
    ReaperImportError verify_error;
    if (output_bytes != NULL) *output_bytes = 0u;
    if (output != NULL && output_capacity != 0u) output[0] = '\0';
    if (output == NULL || output_capacity == 0u || output_bytes == NULL ||
        module == NULL)
        return backend_fail(error, REAPER_IMPORT_INVALID_ARGUMENT, 0u,
                            "module and bounded output buffer are required");
    status = reaper_canonical_typed_module_verify(module, &verify_error);
    if (status != REAPER_IMPORT_OK)
        return backend_fail(error, status, verify_error.instruction_index,
                            verify_error.message);
    for (i = 0u; i < module->length; ++i) {
        if (module->nodes[i].instruction.opcode == REAPER_IR_OP_RETURN) {
            ++return_count;
            return_index = i;
        }
    }
    if (return_count != 1u || return_index != module->length - 1u)
        return backend_fail(error, REAPER_IMPORT_VERIFICATION_ERROR,
                            return_index, "host backend requires exactly one final RETURN");

    if (!append_text(output, output_capacity, &used,
        "#include <stdint.h>\n"
        "#include <limits.h>\n\n"
        "static int reaper_add_i64(int64_t a, int64_t b, int64_t *out) {\n"
        "    if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b)) return 0;\n"
        "    *out = a + b; return 1;\n"
        "}\n"
        "static int reaper_sub_i64(int64_t a, int64_t b, int64_t *out) {\n"
        "    if ((b < 0 && a > INT64_MAX + b) || (b > 0 && a < INT64_MIN + b)) return 0;\n"
        "    *out = a - b; return 1;\n"
        "}\n"
        "static int reaper_mul_i64(int64_t a, int64_t b, int64_t *out) {\n"
        "    if (a == 0 || b == 0) { *out = 0; return 1; }\n"
        "    if ((a == -1 && b == INT64_MIN) || (b == -1 && a == INT64_MIN)) return 0;\n"
        "    if (a > 0) {\n"
        "        if ((b > 0 && a > INT64_MAX / b) || (b < 0 && b < INT64_MIN / a)) return 0;\n"
        "    } else {\n"
        "        if ((b > 0 && a < INT64_MIN / b) || (b < 0 && a < INT64_MAX / b)) return 0;\n"
        "    }\n"
        "    *out = a * b; return 1;\n"
        "}\n"
        "static int reaper_div_i64(int64_t a, int64_t b, int64_t *out) {\n"
        "    if (b == 0 || (a == INT64_MIN && b == -1)) return 0;\n"
        "    *out = a / b; return 1;\n"
        "}\n\n"
        "int reaper_generated_entry(int64_t *result) {\n"
        "    if (result == 0) return 0;\n")) {
        return backend_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, 0u,
                            "host backend output buffer is too small");
    }
    for (i = 0u; i < module->length; ++i) {
        const ReaperIrNode *node = &module->nodes[i].instruction;
        if (node->opcode == REAPER_IR_OP_CONST_I64) {
            char literal[64];
            if (!format_i64(node->immediate, literal, sizeof(literal)) ||
                !append_format(output, output_capacity, &used,
                               "    int64_t v%zu = %s;\n", i, literal))
                return backend_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, i,
                                    "host backend output buffer is too small");
        } else if (node->opcode == REAPER_IR_OP_RETURN) {
            if (!append_format(output, output_capacity, &used,
                               "    *result = v%u;\n    return 1;\n",
                               node->lhs))
                return backend_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, i,
                                    "host backend output buffer is too small");
        } else {
            const char *helper = helper_for_opcode(node->opcode);
            if (helper == NULL)
                return backend_fail(error, REAPER_IMPORT_UNSUPPORTED, i,
                                    "host backend does not implement this IR opcode");
            if (!append_format(output, output_capacity, &used,
                               "    int64_t v%zu;\n"
                               "    if (!%s(v%u, v%u, &v%zu)) return 0;\n",
                               i, helper, node->lhs, node->rhs, i))
                return backend_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, i,
                                    "host backend output buffer is too small");
        }
    }
    if (!append_text(output, output_capacity, &used, "}\n"))
        return backend_fail(error, REAPER_IMPORT_CAPACITY_EXCEEDED, module->length,
                            "host backend output buffer is too small");
    *output_bytes = used;
    if (error != NULL) {
        error->status = REAPER_IMPORT_OK;
        error->message[0] = '\0';
    }
    return REAPER_IMPORT_OK;
}

void reaper_backend_qualification_evaluate(
    uint32_t evidence, ReaperBackendQualification *out) {
    const uint32_t required =
        REAPER_BACKEND_EVIDENCE_SOURCE_GOLDEN |
        REAPER_BACKEND_EVIDENCE_COMPILED_FIXTURE |
        REAPER_BACKEND_EVIDENCE_EXECUTED_FIXTURE |
        REAPER_BACKEND_EVIDENCE_IR_PARITY |
        REAPER_BACKEND_EVIDENCE_SPAN_VERIFIED;
    if (out == NULL) return;
    memset(out, 0, sizeof(*out));
    (void)snprintf(out->backend_id, sizeof(out->backend_id), "%s",
                   REAPER_HOST_C17_BACKEND_ID);
    (void)snprintf(out->abi_id, sizeof(out->abi_id), "%s",
                   REAPER_HOST_C17_ABI_ID);
    out->evidence = evidence & required;
    out->native_machine_code = 0u;
    out->abi_delegated_to_host_compiler = 1u;
    if ((out->evidence & REAPER_BACKEND_EVIDENCE_SOURCE_GOLDEN) != 0u &&
        (out->evidence & REAPER_BACKEND_EVIDENCE_SPAN_VERIFIED) != 0u)
        out->level = REAPER_BACKEND_QUALIFICATION_STRUCTURAL;
    if ((out->evidence & REAPER_BACKEND_EVIDENCE_IR_PARITY) != 0u)
        out->level = REAPER_BACKEND_QUALIFICATION_SEMANTIC;
    if ((out->evidence & REAPER_BACKEND_EVIDENCE_COMPILED_FIXTURE) != 0u &&
        (out->evidence & REAPER_BACKEND_EVIDENCE_EXECUTED_FIXTURE) != 0u)
        out->level = REAPER_BACKEND_QUALIFICATION_HOST_ABI;
    if ((out->evidence & required) == required) {
        out->level = REAPER_BACKEND_QUALIFICATION_QUALIFIED;
        (void)snprintf(out->message, sizeof(out->message),
            "Qualified C17 source backend; machine code and platform ABI are delegated to the host compiler.");
    } else {
        (void)snprintf(out->message, sizeof(out->message),
            "Qualification incomplete; missing evidence is not inferred.");
    }
}
