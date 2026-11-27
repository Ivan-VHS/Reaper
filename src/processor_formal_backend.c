#include "reaper/processor_backends.h"
#include "processor_backend_internal.h"

static uint8_t evaluate_net(const ReaperLogicNet *net, uint32_t input_value) {
    uint8_t wires[REAPER_LOGIC_MAX_WIRES] = {0};
    uint32_t i;
    for (i = 0u; i < net->input_count; ++i)
        wires[i] = (uint8_t)((input_value >> i) & 1u);
    for (i = 0u; i < net->gate_count; ++i) {
        const ReaperLogicGate *gate = &net->gates[i];
        const uint32_t output = (uint32_t)net->input_count + i;
        const uint8_t a = wires[gate->input_a];
        const uint8_t b = wires[gate->input_b];
        switch (gate->operation) {
        case REAPER_LOGIC_AND: wires[output] = (uint8_t)(a & b); break;
        case REAPER_LOGIC_OR: wires[output] = (uint8_t)(a | b); break;
        case REAPER_LOGIC_XOR: wires[output] = (uint8_t)(a ^ b); break;
        case REAPER_LOGIC_NOT: wires[output] = (uint8_t)(a ^ 1u); break;
        default: return 0u;
        }
    }
    return wires[net->output_wire];
}

ReaperProcessorBackendStatus reaper_formal_equivalence(
    const ReaperLogicNet *left, const ReaperLogicNet *right,
    ReaperFormalReport *report
) {
    uint32_t input_value;
    uint32_t case_count;
    ReaperProcessorBackendStatus status;
    if (report == NULL || left == NULL || right == NULL)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    memset(report, 0, sizeof(*report));
    report->outcome = REAPER_FORMAL_UNKNOWN;
    if (left->input_count > REAPER_LOGIC_MAX_FORMAL_INPUTS ||
        right->input_count > REAPER_LOGIC_MAX_FORMAL_INPUTS)
        return REAPER_BACKEND_LIMIT_EXCEEDED;
    status = reaper_logic_net_validate(left);
    if (status != REAPER_BACKEND_OK) return status;
    status = reaper_logic_net_validate(right);
    if (status != REAPER_BACKEND_OK) return status;
    if (left->input_count != right->input_count)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    case_count = UINT32_C(1) << left->input_count;
    report->outcome = REAPER_FORMAL_PROVED;
    for (input_value = 0u; input_value < case_count; ++input_value) {
        const uint8_t left_output = evaluate_net(left, input_value);
        const uint8_t right_output = evaluate_net(right, input_value);
        ++report->cases_checked;
        if (left_output != right_output) {
            report->outcome = REAPER_FORMAL_COUNTEREXAMPLE;
            report->counterexample_inputs = input_value;
            report->left_output = left_output;
            report->right_output = right_output;
            break;
        }
    }
    return REAPER_BACKEND_OK;
}
