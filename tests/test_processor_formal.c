#include "reaper/processor_backends.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    ReaperLogicNet xor_net, equivalent_net, different_net, too_wide;
    ReaperFormalReport report;
    memset(&xor_net, 0, sizeof(xor_net));
    xor_net.input_count = 2u;
    xor_net.gate_count = 1u;
    xor_net.gates[0] = (ReaperLogicGate){REAPER_LOGIC_XOR, 0u, 1u};
    xor_net.output_wire = 2u;

    memset(&equivalent_net, 0, sizeof(equivalent_net));
    equivalent_net.input_count = 2u;
    equivalent_net.gate_count = 4u;
    equivalent_net.gates[0] = (ReaperLogicGate){REAPER_LOGIC_OR, 0u, 1u};
    equivalent_net.gates[1] = (ReaperLogicGate){REAPER_LOGIC_AND, 0u, 1u};
    equivalent_net.gates[2] = (ReaperLogicGate){REAPER_LOGIC_NOT, 3u, 0u};
    equivalent_net.gates[3] = (ReaperLogicGate){REAPER_LOGIC_AND, 2u, 4u};
    equivalent_net.output_wire = 5u;
    assert(reaper_formal_equivalence(&xor_net, &equivalent_net, &report) ==
           REAPER_BACKEND_OK);
    assert(report.outcome == REAPER_FORMAL_PROVED);
    assert(report.cases_checked == 4u);

    memset(&different_net, 0, sizeof(different_net));
    different_net.input_count = 2u;
    different_net.gate_count = 1u;
    different_net.gates[0] = (ReaperLogicGate){REAPER_LOGIC_AND, 0u, 1u};
    different_net.output_wire = 2u;
    assert(reaper_formal_equivalence(&xor_net, &different_net, &report) ==
           REAPER_BACKEND_OK);
    assert(report.outcome == REAPER_FORMAL_COUNTEREXAMPLE);
    assert(report.cases_checked < 4u);

    too_wide = xor_net;
    too_wide.input_count = 9u;
    assert(reaper_formal_equivalence(&too_wide, &too_wide, &report) ==
           REAPER_BACKEND_LIMIT_EXCEEDED);
    assert(report.outcome == REAPER_FORMAL_UNKNOWN);
    puts("Bounded formal Boolean equivalence tests passed");
    return 0;
}
