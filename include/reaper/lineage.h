#ifndef REAPER_LINEAGE_H
#define REAPER_LINEAGE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_LINEAGE_MAX_NODES 4096u
#define REAPER_LINEAGE_MAX_PARENTS 8u
#define REAPER_LINEAGE_SOURCE_MAX 256u
#define REAPER_LINEAGE_OPERATION_MAX 64u
#define REAPER_LINEAGE_TYPE_MAX 32u

typedef enum {
    REAPER_LINEAGE_OK = 0,
    REAPER_LINEAGE_INVALID_ARGUMENT,
    REAPER_LINEAGE_DUPLICATE_ID,
    REAPER_LINEAGE_UNKNOWN_PARENT,
    REAPER_LINEAGE_LIMIT,
    REAPER_LINEAGE_NOT_FOUND
} ReaperLineageStatus;

typedef struct {
    uint64_t id;
    uint64_t parents[REAPER_LINEAGE_MAX_PARENTS];
    size_t parent_count;
    char source_path[REAPER_LINEAGE_SOURCE_MAX];
    char operation[REAPER_LINEAGE_OPERATION_MAX];
    char value_type[REAPER_LINEAGE_TYPE_MAX];
    uint32_t source_line;
    uint32_t source_column;
} ReaperLineageNode;

/* Caller owns the fixed-capacity node array. IDs are immutable and parents
 * must be inserted before children, which guarantees an acyclic provenance DAG. */
typedef struct {
    ReaperLineageNode *nodes;
    size_t length;
    size_t capacity;
} ReaperLineageGraph;

ReaperLineageStatus reaper_lineage_init(
    ReaperLineageGraph *graph, ReaperLineageNode *storage, size_t capacity
);
ReaperLineageStatus reaper_lineage_add(
    ReaperLineageGraph *graph, const ReaperLineageNode *node
);
/* Writes ancestors first and the requested node last. On insufficient
 * output capacity, no output IDs are written. */
ReaperLineageStatus reaper_lineage_trace(
    const ReaperLineageGraph *graph, uint64_t node_id,
    uint64_t *output_ids, size_t output_capacity, size_t *output_count
);
const char *reaper_lineage_status_name(ReaperLineageStatus status);

#ifdef __cplusplus
}
#endif
#endif
