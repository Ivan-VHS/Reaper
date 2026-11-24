#include "reaper/hardware.h"

#include <stdio.h>

static ReaperHwStatus fail(
    ReaperHwError *error, ReaperHwStatus status,
    uint64_t address, const char *message
) {
    if (error != NULL) {
        error->status = status;
        error->address = address;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

static void clear_error(ReaperHwError *error) {
    if (error != NULL) {
        error->status = REAPER_HW_OK;
        error->address = 0;
        error->message[0] = '\0';
    }
}

ReaperHwStatus reaper_hw_region_validate(
    const ReaperHwRegion *region, ReaperHwError *error
) {
    clear_error(error);
    if (region == NULL)
        return fail(error, REAPER_HW_INVALID_ARGUMENT, 0, "region is required");
    if (region->space != REAPER_HW_SPACE_MMIO)
        return fail(error, REAPER_HW_UNSUPPORTED_SPACE, region->base,
                    "only MMIO regions are supported by this API version");
    if (region->size == 0)
        return fail(error, REAPER_HW_INVALID_REGION, region->base,
                    "region size must be greater than zero");
    if (region->size > UINT64_MAX - region->base)
        return fail(error, REAPER_HW_INVALID_REGION, region->base,
                    "region address range overflows uint64");
    return REAPER_HW_OK;
}

ReaperHwStatus reaper_hw_register_validate(
    const ReaperHwRegion *region, const ReaperHwRegister *reg,
    uint64_t *absolute_address, ReaperHwError *error
) {
    clear_error(error);
    if (absolute_address != NULL) *absolute_address = 0;
    if (reg == NULL || absolute_address == NULL)
        return fail(error, REAPER_HW_INVALID_ARGUMENT, 0,
                    "register and address output are required");

    ReaperHwStatus status = reaper_hw_region_validate(region, error);
    if (status != REAPER_HW_OK) return status;

    uint64_t width_bytes = 0;
    switch (reg->width_bits) {
    case 8: width_bytes = 1; break;
    case 16: width_bytes = 2; break;
    case 32: width_bytes = 4; break;
    case 64: width_bytes = 8; break;
    default:
        return fail(error, REAPER_HW_INVALID_REGISTER, region->base,
                    "register width must be 8, 16, 32, or 64 bits");
    }

    switch (reg->access) {
    case REAPER_HW_ACCESS_READ_ONLY:
    case REAPER_HW_ACCESS_WRITE_ONLY:
    case REAPER_HW_ACCESS_READ_WRITE:
    case REAPER_HW_ACCESS_WRITE_ONE_TO_CLEAR:
    case REAPER_HW_ACCESS_WRITE_ONE_TO_SET:
        break;
    default:
        return fail(error, REAPER_HW_INVALID_REGISTER, region->base,
                    "register access policy is invalid");
    }

    switch (reg->endian) {
    case REAPER_HW_ENDIAN_NATIVE:
    case REAPER_HW_ENDIAN_LITTLE:
    case REAPER_HW_ENDIAN_BIG:
        break;
    default:
        return fail(error, REAPER_HW_INVALID_REGISTER, region->base,
                    "register byte order is invalid");
    }

    if (reg->offset > region->size ||
        width_bytes > region->size - reg->offset)
        return fail(error, REAPER_HW_OUT_OF_BOUNDS, region->base,
                    "register lies outside its MMIO region");
    if (reg->offset > UINT64_MAX - region->base)
        return fail(error, REAPER_HW_OUT_OF_BOUNDS, region->base,
                    "register address overflows uint64");

    uint64_t address = region->base + reg->offset;
    if ((address % width_bytes) != 0)
        return fail(error, REAPER_HW_MISALIGNED, address,
                    "register address is not naturally aligned");

    *absolute_address = address;
    return REAPER_HW_OK;
}

static int valid_read_order(ReaperHwMemoryOrder order) {
    return order == REAPER_HW_ORDER_RELAXED ||
           order == REAPER_HW_ORDER_ACQUIRE ||
           order == REAPER_HW_ORDER_SEQ_CST;
}

static int valid_write_order(ReaperHwMemoryOrder order) {
    return order == REAPER_HW_ORDER_RELAXED ||
           order == REAPER_HW_ORDER_RELEASE ||
           order == REAPER_HW_ORDER_SEQ_CST;
}

ReaperHwStatus reaper_hw_read(
    const ReaperHwBus *bus, const ReaperHwRegion *region,
    const ReaperHwRegister *reg, uint32_t granted_capabilities,
    ReaperHwMemoryOrder order, uint64_t *value, ReaperHwError *error
) {
    clear_error(error);
    if (bus == NULL || bus->read == NULL || value == NULL)
        return fail(error, REAPER_HW_INVALID_ARGUMENT, 0,
                    "read adapter and value output are required");

    uint64_t address = 0;
    ReaperHwStatus status = reaper_hw_register_validate(
        region, reg, &address, error
    );
    if (status != REAPER_HW_OK) return status;
    if (reg->access == REAPER_HW_ACCESS_WRITE_ONLY)
        return fail(error, REAPER_HW_ACCESS_DENIED, address,
                    "write-only register cannot be read");

    uint32_t required = REAPER_HW_CAP_MMIO_READ | reg->required_capabilities;
    if ((granted_capabilities & required) != required)
        return fail(error, REAPER_HW_ACCESS_DENIED, address,
                    "MMIO read capability was not granted");
    if (!valid_read_order(order))
        return fail(error, REAPER_HW_INVALID_MEMORY_ORDER, address,
                    "read accepts relaxed, acquire, or seq_cst ordering");

    uint64_t read_value = 0;
    if (!bus->read(bus->context, region->space, address, reg->width_bits,
                   reg->endian, order, &read_value))
        return fail(error, REAPER_HW_BUS_FAILURE, address,
                    "hardware bus adapter rejected the read");
    *value = read_value;
    return REAPER_HW_OK;
}

ReaperHwStatus reaper_hw_write(
    const ReaperHwBus *bus, const ReaperHwRegion *region,
    const ReaperHwRegister *reg, uint32_t granted_capabilities,
    ReaperHwMemoryOrder order, uint64_t value, ReaperHwError *error
) {
    clear_error(error);
    if (bus == NULL || bus->write == NULL)
        return fail(error, REAPER_HW_INVALID_ARGUMENT, 0,
                    "write adapter is required");

    uint64_t address = 0;
    ReaperHwStatus status = reaper_hw_register_validate(
        region, reg, &address, error
    );
    if (status != REAPER_HW_OK) return status;
    if (reg->access == REAPER_HW_ACCESS_READ_ONLY)
        return fail(error, REAPER_HW_ACCESS_DENIED, address,
                    "read-only register cannot be written");

    uint32_t required = REAPER_HW_CAP_MMIO_WRITE | reg->required_capabilities;
    if ((granted_capabilities & required) != required)
        return fail(error, REAPER_HW_ACCESS_DENIED, address,
                    "MMIO write capability was not granted");
    if (!valid_write_order(order))
        return fail(error, REAPER_HW_INVALID_MEMORY_ORDER, address,
                    "write accepts relaxed, release, or seq_cst ordering");

    if (!bus->write(bus->context, region->space, address, reg->width_bits,
                    reg->endian, order, value))
        return fail(error, REAPER_HW_BUS_FAILURE, address,
                    "hardware bus adapter rejected the write");
    return REAPER_HW_OK;
}

const char *reaper_hw_status_name(ReaperHwStatus status) {
    switch (status) {
    case REAPER_HW_OK: return "ok";
    case REAPER_HW_INVALID_ARGUMENT: return "invalid_argument";
    case REAPER_HW_UNSUPPORTED_SPACE: return "unsupported_space";
    case REAPER_HW_INVALID_REGION: return "invalid_region";
    case REAPER_HW_INVALID_REGISTER: return "invalid_register";
    case REAPER_HW_OUT_OF_BOUNDS: return "out_of_bounds";
    case REAPER_HW_MISALIGNED: return "misaligned";
    case REAPER_HW_ACCESS_DENIED: return "access_denied";
    case REAPER_HW_INVALID_MEMORY_ORDER: return "invalid_memory_order";
    case REAPER_HW_BUS_FAILURE: return "bus_failure";
    default: return "unknown";
    }
}
