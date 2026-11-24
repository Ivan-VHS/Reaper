#include "reaper/lineage.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static ReaperLineageNode node(uint64_t id, const char *path, uint32_t line,
                              const char *operation, const char *type) {
    ReaperLineageNode value = {0};
    value.id = id;
    (void)snprintf(value.source_path, sizeof value.source_path, "%s", path);
    (void)snprintf(value.operation, sizeof value.operation, "%s", operation);
    (void)snprintf(value.value_type, sizeof value.value_type, "%s", type);
    value.source_line = line;
    value.source_column = 1u;
    return value;
}

int main(void) {
    ReaperLineageNode storage[8];
    ReaperLineageGraph graph;
    ReaperLineageNode source = node(1u, "examples/input.rpr", 2u, "read.source", "bytes");
    ReaperLineageNode parse = node(2u, "examples/input.rpr", 4u, "parse", "ast");
    ReaperLineageNode transform = node(3u, "examples/input.rpr", 7u, "normalize", "ir");
    ReaperLineageNode output = node(4u, "examples/input.rpr", 9u, "emit", "artifact");
    uint64_t trace[8] = {0};
    size_t count = 0u;

    assert(reaper_lineage_init(&graph, storage, 8u) == REAPER_LINEAGE_OK);
    assert(reaper_lineage_add(&graph, &source) == REAPER_LINEAGE_OK);
    parse.parents[0] = 1u;
    parse.parent_count = 1u;
    assert(reaper_lineage_add(&graph, &parse) == REAPER_LINEAGE_OK);
    transform.parents[0] = 2u;
    transform.parent_count = 1u;
    assert(reaper_lineage_add(&graph, &transform) == REAPER_LINEAGE_OK);
    output.parents[0] = 3u;
    output.parent_count = 1u;
    assert(reaper_lineage_add(&graph, &output) == REAPER_LINEAGE_OK);

    assert(reaper_lineage_trace(&graph, 4u, trace, 8u, &count) == REAPER_LINEAGE_OK);
    assert(count == 4u);
    assert(trace[0] == 1u && trace[1] == 2u && trace[2] == 3u && trace[3] == 4u);
    assert(reaper_lineage_trace(&graph, 4u, trace, 3u, &count) == REAPER_LINEAGE_LIMIT);
    assert(count == 0u);

    assert(reaper_lineage_add(&graph, &output) == REAPER_LINEAGE_DUPLICATE_ID);
    {
        ReaperLineageNode missing = node(5u, "missing.rpr", 1u, "derive", "value");
        missing.parents[0] = 99u;
        missing.parent_count = 1u;
        assert(reaper_lineage_add(&graph, &missing) == REAPER_LINEAGE_UNKNOWN_PARENT);
    }
    assert(reaper_lineage_trace(&graph, 99u, trace, 8u, &count) == REAPER_LINEAGE_NOT_FOUND);
    assert(strcmp(reaper_lineage_status_name(REAPER_LINEAGE_OK), "ok") == 0);
    puts("Reaper data lineage tests passed.");
    return 0;
}
