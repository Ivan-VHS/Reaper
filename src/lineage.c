#include "reaper/lineage.h"

#include <string.h>

static int fixed_text_valid(const char *text, size_t capacity) {
    size_t index;
    if (text == NULL || capacity < 2u || text[0] == '\0') return 0;
    for (index = 0u; index < capacity; ++index) {
        const unsigned char value = (unsigned char)text[index];
        if (value == '\0') return index > 0u;
        if (value < 0x20u || value == 0x7fu) return 0;
    }
    return 0;
}

static size_t find_node(const ReaperLineageGraph *graph, uint64_t id) {
    size_t index;
    for (index = 0u; index < graph->length; ++index) {
        if (graph->nodes[index].id == id) return index;
    }
    return graph->length;
}

ReaperLineageStatus reaper_lineage_init(ReaperLineageGraph *graph,
                                        ReaperLineageNode *storage,
                                        size_t capacity) {
    if (graph == NULL || storage == NULL || capacity == 0u ||
        capacity > REAPER_LINEAGE_MAX_NODES)
        return REAPER_LINEAGE_INVALID_ARGUMENT;
    graph->nodes = storage;
    graph->length = 0u;
    graph->capacity = capacity;
    return REAPER_LINEAGE_OK;
}

ReaperLineageStatus reaper_lineage_add(ReaperLineageGraph *graph,
                                       const ReaperLineageNode *node) {
    size_t index, parent;
    if (graph == NULL || node == NULL || graph->nodes == NULL ||
        graph->length > graph->capacity || graph->capacity > REAPER_LINEAGE_MAX_NODES)
        return REAPER_LINEAGE_INVALID_ARGUMENT;
    if (node->id == 0u || node->parent_count > REAPER_LINEAGE_MAX_PARENTS ||
        node->source_line == 0u || node->source_column == 0u ||
        !fixed_text_valid(node->source_path, sizeof node->source_path) ||
        !fixed_text_valid(node->operation, sizeof node->operation) ||
        !fixed_text_valid(node->value_type, sizeof node->value_type))
        return REAPER_LINEAGE_INVALID_ARGUMENT;
    if (graph->length == graph->capacity) return REAPER_LINEAGE_LIMIT;
    if (find_node(graph, node->id) != graph->length) return REAPER_LINEAGE_DUPLICATE_ID;
    for (index = 0u; index < node->parent_count; ++index) {
        if (node->parents[index] == 0u || node->parents[index] == node->id)
            return REAPER_LINEAGE_INVALID_ARGUMENT;
        for (parent = index + 1u; parent < node->parent_count; ++parent) {
            if (node->parents[index] == node->parents[parent])
                return REAPER_LINEAGE_INVALID_ARGUMENT;
        }
        if (find_node(graph, node->parents[index]) == graph->length)
            return REAPER_LINEAGE_UNKNOWN_PARENT;
    }
    graph->nodes[graph->length++] = *node;
    return REAPER_LINEAGE_OK;
}

ReaperLineageStatus reaper_lineage_trace(const ReaperLineageGraph *graph,
                                         uint64_t node_id, uint64_t *output_ids,
                                         size_t output_capacity, size_t *output_count) {
    unsigned char visited[REAPER_LINEAGE_MAX_NODES] = {0};
    size_t stack[REAPER_LINEAGE_MAX_NODES];
    size_t stack_size = 0u, index, count = 0u;
    if (output_count != NULL) *output_count = 0u;
    if (graph == NULL || graph->nodes == NULL || output_ids == NULL ||
        output_count == NULL || graph->length > graph->capacity ||
        graph->length > REAPER_LINEAGE_MAX_NODES)
        return REAPER_LINEAGE_INVALID_ARGUMENT;
    index = find_node(graph, node_id);
    if (index == graph->length) return REAPER_LINEAGE_NOT_FOUND;
    visited[index] = 1u;
    stack[stack_size++] = index;
    while (stack_size > 0u) {
        const size_t current = stack[--stack_size];
        const ReaperLineageNode *node = &graph->nodes[current];
        size_t parent;
        ++count;
        for (parent = 0u; parent < node->parent_count; ++parent) {
            const size_t parent_index = find_node(graph, node->parents[parent]);
            if (parent_index == graph->length) return REAPER_LINEAGE_UNKNOWN_PARENT;
            if (!visited[parent_index]) {
                visited[parent_index] = 1u;
                stack[stack_size++] = parent_index;
            }
        }
    }
    if (count > output_capacity) return REAPER_LINEAGE_LIMIT;
    count = 0u;
    for (index = 0u; index < graph->length; ++index) {
        if (visited[index]) output_ids[count++] = graph->nodes[index].id;
    }
    *output_count = count;
    return REAPER_LINEAGE_OK;
}

const char *reaper_lineage_status_name(ReaperLineageStatus status) {
    switch (status) {
    case REAPER_LINEAGE_OK: return "ok";
    case REAPER_LINEAGE_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_LINEAGE_DUPLICATE_ID: return "duplicate-id";
    case REAPER_LINEAGE_UNKNOWN_PARENT: return "unknown-parent";
    case REAPER_LINEAGE_LIMIT: return "limit";
    case REAPER_LINEAGE_NOT_FOUND: return "not-found";
    default: return "invalid-status";
    }
}
