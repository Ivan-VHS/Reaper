.section .text.boot,"ax"
.global _start
.type _start,@function

_start:
    cli
    leaq boot_stack_top(%rip), %rsp
    andq $-16, %rsp
    xorq %rbp, %rbp
    call reaper_kernel_main

.Lhalt:
    cli
    hlt
    jmp .Lhalt

.size _start, . - _start

.section .bss.stack,"aw",@nobits
.balign 16
boot_stack_bottom:
    .skip 16384
boot_stack_top:
