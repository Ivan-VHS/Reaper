#include "reaper/pytyliki_bridge.h"
#include "interop.h"

#include <assert.h>
#include <string.h>
#include <stdio.h>

static uint32_t incompatible_abi(void) {
    return PYTYLIKI_ABI_VERSION + 1u;
}

int main(void) {
    ReaperPytylikiProvider provider = {
        pytyliki_abi_version,
        pytyliki_v1_native_snapshot_descriptor,
        pytyliki_v1_native_snapshot_collect,
        pytyliki_v1_native_placement
    };
    ReaperPytylikiProvider incompatible = provider;
    pl_ni_snapshot snapshot;
    pl_ppf_request request;
    pl_ppf_report report;

    assert(reaper_pytyliki_snapshot_read(&provider, &snapshot) == REAPER_PYTYLIKI_OK);
    assert(snapshot.cpu_count != 0u);
    assert(snapshot.provenance.snapshot_fingerprint != 0u);
    assert(snapshot.provenance.generation == snapshot.provenance.snapshot_fingerprint);

    memset(&request, 0, sizeof(request));
    request.preferred_numa_node = UINT16_MAX;
    request.current_cpu_index = UINT16_MAX;
    request.require_online = 1u;
    for (size_t i = 0u; i < 5u; ++i) request.weights[i] = 1u;

    assert(reaper_pytyliki_plan_placement(
        &provider, &request, NULL, 0u, &snapshot, &report
    ) == REAPER_PYTYLIKI_OK);
    assert(report.candidate_count == snapshot.cpu_count);
    assert(report.has_selection == 1u);
    assert(report.selected_cpu_index < snapshot.cpu_count);
    assert(report.topology_generation == snapshot.provenance.generation);

    incompatible.abi_version = incompatible_abi;
    assert(reaper_pytyliki_snapshot_read(&incompatible, &snapshot) ==
           REAPER_PYTYLIKI_ABI_MISMATCH);
    assert(reaper_pytyliki_snapshot_read(NULL, &snapshot) ==
           REAPER_PYTYLIKI_INVALID_ARGUMENT);
    puts("Reaper <-> Pytyliki native hardware bridge tests passed");
    return 0;
}
