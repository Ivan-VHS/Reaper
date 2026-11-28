#include "reaper/backend.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef REAPER_HOST_BACKEND_ARITHMETIC_FIXTURE_PATH
#error "REAPER_HOST_BACKEND_ARITHMETIC_FIXTURE_PATH must point to the compiled fixture"
#endif

int reaper_generated_entry(int64_t *result);

static char *read_fixture(size_t *length) {
    FILE *file = fopen(REAPER_HOST_BACKEND_ARITHMETIC_FIXTURE_PATH, "rb");
    long size;
    char *data;
    assert(file != NULL);
    assert(fseek(file, 0, SEEK_END) == 0);
    size = ftell(file);
    assert(size >= 0);
    assert(fseek(file, 0, SEEK_SET) == 0);
    data = (char *)malloc((size_t)size + 1u);
    assert(data != NULL);
    assert(fread(data, 1u, (size_t)size, file) == (size_t)size);
    data[size] = '\0';
    fclose(file);
    *length = (size_t)size;
    return data;
}

int main(void) {
    const char source[] = "7 - 2 * 3 + 8 / 2";
    ReaperSourceImportManifest manifest;
    ReaperTypedInstruction storage[32];
    ReaperCanonicalTypedModule module;
    ReaperImportError error;
    ReaperIrNode nodes[32];
    int64_t values[32] = {0}, interpreted = 0, compiled = 0;
    char generated[16384];
    size_t generated_bytes = 0u, fixture_bytes = 0u;
    char *golden;

    memset(&manifest, 0, sizeof(manifest));
    (void)snprintf(manifest.module_id, sizeof(manifest.module_id),
                   "%s", "qualification.arithmetic");
    manifest.generation = 19u;
    manifest.expected_generation = 19u;
    reaper_source_sha256(source, sizeof(source) - 1u,
                         manifest.expected_source_digest);

    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 32u, &module, &error) == REAPER_IMPORT_OK);
    for (size_t i = 0u; i < module.length; ++i)
        nodes[i] = module.nodes[i].instruction;
    {
        ReaperIrModule ir = {nodes, module.length};
        assert(reaper_ir_execute_i64(&ir, values, 32u, &interpreted, &error));
    }
    assert(interpreted == 5);
    assert(reaper_backend_host_c17_emit(&module, generated, sizeof(generated),
        &generated_bytes, &error) == REAPER_IMPORT_OK);
    golden = read_fixture(&fixture_bytes);
    assert(generated_bytes == fixture_bytes);
    assert(memcmp(generated, golden, generated_bytes) == 0);
    free(golden);
    assert(reaper_generated_entry(&compiled) == 1);
    assert(compiled == interpreted);
    puts("host C17 backend arithmetic fixture passed");
    return 0;
}
