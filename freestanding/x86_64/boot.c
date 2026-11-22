#include "reaper/freestanding.h"

#define COM1 0x3F8u
#define COM1_LINE_STATUS (COM1 + 5u)

static void serial_init(void) {
    rpr_x86_out8((rpr_u16)(COM1 + 1u), 0x00u);
    rpr_x86_out8((rpr_u16)(COM1 + 3u), 0x80u);
    rpr_x86_out8((rpr_u16)(COM1 + 0u), 0x03u);
    rpr_x86_out8((rpr_u16)(COM1 + 1u), 0x00u);
    rpr_x86_out8((rpr_u16)(COM1 + 3u), 0x03u);
    rpr_x86_out8((rpr_u16)(COM1 + 2u), 0xC7u);
    rpr_x86_out8((rpr_u16)(COM1 + 4u), 0x0Bu);
}

static void serial_write_char(char value) {
    while ((rpr_x86_in8(COM1_LINE_STATUS) & 0x20u) == 0u) {
        __asm__ volatile("pause");
    }
    rpr_x86_out8((rpr_u16)COM1, (rpr_u8)value);
}

static void serial_write(const char *text) {
    while (*text != '\0') {
        serial_write_char(*text++);
    }
}

RPR_NORETURN RPR_SECTION(".text.boot") void _start(void) {
    rpr_x86_disable_interrupts();
    serial_init();
    serial_write("Reaper freestanding kernel: booted\r\n");

    for (;;) {
        rpr_x86_halt();
    }
}
