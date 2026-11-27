#ifndef REAPER_PROCESSOR_BACKENDS_INTERNAL_H
#define REAPER_PROCESSOR_BACKENDS_INTERNAL_H

#include "reaper/processor_backends.h"

#include <limits.h>
#include <string.h>

static int reaper_fits_signed(int32_t value, unsigned bits) {
    const int64_t minimum = -(INT64_C(1) << (bits - 1u));
    const int64_t maximum = (INT64_C(1) << (bits - 1u)) - 1;
    return (int64_t)value >= minimum && (int64_t)value <= maximum;
}

static uint32_t reaper_encode_i(uint32_t opcode, uint32_t funct3,
                                uint8_t rd, uint8_t rs1, int32_t immediate) {
    return (((uint32_t)immediate & UINT32_C(0xFFF)) << 20u) |
           ((uint32_t)rs1 << 15u) | (funct3 << 12u) |
           ((uint32_t)rd << 7u) | opcode;
}

static uint32_t reaper_encode_s(uint32_t funct3, uint8_t rs1,
                                uint8_t rs2, int32_t immediate) {
    const uint32_t value = (uint32_t)immediate & UINT32_C(0xFFF);
    return (((value >> 5u) & UINT32_C(0x7F)) << 25u) |
           ((uint32_t)rs2 << 20u) | ((uint32_t)rs1 << 15u) |
           (funct3 << 12u) | ((value & UINT32_C(0x1F)) << 7u) | UINT32_C(0x23);
}

static uint32_t reaper_encode_b(uint32_t funct3, uint8_t rs1,
                                uint8_t rs2, int32_t immediate) {
    const uint32_t value = (uint32_t)immediate;
    return (((value >> 12u) & 1u) << 31u) |
           (((value >> 5u) & UINT32_C(0x3F)) << 25u) |
           ((uint32_t)rs2 << 20u) | ((uint32_t)rs1 << 15u) |
           (funct3 << 12u) | (((value >> 1u) & UINT32_C(0xF)) << 8u) |
           (((value >> 11u) & 1u) << 7u) | UINT32_C(0x63);
}

static uint32_t reaper_encode_j(uint8_t rd, int32_t immediate) {
    const uint32_t value = (uint32_t)immediate;
    return (((value >> 20u) & 1u) << 31u) |
           (((value >> 1u) & UINT32_C(0x3FF)) << 21u) |
           (((value >> 11u) & 1u) << 20u) |
           (((value >> 12u) & UINT32_C(0xFF)) << 12u) |
           ((uint32_t)rd << 7u) | UINT32_C(0x6F);
}

static int32_t reaper_sign_extend(uint32_t value, unsigned bits) {
    const uint32_t sign = UINT32_C(1) << (bits - 1u);
    const uint32_t mask = (UINT32_C(1) << bits) - 1u;
    const int64_t signed_value = (int64_t)(value & mask) -
        (((value & sign) != 0u) ? (INT64_C(1) << bits) : 0);
    return (int32_t)signed_value;
}

static void reaper_write_le32(uint8_t *buffer, uint32_t value) {
    buffer[0] = (uint8_t)(value & UINT32_C(0xFF));
    buffer[1] = (uint8_t)((value >> 8u) & UINT32_C(0xFF));
    buffer[2] = (uint8_t)((value >> 16u) & UINT32_C(0xFF));
    buffer[3] = (uint8_t)((value >> 24u) & UINT32_C(0xFF));
}

static uint32_t reaper_read_le32(const uint8_t *buffer) {
    return (uint32_t)buffer[0] |
           ((uint32_t)buffer[1] << 8u) |
           ((uint32_t)buffer[2] << 16u) |
           ((uint32_t)buffer[3] << 24u);
}

#endif
