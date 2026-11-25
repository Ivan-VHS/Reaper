#include "reaper/system_runtime.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

#define OP(id_, subsystem_, operation_, effects_, adapter_, profiles_, maturity_, boundary_) \
    { id_, subsystem_, operation_, effects_, adapter_, profiles_, maturity_, boundary_ }
#define HOSTED (REAPER_SYSTEM_PROFILE_HOSTED | REAPER_SYSTEM_PROFILE_SIMULATOR)
#define HOSTED_KERNEL (HOSTED | REAPER_SYSTEM_PROFILE_KERNEL)
#define KERNEL_BOOT (REAPER_SYSTEM_PROFILE_KERNEL | REAPER_SYSTEM_PROFILE_BOOT)

static const ReaperSystemOperation OPERATIONS[REAPER_SYSTEM_OPERATION_COUNT] = {
    OP("111", "system-services", "service.daemonize",
       REAPER_SYSTEM_EFFECT_PROCESS_CONTROL | REAPER_SYSTEM_EFFECT_SERVICE_CONTROL,
       REAPER_SYSTEM_ADAPTER_SERVICE_MANAGER, HOSTED, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "The host service manager owns process detachment, session setup and descriptor policy."),
    OP("112", "system-services", "service.lifecycle_hooks",
       REAPER_SYSTEM_EFFECT_SERVICE_CONTROL,
       REAPER_SYSTEM_ADAPTER_SERVICE_MANAGER, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "Callbacks require an owning service object, stable lifetime and serialized state transitions."),
    OP("113", "system-services", "scheduler.cron_schedule",
       REAPER_SYSTEM_EFFECT_SCHEDULE,
       REAPER_SYSTEM_ADAPTER_SCHEDULER, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Cron syntax validation is native; timer persistence and dispatch belong to a scheduler adapter."),
    OP("114", "system-services", "logging.append",
       REAPER_SYSTEM_EFFECT_LOG_WRITE,
       REAPER_SYSTEM_ADAPTER_JOURNAL, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "A bounded SPSC record queue is native; durable journal storage and rotation require a writer."),
    OP("115", "system-services", "service.start_unit",
       REAPER_SYSTEM_EFFECT_SERVICE_CONTROL | REAPER_SYSTEM_EFFECT_PROCESS_CONTROL,
       REAPER_SYSTEM_ADAPTER_INIT, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Dependency ordering is native; process creation and readiness checks require an init adapter."),
    OP("116", "system-services", "system.graceful_shutdown",
       REAPER_SYSTEM_EFFECT_PROCESS_CONTROL | REAPER_SYSTEM_EFFECT_POWER_CONTROL,
       REAPER_SYSTEM_ADAPTER_POWER, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "Shutdown sequencing, deadlines, vetoes and storage flush results must be owned by the OS."),
    OP("117", "system-services", "system.emergency_mode",
       REAPER_SYSTEM_EFFECT_BOOT_CONTROL | REAPER_SYSTEM_EFFECT_PROCESS_CONTROL,
       REAPER_SYSTEM_ADAPTER_BOOT, KERNEL_BOOT, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "Recovery shell scheduling and kernel halt policy are platform responsibilities."),
    OP("118", "hardware-services", "device.handle_event",
       REAPER_SYSTEM_EFFECT_DEVICE_DISCOVERY | REAPER_SYSTEM_EFFECT_DRIVER_CONTROL,
       REAPER_SYSTEM_ADAPTER_DEVICE_MANAGER, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "Device identity, driver binding and node publication require a trusted device manager."),
    OP("119", "hardware-services", "firmware.load",
       REAPER_SYSTEM_EFFECT_FIRMWARE_WRITE | REAPER_SYSTEM_EFFECT_DEVICE_DISCOVERY,
       REAPER_SYSTEM_ADAPTER_FIRMWARE, KERNEL_BOOT, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Image bounds and signature verification callback are native; flashing requires a signed device adapter."),
    OP("120", "hardware-services", "acpi.parse",
       REAPER_SYSTEM_EFFECT_ACPI_READ,
       REAPER_SYSTEM_ADAPTER_ACPI, KERNEL_BOOT, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "ACPI table length and checksum validation are native; mapping and AML execution are not."),
    OP("121", "ai-runtime", "ai.npu_initialize",
       REAPER_SYSTEM_EFFECT_NPU_ACCESS | REAPER_SYSTEM_EFFECT_DEVICE_DISCOVERY,
       REAPER_SYSTEM_ADAPTER_NPU, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "NPU discovery, allocation and command submission require a device-specific driver."),
    OP("122", "ai-runtime", "ai.tensor_matmul",
       REAPER_SYSTEM_EFFECT_AI_COMPUTE | REAPER_SYSTEM_EFFECT_DMA,
       REAPER_SYSTEM_ADAPTER_AI_RUNTIME, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Tensor shape, type and storage validation are native; execution requires a CPU/GPU/NPU backend."),
    OP("123", "ai-runtime", "ai.inference",
       REAPER_SYSTEM_EFFECT_AI_COMPUTE,
       REAPER_SYSTEM_ADAPTER_AI_RUNTIME, HOSTED_KERNEL, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "Operator dispatch, graph scheduling and tensor allocation require a concrete compute backend."),
    OP("124", "ai-runtime", "ai.model_load_onnx",
       REAPER_SYSTEM_EFFECT_MODEL_READ | REAPER_SYSTEM_EFFECT_FILESYSTEM_READ,
       REAPER_SYSTEM_ADAPTER_MODEL_LOADER, HOSTED, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "ONNX protobuf parsing, opset validation and operator lowering are not implemented in this core."),
    OP("125", "ai-runtime", "ai.private_inference",
       REAPER_SYSTEM_EFFECT_AI_COMPUTE | REAPER_SYSTEM_EFFECT_CRYPTO,
       REAPER_SYSTEM_ADAPTER_HE, HOSTED, REAPER_SYSTEM_MATURITY_CONTRACT_ONLY,
       "Homomorphic evaluation requires a reviewed cryptographic backend and explicit key lifecycle."),
    OP("126", "isolation", "container.create",
       REAPER_SYSTEM_EFFECT_PROCESS_ISOLATION | REAPER_SYSTEM_EFFECT_FILESYSTEM_MOUNT,
       REAPER_SYSTEM_ADAPTER_CONTAINER, KERNEL_BOOT, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Isolation-policy validation is native; namespaces, cgroups, mounts and seccomp require kernel support."),
    OP("127", "virtualization", "virtualization.create_vm",
       REAPER_SYSTEM_EFFECT_VIRTUALIZATION,
       REAPER_SYSTEM_ADAPTER_HYPERVISOR, REAPER_SYSTEM_PROFILE_HYPERVISOR,
       REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "VM resource-profile validation is native; vCPU execution and VM exits require a hypervisor backend."),
    OP("128", "packages", "package.install_sandboxed",
       REAPER_SYSTEM_EFFECT_PACKAGE_INSTALL | REAPER_SYSTEM_EFFECT_FILESYSTEM_WRITE,
       REAPER_SYSTEM_ADAPTER_PACKAGE, HOSTED, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Manifest/signature validation is native through a verifier callback; sandbox installation is adapter-owned."),
    OP("129", "packages", "package.install",
       REAPER_SYSTEM_EFFECT_PACKAGE_INSTALL | REAPER_SYSTEM_EFFECT_FILESYSTEM_WRITE,
       REAPER_SYSTEM_ADAPTER_PACKAGE, HOSTED, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Package identity and signature validation are native; atomic deployment and rollback require a package adapter."),
    OP("130", "build-infrastructure", "build.cross_compile",
       REAPER_SYSTEM_EFFECT_TOOLCHAIN_EXEC | REAPER_SYSTEM_EFFECT_FILESYSTEM_READ |
           REAPER_SYSTEM_EFFECT_FILESYSTEM_WRITE,
       REAPER_SYSTEM_ADAPTER_TOOLCHAIN, HOSTED, REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE,
       "Target identity validation is native; tool discovery and execution belong to an argv-based toolchain adapter.")
};

static ReaperSystemStatus fail(
    ReaperSystemError *error, ReaperSystemStatus status, const char *message
) {
    if (error != NULL) {
        error->status = status;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

static void clear_error(ReaperSystemError *error) {
    if (error != NULL) {
        error->status = REAPER_SYSTEM_OK;
        error->message[0] = '\0';
    }
}

static int equal_text(const char *left, const char *right) {
    if (left == NULL || right == NULL) return 0;
    while (*left != '\0' && *right != '\0') {
        if (tolower((unsigned char)*left) != tolower((unsigned char)*right)) return 0;
        ++left;
        ++right;
    }
    return *left == '\0' && *right == '\0';
}

size_t reaper_system_operation_count(void) {
    return REAPER_SYSTEM_OPERATION_COUNT;
}

const ReaperSystemOperation *reaper_system_operation_at(size_t index) {
    return index < REAPER_SYSTEM_OPERATION_COUNT ? &OPERATIONS[index] : NULL;
}

const ReaperSystemOperation *reaper_system_operation_find(const char *id_or_operation) {
    if (id_or_operation == NULL || id_or_operation[0] == '\0') return NULL;
    for (size_t index = 0U; index < REAPER_SYSTEM_OPERATION_COUNT; ++index) {
        if (equal_text(OPERATIONS[index].id, id_or_operation) ||
            equal_text(OPERATIONS[index].operation, id_or_operation))
            return &OPERATIONS[index];
    }
    return NULL;
}

ReaperSystemStatus reaper_system_authorize(
    const ReaperSystemOperation *operation, uint32_t runtime_profile,
    uint64_t granted_effects, uint64_t available_adapters,
    ReaperSystemAuthorization *authorization, ReaperSystemError *error
) {
    clear_error(error);
    if (authorization != NULL) {
        authorization->authorized = 0;
        authorization->dispatchable = 0;
        authorization->maturity = REAPER_SYSTEM_MATURITY_CONTRACT_ONLY;
    }
    if (operation == NULL || authorization == NULL || runtime_profile == 0U ||
        (runtime_profile & (runtime_profile - 1U)) != 0U)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "operation, one runtime profile and output are required");

    int owned_entry = 0;
    for (size_t index = 0U; index < REAPER_SYSTEM_OPERATION_COUNT; ++index) {
        if (operation == &OPERATIONS[index]) {
            owned_entry = 1;
            break;
        }
    }
    if (!owned_entry)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "operation must come from the canonical registry");
    if ((operation->allowed_profiles & runtime_profile) == 0U)
        return fail(error, REAPER_SYSTEM_PROFILE_DENIED,
                    "operation is not valid in this runtime profile");
    if ((granted_effects & operation->required_effects) != operation->required_effects)
        return fail(error, REAPER_SYSTEM_PERMISSION_DENIED,
                    "one or more required effects were not granted");
    if ((available_adapters & operation->required_adapter) != operation->required_adapter)
        return fail(error, REAPER_SYSTEM_ADAPTER_UNAVAILABLE,
                    "required host or platform adapter is unavailable");

    authorization->authorized = 1;
    authorization->dispatchable = 0;
    authorization->maturity = operation->maturity;
    return REAPER_SYSTEM_OK;
}

static int parse_decimal(const char **cursor, unsigned maximum, unsigned *value) {
    const char *position = *cursor;
    unsigned parsed = 0U;
    if (!isdigit((unsigned char)*position)) return 0;
    do {
        unsigned digit = (unsigned)(*position - '0');
        if (digit > maximum || parsed > (maximum - digit) / 10U) return 0;
        parsed = parsed * 10U + digit;
        ++position;
    } while (isdigit((unsigned char)*position));
    *cursor = position;
    *value = parsed;
    return 1;
}

static int parse_cron_item(const char **cursor, unsigned minimum, unsigned maximum) {
    unsigned start = minimum, end = maximum, step = 1U;
    int wildcard = 0;
    if (**cursor == '*') {
        wildcard = 1;
        ++*cursor;
    } else {
        if (!parse_decimal(cursor, maximum, &start) || start < minimum) return 0;
        end = start;
        if (**cursor == '-') {
            ++*cursor;
            if (!parse_decimal(cursor, maximum, &end) || end < start) return 0;
        }
    }
    if (**cursor == '/') {
        ++*cursor;
        if (!parse_decimal(cursor, maximum, &step) || step == 0U) return 0;
        if (wildcard) {
            start = minimum;
            end = maximum;
        } else if (start == end) {
            end = maximum;
        }
    }
    return start >= minimum && end <= maximum && start <= end &&
           (**cursor == '\0' || **cursor == ',');
}

static int parse_cron_field(const char *field, unsigned minimum, unsigned maximum) {
    const char *cursor = field;
    if (field == NULL || field[0] == '\0') return 0;
    while (*cursor != '\0') {
        if (!parse_cron_item(&cursor, minimum, maximum)) return 0;
        if (*cursor == ',') {
            ++cursor;
            if (*cursor == '\0') return 0;
        } else {
            return *cursor == '\0';
        }
    }
    return 1;
}

ReaperSystemStatus reaper_system_cron_validate(
    const char *expression, ReaperSystemError *error
) {
    clear_error(error);
    if (expression == NULL || expression[0] == '\0')
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, "cron expression is required");
    static const unsigned minimums[5] = { 0U, 0U, 1U, 1U, 0U };
    static const unsigned maximums[5] = { 59U, 23U, 31U, 12U, 7U };
    const char *cursor = expression;
    for (size_t field = 0U; field < 5U; ++field) {
        while (*cursor == ' ' || *cursor == '\t') ++cursor;
        const char *start = cursor;
        while (*cursor != '\0' && *cursor != ' ' && *cursor != '\t') ++cursor;
        size_t length = (size_t)(cursor - start);
        if (length == 0U || length >= 64U)
            return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                        "cron expression must contain five bounded fields");
        char token[64];
        memcpy(token, start, length);
        token[length] = '\0';
        if (!parse_cron_field(token, minimums[field], maximums[field]))
            return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                        "cron field contains an invalid value, range, list or step");
    }
    while (*cursor == ' ' || *cursor == '\t') ++cursor;
    if (*cursor != '\0')
        return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                    "cron expression must contain exactly five fields");
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_dependency_order(
    size_t node_count, const uint8_t *dependencies, size_t dependency_bytes,
    size_t *order, size_t order_capacity, ReaperSystemError *error
) {
    clear_error(error);
    if (node_count == 0U || node_count > REAPER_SYSTEM_MAX_DEPENDENCIES ||
        dependencies == NULL || order == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "dependency matrix, order output and 1..256 nodes are required");
    if (node_count > SIZE_MAX / node_count)
        return fail(error, REAPER_SYSTEM_OVERFLOW, "dependency matrix size overflows");
    size_t required_bytes = node_count * node_count;
    if (dependency_bytes < required_bytes || order_capacity < node_count)
        return fail(error, REAPER_SYSTEM_CAPACITY,
                    "dependency matrix or order output is too small");

    size_t indegree[REAPER_SYSTEM_MAX_DEPENDENCIES] = { 0U };
    size_t candidate_order[REAPER_SYSTEM_MAX_DEPENDENCIES] = { 0U };
    uint8_t emitted[REAPER_SYSTEM_MAX_DEPENDENCIES] = { 0U };
    for (size_t node = 0U; node < node_count; ++node) {
        for (size_t dependency = 0U; dependency < node_count; ++dependency) {
            uint8_t edge = dependencies[node * node_count + dependency];
            if (edge > 1U)
                return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                            "dependency matrix values must be zero or one");
            if (edge != 0U) ++indegree[node];
        }
    }
    for (size_t output_index = 0U; output_index < node_count; ++output_index) {
        size_t selected = node_count;
        for (size_t node = 0U; node < node_count; ++node) {
            if (emitted[node] == 0U && indegree[node] == 0U) {
                selected = node;
                break;
            }
        }
        if (selected == node_count)
            return fail(error, REAPER_SYSTEM_DEPENDENCY_CYCLE,
                        "service dependency graph contains a cycle");
        candidate_order[output_index] = selected;
        emitted[selected] = 1U;
        for (size_t dependent = 0U; dependent < node_count; ++dependent)
            if (dependencies[dependent * node_count + selected] != 0U)
                --indegree[dependent];
    }
    memcpy(order, candidate_order, node_count * sizeof(*order));
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_log_ring_init(
    ReaperSystemLogRing *ring, ReaperSystemLogRecord *storage,
    size_t capacity, ReaperSystemError *error
) {
    clear_error(error);
    if (ring == NULL || storage == NULL || capacity < 2U)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "log ring requires storage and capacity of at least two");
    ring->records = storage;
    ring->capacity = capacity;
    atomic_init(&ring->head, 0U);
    atomic_init(&ring->tail, 0U);
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_log_ring_push(
    ReaperSystemLogRing *ring, const ReaperSystemLogRecord *record,
    ReaperSystemError *error
) {
    clear_error(error);
    if (ring == NULL || record == NULL || ring->records == NULL || ring->capacity < 2U)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "initialized ring and record are required");
    if (record->length > REAPER_SYSTEM_LOG_MESSAGE_MAX)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "log message exceeds the fixed record payload");
    size_t head = atomic_load_explicit(&ring->head, memory_order_relaxed);
    size_t next = head + 1U;
    if (next == ring->capacity) next = 0U;
    if (next == atomic_load_explicit(&ring->tail, memory_order_acquire))
        return fail(error, REAPER_SYSTEM_QUEUE_FULL, "log ring is full");
    ReaperSystemLogRecord copy = *record;
    if (copy.length < REAPER_SYSTEM_LOG_MESSAGE_MAX)
        copy.message[copy.length] = '\0';
    ring->records[head] = copy;
    atomic_store_explicit(&ring->head, next, memory_order_release);
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_log_ring_pop(
    ReaperSystemLogRing *ring, ReaperSystemLogRecord *record,
    ReaperSystemError *error
) {
    clear_error(error);
    if (ring == NULL || record == NULL || ring->records == NULL || ring->capacity < 2U)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "initialized ring and output record are required");
    size_t tail = atomic_load_explicit(&ring->tail, memory_order_relaxed);
    if (tail == atomic_load_explicit(&ring->head, memory_order_acquire))
        return fail(error, REAPER_SYSTEM_QUEUE_EMPTY, "log ring is empty");
    *record = ring->records[tail];
    size_t next = tail + 1U;
    if (next == ring->capacity) next = 0U;
    atomic_store_explicit(&ring->tail, next, memory_order_release);
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_acpi_table_validate(
    const uint8_t *table, size_t available_bytes, size_t maximum_table_bytes,
    size_t *table_bytes, ReaperSystemError *error
) {
    clear_error(error);
    if (table_bytes != NULL) *table_bytes = 0U;
    if (table == NULL || table_bytes == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "ACPI table bytes and length output are required");
    if (available_bytes < REAPER_SYSTEM_ACPI_HEADER_SIZE)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "ACPI table is shorter than the standard header");
    uint32_t declared = (uint32_t)table[4] | ((uint32_t)table[5] << 8) |
        ((uint32_t)table[6] << 16) | ((uint32_t)table[7] << 24);
    if (declared < REAPER_SYSTEM_ACPI_HEADER_SIZE ||
        (size_t)declared > available_bytes || (size_t)declared > maximum_table_bytes)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "ACPI declared length exceeds the available or configured bounds");
    uint8_t checksum = 0U;
    for (size_t index = 0U; index < (size_t)declared; ++index)
        checksum = (uint8_t)(checksum + table[index]);
    if (checksum != 0U)
        return fail(error, REAPER_SYSTEM_CHECKSUM_INVALID,
                    "ACPI table checksum does not match");
    *table_bytes = (size_t)declared;
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_firmware_verify(
    const uint8_t *image, size_t image_bytes, size_t maximum_image_bytes,
    const uint8_t *signature, size_t signature_bytes,
    ReaperSystemSignatureVerifier verifier, void *context,
    ReaperSystemError *error
) {
    clear_error(error);
    if (image == NULL || signature == NULL || verifier == NULL ||
        image_bytes == 0U || signature_bytes == 0U)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "firmware image, signature and trusted verifier are required");
    if (image_bytes > maximum_image_bytes)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "firmware image exceeds the configured size limit");
    if (!verifier(context, image, image_bytes, signature, signature_bytes))
        return fail(error, REAPER_SYSTEM_SIGNATURE_INVALID,
                    "firmware signature verification failed");
    return REAPER_SYSTEM_OK;
}

static size_t tensor_element_bytes(ReaperSystemTensorType type) {
    switch (type) {
    case REAPER_SYSTEM_TENSOR_F16:
    case REAPER_SYSTEM_TENSOR_BF16: return 2U;
    case REAPER_SYSTEM_TENSOR_F32:
    case REAPER_SYSTEM_TENSOR_I32: return 4U;
    case REAPER_SYSTEM_TENSOR_I8: return 1U;
    default: return 0U;
    }
}

static int checked_tensor_bytes(size_t rows, size_t columns,
                                size_t element_bytes, size_t *result) {
    if (rows == 0U || columns == 0U || element_bytes == 0U ||
        rows > SIZE_MAX / columns) return 0;
    size_t elements = rows * columns;
    if (elements > SIZE_MAX / element_bytes) return 0;
    *result = elements * element_bytes;
    return 1;
}

ReaperSystemStatus reaper_system_tensor_matmul_validate(
    const ReaperSystemTensor *left, const ReaperSystemTensor *right,
    const ReaperSystemTensor *output, size_t *output_bytes,
    ReaperSystemError *error
) {
    clear_error(error);
    if (output_bytes != NULL) *output_bytes = 0U;
    if (left == NULL || right == NULL || output == NULL || output_bytes == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "three tensor descriptors and output size are required");
    if (left->columns != right->rows ||
        output->rows != left->rows || output->columns != right->columns)
        return fail(error, REAPER_SYSTEM_DIMENSION_MISMATCH,
                    "matrix dimensions are incompatible");
    size_t element_bytes = tensor_element_bytes(left->element_type);
    if (element_bytes == 0U || right->element_type != left->element_type ||
        output->element_type != left->element_type)
        return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                    "tensor element types must match a supported numeric format");
    size_t left_required = 0U, right_required = 0U, output_required = 0U;
    if (!checked_tensor_bytes(left->rows, left->columns, element_bytes, &left_required) ||
        !checked_tensor_bytes(right->rows, right->columns, element_bytes, &right_required) ||
        !checked_tensor_bytes(output->rows, output->columns, element_bytes, &output_required))
        return fail(error, REAPER_SYSTEM_OVERFLOW, "tensor byte size overflows size_t");
    if (left->storage_bytes < left_required || right->storage_bytes < right_required ||
        output->storage_bytes < output_required)
        return fail(error, REAPER_SYSTEM_CAPACITY,
                    "tensor storage is smaller than its declared shape");
    *output_bytes = output_required;
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_container_policy_validate(
    const ReaperSystemContainerPolicy *policy, ReaperSystemError *error
) {
    clear_error(error);
    if (policy == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, "container policy is required");
    const uint8_t flags[] = {
        policy->user_namespace, policy->mount_namespace, policy->pid_namespace,
        policy->network_namespace, policy->root_read_only, policy->no_new_privileges,
        policy->seccomp_profile_present, policy->network_allowed
    };
    for (size_t index = 0U; index < sizeof flags / sizeof flags[0]; ++index)
        if (flags[index] > 1U)
            return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                        "container policy flags must be boolean values");
    if (!policy->user_namespace || !policy->mount_namespace || !policy->pid_namespace ||
        !policy->root_read_only || !policy->no_new_privileges ||
        !policy->seccomp_profile_present)
        return fail(error, REAPER_SYSTEM_PERMISSION_DENIED,
                    "container requires user, mount and PID isolation, read-only root, no_new_privileges and seccomp");
    if (policy->network_allowed && !policy->network_namespace)
        return fail(error, REAPER_SYSTEM_PERMISSION_DENIED,
                    "network access requires an isolated network namespace");
    if (policy->memory_limit_bytes == 0U || policy->cpu_quota_us == 0U ||
        policy->process_limit == 0U)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "container memory, CPU and process quotas must be non-zero");
    return REAPER_SYSTEM_OK;
}

static int safe_component(const char *value, size_t maximum, int allow_dots) {
    if (value == NULL || value[0] == '\0' || strlen(value) > maximum) return 0;
    if (value[0] == '.' || strstr(value, "..") != NULL) return 0;
    for (const unsigned char *p = (const unsigned char *)value; *p != '\0'; ++p) {
        if (isalnum(*p) || *p == '-' || *p == '_') continue;
        if (allow_dots && *p == '.') continue;
        return 0;
    }
    return 1;
}

ReaperSystemStatus reaper_system_vm_profile_validate(
    const ReaperSystemVmProfile *profile, ReaperSystemError *error
) {
    clear_error(error);
    if (profile == NULL || profile->guest_architecture == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT, "VM profile is required");
    const uint8_t flags[] = {
        profile->host_virtualization_available, profile->device_passthrough,
        profile->iommu_available
    };
    for (size_t index = 0U; index < sizeof flags / sizeof flags[0]; ++index)
        if (flags[index] > 1U)
            return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                        "VM profile flags must be boolean values");
    if (!equal_text(profile->guest_architecture, "x86_64") &&
        !equal_text(profile->guest_architecture, "aarch64") &&
        !equal_text(profile->guest_architecture, "riscv64") &&
        !equal_text(profile->guest_architecture, "e2k"))
        return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                    "guest architecture is not in the declared support set");
    if (!profile->host_virtualization_available)
        return fail(error, REAPER_SYSTEM_ADAPTER_UNAVAILABLE,
                    "host virtualization capability is unavailable");
    if (profile->virtual_cpu_count == 0U || profile->virtual_cpu_count > 256U)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "virtual CPU count must be between 1 and 256");
    if (profile->memory_bytes < UINT64_C(16777216) ||
        profile->memory_bytes > UINT64_C(1099511627776) ||
        (profile->memory_bytes % UINT64_C(4096)) != 0U)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "VM memory must be page-aligned and between 16 MiB and 1 TiB");
    if (profile->device_passthrough && !profile->iommu_available)
        return fail(error, REAPER_SYSTEM_PERMISSION_DENIED,
                    "device passthrough requires an available IOMMU");
    return REAPER_SYSTEM_OK;
}

static int valid_digest(const char *digest) {
    if (digest == NULL || strlen(digest) != 64U) return 0;
    for (size_t index = 0U; index < 64U; ++index)
        if (!isxdigit((unsigned char)digest[index])) return 0;
    return 1;
}

static int valid_version(const char *version) {
    if (version == NULL || strlen(version) > 64U) return 0;
    const char *cursor = version;
    for (unsigned part = 0U; part < 3U; ++part) {
        if (!isdigit((unsigned char)*cursor)) return 0;
        while (isdigit((unsigned char)*cursor)) ++cursor;
        if (part < 2U) {
            if (*cursor != '.') return 0;
            ++cursor;
        }
    }
    return *cursor == '\0';
}

ReaperSystemStatus reaper_system_package_manifest_validate(
    const ReaperSystemPackageManifest *manifest,
    ReaperSystemManifestVerifier verifier, void *context,
    ReaperSystemError *error
) {
    clear_error(error);
    if (manifest == NULL || verifier == NULL ||
        manifest->canonical_manifest == NULL || manifest->manifest_bytes == 0U ||
        manifest->signature == NULL || manifest->signature_bytes == 0U)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "canonical manifest, signature and verifier are required");
    if (manifest->manifest_bytes > 1024U * 1024U)
        return fail(error, REAPER_SYSTEM_OUT_OF_RANGE,
                    "canonical package manifest exceeds one MiB");
    if (!safe_component(manifest->name, 128U, 1) ||
        !valid_version(manifest->version) || !valid_digest(manifest->image_digest_hex))
        return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                    "package name, semantic version or SHA-256 digest is invalid");
    if (manifest->rollback_protection > 1U || manifest->isolated_install_root > 1U)
        return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                    "package policy flags must be boolean values");
    if (!manifest->rollback_protection || !manifest->isolated_install_root)
        return fail(error, REAPER_SYSTEM_PERMISSION_DENIED,
                    "package updates require rollback protection and an isolated install root");
    if (!verifier(context, manifest->canonical_manifest, manifest->manifest_bytes,
                  manifest->signature, manifest->signature_bytes))
        return fail(error, REAPER_SYSTEM_SIGNATURE_INVALID,
                    "package manifest signature verification failed");
    return REAPER_SYSTEM_OK;
}

ReaperSystemStatus reaper_system_target_validate(
    const char *target_triple, const char *toolchain_id, const char *sysroot_id,
    ReaperSystemError *error
) {
    clear_error(error);
    if (target_triple == NULL || toolchain_id == NULL || sysroot_id == NULL)
        return fail(error, REAPER_SYSTEM_INVALID_ARGUMENT,
                    "target triple, toolchain id and sysroot id are required");
    static const char *const prefixes[] = {
        "x86_64-", "aarch64-", "riscv64-", "e2k-", "armv7-", "wasm32-"
    };
    int supported = 0;
    for (size_t index = 0U; index < sizeof prefixes / sizeof prefixes[0]; ++index)
        if (strncmp(target_triple, prefixes[index], strlen(prefixes[index])) == 0)
            supported = 1;
    if (!supported || strlen(target_triple) > 96U ||
        !safe_component(toolchain_id, 96U, 1) ||
        !safe_component(sysroot_id, 96U, 1))
        return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                    "target identity or toolchain references are invalid");
    for (const unsigned char *p = (const unsigned char *)target_triple; *p != '\0'; ++p)
        if (!(islower(*p) || isdigit(*p) || *p == '_' || *p == '-' || *p == '.'))
            return fail(error, REAPER_SYSTEM_INVALID_FORMAT,
                        "target triple contains an unsupported character");
    return REAPER_SYSTEM_OK;
}

const char *reaper_system_status_name(ReaperSystemStatus status) {
    switch (status) {
    case REAPER_SYSTEM_OK: return "ok";
    case REAPER_SYSTEM_INVALID_ARGUMENT: return "invalid_argument";
    case REAPER_SYSTEM_NOT_FOUND: return "not_found";
    case REAPER_SYSTEM_PERMISSION_DENIED: return "permission_denied";
    case REAPER_SYSTEM_ADAPTER_UNAVAILABLE: return "adapter_unavailable";
    case REAPER_SYSTEM_PROFILE_DENIED: return "profile_denied";
    case REAPER_SYSTEM_INVALID_FORMAT: return "invalid_format";
    case REAPER_SYSTEM_OUT_OF_RANGE: return "out_of_range";
    case REAPER_SYSTEM_CAPACITY: return "capacity";
    case REAPER_SYSTEM_DEPENDENCY_CYCLE: return "dependency_cycle";
    case REAPER_SYSTEM_QUEUE_EMPTY: return "queue_empty";
    case REAPER_SYSTEM_QUEUE_FULL: return "queue_full";
    case REAPER_SYSTEM_CHECKSUM_INVALID: return "checksum_invalid";
    case REAPER_SYSTEM_SIGNATURE_INVALID: return "signature_invalid";
    case REAPER_SYSTEM_DIMENSION_MISMATCH: return "dimension_mismatch";
    case REAPER_SYSTEM_OVERFLOW: return "overflow";
    default: return "unknown";
    }
}
