#ifndef REAPER_ARCHITECTURE_H
#define REAPER_ARCHITECTURE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_ARCHITECTURE_ABI_VERSION 1U
#define REAPER_ARCHITECTURE_CONCEPT_COUNT 66U
#define REAPER_ARCHITECTURE_MAX_CONCEPTS 66U
#define REAPER_ARCHITECTURE_MAX_DEPENDENCIES 512U

typedef enum {
    REAPER_ARCH_CONCEPT_FRAMEWORK_FRAME = 1,
    REAPER_ARCH_CONCEPT_PLATFORM = 2,
    REAPER_ARCH_CONCEPT_ENVIRONMENT = 3,
    REAPER_ARCH_CONCEPT_INFRASTRUCTURE = 4,
    REAPER_ARCH_CONCEPT_ARCHITECTURE = 5,
    REAPER_ARCH_CONCEPT_BASIS = 6,
    REAPER_ARCH_CONCEPT_BASE = 7,
    REAPER_ARCH_CONCEPT_FOUNDATION = 8,
    REAPER_ARCH_CONCEPT_SKELETON = 9,
    REAPER_ARCH_CONCEPT_BACKBONE = 10,
    REAPER_ARCH_CONCEPT_STRUCTURE = 11,
    REAPER_ARCH_CONCEPT_CONSTRUCTION = 12,
    REAPER_ARCH_CONCEPT_ECOSYSTEM = 13,
    REAPER_ARCH_CONCEPT_EXTENSION_LAYER = 14,
    REAPER_ARCH_CONCEPT_SHELL = 15,
    REAPER_ARCH_CONCEPT_RUNTIME = 16,
    REAPER_ARCH_CONCEPT_EXECUTION_ENVIRONMENT = 17,
    REAPER_ARCH_CONCEPT_ENGINE = 18,
    REAPER_ARCH_CONCEPT_KERNEL = 19,
    REAPER_ARCH_CONCEPT_LIBRARY = 20,
    REAPER_ARCH_CONCEPT_TOOLSET = 21,
    REAPER_ARCH_CONCEPT_TOOLING = 22,
    REAPER_ARCH_CONCEPT_TOOLKIT = 23,
    REAPER_ARCH_CONCEPT_PACKAGE = 24,
    REAPER_ARCH_CONCEPT_STACK = 25,
    REAPER_ARCH_CONCEPT_TECHNOLOGY_STACK = 26,
    REAPER_ARCH_CONCEPT_TEMPLATE = 27,
    REAPER_ARCH_CONCEPT_SKELETON_TEMPLATE = 28,
    REAPER_ARCH_CONCEPT_BOILERPLATE = 29,
    REAPER_ARCH_CONCEPT_BASE_LAYER = 30,
    REAPER_ARCH_CONCEPT_MIDDLE_LAYER = 31,
    REAPER_ARCH_CONCEPT_MIDDLEWARE = 32,
    REAPER_ARCH_CONCEPT_GLUE_SOFTWARE = 33,
    REAPER_ARCH_CONCEPT_CONTAINER = 34,
    REAPER_ARCH_CONCEPT_HOST = 35,
    REAPER_ARCH_CONCEPT_CONTEXT = 36,
    REAPER_ARCH_CONCEPT_MODEL = 37,
    REAPER_ARCH_CONCEPT_PATTERN = 38,
    REAPER_ARCH_CONCEPT_PARADIGM = 39,
    REAPER_ARCH_CONCEPT_CONCEPT = 40,
    REAPER_ARCH_CONCEPT_METHODOLOGY = 41,
    REAPER_ARCH_CONCEPT_APPROACH = 42,
    REAPER_ARCH_CONCEPT_SYSTEM = 43,
    REAPER_ARCH_CONCEPT_SUBSYSTEM = 44,
    REAPER_ARCH_CONCEPT_MODULE = 45,
    REAPER_ARCH_CONCEPT_COMPONENT = 46,
    REAPER_ARCH_CONCEPT_BLOCK = 47,
    REAPER_ARCH_CONCEPT_NODE = 48,
    REAPER_ARCH_CONCEPT_INTERFACE = 49,
    REAPER_ARCH_CONCEPT_PROTOCOL = 50,
    REAPER_ARCH_CONCEPT_STANDARD = 51,
    REAPER_ARCH_CONCEPT_POLICY = 52,
    REAPER_ARCH_CONCEPT_SPECIFICATION = 53,
    REAPER_ARCH_CONCEPT_SCHEMA = 54,
    REAPER_ARCH_CONCEPT_MATRIX = 55,
    REAPER_ARCH_CONCEPT_GRID = 56,
    REAPER_ARCH_CONCEPT_BOUNDARY = 57,
    REAPER_ARCH_CONCEPT_PERIMETER = 58,
    REAPER_ARCH_CONCEPT_WORK_ENVIRONMENT = 59,
    REAPER_ARCH_CONCEPT_WORKSPACE = 60,
    REAPER_ARCH_CONCEPT_FOOTHOLD = 61,
    REAPER_ARCH_CONCEPT_ANCHOR_POINT = 62,
    REAPER_ARCH_CONCEPT_BASELINE = 63,
    REAPER_ARCH_CONCEPT_LOAD_BEARING_STRUCTURE = 64,
    REAPER_ARCH_CONCEPT_HARDWARE_SOFTWARE_BASE = 65,
    REAPER_ARCH_CONCEPT_SOFTWARE_FRAMEWORK = 66
} ReaperArchitectureConceptId;

typedef enum {
    REAPER_ARCH_LAYER_FOUNDATION = 0,
    REAPER_ARCH_LAYER_PLATFORM_EXECUTION,
    REAPER_ARCH_LAYER_TOOLCHAIN_ASSETS,
    REAPER_ARCH_LAYER_DESIGN_MODELS,
    REAPER_ARCH_LAYER_COMPOSITION,
    REAPER_ARCH_LAYER_CONTRACTS,
    REAPER_ARCH_LAYER_TOPOLOGY,
    REAPER_ARCH_LAYER_WORKSPACE,
    REAPER_ARCH_LAYER_HARDWARE_INTEGRATION,
    REAPER_ARCH_LAYER_COUNT
} ReaperArchitectureLayer;

typedef struct {
    ReaperArchitectureLayer layer;
    const char *key;
    const char *name_en;
    const char *name_ru;
    const char *description;
} ReaperArchitectureLayerInfo;

typedef struct {
    ReaperArchitectureConceptId id;
    ReaperArchitectureLayer layer;
    const char *key;
    const char *name_en;
    const char *name_ru;
    const char *description;
} ReaperArchitectureConceptInfo;

typedef enum {
    REAPER_ARCHITECTURE_OK = 0,
    REAPER_ARCHITECTURE_INVALID_ARGUMENT,
    REAPER_ARCHITECTURE_LIMIT_EXCEEDED,
    REAPER_ARCHITECTURE_UNKNOWN_CONCEPT,
    REAPER_ARCHITECTURE_DUPLICATE_CONCEPT,
    REAPER_ARCHITECTURE_MISSING_CONCEPT,
    REAPER_ARCHITECTURE_MISSING_DEPENDENCY,
    REAPER_ARCHITECTURE_SELF_DEPENDENCY,
    REAPER_ARCHITECTURE_DUPLICATE_DEPENDENCY,
    REAPER_ARCHITECTURE_DEPENDENCY_CYCLE,
    REAPER_ARCHITECTURE_BUFFER_TOO_SMALL
} ReaperArchitectureStatus;

typedef struct {
    ReaperArchitectureConceptId dependent;
    ReaperArchitectureConceptId dependency;
} ReaperArchitectureDependency;

typedef struct {
    const ReaperArchitectureConceptId *concepts;
    size_t concept_count;
    const ReaperArchitectureDependency *dependencies;
    size_t dependency_count;
} ReaperArchitectureGraph;

typedef struct {
    ReaperArchitectureStatus status;
    ReaperArchitectureConceptId concept_id;
    char message[128];
} ReaperArchitectureError;

size_t reaper_architecture_concept_count(void);
size_t reaper_architecture_layer_count(void);
const ReaperArchitectureConceptInfo *reaper_architecture_concept_at(size_t index);
const ReaperArchitectureConceptInfo *reaper_architecture_concept_find_by_id(
    ReaperArchitectureConceptId id
);
const ReaperArchitectureConceptInfo *reaper_architecture_concept_find(
    const char *key
);
const ReaperArchitectureConceptInfo *reaper_architecture_concept_find_ru(
    const char *name_ru
);
const ReaperArchitectureLayerInfo *reaper_architecture_layer_at(size_t index);
const char *reaper_architecture_status_name(ReaperArchitectureStatus status);

ReaperArchitectureStatus reaper_architecture_graph_validate(
    const ReaperArchitectureGraph *graph,
    ReaperArchitectureError *error
);

/* Returns a deterministic dependency-first order, breaking ties by concept ID. */
ReaperArchitectureStatus reaper_architecture_graph_order(
    const ReaperArchitectureGraph *graph,
    ReaperArchitectureConceptId *ordered,
    size_t capacity,
    size_t *written,
    ReaperArchitectureError *error
);

#ifdef __cplusplus
}
#endif

#endif
