#include "reaper/processor_backends.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    ReaperLogicNet net;
    char output[1024];
    size_t written = 0u;
    memset(&net, 0, sizeof(net));
    net.input_count = 2u;
    net.gate_count = 1u;
    net.gates[0].operation = REAPER_LOGIC_XOR;
    net.gates[0].input_a = 0u;
    net.gates[0].input_b = 1u;
    net.output_wire = 2u;
    assert(reaper_logic_net_validate(&net) == REAPER_BACKEND_OK);
    assert(reaper_rtl_emit_systemverilog(&net, output, sizeof(output), &written) ==
           REAPER_BACKEND_OK);
    assert(written > 0u);
    assert(strstr(output, "module reaper_fabric_logic") != NULL);
    assert(strstr(output, "wire_value[2] = wire_value[0] ^ wire_value[1]") != NULL);
    assert(strstr(output, "assign out = wire_value[2]") != NULL);
    assert(reaper_rtl_emit_systemverilog(&net, output, 8u, &written) ==
           REAPER_BACKEND_OUTPUT_TOO_SMALL);
    net.gates[0].input_a = 2u;
    assert(reaper_logic_net_validate(&net) == REAPER_BACKEND_INVALID_NET);
    puts("Combinational RTL emitter tests passed");
    return 0;
}
