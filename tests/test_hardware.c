#include "reaper/hardware.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint64_t address;
    uint64_t value;
    uint8_t width_bits;
    ReaperHwEndian endian;
    ReaperHwMemoryOrder order;
    int should_fail;
    int reads;
    int writes;
} FakeBus;

static int fake_read(
    void *context, ReaperHwSpace space, uint64_t address,
    uint8_t width_bits, ReaperHwEndian endian,
    ReaperHwMemoryOrder order, uint64_t *value
) {
    FakeBus *bus = (FakeBus *)context;
    assert(space == REAPER_HW_SPACE_MMIO);
    bus->address = address;
    bus->width_bits = width_bits;
    bus->endian = endian;
    bus->order = order;
    ++bus->reads;
    if (bus->should_fail) return 0;
    *value = bus->value;
    return 1;
}

static int fake_write(
    void *context, ReaperHwSpace space, uint64_t address,
    uint8_t width_bits, ReaperHwEndian endian,
    ReaperHwMemoryOrder order, uint64_t value
) {
    FakeBus *bus = (FakeBus *)context;
    assert(space == REAPER_HW_SPACE_MMIO);
    bus->address = address;
    bus->width_bits = width_bits;
    bus->endian = endian;
    bus->order = order;
    ++bus->writes;
    if (bus->should_fail) return 0;
    bus->value = value;
    return 1;
}

static ReaperHwBus make_bus(FakeBus *fake) {
    ReaperHwBus bus = { fake, fake_read, fake_write };
    return bus;
}

static void test_read_and_write(void) {
    FakeBus fake = {0};
    ReaperHwBus bus = make_bus(&fake);
    ReaperHwRegion region = { UINT64_C(0x40000000), 0x100, REAPER_HW_SPACE_MMIO };
    ReaperHwRegister reg = {
        "STATUS", 0x20, 32, REAPER_HW_ACCESS_READ_WRITE,
        REAPER_HW_ENDIAN_LITTLE, 0
    };
    ReaperHwError error = {0};
    uint64_t value = 0;

    fake.value = UINT64_C(0x1234ABCD);
    assert(reaper_hw_read(&bus, &region, &reg,
        REAPER_HW_CAP_MMIO_READ, REAPER_HW_ORDER_ACQUIRE,
        &value, &error) == REAPER_HW_OK);
    assert(value == UINT64_C(0x1234ABCD));
    assert(fake.address == UINT64_C(0x40000020));
    assert(fake.width_bits == 32);
    assert(fake.endian == REAPER_HW_ENDIAN_LITTLE);
    assert(fake.order == REAPER_HW_ORDER_ACQUIRE);

    assert(reaper_hw_write(&bus, &region, &reg,
        REAPER_HW_CAP_MMIO_WRITE, REAPER_HW_ORDER_RELEASE,
        UINT64_C(0x55AA), &error) == REAPER_HW_OK);
    assert(fake.value == UINT64_C(0x55AA));
    assert(fake.address == UINT64_C(0x40000020));
    assert(fake.order == REAPER_HW_ORDER_RELEASE);
}

static void test_region_and_register_bounds(void) {
    ReaperHwError error = {0};
    uint64_t address = 0;
    ReaperHwRegion overflow = { UINT64_MAX - 3U, 8U, REAPER_HW_SPACE_MMIO };
    ReaperHwRegister reg = {
        "DATA", 0, 32, REAPER_HW_ACCESS_READ_WRITE,
        REAPER_HW_ENDIAN_NATIVE, 0
    };
    assert(reaper_hw_region_validate(&overflow, &error) == REAPER_HW_INVALID_REGION);

    ReaperHwRegion region = { 0x1000, 0x10, REAPER_HW_SPACE_MMIO };
    reg.offset = 0x0E;
    assert(reaper_hw_register_validate(&region, &reg, &address, &error)
           == REAPER_HW_OUT_OF_BOUNDS);
    reg.offset = 0x02;
    assert(reaper_hw_register_validate(&region, &reg, &address, &error)
           == REAPER_HW_MISALIGNED);
    reg.offset = 0x04;
    assert(reaper_hw_register_validate(&region, &reg, &address, &error)
           == REAPER_HW_OK);
    assert(address == UINT64_C(0x1004));
}

static void test_permissions_and_access_policy(void) {
    FakeBus fake = {0};
    ReaperHwBus bus = make_bus(&fake);
    ReaperHwRegion region = { 0x2000, 0x40, REAPER_HW_SPACE_MMIO };
    ReaperHwRegister read_only = {
        "ID", 0, 32, REAPER_HW_ACCESS_READ_ONLY,
        REAPER_HW_ENDIAN_NATIVE, 0
    };
    ReaperHwError error = {0};
    uint64_t value = 0;

    assert(reaper_hw_read(&bus, &region, &read_only, 0,
        REAPER_HW_ORDER_RELAXED, &value, &error) == REAPER_HW_ACCESS_DENIED);
    assert(fake.reads == 0);
    assert(reaper_hw_write(&bus, &region, &read_only,
        REAPER_HW_CAP_MMIO_WRITE, REAPER_HW_ORDER_RELEASE,
        1, &error) == REAPER_HW_ACCESS_DENIED);
    assert(fake.writes == 0);

    read_only.access = REAPER_HW_ACCESS_WRITE_ONLY;
    assert(reaper_hw_read(&bus, &region, &read_only,
        REAPER_HW_CAP_MMIO_READ, REAPER_HW_ORDER_ACQUIRE,
        &value, &error) == REAPER_HW_ACCESS_DENIED);
    assert(fake.reads == 0);
}

static void test_required_capability_and_ordering(void) {
    FakeBus fake = {0};
    ReaperHwBus bus = make_bus(&fake);
    ReaperHwRegion region = { 0x3000, 0x40, REAPER_HW_SPACE_MMIO };
    ReaperHwRegister reg = {
        "CONTROL", 0, 16, REAPER_HW_ACCESS_READ_WRITE,
        REAPER_HW_ENDIAN_BIG, UINT32_C(1) << 7
    };
    ReaperHwError error = {0};
    uint64_t value = 0;
    uint32_t grants = REAPER_HW_CAP_MMIO_READ | REAPER_HW_CAP_MMIO_WRITE;

    assert(reaper_hw_read(&bus, &region, &reg, grants,
        REAPER_HW_ORDER_RELEASE, &value, &error)
        == REAPER_HW_ACCESS_DENIED);
    assert(fake.reads == 0);
    assert(reaper_hw_read(&bus, &region, &reg,
        grants | (UINT32_C(1) << 7), REAPER_HW_ORDER_RELEASE,
        &value, &error) == REAPER_HW_INVALID_MEMORY_ORDER);
    assert(fake.reads == 0);
    assert(reaper_hw_write(&bus, &region, &reg,
        grants | (UINT32_C(1) << 7), REAPER_HW_ORDER_ACQUIRE,
        1, &error) == REAPER_HW_INVALID_MEMORY_ORDER);
    assert(fake.writes == 0);
}

static void test_bus_failure(void) {
    FakeBus fake = {0};
    ReaperHwBus bus = make_bus(&fake);
    ReaperHwRegion region = { 0x5000, 0x40, REAPER_HW_SPACE_MMIO };
    ReaperHwRegister reg = {
        "DATA", 0, 8, REAPER_HW_ACCESS_READ_WRITE,
        REAPER_HW_ENDIAN_NATIVE, 0
    };
    ReaperHwError error = {0};
    uint64_t value = 0;
    fake.should_fail = 1;

    assert(reaper_hw_read(&bus, &region, &reg,
        REAPER_HW_CAP_MMIO_READ, REAPER_HW_ORDER_RELAXED,
        &value, &error) == REAPER_HW_BUS_FAILURE);
    assert(strcmp(reaper_hw_status_name(error.status), "bus_failure") == 0);
    assert(error.address == UINT64_C(0x5000));
}

int main(void) {
    test_read_and_write();
    test_region_and_register_bounds();
    test_permissions_and_access_policy();
    test_required_capability_and_ordering();
    test_bus_failure();
    puts("hardware descriptor and MMIO adapter tests passed");
    return 0;
}
