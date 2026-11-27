#include "reaper/processor_backends.h"
#include "processor_backend_internal.h"

static int64_t signed_word(uint32_t value) {
    return (value & UINT32_C(0x80000000)) != 0u
        ? (int64_t)value - INT64_C(4294967296)
        : (int64_t)value;
}

static uint32_t add_signed(uint32_t value, int32_t immediate) {
    return (uint32_t)((int64_t)value + (int64_t)immediate);
}

static void write_register(ReaperRv32ExecutionReport *report,
                           uint32_t index, uint32_t value) {
    if (index != 0u && index < 32u) report->registers[index] = value;
}

static int read_word(const uint8_t *memory, uint32_t length,
                     uint32_t address, uint32_t *value) {
    if ((address & 3u) != 0u || address > length || length - address < 4u)
        return 0;
    *value = (uint32_t)memory[address] |
             ((uint32_t)memory[address + 1u] << 8u) |
             ((uint32_t)memory[address + 2u] << 16u) |
             ((uint32_t)memory[address + 3u] << 24u);
    return 1;
}

static int write_word(uint8_t *memory, uint32_t length,
                      uint32_t address, uint32_t value) {
    if ((address & 3u) != 0u || address > length || length - address < 4u)
        return 0;
    memory[address] = (uint8_t)(value & 0xFFu);
    memory[address + 1u] = (uint8_t)((value >> 8u) & 0xFFu);
    memory[address + 2u] = (uint8_t)((value >> 16u) & 0xFFu);
    memory[address + 3u] = (uint8_t)((value >> 24u) & 0xFFu);
    return 1;
}

ReaperProcessorBackendStatus reaper_rv32_emulate(
    const ReaperRv32LinkedImage *image,
    const ReaperRv32MachineState *initial_state,
    uint64_t max_steps,
    ReaperRv32ExecutionReport *report
) {
    uint64_t code_end;
    if (image == NULL || report == NULL || image->magic != REAPER_RV32_IMAGE_MAGIC ||
        image->abi_major != REAPER_PROCESSOR_BACKEND_ABI_MAJOR ||
        image->target_id != REAPER_RV32_TARGET_RV32I ||
        image->abi_id != REAPER_RV32_ABI_ILP32 || image->byte_count == 0u ||
        image->byte_count > REAPER_RV32_MAX_IMAGE_BYTES ||
        max_steps == 0u || max_steps > REAPER_RV32_MAX_STEPS)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    if ((uint64_t)image->base_address + image->byte_count > UINT32_MAX)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    code_end = (uint64_t)image->base_address + image->byte_count;
    memset(report, 0, sizeof(*report));
    if (initial_state != NULL) {
        if (initial_state->memory_size > REAPER_RV32_DATA_MEMORY_BYTES)
            return REAPER_BACKEND_INVALID_ARGUMENT;
        memcpy(report->registers, initial_state->registers, sizeof(report->registers));
        memcpy(report->memory, initial_state->memory, sizeof(report->memory));
        report->memory_size = initial_state->memory_size == 0u
            ? REAPER_RV32_DATA_MEMORY_BYTES : initial_state->memory_size;
        report->pc = initial_state->pc == 0u ? image->entry_address : initial_state->pc;
    } else {
        report->memory_size = REAPER_RV32_DATA_MEMORY_BYTES;
        report->pc = image->entry_address;
    }
    report->registers[0] = 0u;

    while (report->steps < max_steps) {
        uint32_t offset, word, opcode, rd, funct3, rs1, rs2, funct7;
        uint32_t next_pc, value = 0u;
        int32_t immediate = 0;
        uint32_t address;
        if ((uint64_t)report->pc == code_end) {
            report->halted = 1u;
            return REAPER_BACKEND_OK;
        }
        if (report->pc < image->base_address || (uint64_t)report->pc > code_end - UINT64_C(4) ||
            ((report->pc - image->base_address) & 3u) != 0u)
            return REAPER_BACKEND_INVALID_MEMORY_ACCESS;
        offset = report->pc - image->base_address;
        if (!read_word(image->bytes, image->byte_count, offset, &word))
            return REAPER_BACKEND_INVALID_MEMORY_ACCESS;
        opcode = word & UINT32_C(0x7F);
        rd = (word >> 7u) & 31u;
        funct3 = (word >> 12u) & 7u;
        rs1 = (word >> 15u) & 31u;
        rs2 = (word >> 20u) & 31u;
        funct7 = word >> 25u;
        next_pc = report->pc + 4u;

        switch (opcode) {
        case 0x37u: /* LUI */
            write_register(report, rd, word & UINT32_C(0xFFFFF000));
            break;
        case 0x17u: /* AUIPC */
            write_register(report, rd, report->pc + (word & UINT32_C(0xFFFFF000)));
            break;
        case 0x13u: /* OP-IMM */
            immediate = reaper_sign_extend(word >> 20u, 12u);
            if (funct3 == 0u) value = add_signed(report->registers[rs1], immediate);
            else if (funct3 == 7u) value = report->registers[rs1] & (uint32_t)immediate;
            else if (funct3 == 6u) value = report->registers[rs1] | (uint32_t)immediate;
            else if (funct3 == 4u) value = report->registers[rs1] ^ (uint32_t)immediate;
            else if (funct3 == 2u)
                value = signed_word(report->registers[rs1]) < (int64_t)immediate ? 1u : 0u;
            else return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
            write_register(report, rd, value);
            break;
        case 0x33u: /* OP */
            if (funct3 == 0u && funct7 == 0u) value = report->registers[rs1] + report->registers[rs2];
            else if (funct3 == 0u && funct7 == 0x20u) value = report->registers[rs1] - report->registers[rs2];
            else if (funct3 == 7u && funct7 == 0u) value = report->registers[rs1] & report->registers[rs2];
            else if (funct3 == 6u && funct7 == 0u) value = report->registers[rs1] | report->registers[rs2];
            else if (funct3 == 4u && funct7 == 0u) value = report->registers[rs1] ^ report->registers[rs2];
            else if (funct3 == 2u && funct7 == 0u)
                value = signed_word(report->registers[rs1]) < signed_word(report->registers[rs2]) ? 1u : 0u;
            else return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
            write_register(report, rd, value);
            break;
        case 0x03u: /* LOAD */
            if (funct3 != 2u) return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
            immediate = reaper_sign_extend(word >> 20u, 12u);
            address = add_signed(report->registers[rs1], immediate);
            if (!read_word(report->memory, report->memory_size, address, &value))
                return REAPER_BACKEND_INVALID_MEMORY_ACCESS;
            write_register(report, rd, value);
            break;
        case 0x23u: /* STORE */
            if (funct3 != 2u) return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
            immediate = reaper_sign_extend(
                (((word >> 25u) & 0x7Fu) << 5u) | ((word >> 7u) & 0x1Fu), 12u);
            address = add_signed(report->registers[rs1], immediate);
            if (!write_word(report->memory, report->memory_size, address,
                            report->registers[rs2]))
                return REAPER_BACKEND_INVALID_MEMORY_ACCESS;
            break;
        case 0x63u: /* BRANCH */
            if (funct3 != 0u && funct3 != 1u) return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
            immediate = reaper_sign_extend(
                (((word >> 31u) & 1u) << 12u) |
                (((word >> 7u) & 1u) << 11u) |
                (((word >> 25u) & 0x3Fu) << 5u) |
                (((word >> 8u) & 0xFu) << 1u), 13u);
            if ((funct3 == 0u && report->registers[rs1] == report->registers[rs2]) ||
                (funct3 == 1u && report->registers[rs1] != report->registers[rs2]))
                next_pc = add_signed(report->pc, immediate);
            break;
        case 0x6Fu: /* JAL */
            immediate = reaper_sign_extend(
                (((word >> 31u) & 1u) << 20u) |
                (((word >> 12u) & 0xFFu) << 12u) |
                (((word >> 20u) & 1u) << 11u) |
                (((word >> 21u) & 0x3FFu) << 1u), 21u);
            write_register(report, rd, next_pc);
            next_pc = add_signed(report->pc, immediate);
            break;
        case 0x67u: /* JALR */
            if (funct3 != 0u) return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
            immediate = reaper_sign_extend(word >> 20u, 12u);
            value = add_signed(report->registers[rs1], immediate) & ~UINT32_C(1);
            write_register(report, rd, next_pc);
            next_pc = value;
            break;
        default:
            return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
        }

        if (report->trace_count < REAPER_RV32_TRACE_CAPACITY) {
            report->trace[report->trace_count].pc = report->pc;
            report->trace[report->trace_count].instruction = word;
            ++report->trace_count;
        } else {
            report->trace_truncated = 1u;
        }
        report->registers[0] = 0u;
        report->pc = next_pc;
        ++report->steps;
    }
    if (report->pc == code_end) {
        report->halted = 1u;
        return REAPER_BACKEND_OK;
    }
    return REAPER_BACKEND_STEP_LIMIT;
}
