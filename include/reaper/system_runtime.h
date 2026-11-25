#ifndef REAPER_SYSTEM_RUNTIME_H
#define REAPER_SYSTEM_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
#include <atomic>
typedef std::atomic<size_t> ReaperSystemAtomicSize;
extern "C" {
#else
#include <stdatomic.h>
typedef atomic_size_t ReaperSystemAtomicSize;
#endif

#define REAPER_SYSTEM_RUNTIME_ABI 1U
#define REAPER_SYSTEM_OPERATION_COUNT 20U
#define REAPER_SYSTEM_MAX_DEPENDENCIES 256U
#define REAPER_SYSTEM_LOG_MESSAGE_MAX 192U
#define REAPER_SYSTEM_ACPI_HEADER_SIZE 36U

typedef enum {
    REAPER_SYSTEM_OK = 0,
    REAPER_SYSTEM_INVALID_ARGUMENT,
    REAPER_SYSTEM_NOT_FOUND,
    REAPER_SYSTEM_PERMISSION_DENIED,
    REAPER_SYSTEM_ADAPTER_UNAVAILABLE,
    REAPER_SYSTEM_PROFILE_DENIED,
    REAPER_SYSTEM_INVALID_FORMAT,
    REAPER_SYSTEM_OUT_OF_RANGE,
    REAPER_SYSTEM_CAPACITY,
    REAPER_SYSTEM_DEPENDENCY_CYCLE,
    REAPER_SYSTEM_QUEUE_EMPTY,
    REAPER_SYSTEM_QUEUE_FULL,
    REAPER_SYSTEM_CHECKSUM_INVALID,
    REAPER_SYSTEM_SIGNATURE_INVALID,
    REAPER_SYSTEM_DIMENSION_MISMATCH,
    REAPER_SYSTEM_OVERFLOW
} ReaperSystemStatus;

typedef enum {
    REAPER_SYSTEM_PROFILE_HOSTED = UINT32_C(1) << 0,
    REAPER_SYSTEM_PROFILE_KERNEL = UINT32_C(1) << 1,
    REAPER_SYSTEM_PROFILE_BOOT = UINT32_C(1) << 2,
    REAPER_SYSTEM_PROFILE_HYPERVISOR = UINT32_C(1) << 3,
    REAPER_SYSTEM_PROFILE_FREESTANDING = UINT32_C(1) << 4,
    REAPER_SYSTEM_PROFILE_SIMULATOR = UINT32_C(1) << 5
} ReaperSystemProfile;

typedef enum {
    REAPER_SYSTEM_EFFECT_PROCESS_CONTROL = UINT64_C(1) << 0,
    REAPER_SYSTEM_EFFECT_SERVICE_CONTROL = UINT64_C(1) << 1,
    REAPER_SYSTEM_EFFECT_SCHEDULE = UINT64_C(1) << 2,
    REAPER_SYSTEM_EFFECT_LOG_WRITE = UINT64_C(1) << 3,
    REAPER_SYSTEM_EFFECT_POWER_CONTROL = UINT64_C(1) << 4,
    REAPER_SYSTEM_EFFECT_BOOT_CONTROL = UINT64_C(1) << 5,
    REAPER_SYSTEM_EFFECT_DEVICE_DISCOVERY = UINT64_C(1) << 6,
    REAPER_SYSTEM_EFFECT_DRIVER_CONTROL = UINT64_C(1) << 7,
    REAPER_SYSTEM_EFFECT_FIRMWARE_WRITE = UINT64_C(1) << 8,
    REAPER_SYSTEM_EFFECT_ACPI_READ = UINT64_C(1) << 9,
    REAPER_SYSTEM_EFFECT_NPU_ACCESS = UINT64_C(1) << 10,
    REAPER_SYSTEM_EFFECT_DMA = UINT64_C(1) << 11,
    REAPER_SYSTEM_EFFECT_AI_COMPUTE = UINT64_C(1) << 12,
    REAPER_SYSTEM_EFFECT_MODEL_READ = UINT64_C(1) << 13,
    REAPER_SYSTEM_EFFECT_CRYPTO = UINT64_C(1) << 14,
    REAPER_SYSTEM_EFFECT_PROCESS_ISOLATION = UINT64_C(1) << 15,
    REAPER_SYSTEM_EFFECT_FILESYSTEM_MOUNT = UINT64_C(1) << 16,
    REAPER_SYSTEM_EFFECT_NETWORK_NAMESPACE = UINT64_C(1) << 17,
    REAPER_SYSTEM_EFFECT_VIRTUALIZATION = UINT64_C(1) << 18,
    REAPER_SYSTEM_EFFECT_PACKAGE_INSTALL = UINT64_C(1) << 19,
    REAPER_SYSTEM_EFFECT_FILESYSTEM_READ = UINT64_C(1) << 20,
    REAPER_SYSTEM_EFFECT_FILESYSTEM_WRITE = UINT64_C(1) << 21,
    REAPER_SYSTEM_EFFECT_TOOLCHAIN_EXEC = UINT64_C(1) << 22
} ReaperSystemEffect;

typedef enum {
    REAPER_SYSTEM_ADAPTER_SERVICE_MANAGER = UINT64_C(1) << 0,
    REAPER_SYSTEM_ADAPTER_SCHEDULER = UINT64_C(1) << 1,
    REAPER_SYSTEM_ADAPTER_JOURNAL = UINT64_C(1) << 2,
    REAPER_SYSTEM_ADAPTER_INIT = UINT64_C(1) << 3,
    REAPER_SYSTEM_ADAPTER_POWER = UINT64_C(1) << 4,
    REAPER_SYSTEM_ADAPTER_BOOT = UINT64_C(1) << 5,
    REAPER_SYSTEM_ADAPTER_DEVICE_MANAGER = UINT64_C(1) << 6,
    REAPER_SYSTEM_ADAPTER_FIRMWARE = UINT64_C(1) << 7,
    REAPER_SYSTEM_ADAPTER_ACPI = UINT64_C(1) << 8,
    REAPER_SYSTEM_ADAPTER_NPU = UINT64_C(1) << 9,
    REAPER_SYSTEM_ADAPTER_AI_RUNTIME = UINT64_C(1) << 10,
    REAPER_SYSTEM_ADAPTER_MODEL_LOADER = UINT64_C(1) << 11,
    REAPER_SYSTEM_ADAPTER_HE = UINT64_C(1) << 12,
    REAPER_SYSTEM_ADAPTER_CONTAINER = UINT64_C(1) << 13,
    REAPER_SYSTEM_ADAPTER_HYPERVISOR = UINT64_C(1) << 14,
    REAPER_SYSTEM_ADAPTER_PACKAGE = UINT64_C(1) << 15,
    REAPER_SYSTEM_ADAPTER_TOOLCHAIN = UINT64_C(1) << 16
} ReaperSystemAdapter;

typedef enum {
    REAPER_SYSTEM_MATURITY_CONTRACT_ONLY = 0,
    REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE = 1
} ReaperSystemMaturity;

typedef struct {
    const char *id;
    const char *subsystem;
    const char *operation;
    uint64_t required_effects;
    uint64_t required_adapter;
    uint32_t allowed_profiles;
    ReaperSystemMaturity maturity;
    const char *boundary;
} ReaperSystemOperation;

typedef struct {
    ReaperSystemStatus status;
    char message[160];
} ReaperSystemError;

typedef struct {
    int authorized;
    int dispatchable;
    ReaperSystemMaturity maturity;
} ReaperSystemAuthorization;

size_t reaper_system_operation_count(void);
const ReaperSystemOperation *reaper_system_operation_at(size_t index);
const ReaperSystemOperation *reaper_system_operation_find(const char *id_or_operation);
ReaperSystemStatus reaper_system_authorize(
    const ReaperSystemOperation *operation,
    uint32_t runtime_profile,
    uint64_t granted_effects,
    uint64_t available_adapters,
    ReaperSystemAuthorization *authorization,
    ReaperSystemError *error
);

ReaperSystemStatus reaper_system_cron_validate(
    const char *expression, ReaperSystemError *error
);
ReaperSystemStatus reaper_system_dependency_order(
    size_t node_count, const uint8_t *dependencies, size_t dependency_bytes,
    size_t *order, size_t order_capacity, ReaperSystemError *error
);

typedef struct {
    uint64_t timestamp_ns;
    uint32_t process_id;
    uint8_t priority;
    uint16_t length;
    char message[REAPER_SYSTEM_LOG_MESSAGE_MAX];
} ReaperSystemLogRecord;

/* Single-producer/single-consumer bounded queue. Capacity includes the
 * reserved slot; usable capacity is capacity - 1. */
typedef struct {
    ReaperSystemLogRecord *records;
    size_t capacity;
    ReaperSystemAtomicSize head;
    ReaperSystemAtomicSize tail;
} ReaperSystemLogRing;

ReaperSystemStatus reaper_system_log_ring_init(
    ReaperSystemLogRing *ring, ReaperSystemLogRecord *storage, size_t capacity,
    ReaperSystemError *error
);
ReaperSystemStatus reaper_system_log_ring_push(
    ReaperSystemLogRing *ring, const ReaperSystemLogRecord *record,
    ReaperSystemError *error
);
ReaperSystemStatus reaper_system_log_ring_pop(
    ReaperSystemLogRing *ring, ReaperSystemLogRecord *record,
    ReaperSystemError *error
);

ReaperSystemStatus reaper_system_acpi_table_validate(
    const uint8_t *table, size_t available_bytes, size_t maximum_table_bytes,
    size_t *table_bytes, ReaperSystemError *error
);
typedef int (*ReaperSystemSignatureVerifier)(
    void *context, const uint8_t *image, size_t image_bytes,
    const uint8_t *signature, size_t signature_bytes
);
ReaperSystemStatus reaper_system_firmware_verify(
    const uint8_t *image, size_t image_bytes, size_t maximum_image_bytes,
    const uint8_t *signature, size_t signature_bytes,
    ReaperSystemSignatureVerifier verifier, void *context,
    ReaperSystemError *error
);

typedef enum {
    REAPER_SYSTEM_TENSOR_F16 = 1,
    REAPER_SYSTEM_TENSOR_BF16,
    REAPER_SYSTEM_TENSOR_F32,
    REAPER_SYSTEM_TENSOR_I8,
    REAPER_SYSTEM_TENSOR_I32
} ReaperSystemTensorType;
typedef struct {
    size_t rows;
    size_t columns;
    size_t storage_bytes;
    ReaperSystemTensorType element_type;
} ReaperSystemTensor;
ReaperSystemStatus reaper_system_tensor_matmul_validate(
    const ReaperSystemTensor *left, const ReaperSystemTensor *right,
    const ReaperSystemTensor *output, size_t *output_bytes,
    ReaperSystemError *error
);

typedef struct {
    uint8_t user_namespace;
    uint8_t mount_namespace;
    uint8_t pid_namespace;
    uint8_t network_namespace;
    uint8_t root_read_only;
    uint8_t no_new_privileges;
    uint8_t seccomp_profile_present;
    uint8_t network_allowed;
    uint64_t memory_limit_bytes;
    uint64_t cpu_quota_us;
    uint32_t process_limit;
} ReaperSystemContainerPolicy;
ReaperSystemStatus reaper_system_container_policy_validate(
    const ReaperSystemContainerPolicy *policy, ReaperSystemError *error
);

typedef struct {
    const char *guest_architecture;
    uint64_t memory_bytes;
    uint32_t page_size_bytes;
    uint32_t virtual_cpu_count;
    uint8_t host_virtualization_available;
    uint8_t device_passthrough;
    uint8_t iommu_available;
} ReaperSystemVmProfile;
ReaperSystemStatus reaper_system_vm_profile_validate(
    const ReaperSystemVmProfile *profile, ReaperSystemError *error
);

typedef int (*ReaperSystemManifestVerifier)(
    void *context, const uint8_t *canonical_manifest, size_t manifest_bytes,
    const uint8_t *signature, size_t signature_bytes
);
typedef struct {
    const char *name;
    const char *version;
    const char *image_digest_hex;
    const uint8_t *canonical_manifest;
    size_t manifest_bytes;
    const uint8_t *signature;
    size_t signature_bytes;
    uint8_t rollback_protection;
    uint8_t isolated_install_root;
} ReaperSystemPackageManifest;
ReaperSystemStatus reaper_system_package_manifest_validate(
    const ReaperSystemPackageManifest *manifest,
    ReaperSystemManifestVerifier verifier, void *context,
    ReaperSystemError *error
);

ReaperSystemStatus reaper_system_target_validate(
    const char *target_triple, const char *toolchain_id, const char *sysroot_id,
    ReaperSystemError *error
);
const char *reaper_system_status_name(ReaperSystemStatus status);

#ifdef __cplusplus
}
#endif

#endif
