#include "reaper/pytyliki_bridge.h"

#include <string.h>

#define REAPER_PYTYLIKI_KNOWN_ISA_MASK \
    (PL_NI_ISA_SSE2 | PL_NI_ISA_SSE42 | PL_NI_ISA_AES | PL_NI_ISA_AVX | \
     PL_NI_ISA_AVX2 | PL_NI_ISA_FMA | PL_NI_ISA_AVX512F | PL_NI_ISA_NEON | \
     PL_NI_ISA_SVE | PL_NI_ISA_SVE2 | PL_NI_ISA_ARM_AES | PL_NI_ISA_ARM_SHA1 | \
     PL_NI_ISA_ARM_SHA2 | PL_NI_ISA_ARM_CRC32 | PL_NI_ISA_ARM_ATOMICS)

static int mask_bit(const uint64_t *mask, uint32_t bit) {
    return (mask[bit / 64u] & (UINT64_C(1) << (bit % 64u))) != 0u;
}

static int snapshot_header_valid(const pl_ni_snapshot *snapshot) {
    uint32_t i, j;
    if (snapshot->abi_version != PL_NI_ABI_VERSION ||
        snapshot->cpu_count == 0u || snapshot->cpu_count > PL_NI_MAX_CPUS ||
        snapshot->cache_count > PL_NI_MAX_CACHES ||
        snapshot->numa_count > PL_NI_MAX_NUMA_NODES ||
        snapshot->available_memory_bytes > snapshot->total_memory_bytes ||
        snapshot->provenance.schema_version != PL_NI_ABI_VERSION ||
        snapshot->provenance.topology_state < PL_NI_FACT_KNOWN ||
        snapshot->provenance.topology_state > PL_NI_FACT_CONFLICTING ||
        snapshot->provenance.allowed_state < PL_NI_FACT_KNOWN ||
        snapshot->provenance.allowed_state > PL_NI_FACT_CONFLICTING ||
        snapshot->provenance.isa_state < PL_NI_FACT_KNOWN ||
        snapshot->provenance.isa_state > PL_NI_FACT_CONFLICTING ||
        snapshot->provenance.isa_scope > PL_NI_ISA_SCOPE_PER_LOGICAL_CPU ||
        snapshot->provenance.memory_state < PL_NI_FACT_KNOWN ||
        snapshot->provenance.memory_state > PL_NI_FACT_CONFLICTING ||
        snapshot->provenance.snapshot_fingerprint == 0u ||
        snapshot->provenance.generation != snapshot->provenance.snapshot_fingerprint ||
        (snapshot->isa_mask & ~REAPER_PYTYLIKI_KNOWN_ISA_MASK) != 0u)
        return 0;
    if (memchr(snapshot->provenance.platform, '\0',
               sizeof(snapshot->provenance.platform)) == NULL ||
        memchr(snapshot->provenance.topology_source, '\0',
               sizeof(snapshot->provenance.topology_source)) == NULL ||
        memchr(snapshot->provenance.allowed_source, '\0',
               sizeof(snapshot->provenance.allowed_source)) == NULL ||
        memchr(snapshot->provenance.isa_source, '\0',
               sizeof(snapshot->provenance.isa_source)) == NULL ||
        memchr(snapshot->provenance.memory_source, '\0',
               sizeof(snapshot->provenance.memory_source)) == NULL)
        return 0;
    for (i = 0u; i < snapshot->cpu_count; ++i) {
        const pl_ni_cpu *cpu = &snapshot->cpus[i];
        if ((cpu->isa_mask & ~REAPER_PYTYLIKI_KNOWN_ISA_MASK) != 0u)
            return 0;
        for (j = i + 1u; j < snapshot->cpu_count; ++j)
            if (cpu->group_id == snapshot->cpus[j].group_id &&
                cpu->os_cpu_id == snapshot->cpus[j].os_cpu_id)
                return 0;
    }
    for (i = 0u; i < snapshot->cache_count; ++i) {
        const pl_ni_cache *cache = &snapshot->caches[i];
        uint32_t sharing = 0u;
        if (cache->level == 0u || cache->size_bytes == 0u ||
            cache->sharing_count == 0u)
            return 0;
        for (j = 0u; j < snapshot->cpu_count; ++j)
            if (mask_bit(cache->sharing_mask, j)) ++sharing;
        if (sharing != cache->sharing_count) return 0;
        for (j = snapshot->cpu_count; j < PL_NI_MAX_CPUS; ++j)
            if (mask_bit(cache->sharing_mask, j)) return 0;
    }
    for (i = 0u; i < snapshot->numa_count; ++i) {
        const pl_ni_numa_node *node = &snapshot->numa[i];
        uint32_t count = 0u;
        for (j = 0u; j < snapshot->cpu_count; ++j)
            if (mask_bit(node->cpu_mask, j)) ++count;
        if (count != node->cpu_count) return 0;
        for (j = snapshot->cpu_count; j < PL_NI_MAX_CPUS; ++j)
            if (mask_bit(node->cpu_mask, j)) return 0;
    }
    return 1;
}

ReaperPytylikiStatus reaper_pytyliki_snapshot_read(
    const ReaperPytylikiProvider *provider, pl_ni_snapshot *out) {
    uint32_t contract_version = 0u;
    uint64_t structure_size = 0u;
    if (provider == NULL || out == NULL || provider->abi_version == NULL ||
        provider->snapshot_descriptor == NULL ||
        provider->snapshot_collect == NULL)
        return REAPER_PYTYLIKI_INVALID_ARGUMENT;
    memset(out, 0, sizeof(*out));
    if (provider->abi_version() != REAPER_PYTYLIKI_ABI_VERSION ||
        provider->snapshot_descriptor(&contract_version, &structure_size) != 0 ||
        contract_version != PL_NI_ABI_VERSION ||
        structure_size != (uint64_t)sizeof(*out))
        return REAPER_PYTYLIKI_ABI_MISMATCH;
    if (provider->snapshot_collect(out, structure_size) != 0)
        return REAPER_PYTYLIKI_PROVIDER_FAILURE;
    if (!snapshot_header_valid(out))
        return REAPER_PYTYLIKI_INVALID_SNAPSHOT;
    return REAPER_PYTYLIKI_OK;
}

ReaperPytylikiStatus reaper_pytyliki_plan_placement(
    const ReaperPytylikiProvider *provider,
    const pl_ppf_request *request,
    const pl_ppf_telemetry *telemetry,
    uint64_t telemetry_count,
    pl_ni_snapshot *snapshot_out,
    pl_ppf_report *report_out) {
    ReaperPytylikiStatus status;
    if (provider == NULL || request == NULL || snapshot_out == NULL ||
        report_out == NULL || provider->placement == NULL ||
        (telemetry == NULL && telemetry_count != 0u))
        return REAPER_PYTYLIKI_INVALID_ARGUMENT;
    memset(report_out, 0, sizeof(*report_out));
    status = reaper_pytyliki_snapshot_read(provider, snapshot_out);
    if (status != REAPER_PYTYLIKI_OK) return status;
    if (provider->placement(snapshot_out, request, telemetry,
                            telemetry_count, report_out) != 0)
        return REAPER_PYTYLIKI_PROVIDER_FAILURE;
    if (report_out->candidate_count != snapshot_out->cpu_count ||
        report_out->topology_generation != snapshot_out->provenance.generation ||
        report_out->topology_fingerprint != snapshot_out->provenance.snapshot_fingerprint ||
        report_out->has_selection > 1u ||
        (report_out->has_selection != 0u &&
         report_out->selected_cpu_index >= snapshot_out->cpu_count))
        return REAPER_PYTYLIKI_STALE_PLACEMENT;
    for (uint32_t i = 0u; i < report_out->candidate_count; ++i) {
        if (report_out->candidates[i].cpu_index != i ||
            report_out->candidates[i].accepted > 1u)
            return REAPER_PYTYLIKI_INVALID_SNAPSHOT;
    }
    if (report_out->has_selection != 0u &&
        report_out->candidates[report_out->selected_cpu_index].accepted == 0u)
        return REAPER_PYTYLIKI_STALE_PLACEMENT;
    return REAPER_PYTYLIKI_OK;
}
