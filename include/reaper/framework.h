#ifndef REAPER_FRAMEWORK_H
#define REAPER_FRAMEWORK_H

#include <stddef.h>
#include <stdint.h>
#include "reaper/system.h"

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_FRAMEWORK_ABI_MAJOR 1U
#define REAPER_FRAMEWORK_ABI_MINOR 0U
#define REAPER_FRAMEWORK_REGISTRY_CAPACITY 32U
#define REAPER_FRAMEWORK_ID_MAX 64U
#define REAPER_FRAMEWORK_NAME_MAX 96U
#define REAPER_FRAMEWORK_TEXT_MAX 512U
#define REAPER_FRAMEWORK_LIST_MAX 32U
#define REAPER_FRAMEWORK_DECLARATIVE_ONLY UINT32_C(1)

typedef struct {
    uint32_t major;
    uint32_t minor;
    uint32_t patch;
} ReaperFrameworkVersion;

typedef struct {
    const char *id;
    ReaperFrameworkVersion minimum_version;
    /* An all-zero maximum means unbounded. Otherwise the maximum is exclusive. */
    ReaperFrameworkVersion maximum_version_exclusive;
} ReaperFrameworkDependency;

typedef int (*ReaperFrameworkStart)(void *context, uint64_t granted_capabilities);
typedef int (*ReaperFrameworkStop)(void *context);

typedef struct {
    const char *id;
    const char *name;
    const char *description;
    ReaperFrameworkVersion version;
    uint32_t abi_major;
    uint32_t abi_minor;
    const ReaperFrameworkDependency *dependencies;
    size_t dependency_count;
    const char *const *conflicts;
    size_t conflict_count;
    const char *const *provides;
    size_t provides_count;
    const char *const *extension_points;
    size_t extension_point_count;
    uint64_t required_capabilities;
    uint32_t flags;
    ReaperFrameworkStart start;
    ReaperFrameworkStop stop;
    void *context;
} ReaperFrameworkManifest;

typedef enum {
    REAPER_FRAMEWORK_OK = 0,
    REAPER_FRAMEWORK_INVALID_ARGUMENT = -1,
    REAPER_FRAMEWORK_INVALID_MANIFEST = -2,
    REAPER_FRAMEWORK_ABI_MISMATCH = -3,
    REAPER_FRAMEWORK_DUPLICATE = -4,
    REAPER_FRAMEWORK_NOT_FOUND = -5,
    REAPER_FRAMEWORK_CAPACITY = -6,
    REAPER_FRAMEWORK_CAPABILITY_DENIED = -7,
    REAPER_FRAMEWORK_DEPENDENCY_MISSING = -8,
    REAPER_FRAMEWORK_VERSION_MISMATCH = -9,
    REAPER_FRAMEWORK_CONFLICT = -10,
    REAPER_FRAMEWORK_DEPENDENCY_CYCLE = -11,
    REAPER_FRAMEWORK_INVALID_STATE = -12,
    REAPER_FRAMEWORK_CALLBACK_FAILED = -13
} ReaperFrameworkStatus;

typedef enum {
    REAPER_FRAMEWORK_STATE_REGISTERED = 1,
    REAPER_FRAMEWORK_STATE_RESOLVED = 2,
    REAPER_FRAMEWORK_STATE_ACTIVE = 3,
    REAPER_FRAMEWORK_STATE_STOPPED = 4,
    REAPER_FRAMEWORK_STATE_FAILED = 5
} ReaperFrameworkState;

typedef struct {
    ReaperFrameworkStatus code;
    char framework_id[REAPER_FRAMEWORK_ID_MAX + 1U];
    char related_id[REAPER_FRAMEWORK_ID_MAX + 1U];
    char message[192];
} ReaperFrameworkError;

typedef struct {
    const ReaperFrameworkManifest *manifest;
    ReaperFrameworkState state;
} ReaperFrameworkEntry;

typedef struct {
    uint64_t registrations;
    uint64_t resolution_runs;
    uint64_t activation_runs;
    uint64_t deactivation_runs;
    uint64_t callback_failures;
    uint64_t rollback_stops;
    size_t total;
    size_t registered;
    size_t resolved;
    size_t active;
    size_t stopped;
    size_t failed;
} ReaperFrameworkStats;

/*
 * Caller-owned, allocation-free registry. Manifest strings, arrays, callback
 * code and callback context must outlive the registry entry. Serialize access
 * externally; this core deliberately contains no hidden global locks.
 */
typedef struct {
    ReaperFrameworkEntry entries[REAPER_FRAMEWORK_REGISTRY_CAPACITY];
    size_t count;
    size_t resolved_order[REAPER_FRAMEWORK_REGISTRY_CAPACITY];
    size_t resolved_count;
    uint64_t granted_capabilities;
    ReaperFrameworkStats totals;
} ReaperFrameworkRegistry;

ReaperFrameworkStatus reaper_framework_manifest_validate(
    const ReaperFrameworkManifest *manifest,
    ReaperFrameworkError *error
);

void reaper_framework_registry_init(
    ReaperFrameworkRegistry *registry,
    uint64_t granted_capabilities
);

ReaperFrameworkStatus reaper_framework_register(
    ReaperFrameworkRegistry *registry,
    const ReaperFrameworkManifest *manifest,
    ReaperFrameworkError *error
);

ReaperFrameworkStatus reaper_framework_register_builtins(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
);

ReaperFrameworkStatus reaper_framework_resolve(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
);

ReaperFrameworkStatus reaper_framework_activate(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
);

ReaperFrameworkStatus reaper_framework_deactivate(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
);

size_t reaper_framework_builtin_count(void);
const ReaperFrameworkManifest *reaper_framework_builtin_at(size_t index);
const ReaperFrameworkManifest *reaper_framework_builtin_find(const char *id_or_name);

size_t reaper_framework_registry_count(const ReaperFrameworkRegistry *registry);
const ReaperFrameworkEntry *reaper_framework_registry_at(
    const ReaperFrameworkRegistry *registry, size_t index
);
const ReaperFrameworkEntry *reaper_framework_registry_find(
    const ReaperFrameworkRegistry *registry, const char *id
);
const ReaperFrameworkEntry *reaper_framework_resolved_at(
    const ReaperFrameworkRegistry *registry, size_t position
);

void reaper_framework_stats_snapshot(
    const ReaperFrameworkRegistry *registry,
    ReaperFrameworkStats *stats
);

const char *reaper_framework_status_name(ReaperFrameworkStatus status);
const char *reaper_framework_state_name(ReaperFrameworkState state);

#ifdef __cplusplus
}
#endif

#endif
