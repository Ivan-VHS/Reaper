#ifndef REAPER_PROCESSOR_BACKENDS_H
#define REAPER_PROCESSOR_BACKENDS_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_PROCESSOR_BACKEND_ABI_MAJOR 1u
#define REAPER_RV32_OBJECT_MAGIC UINT32_C(0x52505631)
#define REAPER_RV32_IMAGE_MAGIC UINT32_C(0x52504931)
#define REAPER_RV32_TARGET_RV32I 1u
#define REAPER_RV32_ABI_ILP32 1u
#define REAPER_RV32_MAX_INSTRUCTIONS 256u
#define REAPER_RV32_MAX_SYMBOLS 64u
#define REAPER_RV32_MAX_RELOCATIONS 128u
#define REAPER_RV32_MAX_OBJECTS 8u
#define REAPER_RV32_MAX_LINK_SYMBOLS (REAPER_RV32_MAX_OBJECTS * REAPER_RV32_MAX_SYMBOLS)
#define REAPER_RV32_MAX_IMAGE_BYTES (REAPER_RV32_MAX_OBJECTS * REAPER_RV32_MAX_INSTRUCTIONS * 4u)
#define REAPER_RV32_DATA_MEMORY_BYTES 4096u
#define REAPER_RV32_MAX_STEPS UINT64_C(1000000)
#define REAPER_RV32_TRACE_CAPACITY 128u
#define REAPER_LOGIC_MAX_INPUTS 32u
#define REAPER_LOGIC_MAX_FORMAL_INPUTS 8u
#define REAPER_LOGIC_MAX_GATES 64u
#define REAPER_LOGIC_MAX_WIRES (REAPER_LOGIC_MAX_INPUTS + REAPER_LOGIC_MAX_GATES)

typedef enum {
    REAPER_BACKEND_OK = 0,
    REAPER_BACKEND_INVALID_ARGUMENT,
    REAPER_BACKEND_LIMIT_EXCEEDED,
    REAPER_BACKEND_INVALID_ABI,
    REAPER_BACKEND_DUPLICATE_SYMBOL,
    REAPER_BACKEND_UNRESOLVED_SYMBOL,
    REAPER_BACKEND_RELOCATION_RANGE,
    REAPER_BACKEND_ILLEGAL_INSTRUCTION,
    REAPER_BACKEND_INVALID_MEMORY_ACCESS,
    REAPER_BACKEND_STEP_LIMIT,
    REAPER_BACKEND_OUTPUT_TOO_SMALL,
    REAPER_BACKEND_INVALID_NET
} ReaperProcessorBackendStatus;

const char *reaper_processor_backend_status_name(ReaperProcessorBackendStatus status);

/* ---------- Native assembler: structured RV32I instruction selection/encoding ---------- */

typedef enum {
    REAPER_RV32_NOP = 0,
    REAPER_RV32_ADDI,
    REAPER_RV32_ANDI,
    REAPER_RV32_ORI,
    REAPER_RV32_XORI,
    REAPER_RV32_SLTI,
    REAPER_RV32_LUI,
    REAPER_RV32_AUIPC,
    REAPER_RV32_ADD,
    REAPER_RV32_SUB,
    REAPER_RV32_AND,
    REAPER_RV32_OR,
    REAPER_RV32_XOR,
    REAPER_RV32_SLT,
    REAPER_RV32_LW,
    REAPER_RV32_SW,
    REAPER_RV32_BEQ,
    REAPER_RV32_BNE,
    REAPER_RV32_JAL,
    REAPER_RV32_JALR
} ReaperRv32Opcode;

typedef struct {
    ReaperRv32Opcode opcode;
    uint8_t rd;
    uint8_t rs1;
    uint8_t rs2;
    int32_t immediate;
    uint32_t symbol_id; /* Non-zero creates a PC-relative relocation for JAL/BEQ/BNE. */
} ReaperRv32Instruction;

typedef struct {
    uint32_t symbol_id;
    uint32_t instruction_index;
    uint8_t global_symbol;
} ReaperRv32Label;

typedef struct {
    uint32_t symbol_id;
    uint32_t value_offset;
    uint8_t global_symbol;
} ReaperRv32Symbol;

typedef enum {
    REAPER_RV32_RELOC_JAL20 = 1,
    REAPER_RV32_RELOC_BRANCH13 = 2
} ReaperRv32RelocationKind;

typedef struct {
    uint32_t word_index;
    uint32_t symbol_id;
    int32_t addend;
    ReaperRv32RelocationKind kind;
} ReaperRv32Relocation;

typedef struct {
    uint32_t magic;
    uint32_t abi_major;
    uint32_t target_id;
    uint32_t abi_id;
    uint32_t word_count;
    uint32_t words[REAPER_RV32_MAX_INSTRUCTIONS];
    uint32_t symbol_count;
    ReaperRv32Symbol symbols[REAPER_RV32_MAX_SYMBOLS];
    uint32_t relocation_count;
    ReaperRv32Relocation relocations[REAPER_RV32_MAX_RELOCATIONS];
} ReaperRv32Object;

ReaperProcessorBackendStatus reaper_rv32_assemble(
    const ReaperRv32Instruction *instructions, size_t instruction_count,
    const ReaperRv32Label *labels, size_t label_count,
    ReaperRv32Object *output
);

/* ---------- Native linker: deterministic bounded flat-image linker ---------- */

typedef struct {
    uint32_t symbol_id;
    uint32_t address;
} ReaperRv32LinkedSymbol;

typedef struct {
    uint32_t magic;
    uint32_t abi_major;
    uint32_t target_id;
    uint32_t abi_id;
    uint32_t base_address;
    uint32_t entry_address;
    uint32_t byte_count;
    uint8_t bytes[REAPER_RV32_MAX_IMAGE_BYTES];
    uint32_t symbol_count;
    ReaperRv32LinkedSymbol symbols[REAPER_RV32_MAX_LINK_SYMBOLS];
} ReaperRv32LinkedImage;

ReaperProcessorBackendStatus reaper_rv32_link(
    const ReaperRv32Object *objects, size_t object_count,
    uint32_t entry_symbol_id, uint32_t base_address,
    ReaperRv32LinkedImage *output
);

/* ---------- Emulator: bounded RV32I subset over caller-owned RAM ---------- */

typedef struct {
    uint32_t registers[32];
    uint32_t pc; /* Zero selects the linked image entry point. */
    uint32_t memory_size; /* Zero selects the fixed 4096-byte local RAM. */
    uint8_t memory[REAPER_RV32_DATA_MEMORY_BYTES];
} ReaperRv32MachineState;

typedef struct {
    uint32_t pc;
    uint32_t instruction;
} ReaperRv32TraceEntry;

typedef struct {
    uint32_t registers[32];
    uint32_t pc;
    uint32_t memory_size;
    uint8_t memory[REAPER_RV32_DATA_MEMORY_BYTES];
    uint64_t steps;
    uint32_t trace_count;
    uint8_t trace_truncated;
    uint8_t halted;
    ReaperRv32TraceEntry trace[REAPER_RV32_TRACE_CAPACITY];
} ReaperRv32ExecutionReport;

ReaperProcessorBackendStatus reaper_rv32_emulate(
    const ReaperRv32LinkedImage *image,
    const ReaperRv32MachineState *initial_state,
    uint64_t max_steps,
    ReaperRv32ExecutionReport *report
);

/* ---------- RTL: combinational Boolean netlist to synthesizable SystemVerilog ---------- */

typedef enum {
    REAPER_LOGIC_AND = 0,
    REAPER_LOGIC_OR,
    REAPER_LOGIC_XOR,
    REAPER_LOGIC_NOT
} ReaperLogicOperation;

typedef struct {
    ReaperLogicOperation operation;
    uint8_t input_a;
    uint8_t input_b;
} ReaperLogicGate;

typedef struct {
    uint8_t input_count;
    uint8_t gate_count;
    ReaperLogicGate gates[REAPER_LOGIC_MAX_GATES];
    uint8_t output_wire;
} ReaperLogicNet;

ReaperProcessorBackendStatus reaper_logic_net_validate(const ReaperLogicNet *net);
ReaperProcessorBackendStatus reaper_rtl_emit_systemverilog(
    const ReaperLogicNet *net, char *buffer, size_t capacity, size_t *written
);

/* ---------- Formal: exhaustive equivalence for bounded combinational nets ---------- */

typedef enum {
    REAPER_FORMAL_PROVED = 0,
    REAPER_FORMAL_COUNTEREXAMPLE,
    REAPER_FORMAL_UNKNOWN
} ReaperFormalOutcome;

typedef struct {
    ReaperFormalOutcome outcome;
    uint32_t cases_checked;
    uint32_t counterexample_inputs;
    uint8_t left_output;
    uint8_t right_output;
} ReaperFormalReport;

ReaperProcessorBackendStatus reaper_formal_equivalence(
    const ReaperLogicNet *left,
    const ReaperLogicNet *right,
    ReaperFormalReport *report
);

#ifdef __cplusplus
}
#endif
#endif
