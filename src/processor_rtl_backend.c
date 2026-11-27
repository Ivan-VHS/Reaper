#include "reaper/processor_backends.h"

#include <stdarg.h>
#include <stdio.h>


static ReaperProcessorBackendStatus append_text(
    char *buffer, size_t capacity, size_t *used, const char *format, ...
) {
    int count;
    va_list arguments;
    if (*used >= capacity) return REAPER_BACKEND_OUTPUT_TOO_SMALL;
    va_start(arguments, format);
    count = vsnprintf(buffer + *used, capacity - *used, format, arguments);
    va_end(arguments);
    if (count < 0 || (size_t)count >= capacity - *used)
        return REAPER_BACKEND_OUTPUT_TOO_SMALL;
    *used += (size_t)count;
    return REAPER_BACKEND_OK;
}

ReaperProcessorBackendStatus reaper_rtl_emit_systemverilog(
    const ReaperLogicNet *net, char *buffer, size_t capacity, size_t *written
) {
    uint32_t i, wire_count;
    size_t used = 0u;
    ReaperProcessorBackendStatus status;
    if (written == NULL || buffer == NULL || capacity == 0u)
        return REAPER_BACKEND_INVALID_ARGUMENT;
    *written = 0u;
    status = reaper_logic_net_validate(net);
    if (status != REAPER_BACKEND_OK) return status;
    wire_count = (uint32_t)net->input_count + net->gate_count;
    status = append_text(buffer, capacity, &used,
        "module reaper_fabric_logic(input logic [%u:0] in, output logic out);\n",
        (unsigned)net->input_count - 1u);
    if (status != REAPER_BACKEND_OK) return status;
    status = append_text(buffer, capacity, &used, "  logic [%u:0] wire_value;\n",
                         wire_count - 1u);
    if (status != REAPER_BACKEND_OK) return status;
    for (i = 0u; i < net->input_count; ++i) {
        status = append_text(buffer, capacity, &used,
                             "  assign wire_value[%u] = in[%u];\n", i, i);
        if (status != REAPER_BACKEND_OK) return status;
    }
    for (i = 0u; i < net->gate_count; ++i) {
        const ReaperLogicGate *gate = &net->gates[i];
        const uint32_t target = (uint32_t)net->input_count + i;
        const char *operator_text = gate->operation == REAPER_LOGIC_AND ? "&" :
            gate->operation == REAPER_LOGIC_OR ? "|" :
            gate->operation == REAPER_LOGIC_XOR ? "^" : "~";
        if (gate->operation == REAPER_LOGIC_NOT)
            status = append_text(buffer, capacity, &used,
                "  assign wire_value[%u] = ~wire_value[%u];\n", target, gate->input_a);
        else
            status = append_text(buffer, capacity, &used,
                "  assign wire_value[%u] = wire_value[%u] %s wire_value[%u];\n",
                target, gate->input_a, operator_text, gate->input_b);
        if (status != REAPER_BACKEND_OK) return status;
    }
    status = append_text(buffer, capacity, &used,
                         "  assign out = wire_value[%u];\nendmodule\n",
                         net->output_wire);
    if (status != REAPER_BACKEND_OK) return status;
    *written = used;
    return REAPER_BACKEND_OK;
}
