#include "appguard.h"
#include <assert.h>
#include <stdio.h>

typedef struct audit_state { unsigned count, denied, degraded; } audit_state;

static void capture_audit(const vee_finding *finding, void *context)
{
    audit_state *state = (audit_state *)context;
    assert(finding != NULL);
    assert(finding->level_id >= 1U && finding->level_id <= 666U);
    assert(finding->rule_id != NULL && finding->rule_id[0] != '\0');
    assert(finding->object_id != NULL && finding->object_id[0] != '\0');
    assert(finding->reason != NULL && finding->reason[0] != '\0');
    state->count += 1U;
    if (finding->decision == VEEELZEVUL_DENY) state->denied += 1U;
    if (finding->decision == VEEELZEVUL_DEGRADE) state->degraded += 1U;
}

int main(void)
{
    vee_guard guard;
    audit_state audit = {0U, 0U, 0U};
    vee_guard_init(&guard, 1024U, 32U, 64U, 128U, capture_audit, &audit);

    assert(vee_guard_check_payload(&guard, 112U, "A-09", "request-1", 512U) == VEEELZEVUL_ALLOW);
    assert(vee_guard_check_payload(&guard, 112U, "A-09", "request-2", 2048U) == VEEELZEVUL_DENY);
    assert(vee_guard_check_collection(&guard, 334U, "M-13", "batch-1", 16U) == VEEELZEVUL_ALLOW);
    assert(vee_guard_check_collection(&guard, 334U, "M-13", "batch-2", 64U) == VEEELZEVUL_DEGRADE);
    assert(vee_guard_check_identifier(&guard, 223U, "M-03", "plugin-1", "plugin-v1") == VEEELZEVUL_ALLOW);
    assert(vee_guard_check_identifier(&guard, 223U, "M-03", "plugin-2", "bad/name") == VEEELZEVUL_DENY);
    assert(vee_guard_check_relative_path(&guard, 445U, "A-12", "plugin-path-1", "plugins/eq.vst3") == VEEELZEVUL_ALLOW);
    assert(vee_guard_check_relative_path(&guard, 445U, "A-12", "plugin-path-2", "../outside.dll") == VEEELZEVUL_DENY);
    assert(vee_guard_check_relative_path(&guard, 445U, "A-12", "plugin-path-3", "/etc/passwd") == VEEELZEVUL_DENY);
    assert(vee_guard_authorize(&guard, 223U, "Я-03", "driver-install", 1) == VEEELZEVUL_ALLOW);
    assert(vee_guard_authorize(&guard, 223U, "Я-03", "driver-install", 0) == VEEELZEVUL_DENY);
    assert(vee_guard_authorize(&guard, 223U, "Я-03", "driver-install", -1) == VEEELZEVUL_DENY);

    assert(audit.count == 12U);
    assert(audit.denied >= 5U);
    assert(audit.degraded == 1U);
    puts("Veelsevul AppGuard runtime smoke tests: PASS");
    return 0;
}
