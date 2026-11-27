#include "reaper/processor_backends.h"
#include "processor_backend_internal.h"

static ReaperProcessorBackendStatus encode_instruction(
    const ReaperRv32Instruction *instruction, uint32_t *word,
    ReaperRv32Relocation *relocation, uint32_t word_index
) {
    const uint8_t rd = instruction->rd;
    const uint8_t rs1 = instruction->rs1;
    const uint8_t rs2 = instruction->rs2;
    const int32_t imm = instruction->immediate;
    if (rd > 31u || rs1 > 31u || rs2 > 31u)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    if (instruction->symbol_id != 0u &&
        instruction->opcode != REAPER_RV32_JAL &&
        instruction->opcode != REAPER_RV32_BEQ &&
        instruction->opcode != REAPER_RV32_BNE)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    switch (instruction->opcode) {
    case REAPER_RV32_NOP:
        *word = UINT32_C(0x00000013);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_ADDI:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_i(0x13u, 0u, rd, rs1, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_ANDI:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_i(0x13u, 7u, rd, rs1, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_ORI:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_i(0x13u, 6u, rd, rs1, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_XORI:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_i(0x13u, 4u, rd, rs1, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_SLTI:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_i(0x13u, 2u, rd, rs1, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_LUI:
        if (!reaper_fits_signed(imm, 20u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = (((uint32_t)imm & UINT32_C(0xFFFFF)) << 12u) |
                ((uint32_t)rd << 7u) | UINT32_C(0x37);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_AUIPC:
        if (!reaper_fits_signed(imm, 20u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = (((uint32_t)imm & UINT32_C(0xFFFFF)) << 12u) |
                ((uint32_t)rd << 7u) | UINT32_C(0x17);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_ADD:
    case REAPER_RV32_SUB:
    case REAPER_RV32_AND:
    case REAPER_RV32_OR:
    case REAPER_RV32_XOR:
    case REAPER_RV32_SLT: {
        uint32_t funct3 = 0u;
        uint32_t funct7 = 0u;
        if (instruction->opcode == REAPER_RV32_SUB) funct7 = 0x20u;
        else if (instruction->opcode == REAPER_RV32_AND) funct3 = 7u;
        else if (instruction->opcode == REAPER_RV32_OR) funct3 = 6u;
        else if (instruction->opcode == REAPER_RV32_XOR) funct3 = 4u;
        else if (instruction->opcode == REAPER_RV32_SLT) funct3 = 2u;
        *word = (funct7 << 25u) | ((uint32_t)rs2 << 20u) |
                ((uint32_t)rs1 << 15u) | (funct3 << 12u) |
                ((uint32_t)rd << 7u) | UINT32_C(0x33);
        return REAPER_BACKEND_OK;
    }
    case REAPER_RV32_LW:
    case REAPER_RV32_JALR:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_i(instruction->opcode == REAPER_RV32_LW ? 0x03u : 0x67u,
                                instruction->opcode == REAPER_RV32_LW ? 2u : 0u,
                                rd, rs1, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_SW:
        if (!reaper_fits_signed(imm, 12u)) return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_s(2u, rs1, rs2, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_BEQ:
    case REAPER_RV32_BNE:
        if (instruction->symbol_id != 0u) {
            *word = reaper_encode_b(instruction->opcode == REAPER_RV32_BEQ ? 0u : 1u,
                                    rs1, rs2, 0);
            relocation->word_index = word_index;
            relocation->symbol_id = instruction->symbol_id;
            relocation->addend = imm;
            relocation->kind = REAPER_RV32_RELOC_BRANCH13;
            return REAPER_BACKEND_OK;
        }
        if (!reaper_fits_signed(imm, 13u) || (imm & 1) != 0)
            return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_b(instruction->opcode == REAPER_RV32_BEQ ? 0u : 1u,
                                rs1, rs2, imm);
        return REAPER_BACKEND_OK;
    case REAPER_RV32_JAL:
        if (instruction->symbol_id != 0u) {
            *word = reaper_encode_j(rd, 0);
            relocation->word_index = word_index;
            relocation->symbol_id = instruction->symbol_id;
            relocation->addend = imm;
            relocation->kind = REAPER_RV32_RELOC_JAL20;
            return REAPER_BACKEND_OK;
        }
        if (!reaper_fits_signed(imm, 21u) || (imm & 1) != 0)
            return REAPER_BACKEND_RELOCATION_RANGE;
        *word = reaper_encode_j(rd, imm);
        return REAPER_BACKEND_OK;
    default:
        return REAPER_BACKEND_ILLEGAL_INSTRUCTION;
    }
}

ReaperProcessorBackendStatus reaper_rv32_assemble(
    const ReaperRv32Instruction *instructions, size_t instruction_count,
    const ReaperRv32Label *labels, size_t label_count,
    ReaperRv32Object *output
) {
    size_t i, j;
    if (output == NULL || (instruction_count != 0u && instructions == NULL) ||
        (label_count != 0u && labels == NULL))
        return REAPER_BACKEND_INVALID_ARGUMENT;
    if (instruction_count == 0u || instruction_count > REAPER_RV32_MAX_INSTRUCTIONS ||
        label_count > REAPER_RV32_MAX_SYMBOLS)
        return REAPER_BACKEND_LIMIT_EXCEEDED;
    memset(output, 0, sizeof(*output));
    output->magic = REAPER_RV32_OBJECT_MAGIC;
    output->abi_major = REAPER_PROCESSOR_BACKEND_ABI_MAJOR;
    output->target_id = REAPER_RV32_TARGET_RV32I;
    output->abi_id = REAPER_RV32_ABI_ILP32;
    output->word_count = (uint32_t)instruction_count;
    output->symbol_count = (uint32_t)label_count;

    for (i = 0u; i < label_count; ++i) {
        if (labels[i].symbol_id == 0u ||
            labels[i].instruction_index > instruction_count ||
            labels[i].global_symbol != 1u)
            return REAPER_BACKEND_INVALID_ARGUMENT;
        for (j = 0u; j < i; ++j)
            if (labels[j].symbol_id == labels[i].symbol_id)
                return REAPER_BACKEND_DUPLICATE_SYMBOL;
        output->symbols[i].symbol_id = labels[i].symbol_id;
        output->symbols[i].value_offset = labels[i].instruction_index * 4u;
        output->symbols[i].global_symbol = labels[i].global_symbol;
    }

    for (i = 0u; i < instruction_count; ++i) {
        ReaperRv32Relocation relocation;
        ReaperProcessorBackendStatus status;
        memset(&relocation, 0, sizeof(relocation));
        status = encode_instruction(&instructions[i], &output->words[i],
                                    &relocation, (uint32_t)i);
        if (status != REAPER_BACKEND_OK) return status;
        if (relocation.symbol_id != 0u) {
            if (output->relocation_count >= REAPER_RV32_MAX_RELOCATIONS)
                return REAPER_BACKEND_LIMIT_EXCEEDED;
            output->relocations[output->relocation_count++] = relocation;
        }
    }
    return REAPER_BACKEND_OK;
}
