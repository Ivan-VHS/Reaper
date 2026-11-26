#include "reaper/typed_registry.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static ReaperTypedEntry entries[12];
static size_t buckets[32];
static char strings[2048];
static ReaperTypedArgumentSpec schemas[64];
static ReaperTypedRegistry registry;
static size_t calls;

static ReaperTypedValue i64_value(int64_t number) {
    ReaperTypedValue value;
    memset(&value, 0, sizeof(value));
    value.kind = REAPER_TYPED_I64;
    value.as.i64 = number;
    return value;
}

static ReaperTypedArgumentSpec i64_range(int optional, int64_t minimum, int64_t maximum) {
    ReaperTypedArgumentSpec spec;
    memset(&spec, 0, sizeof(spec));
    spec.kind = REAPER_TYPED_I64;
    spec.flags = optional ? REAPER_TYPED_ARGUMENT_OPTIONAL : 0U;
    spec.constraints = REAPER_TYPED_CONSTRAINT_MINIMUM | REAPER_TYPED_CONSTRAINT_MAXIMUM;
    spec.minimum = i64_value(minimum);
    spec.maximum = i64_value(maximum);
    return spec;
}

static ReaperTypedStatus add_handler(void *context, const ReaperTypedValue *args,
                                     size_t count, ReaperTypedValue *result) {
    int64_t sum;
    (void)context;
    ++calls;
    if (count == 0U || result == NULL) return REAPER_TYPED_HANDLER_ERROR;
    sum = args[0].as.i64;
    if (count == 2U) sum += args[1].as.i64;
    result->kind = REAPER_TYPED_I64;
    result->as.i64 = sum;
    return REAPER_TYPED_OK;
}

static ReaperTypedStatus invalid_result_handler(void *context,
    const ReaperTypedValue *args, size_t count, ReaperTypedValue *result) {
    (void)context; (void)args; (void)count;
    ++calls;
    result->kind = REAPER_TYPED_I64;
    result->as.i64 = 99;
    return REAPER_TYPED_OK;
}

static ReaperTypedStatus denied_handler(void *context, const ReaperTypedValue *args,
    size_t count, ReaperTypedValue *result) {
    (void)context; (void)args; (void)count; (void)result;
    ++calls;
    return REAPER_TYPED_ACCESS_DENIED;
}

static ReaperTypedStatus void_handler(void *context, const ReaperTypedValue *args,
    size_t count, ReaperTypedValue *result) {
    (void)context; (void)args; (void)count; (void)result;
    ++calls;
    return REAPER_TYPED_OK;
}

static ReaperTypedOperationSpec base_operation(const char *domain, const char *name,
    const ReaperTypedArgumentSpec *args, size_t count) {
    ReaperTypedOperationSpec op;
    memset(&op, 0, sizeof(op));
    op.domain = domain;
    op.name = name;
    op.abi_major = 1U;
    op.abi_minor = 2U;
    op.required_capabilities = UINT64_C(4);
    op.arguments = args;
    op.argument_count = count;
    op.result.kind = REAPER_TYPED_I64;
    op.handler = add_handler;
    return op;
}

static void init_registry(void) {
    assert(reaper_typed_registry_init(&registry, entries, 12U, buckets, 32U,
        strings, sizeof(strings), schemas, 64U) == REAPER_TYPED_OK);
}

static void test_initialization(void) {
    ReaperTypedRegistry invalid;
    assert(reaper_typed_registry_init(&invalid, entries, 12U, buckets, 7U,
        strings, sizeof(strings), schemas, 64U) == REAPER_TYPED_INVALID_ARGUMENT);
    assert(reaper_typed_registry_init(&invalid, entries, 17U, buckets, 32U,
        strings, sizeof(strings), schemas, 64U) == REAPER_TYPED_INVALID_ARGUMENT);
    init_registry();
    assert(reaper_typed_registry_count(&registry) == 0U);
    assert(reaper_typed_registry_capacity(&registry) == 12U);
}

static void test_registration_copies_and_deduplicates(void) {
    ReaperTypedArgumentSpec args[2] = { i64_range(0, -100, 100), i64_range(1, 0, 100) };
    ReaperTypedOperationSpec op = base_operation("math", "add", args, 2U);
    char domain[] = "math";
    char name[] = "add";
    op.domain = domain; op.name = name;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    domain[0] = 'X'; name[0] = 'X'; memset(args, 0, sizeof(args));
    assert(reaper_typed_registry_find(&registry, "math", "add", 1U) != NULL);
    assert(reaper_typed_registry_find(&registry, "Xath", "Xdd", 1U) == NULL);
    op.domain = "math"; op.name = "add"; op.arguments = NULL; op.argument_count = 0U;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_DUPLICATE);
}

static void test_dispatch_and_security_order(void) {
    ReaperTypedValue args[2] = { i64_value(12), i64_value(30) }, out;
    const size_t before = calls;
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 2U, 4U,
        args, 2U, &out) == REAPER_TYPED_OK && out.as.i64 == 42);
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 3U, 4U,
        args, 2U, &out) == REAPER_TYPED_ABI_MISMATCH);
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 0U, 0U,
        args, 2U, &out) == REAPER_TYPED_ACCESS_DENIED);
    args[0].kind = REAPER_TYPED_U64;
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 0U, 4U,
        args, 2U, &out) == REAPER_TYPED_TYPE_MISMATCH);
    args[0] = i64_value(101);
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 0U, 4U,
        args, 2U, &out) == REAPER_TYPED_OUT_OF_RANGE);
    assert(calls == before + 1U);
}

static void test_optional_arity(void) {
    ReaperTypedValue arg = i64_value(9), out;
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 0U, 4U,
        &arg, 1U, &out) == REAPER_TYPED_OK && out.as.i64 == 9);
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 0U, 4U,
        NULL, 0U, &out) == REAPER_TYPED_ARITY_MISMATCH);
    assert(reaper_typed_registry_invoke(&registry, "math", "add", 1U, 0U, 4U,
        &arg, 1U, NULL) == REAPER_TYPED_INVALID_ARGUMENT);
}

static void test_utf8_and_bytes(void) {
    ReaperTypedArgumentSpec text_spec = {0}, bytes_spec = {0};
    ReaperTypedOperationSpec op;
    ReaperTypedValue value = {0};
    const char good[] = "Reaper \xe2\x9c\x93";
    const unsigned char bad[] = { 0xc0U, 0xafU }, payload[] = {0U, 1U, 2U, 255U};
    text_spec.kind = REAPER_TYPED_UTF8;
    text_spec.constraints = REAPER_TYPED_CONSTRAINT_MAX_LENGTH;
    text_spec.max_length = 16U;
    op = base_operation("text", "check", &text_spec, 1U);
    op.required_capabilities = 0U; op.result.kind = REAPER_TYPED_VOID; op.handler = void_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    value.kind = REAPER_TYPED_UTF8; value.as.text.data = good; value.as.text.length = sizeof(good)-1U;
    assert(reaper_typed_registry_invoke(&registry, "text", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_OK);
    value.as.text.data = (const char *)bad; value.as.text.length = sizeof(bad);
    assert(reaper_typed_registry_invoke(&registry, "text", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_TYPE_MISMATCH);
    bytes_spec.kind = REAPER_TYPED_BYTES;
    bytes_spec.constraints = REAPER_TYPED_CONSTRAINT_MAX_LENGTH; bytes_spec.max_length = 4U;
    op = base_operation("binary", "check", &bytes_spec, 1U);
    op.required_capabilities = 0U; op.result.kind = REAPER_TYPED_VOID; op.handler = void_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    memset(&value, 0, sizeof(value)); value.kind = REAPER_TYPED_BYTES;
    value.as.bytes.data = payload; value.as.bytes.length = sizeof(payload);
    assert(reaper_typed_registry_invoke(&registry, "binary", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_OK);
    value.as.bytes.length = 5U;
    assert(reaper_typed_registry_invoke(&registry, "binary", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_OUT_OF_RANGE);
}

static void test_handles_and_nullability(void) {
    ReaperTypedArgumentSpec spec = {0};
    ReaperTypedOperationSpec op;
    ReaperTypedValue value = {0};
    spec.kind = REAPER_TYPED_HANDLE; spec.constraints = REAPER_TYPED_CONSTRAINT_HANDLE_KIND;
    spec.expected_handle_kind = 7U;
    op = base_operation("handle", "check", &spec, 1U);
    op.required_capabilities = 0U; op.result.kind = REAPER_TYPED_VOID; op.handler = void_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    value.kind = REAPER_TYPED_HANDLE; value.as.handle.id = 11U; value.as.handle.kind = 7U;
    assert(reaper_typed_registry_invoke(&registry, "handle", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_OK);
    value.as.handle.kind = 8U;
    assert(reaper_typed_registry_invoke(&registry, "handle", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_TYPE_MISMATCH);
    memset(&spec, 0, sizeof(spec)); spec.kind = REAPER_TYPED_UTF8;
    spec.flags = REAPER_TYPED_ARGUMENT_NULLABLE;
    op = base_operation("nullable", "check", &spec, 1U);
    op.required_capabilities = 0U; op.result.kind = REAPER_TYPED_VOID; op.handler = void_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    memset(&value, 0, sizeof(value)); value.kind = REAPER_TYPED_UTF8;
    value.flags = REAPER_TYPED_VALUE_NULL;
    assert(reaper_typed_registry_invoke(&registry, "nullable", "check", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_OK);
}

static void test_invalid_schemas_are_transactional(void) {
    ReaperTypedArgumentSpec args[2] = { i64_range(1, 0, 10), i64_range(0, 0, 10) };
    ReaperTypedOperationSpec op = base_operation("bad", "optional", args, 2U);
    const size_t before = reaper_typed_registry_count(&registry);
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_INVALID_ARGUMENT);
    args[0] = i64_range(0, 20, 10); op.name = "range";
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_INVALID_ARGUMENT);
    args[0] = i64_range(0, 0, 10);
    args[0].constraints |= REAPER_TYPED_CONSTRAINT_MAX_LENGTH; op.name = "constraint";
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_INVALID_ARGUMENT);
    assert(reaper_typed_registry_count(&registry) == before);
}

static void test_return_validation_preserves_output(void) {
    ReaperTypedOperationSpec op = {0};
    ReaperTypedValue out = i64_value(555);
    op.domain = "output"; op.name = "bounded"; op.abi_major = 1U;
    op.result = i64_range(0, 0, 10); op.handler = invalid_result_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    assert(reaper_typed_registry_invoke(&registry, "output", "bounded", 1U, 0U, 0U,
        NULL, 0U, &out) == REAPER_TYPED_OUT_OF_RANGE);
    assert(out.as.i64 == 555);
}

static void test_handler_error_propagation(void) {
    ReaperTypedOperationSpec op = {0};
    op.domain = "handler"; op.name = "reject"; op.abi_major = 1U;
    op.result.kind = REAPER_TYPED_VOID; op.handler = denied_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    assert(reaper_typed_registry_invoke(&registry, "handler", "reject", 1U, 0U, 0U,
        NULL, 0U, NULL) == REAPER_TYPED_ACCESS_DENIED);
}

static void test_declarations_and_sealing(void) {
    ReaperTypedOperationSpec op = {0};
    ReaperTypedValue out;
    op.domain = "declaration"; op.name = "future"; op.abi_major = 1U;
    op.result.kind = REAPER_TYPED_I64;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    assert(reaper_typed_registry_invoke(&registry, "declaration", "future", 1U, 0U, 0U,
        NULL, 0U, &out) == REAPER_TYPED_UNIMPLEMENTED);
    assert(reaper_typed_registry_seal(&registry) == REAPER_TYPED_OK);
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_SEALED);
}

static void test_storage_exhaustion(void) {
    ReaperTypedEntry tiny_entries[1]; size_t tiny_buckets[2]; char tiny_strings[2];
    ReaperTypedRegistry tiny; ReaperTypedOperationSpec op = {0};
    op.domain = "store"; op.name = "op"; op.abi_major = 1U; op.result.kind = REAPER_TYPED_VOID;
    assert(reaper_typed_registry_init(&tiny, tiny_entries, 1U, tiny_buckets, 2U,
        tiny_strings, sizeof(tiny_strings), NULL, 0U) == REAPER_TYPED_OK);
    assert(reaper_typed_registry_register(&tiny, &op) == REAPER_TYPED_OUT_OF_RANGE);
    assert(reaper_typed_registry_count(&tiny) == 0U);
    assert(tiny_buckets[0] == 0U && tiny_buckets[1] == 0U);
}

static void test_versions_and_numeric_values(void) {
    ReaperTypedOperationSpec op = {0};
    ReaperTypedArgumentSpec spec = {0};
    ReaperTypedValue value = {0};
    op.domain = "version"; op.name = "op"; op.abi_major = 2U;
    op.result.kind = REAPER_TYPED_VOID; op.handler = void_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    assert(reaper_typed_registry_find(&registry, "version", "op", 1U) == NULL);
    assert(reaper_typed_registry_find(&registry, "version", "op", 2U) != NULL);
    spec.kind = REAPER_TYPED_F64;
    op = base_operation("number", "finite", &spec, 1U);
    op.required_capabilities = 0U; op.result.kind = REAPER_TYPED_VOID; op.handler = void_handler;
    assert(reaper_typed_registry_register(&registry, &op) == REAPER_TYPED_OK);
    value.kind = REAPER_TYPED_F64; value.as.f64 = 1.25;
    assert(reaper_typed_registry_invoke(&registry, "number", "finite", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_OK);
    value.as.f64 = NAN;
    assert(reaper_typed_registry_invoke(&registry, "number", "finite", 1U, 0U, 0U,
        &value, 1U, NULL) == REAPER_TYPED_TYPE_MISMATCH);
}

static void test_status_names(void) {
    assert(strcmp(reaper_typed_status_name(REAPER_TYPED_OK), "ok") == 0);
    assert(strcmp(reaper_typed_status_name(REAPER_TYPED_ACCESS_DENIED), "access_denied") == 0);
    assert(strcmp(reaper_typed_status_name((ReaperTypedStatus)-99), "unknown_status") == 0);
}

int main(void) {
    test_initialization();
    test_registration_copies_and_deduplicates();
    test_dispatch_and_security_order();
    test_optional_arity();
    test_utf8_and_bytes();
    test_handles_and_nullability();
    test_invalid_schemas_are_transactional();
    test_return_validation_preserves_output();
    test_handler_error_propagation();
    test_declarations_and_sealing();
    test_storage_exhaustion();
    test_versions_and_numeric_values();
    test_status_names();
    puts("native typed registry tests: 12 groups passed");
    return 0;
}
