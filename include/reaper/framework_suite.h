#ifndef REAPER_FRAMEWORK_SUITE_H
#define REAPER_FRAMEWORK_SUITE_H

#include <stdint.h>

#if defined(_WIN32)
# if defined(REAPER_FRAMEWORKS_BUILD)
#  define REAPER_FRAMEWORK_API __declspec(dllexport)
# else
#  define REAPER_FRAMEWORK_API __declspec(dllimport)
# endif
#else
# define REAPER_FRAMEWORK_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_FRAMEWORK_ABI_VERSION UINT32_C(1)
#define REAPER_FRAMEWORK_COUNT UINT32_C(20)
#define REAPER_FRAMEWORK_FUNCTIONS_PER_MODULE UINT32_C(6)
#define REAPER_FRAMEWORK_REGISTRY_API_FUNCTIONS UINT32_C(8)
#define REAPER_FRAMEWORK_MAX_PAYLOAD_BYTES UINT32_C(1048576)

typedef enum {
    REAPER_FRAMEWORK_OK = 0,
    REAPER_FRAMEWORK_INVALID_ARGUMENT = 1,
    REAPER_FRAMEWORK_NOT_FOUND = 2,
    REAPER_FRAMEWORK_ARITY_MISMATCH = 3,
    REAPER_FRAMEWORK_OUT_OF_RANGE = 4,
    REAPER_FRAMEWORK_DISPATCH_FAILED = 5
} ReaperFrameworkStatus;

typedef struct {
    const char *key;
    const char *name;
    uint32_t min_arity;
    uint32_t max_arity;
    const char *description;
} ReaperFrameworkFunction;

typedef struct {
    const char *id;
    const char *name;
    const char *domain;
    const char *feature_key;
    const char *maturity;
    const ReaperFrameworkFunction *functions;
    uint32_t function_count;
} ReaperFramework;

typedef struct {
    uint32_t registered_frameworks;
    uint32_t registered_function_contracts;
    uint32_t registry_api_functions;
    uint32_t executable_domain_handlers;
    uint32_t reaper_source_bindings;
} ReaperFrameworkRegistryStats;

/* A host owns this callback and its context. The registry validates the
 * selected operation and bounded buffers, but never loads or authorizes code. */
typedef ReaperFrameworkStatus (*ReaperFrameworkHostDispatch)(
    const ReaperFramework *framework,
    const ReaperFrameworkFunction *function,
    const void *request_payload,
    uint32_t request_size,
    void *response_payload,
    uint32_t response_capacity,
    uint32_t *response_size,
    void *host_context);

REAPER_FRAMEWORK_API uint32_t reaper_framework_abi_version(void);
REAPER_FRAMEWORK_API uint32_t reaper_framework_count(void);
REAPER_FRAMEWORK_API const ReaperFramework *reaper_framework_at(uint32_t index);
REAPER_FRAMEWORK_API const ReaperFramework *reaper_framework_find(const char *id_or_name);
REAPER_FRAMEWORK_API const ReaperFrameworkFunction *reaper_framework_function_find(
    const ReaperFramework *framework, const char *function_name);
REAPER_FRAMEWORK_API ReaperFrameworkStatus reaper_framework_validate_arity(
    const ReaperFramework *framework, const char *function_name,
    uint32_t argument_count, const ReaperFrameworkFunction **function_out);
REAPER_FRAMEWORK_API ReaperFrameworkStatus reaper_framework_registry_stats(
    ReaperFrameworkRegistryStats *stats);

/* Cross-language call gate. Payload encoding is defined by the calling
 * adapter. A non-OK callback result is normalized to DISPATCH_FAILED. */
REAPER_FRAMEWORK_API ReaperFrameworkStatus reaper_framework_invoke(
    const char *framework_id,
    const char *function_name,
    uint32_t argument_count,
    const void *request_payload,
    uint32_t request_size,
    void *response_payload,
    uint32_t response_capacity,
    uint32_t *response_size,
    ReaperFrameworkHostDispatch host_dispatch,
    void *host_context);

#ifdef __cplusplus
}
#endif

#endif
