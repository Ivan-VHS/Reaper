# Embedded C workbench

Reference MCU profiles, FLASH/SRAM budgets and starter templates are advisory. MMIO is simulated only. No firmware, bootloader, physical register or device is flashed or written. Verify vendor documentation before hardware use.


## Reaper hardware contract

The native core now exposes a checked MMIO descriptor and host-adapter API in include/reaper/hardware.h. It validates region bounds, register width, alignment, access mode, capabilities and read/write ordering before calling a supplied platform adapter. It does not itself map physical addresses or access a device. Existing MCU profiles and generated linker scripts remain advisory until a specific board, vendor memory map, toolchain and hardware-in-the-loop test are qualified. See [HARDWARE_LANGUAGE.md](HARDWARE_LANGUAGE.md).