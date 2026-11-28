#define _GNU_SOURCE
#include "reaper/pytyliki_bridge.h"
#include "reaper/import.h"
#include "reaper/backend.h"
#include "reaper/ir.h"
#include "interop.h"

#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sched.h>

#ifndef REAPER_PYTYLIKI_BRIDGE_FIXTURE_PATH
#error "REAPER_PYTYLIKI_BRIDGE_FIXTURE_PATH must point to the compiled golden fixture"
#endif

int reaper_generated_entry(int64_t *result);

static uint32_t incompatible_abi(void) {
    return PYTYLIKI_ABI_VERSION + 1u;
}

static char *read_fixture(size_t *length) {
    FILE *file = fopen(REAPER_PYTYLIKI_BRIDGE_FIXTURE_PATH, "rb");
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
    ReaperPytylikiProvider provider = {
        .abi_version = pytyliki_abi_version,
        .snapshot_descriptor = pytyliki_v1_native_snapshot_descriptor,
        .snapshot_collect = pytyliki_v1_native_snapshot_collect,
        .placement = pytyliki_v1_native_placement,
        .range_validate = pytyliki_v1_native_range_validate,
        .register_validate = pytyliki_v1_native_register_validate,
        .dma_transition = pytyliki_v1_native_dma_transition,
        .dma_cpu_access_validate = pytyliki_v1_native_dma_cpu_access_validate
    };
    ReaperPytylikiProvider incompatible = provider;
    const char source[] = "19 + 23";
    ReaperSourceImportManifest manifest;
    ReaperTypedInstruction storage[16];
    ReaperCanonicalTypedModule module;
    ReaperImportError import_error;
    pl_ni_snapshot snapshot;
    pl_ppf_request request;
    pl_ppf_report report;
    pl_native_range output_range;
    pl_dma_resource dma;
    ReaperIrNode ir_nodes[16];
    int64_t values[16] = {0};
    int64_t interpreted = -1, compiled = -1;
    char generated[8192];
    size_t generated_bytes = 0u, fixture_bytes = 0u;
    char *golden;

    memset(&manifest, 0, sizeof(manifest));
    (void)snprintf(manifest.module_id, sizeof(manifest.module_id),
                   "%s", "integration.expression");
    manifest.generation = 42u;
    manifest.expected_generation = 42u;
    reaper_source_sha256(source, sizeof(source) - 1u,
                         manifest.expected_source_digest);

    /* 1. Reaper source -> SHA/generation checked Canonical Typed IR. */
    assert(reaper_import_expression(source, sizeof(source) - 1u, &manifest,
        storage, 16u, &module, &import_error) == REAPER_IMPORT_OK);
    assert(reaper_canonical_typed_module_verify(&module, &import_error) ==
        REAPER_IMPORT_OK);
    for (size_t i = 0u; i < module.length; ++i)
        ir_nodes[i] = module.nodes[i].instruction;
    {
        ReaperIrModule ir = {ir_nodes, module.length};
        assert(reaper_ir_execute_i64(&ir, values, 16u,
                                     &interpreted, NULL));
    }
    assert(interpreted == 42);

    /* 2. Pytyliki validates the output memory resource before execution. */
    memset(&output_range, 0, sizeof(output_range));
    output_range.base = (uint64_t)(uintptr_t)&compiled;
    output_range.length = (uint64_t)sizeof(compiled);
    output_range.address_bits = (uint32_t)(sizeof(uintptr_t) * CHAR_BIT);
    output_range.alignment = (uint32_t)_Alignof(int64_t);
    assert(reaper_pytyliki_validate_range(&provider, &output_range) ==
           REAPER_PYTYLIKI_OK);
    output_range.base = UINT64_MAX - 3u;
    assert(reaper_pytyliki_validate_range(&provider, &output_range) ==
           REAPER_PYTYLIKI_INVALID_SNAPSHOT);

    /* Exercise the generation-checked DMA ownership state machine through the ABI.
       This models a resource lifecycle; it does not program a physical device. */
    dma.resource_id = 7u;
    dma.generation = 1u;
    dma.base = (uint64_t)(uintptr_t)&compiled;
    dma.length = (uint64_t)sizeof(compiled);
    dma.state = PL_DMA_CPU_OWNED;
    dma.direction = 2u;
    assert(provider.dma_cpu_access_validate(&dma, 1u) == PYTYLIKI_ABI_OK);
    assert(provider.dma_transition(&dma, 1u, PL_DMA_DEVICE_OWNED) == PYTYLIKI_ABI_OK);
    assert(provider.dma_cpu_access_validate(&dma, 2u) == PYTYLIKI_ABI_ACCESS_DENIED);
    assert(provider.dma_transition(&dma, 2u, PL_DMA_COMPLETED) == PYTYLIKI_ABI_OK);
    assert(provider.dma_cpu_access_validate(&dma, 3u) == PYTYLIKI_ABI_ACCESS_DENIED);
    assert(provider.dma_transition(&dma, 3u, PL_DMA_CPU_OWNED) == PYTYLIKI_ABI_OK);
    assert(provider.dma_cpu_access_validate(&dma, 4u) == PYTYLIKI_ABI_OK);

    /* 3. Canonical Typed IR -> deterministic checked C17 host backend. */
    assert(reaper_backend_host_c17_emit(&module, generated, sizeof(generated),
        &generated_bytes, &import_error) == REAPER_IMPORT_OK);
    golden = read_fixture(&fixture_bytes);
    assert(generated_bytes == fixture_bytes);
    assert(memcmp(generated, golden, generated_bytes) == 0);
    free(golden);

    /* 4. Collect the real host, get a PPF proposal and verify its generation. */
    memset(&request, 0, sizeof(request));
    request.preferred_numa_node = UINT16_MAX;
    request.current_cpu_index = UINT16_MAX;
    request.require_online = 1u;
    request.require_allowed = 1u;
    request.require_known_allowed = 1u;
    for (size_t i = 0u; i < 5u; ++i) request.weights[i] = 1u;
    assert(reaper_pytyliki_plan_placement(
        &provider, &request, NULL, 0u, &snapshot, &report
    ) == REAPER_PYTYLIKI_OK);
    assert(report.candidate_count == snapshot.cpu_count);
    assert(report.has_selection == 1u);
    assert(report.selected_cpu_index < snapshot.cpu_count);
    assert(report.topology_generation == snapshot.provenance.generation);
    assert(report.candidates[report.selected_cpu_index].accepted == 1u);

    /* 5. Explicit test/runtime adapter applies the proposal only for this thread,
       executes the compiled C17 fixture, and restores the original affinity. */
#if defined(__linux__)
    {
        cpu_set_t original_set, selected_set;
        const pl_ni_cpu *selected = &snapshot.cpus[report.selected_cpu_index];
        int execution_ok;
        assert(selected->group_id == 0u);
        assert(selected->os_cpu_id < CPU_SETSIZE);
        assert(sched_getaffinity(0, sizeof(original_set), &original_set) == 0);
        CPU_ZERO(&selected_set);
        CPU_SET(selected->os_cpu_id, &selected_set);
        assert(sched_setaffinity(0, sizeof(selected_set), &selected_set) == 0);
        execution_ok = reaper_generated_entry(&compiled);
        assert(sched_setaffinity(0, sizeof(original_set), &original_set) == 0);
        assert(execution_ok == 1);
    }
#else
    assert(reaper_generated_entry(&compiled) == 1);
#endif
    assert(compiled == interpreted);

    incompatible.abi_version = incompatible_abi;
    assert(reaper_pytyliki_snapshot_read(&incompatible, &snapshot) ==
           REAPER_PYTYLIKI_ABI_MISMATCH);
    assert(reaper_pytyliki_snapshot_read(NULL, &snapshot) ==
           REAPER_PYTYLIKI_INVALID_ARGUMENT);

    puts("Reaper -> typed IR -> resource validation -> backend -> PPF CPU execution passed");
    return 0;
}
