#include "reaper/framework.h"

#include <stdio.h>
#include <string.h>

static const char *const CODEXNO_PROVIDES[] = {
    "framework.scaffold.v1",
    "framework.codegen.extension.v1",
    "framework.source-metadata.v1"
};
static const char *const CODEXNO_POINTS[] = {
    "compiler.backend",
    "source.generator",
    "workspace.scaffold"
};

static const char *const JOINT_BABY_PROVIDES[] = {
    "interop.c-abi.v1",
    "interop.dabi64.v1",
    "interop.wit.wasi-0.3"
};
static const char *const JOINT_BABY_POINTS[] = {
    "interop.language-adapter",
    "interop.host-abi",
    "interop.serialization"
};

static const ReaperFrameworkDependency CORREPSE_DEPENDENCIES[] = {
    { "allocate-purpose", { 1U, 0U, 0U }, { 0U, 0U, 0U } }
};
static const char *const CORREPSE_PROVIDES[] = {
    "composition.graph.v1",
    "composition.dependency-resolution.v1",
    "composition.lifecycle.v1"
};
static const char *const CORREPSE_POINTS[] = {
    "composition.node",
    "composition.policy",
    "framework.lifecycle"
};

static const char *const ALLOCATE_PURPOSE_PROVIDES[] = {
    "resource.budget.v1",
    "resource.pool.v1",
    "resource.allocation-policy.v1"
};
static const char *const ALLOCATE_PURPOSE_POINTS[] = {
    "resource.allocator",
    "resource.budget",
    "resource.pool"
};

static const char *const COLLILLIO_PROVIDES[] = {
    "telemetry.metrics.v1",
    "telemetry.traces.v1",
    "registry.public-stats.v1",
    "telemetry.otel-semantics.v1"
};
static const char *const COLLILLIO_POINTS[] = {
    "telemetry.exporter",
    "telemetry.processor",
    "registry.stats"
};

#define DECLARATIVE_MANIFEST(id_, name_, description_, provides_, points_) \
    { \
        .id = (id_), .name = (name_), .description = (description_), \
        .version = { 1U, 0U, 0U }, \
        .abi_major = REAPER_FRAMEWORK_ABI_MAJOR, \
        .abi_minor = REAPER_FRAMEWORK_ABI_MINOR, \
        .provides = (provides_), \
        .provides_count = sizeof(provides_) / sizeof((provides_)[0]), \
        .extension_points = (points_), \
        .extension_point_count = sizeof(points_) / sizeof((points_)[0]), \
        .flags = REAPER_FRAMEWORK_DECLARATIVE_ONLY \
    }

static const ReaperFrameworkManifest BUILTINS[] = {
    DECLARATIVE_MANIFEST(
        "codexno", "CodexNo",
        "Framework scaffolding, compiler extension contracts and source metadata.",
        CODEXNO_PROVIDES, CODEXNO_POINTS
    ),
    DECLARATIVE_MANIFEST(
        "joint-baby", "Joint Baby",
        "Explicit cross-language adapters and versioned host ABI contracts.",
        JOINT_BABY_PROVIDES, JOINT_BABY_POINTS
    ),
    {
        .id = "correpse",
        .name = "Correpse",
        .description = "Composable framework graphs, dependency resolution and lifecycle policies.",
        .version = { 1U, 0U, 0U },
        .abi_major = REAPER_FRAMEWORK_ABI_MAJOR,
        .abi_minor = REAPER_FRAMEWORK_ABI_MINOR,
        .dependencies = CORREPSE_DEPENDENCIES,
        .dependency_count = sizeof(CORREPSE_DEPENDENCIES) / sizeof(CORREPSE_DEPENDENCIES[0]),
        .provides = CORREPSE_PROVIDES,
        .provides_count = sizeof(CORREPSE_PROVIDES) / sizeof(CORREPSE_PROVIDES[0]),
        .extension_points = CORREPSE_POINTS,
        .extension_point_count = sizeof(CORREPSE_POINTS) / sizeof(CORREPSE_POINTS[0]),
        .flags = REAPER_FRAMEWORK_DECLARATIVE_ONLY
    },
    DECLARATIVE_MANIFEST(
        "allocate-purpose", "Allocate Purpose",
        "Resource budgets, allocation strategies and bounded memory-pool contracts.",
        ALLOCATE_PURPOSE_PROVIDES, ALLOCATE_PURPOSE_POINTS
    ),
    DECLARATIVE_MANIFEST(
        "collillio", "Collillio",
        "Public framework statistics and OpenTelemetry-aligned observability contracts.",
        COLLILLIO_PROVIDES, COLLILLIO_POINTS
    )
};

#undef DECLARATIVE_MANIFEST

static size_t bounded_length(const char *value, size_t maximum) {
    size_t length = 0U;
    if (value == NULL) return 0U;
    while (length <= maximum && value[length] != '\0') ++length;
    return length;
}

static int id_valid(const char *value) {
    const size_t length = bounded_length(value, REAPER_FRAMEWORK_ID_MAX);
    if (length == 0U || length > REAPER_FRAMEWORK_ID_MAX) return 0;
    if (!((value[0] >= 'a' && value[0] <= 'z') ||
          (value[0] >= '0' && value[0] <= '9'))) return 0;
    for (size_t i = 1U; i < length; ++i) {
        const char c = value[i];
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-'))
            return 0;
        if (c == '-' && value[i - 1U] == '-') return 0;
    }
    return value[length - 1U] != '-';
}

static int qualified_name_valid(const char *value) {
    const size_t length = bounded_length(value, REAPER_FRAMEWORK_TEXT_MAX);
    if (length == 0U || length > REAPER_FRAMEWORK_TEXT_MAX) return 0;
    if (!((value[0] >= 'a' && value[0] <= 'z') ||
          (value[0] >= '0' && value[0] <= '9'))) return 0;
    for (size_t i = 1U; i < length; ++i) {
        const char c = value[i];
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
              c == '-' || c == '_' || c == '.')) return 0;
        if ((c == '.' || c == '-' || c == '_') &&
            (value[i - 1U] == '.' || value[i - 1U] == '-' || value[i - 1U] == '_'))
            return 0;
    }
    return value[length - 1U] != '.' && value[length - 1U] != '-' &&
           value[length - 1U] != '_';
}

static int version_is_zero(ReaperFrameworkVersion version) {
    return version.major == 0U && version.minor == 0U && version.patch == 0U;
}

static int version_compare(ReaperFrameworkVersion left, ReaperFrameworkVersion right) {
    if (left.major != right.major) return left.major < right.major ? -1 : 1;
    if (left.minor != right.minor) return left.minor < right.minor ? -1 : 1;
    if (left.patch != right.patch) return left.patch < right.patch ? -1 : 1;
    return 0;
}

static int ascii_equal_ci(const char *left, const char *right) {
    if (left == NULL || right == NULL) return 0;
    while (*left != '\0' && *right != '\0') {
        char a = *left;
        char b = *right;
        if (a >= 'A' && a <= 'Z') a = (char)(a - 'A' + 'a');
        if (b >= 'A' && b <= 'Z') b = (char)(b - 'A' + 'a');
        if (a != b) return 0;
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

static void error_set(
    ReaperFrameworkError *error,
    ReaperFrameworkStatus code,
    const char *framework_id,
    const char *related_id,
    const char *message
) {
    if (error == NULL) return;
    error->code = code;
    (void)snprintf(error->framework_id, sizeof(error->framework_id), "%s",
                   framework_id != NULL ? framework_id : "");
    (void)snprintf(error->related_id, sizeof(error->related_id), "%s",
                   related_id != NULL ? related_id : "");
    (void)snprintf(error->message, sizeof(error->message), "%s",
                   message != NULL ? message : "");
}

static int string_list_valid(
    const char *const *items,
    size_t count,
    size_t maximum,
    int qualified
) {
    if (count > maximum || (count != 0U && items == NULL)) return 0;
    for (size_t i = 0U; i < count; ++i) {
        if (qualified ? !qualified_name_valid(items[i]) : !id_valid(items[i]))
            return 0;
        for (size_t j = 0U; j < i; ++j) {
            if (strcmp(items[i], items[j]) == 0) return 0;
        }
    }
    return 1;
}

ReaperFrameworkStatus reaper_framework_manifest_validate(
    const ReaperFrameworkManifest *manifest,
    ReaperFrameworkError *error
) {
    if (error != NULL) error_set(error, REAPER_FRAMEWORK_OK, NULL, NULL, "");
    if (manifest == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_ARGUMENT, NULL, NULL,
                  "manifest is required");
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    }
    if (!id_valid(manifest->id) ||
        bounded_length(manifest->name, REAPER_FRAMEWORK_NAME_MAX) == 0U ||
        bounded_length(manifest->name, REAPER_FRAMEWORK_NAME_MAX) >
            REAPER_FRAMEWORK_NAME_MAX ||
        bounded_length(manifest->description, REAPER_FRAMEWORK_TEXT_MAX) == 0U ||
        bounded_length(manifest->description, REAPER_FRAMEWORK_TEXT_MAX) >
            REAPER_FRAMEWORK_TEXT_MAX) {
        error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id, NULL,
                  "manifest identity, name or description is invalid");
        return REAPER_FRAMEWORK_INVALID_MANIFEST;
    }
    if (manifest->abi_major != REAPER_FRAMEWORK_ABI_MAJOR ||
        manifest->abi_minor > REAPER_FRAMEWORK_ABI_MINOR) {
        error_set(error, REAPER_FRAMEWORK_ABI_MISMATCH, manifest->id, NULL,
                  "framework host ABI is not supported");
        return REAPER_FRAMEWORK_ABI_MISMATCH;
    }
    if ((manifest->flags & ~REAPER_FRAMEWORK_DECLARATIVE_ONLY) != 0U ||
        (manifest->required_capabilities & ~REAPER_SYSTEM_CAP_KNOWN_MASK) != 0U) {
        error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id, NULL,
                  "manifest contains unknown flags or capability bits");
        return REAPER_FRAMEWORK_INVALID_MANIFEST;
    }
    if ((manifest->flags & REAPER_FRAMEWORK_DECLARATIVE_ONLY) != 0U) {
        if (manifest->start != NULL || manifest->stop != NULL) {
            error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id, NULL,
                      "declarative manifests cannot expose lifecycle callbacks");
            return REAPER_FRAMEWORK_INVALID_MANIFEST;
        }
    } else if (manifest->start == NULL || manifest->stop == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id, NULL,
                  "executable extensions require both start and stop callbacks");
        return REAPER_FRAMEWORK_INVALID_MANIFEST;
    }

    if (manifest->dependency_count > REAPER_FRAMEWORK_LIST_MAX ||
        (manifest->dependency_count != 0U && manifest->dependencies == NULL)) {
        error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id, NULL,
                  "dependency list is missing or exceeds the bound");
        return REAPER_FRAMEWORK_INVALID_MANIFEST;
    }
    for (size_t i = 0U; i < manifest->dependency_count; ++i) {
        const ReaperFrameworkDependency *dependency = &manifest->dependencies[i];
        if (!id_valid(dependency->id) || ascii_equal_ci(dependency->id, manifest->id) ||
            (!version_is_zero(dependency->maximum_version_exclusive) &&
             version_compare(dependency->minimum_version,
                             dependency->maximum_version_exclusive) >= 0)) {
            error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id,
                      dependency->id, "dependency identity or version range is invalid");
            return REAPER_FRAMEWORK_INVALID_MANIFEST;
        }
        for (size_t j = 0U; j < i; ++j) {
            if (strcmp(dependency->id, manifest->dependencies[j].id) == 0) {
                error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id,
                          dependency->id, "dependency is declared more than once");
                return REAPER_FRAMEWORK_INVALID_MANIFEST;
            }
        }
    }
    if (!string_list_valid(manifest->conflicts, manifest->conflict_count,
                           REAPER_FRAMEWORK_LIST_MAX, 0) ||
        !string_list_valid(manifest->provides, manifest->provides_count,
                           REAPER_FRAMEWORK_LIST_MAX, 1) ||
        !string_list_valid(manifest->extension_points,
                           manifest->extension_point_count,
                           REAPER_FRAMEWORK_LIST_MAX, 1)) {
        error_set(error, REAPER_FRAMEWORK_INVALID_MANIFEST, manifest->id, NULL,
                  "conflict, capability or extension-point list is invalid");
        return REAPER_FRAMEWORK_INVALID_MANIFEST;
    }
    return REAPER_FRAMEWORK_OK;
}

void reaper_framework_registry_init(
    ReaperFrameworkRegistry *registry,
    uint64_t granted_capabilities
) {
    if (registry == NULL) return;
    (void)memset(registry, 0, sizeof(*registry));
    registry->granted_capabilities = granted_capabilities;
}

static size_t registry_index(
    const ReaperFrameworkRegistry *registry,
    const char *id
) {
    if (registry == NULL || id == NULL) return REAPER_FRAMEWORK_REGISTRY_CAPACITY;
    for (size_t i = 0U; i < registry->count; ++i) {
        if (ascii_equal_ci(registry->entries[i].manifest->id, id)) return i;
    }
    return REAPER_FRAMEWORK_REGISTRY_CAPACITY;
}

ReaperFrameworkStatus reaper_framework_register(
    ReaperFrameworkRegistry *registry,
    const ReaperFrameworkManifest *manifest,
    ReaperFrameworkError *error
) {
    if (registry == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_ARGUMENT, NULL, NULL,
                  "registry is required");
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    }
    for (size_t i = 0U; i < registry->count; ++i) {
        if (registry->entries[i].state == REAPER_FRAMEWORK_STATE_ACTIVE) {
            error_set(error, REAPER_FRAMEWORK_INVALID_STATE, manifest != NULL ? manifest->id : NULL,
                      NULL, "cannot register while an extension is active");
            return REAPER_FRAMEWORK_INVALID_STATE;
        }
    }
    ReaperFrameworkStatus status = reaper_framework_manifest_validate(manifest, error);
    if (status != REAPER_FRAMEWORK_OK) return status;
    if (registry_index(registry, manifest->id) != REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
        error_set(error, REAPER_FRAMEWORK_DUPLICATE, manifest->id, NULL,
                  "framework ID is already registered");
        return REAPER_FRAMEWORK_DUPLICATE;
    }
    if (registry->count >= REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
        error_set(error, REAPER_FRAMEWORK_CAPACITY, manifest->id, NULL,
                  "framework registry capacity reached");
        return REAPER_FRAMEWORK_CAPACITY;
    }

    for (size_t i = 0U; i < registry->count; ++i) {
        if (registry->entries[i].state == REAPER_FRAMEWORK_STATE_RESOLVED ||
            registry->entries[i].state == REAPER_FRAMEWORK_STATE_STOPPED ||
            registry->entries[i].state == REAPER_FRAMEWORK_STATE_FAILED)
            registry->entries[i].state = REAPER_FRAMEWORK_STATE_REGISTERED;
    }
    registry->resolved_count = 0U;
    registry->entries[registry->count].manifest = manifest;
    registry->entries[registry->count].state = REAPER_FRAMEWORK_STATE_REGISTERED;
    ++registry->count;
    ++registry->totals.registrations;
    error_set(error, REAPER_FRAMEWORK_OK, NULL, NULL, "");
    return REAPER_FRAMEWORK_OK;
}

size_t reaper_framework_builtin_count(void) {
    return sizeof(BUILTINS) / sizeof(BUILTINS[0]);
}

const ReaperFrameworkManifest *reaper_framework_builtin_at(size_t index) {
    if (index >= reaper_framework_builtin_count()) return NULL;
    return &BUILTINS[index];
}

const ReaperFrameworkManifest *reaper_framework_builtin_find(const char *id_or_name) {
    if (id_or_name == NULL) return NULL;
    for (size_t i = 0U; i < reaper_framework_builtin_count(); ++i) {
        if (ascii_equal_ci(BUILTINS[i].id, id_or_name) ||
            ascii_equal_ci(BUILTINS[i].name, id_or_name)) return &BUILTINS[i];
    }
    return NULL;
}

ReaperFrameworkStatus reaper_framework_register_builtins(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
) {
    if (registry == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_ARGUMENT, NULL, NULL,
                  "registry is required");
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    }
    if (registry->count + reaper_framework_builtin_count() >
        REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
        error_set(error, REAPER_FRAMEWORK_CAPACITY, NULL, NULL,
                  "not enough registry capacity for built-in framework profiles");
        return REAPER_FRAMEWORK_CAPACITY;
    }
    for (size_t i = 0U; i < reaper_framework_builtin_count(); ++i) {
        if (registry_index(registry, BUILTINS[i].id) !=
            REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
            error_set(error, REAPER_FRAMEWORK_DUPLICATE, BUILTINS[i].id, NULL,
                      "built-in framework profile is already registered");
            return REAPER_FRAMEWORK_DUPLICATE;
        }
    }
    for (size_t i = 0U; i < reaper_framework_builtin_count(); ++i) {
        const ReaperFrameworkStatus status =
            reaper_framework_register(registry, &BUILTINS[i], error);
        if (status != REAPER_FRAMEWORK_OK) return status;
    }
    return REAPER_FRAMEWORK_OK;
}

static int version_in_range(
    ReaperFrameworkVersion candidate,
    const ReaperFrameworkDependency *dependency
) {
    if (version_compare(candidate, dependency->minimum_version) < 0) return 0;
    if (!version_is_zero(dependency->maximum_version_exclusive) &&
        version_compare(candidate, dependency->maximum_version_exclusive) >= 0)
        return 0;
    return 1;
}

ReaperFrameworkStatus reaper_framework_resolve(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
) {
    unsigned char indegree[REAPER_FRAMEWORK_REGISTRY_CAPACITY] = { 0U };
    unsigned char selected[REAPER_FRAMEWORK_REGISTRY_CAPACITY] = { 0U };
    if (registry == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_ARGUMENT, NULL, NULL,
                  "registry is required");
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    }
    for (size_t i = 0U; i < registry->count; ++i) {
        if (registry->entries[i].state == REAPER_FRAMEWORK_STATE_ACTIVE) {
            error_set(error, REAPER_FRAMEWORK_INVALID_STATE,
                      registry->entries[i].manifest->id, NULL,
                      "resolve requires all active extensions to be stopped");
            return REAPER_FRAMEWORK_INVALID_STATE;
        }
        registry->entries[i].state = REAPER_FRAMEWORK_STATE_REGISTERED;
    }
    registry->resolved_count = 0U;

    for (size_t i = 0U; i < registry->count; ++i) {
        const ReaperFrameworkManifest *manifest = registry->entries[i].manifest;
        if ((manifest->required_capabilities & ~registry->granted_capabilities) != 0U) {
            error_set(error, REAPER_FRAMEWORK_CAPABILITY_DENIED, manifest->id, NULL,
                      "required host capabilities were not granted");
            return REAPER_FRAMEWORK_CAPABILITY_DENIED;
        }
        indegree[i] = (unsigned char)manifest->dependency_count;
        for (size_t d = 0U; d < manifest->dependency_count; ++d) {
            const ReaperFrameworkDependency *dependency = &manifest->dependencies[d];
            const size_t dependency_index = registry_index(registry, dependency->id);
            if (dependency_index == REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
                error_set(error, REAPER_FRAMEWORK_DEPENDENCY_MISSING,
                          manifest->id, dependency->id,
                          "required framework dependency is not registered");
                return REAPER_FRAMEWORK_DEPENDENCY_MISSING;
            }
            if (!version_in_range(registry->entries[dependency_index].manifest->version,
                                  dependency)) {
                error_set(error, REAPER_FRAMEWORK_VERSION_MISMATCH,
                          manifest->id, dependency->id,
                          "dependency version is outside the declared range");
                return REAPER_FRAMEWORK_VERSION_MISMATCH;
            }
        }
        for (size_t c = 0U; c < manifest->conflict_count; ++c) {
            const size_t conflict_index = registry_index(registry, manifest->conflicts[c]);
            if (conflict_index != REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
                error_set(error, REAPER_FRAMEWORK_CONFLICT, manifest->id,
                          manifest->conflicts[c],
                          "conflicting frameworks cannot be resolved together");
                return REAPER_FRAMEWORK_CONFLICT;
            }
        }
    }

    for (size_t position = 0U; position < registry->count; ++position) {
        size_t next = REAPER_FRAMEWORK_REGISTRY_CAPACITY;
        for (size_t i = 0U; i < registry->count; ++i) {
            if (selected[i] == 0U && indegree[i] == 0U &&
                (next == REAPER_FRAMEWORK_REGISTRY_CAPACITY ||
                 strcmp(registry->entries[i].manifest->id,
                        registry->entries[next].manifest->id) < 0))
                next = i;
        }
        if (next == REAPER_FRAMEWORK_REGISTRY_CAPACITY) {
            for (size_t i = 0U; i < registry->count; ++i) {
                if (selected[i] == 0U) {
                    error_set(error, REAPER_FRAMEWORK_DEPENDENCY_CYCLE,
                              registry->entries[i].manifest->id, NULL,
                              "framework dependency graph contains a cycle");
                    return REAPER_FRAMEWORK_DEPENDENCY_CYCLE;
                }
            }
            break;
        }
        selected[next] = 1U;
        registry->resolved_order[registry->resolved_count++] = next;

        for (size_t i = 0U; i < registry->count; ++i) {
            const ReaperFrameworkManifest *manifest = registry->entries[i].manifest;
            if (selected[i] != 0U) continue;
            for (size_t d = 0U; d < manifest->dependency_count; ++d) {
                if (ascii_equal_ci(manifest->dependencies[d].id,
                                   registry->entries[next].manifest->id)) {
                    if (indegree[i] > 0U) --indegree[i];
                    break;
                }
            }
        }
    }

    if (registry->resolved_count != registry->count) {
        error_set(error, REAPER_FRAMEWORK_DEPENDENCY_CYCLE, NULL, NULL,
                  "framework dependency graph could not be ordered");
        registry->resolved_count = 0U;
        return REAPER_FRAMEWORK_DEPENDENCY_CYCLE;
    }
    for (size_t i = 0U; i < registry->count; ++i)
        registry->entries[i].state = REAPER_FRAMEWORK_STATE_RESOLVED;
    ++registry->totals.resolution_runs;
    error_set(error, REAPER_FRAMEWORK_OK, NULL, NULL, "");
    return REAPER_FRAMEWORK_OK;
}

ReaperFrameworkStatus reaper_framework_activate(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
) {
    unsigned char started[REAPER_FRAMEWORK_REGISTRY_CAPACITY] = { 0U };
    if (registry == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_ARGUMENT, NULL, NULL,
                  "registry is required");
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    }
    if (registry->resolved_count != registry->count) {
        error_set(error, REAPER_FRAMEWORK_INVALID_STATE, NULL, NULL,
                  "resolve the complete registry before activation");
        return REAPER_FRAMEWORK_INVALID_STATE;
    }
    for (size_t i = 0U; i < registry->count; ++i) {
        if (registry->entries[i].state != REAPER_FRAMEWORK_STATE_RESOLVED) {
            error_set(error, REAPER_FRAMEWORK_INVALID_STATE,
                      registry->entries[i].manifest->id, NULL,
                      "every registry entry must be resolved before activation");
            return REAPER_FRAMEWORK_INVALID_STATE;
        }
    }
    ++registry->totals.activation_runs;

    for (size_t position = 0U; position < registry->resolved_count; ++position) {
        const size_t index = registry->resolved_order[position];
        ReaperFrameworkEntry *entry = &registry->entries[index];
        const ReaperFrameworkManifest *manifest = entry->manifest;
        if ((manifest->flags & REAPER_FRAMEWORK_DECLARATIVE_ONLY) != 0U)
            continue;
        if (manifest->start(manifest->context, manifest->required_capabilities) != 0) {
            entry->state = REAPER_FRAMEWORK_STATE_FAILED;
            ++registry->totals.callback_failures;
            for (size_t rollback = position; rollback > 0U; --rollback) {
                const size_t previous_position = rollback - 1U;
                if (started[previous_position] != 0U) {
                    ReaperFrameworkEntry *previous =
                        &registry->entries[registry->resolved_order[previous_position]];
                    if (previous->manifest->stop(previous->manifest->context) == 0) {
                        previous->state = REAPER_FRAMEWORK_STATE_STOPPED;
                        ++registry->totals.rollback_stops;
                    } else {
                        previous->state = REAPER_FRAMEWORK_STATE_FAILED;
                        ++registry->totals.callback_failures;
                    }
                }
            }
            error_set(error, REAPER_FRAMEWORK_CALLBACK_FAILED, manifest->id, NULL,
                      "framework start callback failed; prior starts were rolled back");
            return REAPER_FRAMEWORK_CALLBACK_FAILED;
        }
        entry->state = REAPER_FRAMEWORK_STATE_ACTIVE;
        started[position] = 1U;
    }
    error_set(error, REAPER_FRAMEWORK_OK, NULL, NULL, "");
    return REAPER_FRAMEWORK_OK;
}

ReaperFrameworkStatus reaper_framework_deactivate(
    ReaperFrameworkRegistry *registry,
    ReaperFrameworkError *error
) {
    ReaperFrameworkStatus result = REAPER_FRAMEWORK_OK;
    if (registry == NULL) {
        error_set(error, REAPER_FRAMEWORK_INVALID_ARGUMENT, NULL, NULL,
                  "registry is required");
        return REAPER_FRAMEWORK_INVALID_ARGUMENT;
    }
    ++registry->totals.deactivation_runs;
    for (size_t position = registry->resolved_count; position > 0U; --position) {
        ReaperFrameworkEntry *entry =
            &registry->entries[registry->resolved_order[position - 1U]];
        if (entry->state != REAPER_FRAMEWORK_STATE_ACTIVE) continue;
        if (entry->manifest->stop(entry->manifest->context) != 0) {
            entry->state = REAPER_FRAMEWORK_STATE_FAILED;
            ++registry->totals.callback_failures;
            if (result == REAPER_FRAMEWORK_OK) {
                result = REAPER_FRAMEWORK_CALLBACK_FAILED;
                error_set(error, result, entry->manifest->id, NULL,
                          "framework stop callback failed");
            }
        } else {
            entry->state = REAPER_FRAMEWORK_STATE_STOPPED;
        }
    }
    if (result == REAPER_FRAMEWORK_OK)
        error_set(error, REAPER_FRAMEWORK_OK, NULL, NULL, "");
    return result;
}

size_t reaper_framework_registry_count(const ReaperFrameworkRegistry *registry) {
    return registry == NULL ? 0U : registry->count;
}

const ReaperFrameworkEntry *reaper_framework_registry_at(
    const ReaperFrameworkRegistry *registry, size_t index
) {
    if (registry == NULL || index >= registry->count) return NULL;
    return &registry->entries[index];
}

const ReaperFrameworkEntry *reaper_framework_registry_find(
    const ReaperFrameworkRegistry *registry, const char *id
) {
    const size_t index = registry_index(registry, id);
    if (index == REAPER_FRAMEWORK_REGISTRY_CAPACITY) return NULL;
    return &registry->entries[index];
}

void reaper_framework_stats_snapshot(
    const ReaperFrameworkRegistry *registry,
    ReaperFrameworkStats *stats
) {
    if (stats == NULL) return;
    (void)memset(stats, 0, sizeof(*stats));
    if (registry == NULL) return;
    *stats = registry->totals;
    stats->registered = registry->count;
    for (size_t i = 0U; i < registry->count; ++i) {
        switch (registry->entries[i].state) {
        case REAPER_FRAMEWORK_STATE_REGISTERED: ++stats->registered; break;
        case REAPER_FRAMEWORK_STATE_RESOLVED: ++stats->resolved; break;
        case REAPER_FRAMEWORK_STATE_ACTIVE: ++stats->active; break;
        case REAPER_FRAMEWORK_STATE_STOPPED: ++stats->stopped; break;
        case REAPER_FRAMEWORK_STATE_FAILED: ++stats->failed; break;
        default: break;
        }
    }
    stats->registered = registry->count;
}

const char *reaper_framework_status_name(ReaperFrameworkStatus status) {
    switch (status) {
    case REAPER_FRAMEWORK_OK: return "ok";
    case REAPER_FRAMEWORK_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_FRAMEWORK_INVALID_MANIFEST: return "invalid-manifest";
    case REAPER_FRAMEWORK_ABI_MISMATCH: return "abi-mismatch";
    case REAPER_FRAMEWORK_DUPLICATE: return "duplicate";
    case REAPER_FRAMEWORK_NOT_FOUND: return "not-found";
    case REAPER_FRAMEWORK_CAPACITY: return "capacity";
    case REAPER_FRAMEWORK_CAPABILITY_DENIED: return "capability-denied";
    case REAPER_FRAMEWORK_DEPENDENCY_MISSING: return "dependency-missing";
    case REAPER_FRAMEWORK_VERSION_MISMATCH: return "version-mismatch";
    case REAPER_FRAMEWORK_CONFLICT: return "conflict";
    case REAPER_FRAMEWORK_DEPENDENCY_CYCLE: return "dependency-cycle";
    case REAPER_FRAMEWORK_INVALID_STATE: return "invalid-state";
    case REAPER_FRAMEWORK_CALLBACK_FAILED: return "callback-failed";
    default: return "unknown";
    }
}

const char *reaper_framework_state_name(ReaperFrameworkState state) {
    switch (state) {
    case REAPER_FRAMEWORK_STATE_REGISTERED: return "registered";
    case REAPER_FRAMEWORK_STATE_RESOLVED: return "resolved";
    case REAPER_FRAMEWORK_STATE_ACTIVE: return "active";
    case REAPER_FRAMEWORK_STATE_STOPPED: return "stopped";
    case REAPER_FRAMEWORK_STATE_FAILED: return "failed";
    default: return "unknown";
    }
}
