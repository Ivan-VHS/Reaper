#ifndef REAPER_PYTYLIKI_IRON_CORE_H
#define REAPER_PYTYLIKI_IRON_CORE_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define REAPER_IRON_AST_VERSION 1u
#define REAPER_IRON_MAX_SOURCE_BYTES (1024u * 1024u)
#define REAPER_IRON_MAX_BLOCKS 64u
#define REAPER_IRON_MAX_LABEL 96u
#define REAPER_IRON_MARKER_COUNT 20u
typedef enum {
 REAPER_IRON_CLASS_FRAMING=0, REAPER_IRON_CLASS_CONTEXT,
 REAPER_IRON_CLASS_PLAN, REAPER_IRON_CLASS_POLICY,
 REAPER_IRON_CLASS_SOURCE_METADATA
} ReaperIronSemanticClass;
typedef struct {
 const char *semantic_id;
 const char *token;
 ReaperIronSemanticClass semantic_class;
 int opens_block;
} ReaperIronMarkerInfo;
/* AST v1 has byte offsets and lines, but no columns. Do not invent columns. */
typedef struct {
 uint64_t start_offset, body_offset, body_length, end_offset;
 uint32_t line;
} ReaperIronSourceAnchor;
typedef struct {
 const char *semantic_id;
 ReaperIronSourceAnchor source;
 int closed;
} ReaperIronBlockRef;
typedef struct {
 uint32_t schema_version;
 uint64_t source_bytes;
 const char *version_label;
 const char *verification_claim;
 uint32_t policy_declarations;
 const ReaperIronBlockRef *blocks;
 size_t block_count;
} ReaperIronImport;
typedef struct {
 const ReaperIronMarkerInfo *marker;
 ReaperIronSourceAnchor source;
} ReaperIronNode;
typedef struct {
 uint64_t source_bytes;
 char version_label[REAPER_IRON_MAX_LABEL];
 char verification_claim[REAPER_IRON_MAX_LABEL];
 size_t node_count;
 ReaperIronNode nodes[REAPER_IRON_MAX_BLOCKS];
 int source_claim_only;
 int typed_lowering_performed;
 int execution_performed;
 int hardware_effects_performed;
} ReaperIronModule;
typedef struct { size_t block_index; char message[192]; } ReaperIronError;
/* Imports schema-validated, already-deserialized AST v1 records. This is a
 * metadata adapter, not a parser, type checker or IR lowerer. */
int reaper_iron_import(const ReaperIronImport *input,
                       ReaperIronModule *output, ReaperIronError *error);
size_t reaper_iron_marker_catalog(const ReaperIronMarkerInfo **output);
const ReaperIronMarkerInfo *reaper_iron_marker_by_id(const char *semantic_id);
const char *reaper_iron_semantic_class_name(ReaperIronSemanticClass semantic_class);
#ifdef __cplusplus
}
#endif
#endif
