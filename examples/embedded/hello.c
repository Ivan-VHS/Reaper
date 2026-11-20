#include <stdint.h>

/* Portable smoke-test entry point; no MCU registers are touched. */
int main(void) {
    volatile uint32_t heartbeat = 0u;
    heartbeat += 1u;
    return heartbeat == 1u ? 0 : 1;
}
