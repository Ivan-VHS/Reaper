#include "reaper/system_runtime.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int verify_ok(void *context, const uint8_t *payload, size_t payload_bytes,
                     const uint8_t *signature, size_t signature_bytes) {
    (void)context;
    return payload != NULL && payload_bytes > 0U &&
           signature != NULL && signature_bytes == 1U && signature[0] == 0xA5U;
}

static void test_registry_and_authorization(void) {
    static const char *const ids[REAPER_SYSTEM_OPERATION_COUNT] = {
        "111", "112", "113", "114", "115", "116", "117", "118", "119", "120",
        "121", "122", "123", "124", "125", "126", "127", "128", "129", "130"
    };
    assert(reaper_system_operation_count() == 20U);
    for (size_t i = 0U; i < REAPER_SYSTEM_OPERATION_COUNT; ++i) {
        const ReaperSystemOperation *operation = reaper_system_operation_at(i);
        assert(operation != NULL);
        assert(strcmp(operation->id, ids[i]) == 0);
        assert(operation->operation[0] != '\0');
        assert(operation->boundary[0] != '\0');
    }
    assert(reaper_system_operation_at(20U) == NULL);
    const ReaperSystemOperation *cron =
        reaper_system_operation_find("SCHEDULER.CRON_SCHEDULE");
    assert(cron != NULL && strcmp(cron->id, "113") == 0);
    assert(reaper_system_operation_find("999") == NULL);

    ReaperSystemAuthorization authorization = {0};
    ReaperSystemError error = {0};
    assert(reaper_system_authorize(cron, REAPER_SYSTEM_PROFILE_HOSTED,
        REAPER_SYSTEM_EFFECT_SCHEDULE, REAPER_SYSTEM_ADAPTER_SCHEDULER,
        &authorization, &error) == REAPER_SYSTEM_OK);
    assert(authorization.authorized == 1);
    assert(authorization.dispatchable == 0);
    assert(authorization.maturity == REAPER_SYSTEM_MATURITY_VALIDATORS_AVAILABLE);
    assert(reaper_system_authorize(cron, REAPER_SYSTEM_PROFILE_HOSTED, 0U,
        REAPER_SYSTEM_ADAPTER_SCHEDULER, &authorization, &error)
        == REAPER_SYSTEM_PERMISSION_DENIED);
    assert(reaper_system_authorize(cron, REAPER_SYSTEM_PROFILE_KERNEL,
        REAPER_SYSTEM_EFFECT_SCHEDULE, REAPER_SYSTEM_ADAPTER_SCHEDULER,
        &authorization, &error) == REAPER_SYSTEM_PROFILE_DENIED);
    assert(reaper_system_authorize(cron, REAPER_SYSTEM_PROFILE_HOSTED,
        REAPER_SYSTEM_EFFECT_SCHEDULE, 0U, &authorization, &error)
        == REAPER_SYSTEM_ADAPTER_UNAVAILABLE);
    assert(reaper_system_authorize(NULL, REAPER_SYSTEM_PROFILE_HOSTED, 0U, 0U,
        &authorization, &error) == REAPER_SYSTEM_INVALID_ARGUMENT);
}

static void test_cron_validation(void) {
    ReaperSystemError error = {0};
    assert(reaper_system_cron_validate("*/5 0-23/2 1,15 * 0,7", &error)
           == REAPER_SYSTEM_OK);
    assert(reaper_system_cron_validate("0 0 1 1 1", &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_cron_validate("60 * * * *", &error)
           == REAPER_SYSTEM_INVALID_FORMAT);
    assert(reaper_system_cron_validate("*/0 * * * *", &error)
           == REAPER_SYSTEM_INVALID_FORMAT);
    assert(reaper_system_cron_validate("1-31/32 * * * *", &error)
           == REAPER_SYSTEM_INVALID_FORMAT);
    assert(reaper_system_cron_validate("* * * *", &error)
           == REAPER_SYSTEM_INVALID_FORMAT);
    assert(reaper_system_cron_validate("* * * * * extra", &error)
           == REAPER_SYSTEM_INVALID_FORMAT);
}

static void test_dependency_order_and_cycles(void) {
    const uint8_t graph[] = {
        0,0,0,0,
        0,0,0,0,
        1,1,0,0,
        0,0,1,0
    };
    size_t order[4] = { 99U, 99U, 99U, 99U };
    ReaperSystemError error = {0};
    assert(reaper_system_dependency_order(4U, graph, sizeof graph,
        order, 4U, &error) == REAPER_SYSTEM_OK);
    assert(order[0] == 0U && order[1] == 1U &&
           order[2] == 2U && order[3] == 3U);

    const uint8_t cycle[] = { 0,1,1,0 };
    size_t cycle_order[2] = { 77U, 77U };
    assert(reaper_system_dependency_order(2U, cycle, sizeof cycle,
        cycle_order, 2U, &error) == REAPER_SYSTEM_DEPENDENCY_CYCLE);
    assert(cycle_order[0] == 77U && cycle_order[1] == 77U);
    assert(reaper_system_dependency_order(4U, graph, 3U,
        order, 4U, &error) == REAPER_SYSTEM_CAPACITY);
}

static void test_bounded_log_ring(void) {
    ReaperSystemLogRecord storage[3];
    ReaperSystemLogRing ring;
    ReaperSystemLogRecord input = {0}, output = {0};
    ReaperSystemError error = {0};
    assert(reaper_system_log_ring_init(&ring, storage, 3U, &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_log_ring_pop(&ring, &output, &error) == REAPER_SYSTEM_QUEUE_EMPTY);
    input.timestamp_ns = 42U;
    input.priority = 4U;
    input.length = 4U;
    memcpy(input.message, "boot", 4U);
    assert(reaper_system_log_ring_push(&ring, &input, &error) == REAPER_SYSTEM_OK);
    input.timestamp_ns = 43U;
    assert(reaper_system_log_ring_push(&ring, &input, &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_log_ring_push(&ring, &input, &error) == REAPER_SYSTEM_QUEUE_FULL);
    assert(reaper_system_log_ring_pop(&ring, &output, &error) == REAPER_SYSTEM_OK);
    assert(output.timestamp_ns == 42U);
    assert(output.length == 4U && strcmp(output.message, "boot") == 0);
    assert(reaper_system_log_ring_pop(&ring, &output, &error) == REAPER_SYSTEM_OK);
    assert(output.timestamp_ns == 43U);
}

static void test_acpi_table_validation(void) {
    uint8_t table[REAPER_SYSTEM_ACPI_HEADER_SIZE] = {0};
    size_t bytes = 0U;
    ReaperSystemError error = {0};
    memcpy(table, "TEST", 4U);
    table[4] = (uint8_t)sizeof table;
    table[5] = table[6] = table[7] = 0U;
    uint8_t sum = 0U;
    for (size_t i = 0U; i < sizeof table; ++i)
        if (i != 9U) sum = (uint8_t)(sum + table[i]);
    table[9] = (uint8_t)(0U - sum);
    assert(reaper_system_acpi_table_validate(table, sizeof table, 4096U,
        &bytes, &error) == REAPER_SYSTEM_OK);
    assert(bytes == sizeof table);
    table[10] = 1U;
    assert(reaper_system_acpi_table_validate(table, sizeof table, 4096U,
        &bytes, &error) == REAPER_SYSTEM_CHECKSUM_INVALID);
    table[4] = 0U;
    assert(reaper_system_acpi_table_validate(table, sizeof table, 4096U,
        &bytes, &error) == REAPER_SYSTEM_OUT_OF_RANGE);
}

static void test_firmware_and_package_verification(void) {
    const uint8_t image[] = { 1U, 2U, 3U };
    const uint8_t signature[] = { 0xA5U };
    ReaperSystemError error = {0};
    assert(reaper_system_firmware_verify(image, sizeof image, 16U,
        signature, sizeof signature, verify_ok, NULL, &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_firmware_verify(image, sizeof image, 2U,
        signature, sizeof signature, verify_ok, NULL, &error) == REAPER_SYSTEM_OUT_OF_RANGE);

    const uint8_t manifest_bytes[] = "{}";
    ReaperSystemPackageManifest manifest = {
        "duck.runtime", "1.2.3",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        manifest_bytes, sizeof manifest_bytes - 1U, signature, sizeof signature, 1U, 1U
    };
    assert(reaper_system_package_manifest_validate(
        &manifest, verify_ok, NULL, &error) == REAPER_SYSTEM_OK);
    manifest.name = "../runtime";
    assert(reaper_system_package_manifest_validate(
        &manifest, verify_ok, NULL, &error) == REAPER_SYSTEM_INVALID_FORMAT);
    manifest.name = "runtime";
    manifest.rollback_protection = 0U;
    assert(reaper_system_package_manifest_validate(
        &manifest, verify_ok, NULL, &error) == REAPER_SYSTEM_PERMISSION_DENIED);
}

static void test_tensor_shape_validation(void) {
    ReaperSystemTensor left = { 2U, 3U, 12U, REAPER_SYSTEM_TENSOR_F16 };
    ReaperSystemTensor right = { 3U, 4U, 24U, REAPER_SYSTEM_TENSOR_F16 };
    ReaperSystemTensor output = { 2U, 4U, 16U, REAPER_SYSTEM_TENSOR_F16 };
    size_t output_bytes = 0U;
    ReaperSystemError error = {0};
    assert(reaper_system_tensor_matmul_validate(
        &left, &right, &output, &output_bytes, &error) == REAPER_SYSTEM_OK);
    assert(output_bytes == 16U);
    right.rows = 5U;
    assert(reaper_system_tensor_matmul_validate(
        &left, &right, &output, &output_bytes, &error)
        == REAPER_SYSTEM_DIMENSION_MISMATCH);
    right.rows = 3U;
    output.storage_bytes = 2U;
    assert(reaper_system_tensor_matmul_validate(
        &left, &right, &output, &output_bytes, &error) == REAPER_SYSTEM_CAPACITY);
}

static void test_container_and_vm_policy_validation(void) {
    ReaperSystemContainerPolicy policy = {
        1U, 1U, 1U, 0U, 1U, 1U, 1U, 0U,
        UINT64_C(268435456), 10000U, 64U
    };
    ReaperSystemError error = {0};
    assert(reaper_system_container_policy_validate(&policy, &error) == REAPER_SYSTEM_OK);
    policy.network_allowed = 1U;
    assert(reaper_system_container_policy_validate(&policy, &error)
           == REAPER_SYSTEM_PERMISSION_DENIED);
    policy.network_namespace = 1U;
    assert(reaper_system_container_policy_validate(&policy, &error) == REAPER_SYSTEM_OK);

    ReaperSystemVmProfile vm = {
        "x86_64", UINT64_C(1073741824), 4U, 1U, 0U, 0U
    };
    assert(reaper_system_vm_profile_validate(&vm, &error) == REAPER_SYSTEM_OK);
    vm.device_passthrough = 1U;
    assert(reaper_system_vm_profile_validate(&vm, &error)
           == REAPER_SYSTEM_PERMISSION_DENIED);
    vm.iommu_available = 1U;
    assert(reaper_system_vm_profile_validate(&vm, &error) == REAPER_SYSTEM_OK);
}

static void test_cross_target_validation(void) {
    ReaperSystemError error = {0};
    assert(reaper_system_target_validate("x86_64-unknown-duckos",
        "clang-native", "duckos-sysroot", &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_target_validate("e2k-unknown-linux-gnu",
        "e2k-elf", "e2k-sysroot", &error) == REAPER_SYSTEM_OK);
    assert(reaper_system_target_validate("../../bin/cc",
        "clang", "sysroot", &error) == REAPER_SYSTEM_INVALID_FORMAT);
    assert(strcmp(reaper_system_status_name(REAPER_SYSTEM_SIGNATURE_INVALID),
        "signature_invalid") == 0);
}

int main(void) {
    test_registry_and_authorization();
    test_cron_validation();
    test_dependency_order_and_cycles();
    test_bounded_log_ring();
    test_acpi_table_validation();
    test_firmware_and_package_verification();
    test_tensor_shape_validation();
    test_container_and_vm_policy_validation();
    test_cross_target_validation();
    puts("system runtime contracts and safety primitives passed");
    return 0;
}
