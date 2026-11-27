#include "reaper/processor_backends.h"

ReaperProcessorBackendStatus reaper_logic_net_validate(const ReaperLogicNet *net) {
    uint32_t wire_count;
    uint32_t i;
    if (net == NULL || net->input_count == 0u ||
        net->input_count > REAPER_LOGIC_MAX_INPUTS ||
        net->gate_count > REAPER_LOGIC_MAX_GATES)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    wire_count = (uint32_t)net->input_count + net->gate_count;
    if (net->output_wire >= wire_count) return REAPER_BACKEND_INVALID_NET;
    for (i = 0u; i < net->gate_count; ++i) {
        const ReaperLogicGate *gate = &net->gates[i];
        const uint32_t current_wire = (uint32_t)net->input_count + i;
        if ((unsigned)gate->operation > (unsigned)REAPER_LOGIC_NOT ||
            gate->input_a >= current_wire)
            return REAPER_BACKEND_INVALID_NET;
        if (gate->operation != REAPER_LOGIC_NOT && gate->input_b >= current_wire)
            return REAPER_BACKEND_INVALID_NET;
    }
    return REAPER_BACKEND_OK;
}

