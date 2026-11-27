#include "reaper/pytyliki_iron_core.h"

#include <stdio.h>
#include <string.h>

#define ARRAY_COUNT(items) (sizeof(items) / sizeof((items)[0]))

static const ReaperIronMarkerInfo marker_catalog[REAPER_IRON_MARKER_COUNT] = {
    {"module.begin", "begin iron )", REAPER_IRON_CLASS_FRAMING, 0},
    {"core.context", "() core --", REAPER_IRON_CLASS_CONTEXT, 1},
    {"system.context", "[ system ]-", REAPER_IRON_CLASS_CONTEXT, 1},
    {"block.end", "stop option ;", REAPER_IRON_CLASS_FRAMING, 0},
    {"level.context", "] level .", REAPER_IRON_CLASS_CONTEXT, 1},
    {"selection.filter", "{ selective /", REAPER_IRON_CLASS_PLAN, 1},
    {"operation.unit", "} operation P)-", REAPER_IRON_CLASS_PLAN, 1},
    {"work.massive", "?? massive <>", REAPER_IRON_CLASS_PLAN, 1},
    {"startup.plan", "< start >?", REAPER_IRON_CLASS_PLAN, 1},
    {"work.spawn.plan", "grown new-work >/", REAPER_IRON_CLASS_PLAN, 1},
    {"implementation.binding", "> concrete //*", REAPER_IRON_CLASS_PLAN, 1},
    {"utility.helper", "## utility _", REAPER_IRON_CLASS_PLAN, 1},
    {"layout.unify", "# unify TAB", REAPER_IRON_CLASS_PLAN, 1},
    {"branchpass.plan", "setup brachpass ^^", REAPER_IRON_CLASS_PLAN, 1},
    {"tournament.rank", "!+ hyper tournament ^", REAPER_IRON_CLASS_PLAN, 1},
    {"consistency.rules", "CC based rules ^^^", REAPER_IRON_CLASS_POLICY, 0},
    {"execution.jump.plan", "level jump to run *(", REAPER_IRON_CLASS_PLAN, 1},
    {"logic.true_connective", "TRUE connective *+", REAPER_IRON_CLASS_PLAN, 1},
    {"module.version", "verison ///. *", REAPER_IRON_CLASS_SOURCE_METADATA, 0},
    {"source.verification_claim", "verificated /// !!",
     REAPER_IRON_CLASS_SOURCE_METADATA, 0}
};

static int reject(ReaperIronError *error, size_t index, const char *message)
{
    if (error != NULL) {
        error->block_index = index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return 0;
}

static int valid_label(const char *label)
{
    size_t length = 0u;

    if (label == NULL || label[0] == '\0') {
        return 0;
    }

    while (label[length] != '\0') {
        unsigned char value = (unsigned char)label[length];
        int valid =
            (value >= (unsigned char)'a' && value <= (unsigned char)'z') ||
            (value >= (unsigned char)'A' && value <= (unsigned char)'Z') ||
            (value >= (unsigned char)'0' && value <= (unsigned char)'9') ||
            value == (unsigned char)'_' ||
            value == (unsigned char)'.' ||
            value == (unsigned char)'-';

        if (!valid || length >= REAPER_IRON_MAX_LABEL - 1u) {
            return 0;
        }
        ++length;
    }

    return 1;
}

size_t reaper_iron_marker_catalog(const ReaperIronMarkerInfo **output)
{
    if (output != NULL) {
        *output = marker_catalog;
    }
    return ARRAY_COUNT(marker_catalog);
}

const ReaperIronMarkerInfo *reaper_iron_marker_by_id(const char *semantic_id)
{
    size_t index;

    if (semantic_id == NULL) {
        return NULL;
    }

    for (index = 0u; index < ARRAY_COUNT(marker_catalog); ++index) {
        if (strcmp(marker_catalog[index].semantic_id, semantic_id) == 0) {
            return &marker_catalog[index];
        }
    }

    return NULL;
}

const char *reaper_iron_semantic_class_name(ReaperIronSemanticClass semantic_class)
{
    switch (semantic_class) {
    case REAPER_IRON_CLASS_FRAMING:
        return "framing";
    case REAPER_IRON_CLASS_CONTEXT:
        return "context";
    case REAPER_IRON_CLASS_PLAN:
        return "plan";
    case REAPER_IRON_CLASS_POLICY:
        return "policy";
    case REAPER_IRON_CLASS_SOURCE_METADATA:
        return "source-metadata";
    default:
        return "invalid";
    }
}

int reaper_iron_import(const ReaperIronImport *input,
                       ReaperIronModule *output,
                       ReaperIronError *error)
{
    ReaperIronModule candidate;
    size_t index;

    if (error != NULL) {
        error->block_index = 0u;
        error->message[0] = '\0';
    }
    if (input == NULL || output == NULL) {
        return reject(error, 0u, "import input and output are required");
    }
    if (input->schema_version != REAPER_IRON_AST_VERSION) {
        return reject(error, 0u, "unsupported Pytyliki Iron Core AST version");
    }
    if (input->source_bytes == 0u ||
        input->source_bytes > REAPER_IRON_MAX_SOURCE_BYTES) {
        return reject(error, 0u, "source byte length is outside the v1 bound");
    }
    if (!valid_label(input->version_label)) {
        return reject(error, 0u, "version label is missing or invalid");
    }
    if (!valid_label(input->verification_claim)) {
        return reject(error, 0u, "verification claim is missing or invalid");
    }
    if (input->policy_declarations == 0u) {
        return reject(error, 0u, "consistency policy declaration is required");
    }
    if (input->blocks == NULL || input->block_count == 0u ||
        input->block_count > REAPER_IRON_MAX_BLOCKS) {
        return reject(error, 0u, "block collection is empty or exceeds the v1 bound");
    }

    memset(&candidate, 0, sizeof(candidate));
    candidate.source_bytes = input->source_bytes;
    (void)snprintf(candidate.version_label, sizeof candidate.version_label,
                   "%s", input->version_label);
    (void)snprintf(candidate.verification_claim,
                   sizeof candidate.verification_claim, "%s",
                   input->verification_claim);
    candidate.source_claim_only = 1;
    candidate.typed_lowering_performed = 0;
    candidate.execution_performed = 0;
    candidate.hardware_effects_performed = 0;

    for (index = 0u; index < input->block_count; ++index) {
        const ReaperIronBlockRef *block = &input->blocks[index];
        const ReaperIronMarkerInfo *marker =
            reaper_iron_marker_by_id(block->semantic_id);
        const ReaperIronSourceAnchor *source = &block->source;
        uint64_t body_end;

        if (marker == NULL || !marker->opens_block) {
            return reject(error, index, "unknown semantic ID or non-block marker");
        }
        if (!block->closed) {
            return reject(error, index, "unclosed source block is not importable");
        }
        if (source->line == 0u ||
            source->start_offset > source->body_offset ||
            source->body_offset > source->end_offset ||
            source->body_offset > input->source_bytes ||
            source->body_length > input->source_bytes - source->body_offset ||
            source->end_offset > input->source_bytes) {
            return reject(error, index, "source anchor is outside the source document");
        }

        body_end = source->body_offset + source->body_length;
        if (body_end != source->end_offset) {
            return reject(error, index, "source body length does not match its end offset");
        }

        candidate.nodes[index].marker = marker;
        candidate.nodes[index].source = *source;
        ++candidate.node_count;
    }

    *output = candidate;
    return 1;
}
