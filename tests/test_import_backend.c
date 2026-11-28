#include "reaper/backend.h"
#include "reaper/ir.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef REAPER_HOST_BACKEND_FIXTURE_PATH
#error "REAPER_HOST_BACKEND_FIXTURE_PATH must point to the compiled golden fixture"
#endif

int reaper_generated_entry(int64_t *result);

static void hex_to_bytes(const char *hex, uint8_t *bytes, size_t count) {
    for (size_t i = 0u; i < count; ++i) {
        unsigned value = 0u;
        assert(sscanf(hex + i * 2u, "%2x", &value) == 1);
        bytes[i] = (uint8_t)value;
    }
}

static void test_sha256_known_vector(void) {
    static const char expected[] =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    uint8_t digest[REAPER_SOURCE_DIGEST_BYTES], expected_bytes[REAPER_SOURCE_DIGEST_BYTES];
    reaper_source_sha256("abc", 3u, digest);
    hex_to_bytes(expected, expected_bytes, sizeof(expected_bytes));
    assert(memcmp(digest, expected_bytes, sizeof(digest)) == 0);
}

static void make_manifest(const char *source, size_t length,
                          ReaperSourceImportManifest *manifest) {
    memset(manifest, 0, sizeof(*manifest));
    (void)snprintf(manifest->module_id, sizeof(manifest->module_id), "%s", "fixture.expression");
    manifest->generation = 7u;
    manifest->expected_generation = 7u;
    reaper_source_sha256(source, length, manifest->expected_source_digest);
}

static void test_import_digest_generation_types_and_spans(void) {
    const char source[] = "# 🦆\n19 + 23";
    const size_t source_bytes = sizeof(source) - 1u;
    const size_t expression_start = strlen("# 🦆\n");
    ReaperSourceImportManifest manifest;
    ReaperTypedInstruction storage[16];
    ReaperCanonicalTypedModule module;
    ReaperImportError error;
    make_manifest(source, source_bytes, &manifest);
    assert(reaper_import_expression(source, source_bytes, &manifest,
        storage, 16u, &module, &error) == REAPER_IMPORT_OK);
    assert(module.schema_version == REAPER_IMPORT_ABI_VERSION);
    assert(strcmp(module.module_id, "fixture.expression") == 0);
    assert(module.generation == 7u);
    assert(module.source_bytes == source_bytes);
    assert(module.length == 4u);
    assert(module.nodes[0].type == REAPER_TYPED_I64);
    assert(module.nodes[0].effects == REAPER_EFFECT_PURE);
    assert(module.nodes[0].ownership == REAPER_OWNERSHIP_NONE);
    assert(module.nodes[0].source_start_byte == expression_start);
    assert(module.nodes[0].source_end_byte == expression_start + 2u);
    assert(module.nodes[1].source_start_byte == expression_start + 5u);
    assert(module.nodes[1].source_end_byte == expression_start + 7u);
    assert(module.nodes[2].source_start_byte == expression_start);
    assert(module.nodes[2].source_end_byte == expression_start + 7u);
    assert(module.nodes[3].effects == REAPER_EFFECT_CONTROL);
    assert(module.nodes[3].source_start_byte == expression_start);
    assert(module.nodes[3].source_end_byte == expression_start + 7u);
    assert(reaper_canonical_typed_module_verify(&module, &error) == REAPER_IMPORT_OK);

    module.nodes[2].effects = REAPER_EFFECT_MMIO_WRITE;
    assert(reaper_canonical_typed_module_verify(&module, &error) ==
           REAPER_IMPORT_VERIFICATION_ERROR);
    module.nodes[2].effects = REAPER_EFFECT_PURE;
    assert(reaper_canonical_typed_module_verify(&module, &error) == REAPER_IMPORT_OK);
}

static void test_import_rejects_digest_generation_and_capacity(void) {
    const char source[] = "1 + 2";
    ReaperSourceImportManifest manifest;
    ReaperTypedInstruction storage[8];
    ReaperCanonicalTypedModule module;
    ReaperImportError error;
    make_manifest(source, sizeof(source) - 1u, &manifest);
    manifest.expected_generation = 8u;
    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 8u, &module, &error) == REAPER_IMPORT_STALE_GENERATION);
    make_manifest(source, sizeof(source) - 1u, &manifest);
    manifest.expected_source_digest[0] ^= 0xFFu;
    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 8u, &module, &error) == REAPER_IMPORT_DIGEST_MISMATCH);
    make_manifest(source, sizeof(source) - 1u, &manifest);
    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 2u, &module, &error) == REAPER_IMPORT_LOWERING_ERROR ||
        error.status == REAPER_IMPORT_LOWERING_ERROR);
}

static char *read_fixture(size_t *length) {
    FILE *file = fopen(REAPER_HOST_BACKEND_FIXTURE_PATH, "rb");
    char *buffer;
    long size;
    assert(file != NULL);
    assert(fseek(file, 0, SEEK_END) == 0);
    size = ftell(file);
    assert(size >= 0);
    assert(fseek(file, 0, SEEK_SET) == 0);
    buffer = (char *)malloc((size_t)size + 1u);
    assert(buffer != NULL);
    assert(fread(buffer, 1u, (size_t)size, file) == (size_t)size);
    buffer[size] = '\0';
    fclose(file);
    *length = (size_t)size;
    return buffer;
}

static void test_host_c17_backend_fixture_execution_and_qualification(void) {
    const char source[] = "19 + 23";
    ReaperSourceImportManifest manifest;
    ReaperTypedInstruction storage[16];
    ReaperCanonicalTypedModule module;
    ReaperImportError error;
    ReaperIrNode ir_nodes[16];
    int64_t values[16] = {0}, interpreted = -1, compiled = -1;
    char generated[8192];
    size_t generated_bytes = 0u, fixture_bytes = 0u;
    char *golden;
    const uint32_t complete_evidence =
        REAPER_BACKEND_EVIDENCE_SOURCE_GOLDEN |
        REAPER_BACKEND_EVIDENCE_COMPILED_FIXTURE |
        REAPER_BACKEND_EVIDENCE_EXECUTED_FIXTURE |
        REAPER_BACKEND_EVIDENCE_IR_PARITY |
        REAPER_BACKEND_EVIDENCE_SPAN_VERIFIED;
    ReaperBackendQualification qualification;

    make_manifest(source, sizeof(source) - 1u, &manifest);
    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 16u, &module, &error) == REAPER_IMPORT_OK);
    assert(reaper_backend_host_c17_emit(&module, generated, sizeof(generated),
        &generated_bytes, &error) == REAPER_IMPORT_OK);
    golden = read_fixture(&fixture_bytes);
    assert(generated_bytes == fixture_bytes);
    assert(strcmp(generated, golden) == 0);
    free(golden);

    for (size_t i = 0u; i < module.length; ++i)
        ir_nodes[i] = module.nodes[i].instruction;
    {
        ReaperIrModule ir = {ir_nodes, module.length};
        assert(reaper_ir_execute_i64(&ir, values, 16u, &interpreted, NULL));
    }
    assert(reaper_generated_entry(&compiled) == 1);
    assert(interpreted == 42);
    assert(compiled == interpreted);

    reaper_backend_qualification_evaluate(complete_evidence, &qualification);
    assert(qualification.level == REAPER_BACKEND_QUALIFICATION_QUALIFIED);
    assert(qualification.native_machine_code == 0u);
    assert(qualification.abi_delegated_to_host_compiler == 1u);
    assert(strcmp(qualification.backend_id, REAPER_HOST_C17_BACKEND_ID) == 0);
    assert(strstr(qualification.message, "delegated") != NULL);

    reaper_backend_qualification_evaluate(complete_evidence &
        ~REAPER_BACKEND_EVIDENCE_EXECUTED_FIXTURE, &qualification);
    assert(qualification.level != REAPER_BACKEND_QUALIFICATION_QUALIFIED);
}

static void test_overflow_semantics_are_not_silently_wrapped(void) {
    const char source[] = "9223372036854775807 + 1";
    ReaperSourceImportManifest manifest;
    ReaperTypedInstruction storage[16];
    ReaperCanonicalTypedModule module;
    ReaperImportError error;
    ReaperIrNode ir_nodes[16];
    int64_t values[16] = {0}, result = 123;
    char output[8192];
    size_t output_bytes = 0u;
    make_manifest(source, sizeof(source) - 1u, &manifest);
    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 16u, &module, &error) == REAPER_IMPORT_OK);
    for (size_t i = 0u; i < module.length; ++i)
        ir_nodes[i] = module.nodes[i].instruction;
    {
        ReaperIrModule ir = {ir_nodes, module.length};
        assert(!reaper_ir_execute_i64(&ir, values, 16u, &result, NULL));
        assert(result == 123);
    }
    assert(reaper_backend_host_c17_emit(&module, output, sizeof(output),
        &output_bytes, &error) == REAPER_IMPORT_OK);
    assert(strstr(output, "reaper_add_i64") != NULL);
    assert(strstr(output, "INT64_MAX - b") != NULL);
}

int main(void) {
    test_sha256_known_vector();
    test_import_digest_generation_types_and_spans();
    test_import_rejects_digest_generation_and_capacity();
    test_host_c17_backend_fixture_execution_and_qualification();
    test_overflow_semantics_are_not_silently_wrapped();
    puts("native importer and host backend tests passed");
    return 0;
}
