# DABI64 Process ABI v1

**Status:** fixed x86-64 syscall register-frame contract and validators implemented in Reaper. DuckOS syscall entry, ring-3 transition, process switching and kernel-enforced isolation are not yet implemented.

## Purpose and boundary

DABI64 Process ABI v1 defines the user-to-kernel syscall convention and a kernel-owned snapshot of the register state. The snapshot is not supplied by user memory and contains no user-provided capability mask, PID, kernel pointer or authority token.

Reaper's System Runtime operation catalogue supplies stable operation IDs and capability requirements. The kernel derives process identity, address-space ownership, handle tables and capability grants from trusted task state, then dispatches only an operation admitted by the current process.

## Register convention

- RAX: Reaper System operation ID.
- RDI, RSI, RDX, R10, R8, R9: six 64-bit arguments, in that order.
- RCX and R11: architecturally overwritten by SYSCALL with the return RIP and user RFLAGS; original caller values are volatile and are not preserved.
- RAX: result on return; errors use the DABI64 status convention defined by the kernel host.
- User RIP is captured from RCX and user RFLAGS from R11 by the architecture entry stub.
- User RSP must be saved before switching to the per-CPU kernel stack.

The kernel entry stub must not call C or dereference user pointers until it has switched to a trusted kernel stack and saved the complete register state.

## Kernel-owned frame v1

The C representation is exactly 160 bytes:

| Offset | Width | Field |
|---:|---:|---|
| 0 | 8 | R15 |
| 8 | 8 | R14 |
| 16 | 8 | R13 |
| 24 | 8 | R12 |
| 32 | 8 | R11 |
| 40 | 8 | R10 |
| 48 | 8 | R9 |
| 56 | 8 | R8 |
| 64 | 8 | RDI |
| 72 | 8 | RSI |
| 80 | 8 | RBP |
| 88 | 8 | RDX |
| 96 | 8 | RCX |
| 104 | 8 | RBX |
| 112 | 8 | RAX / operation |
| 120 | 8 | user RIP |
| 128 | 8 | user RFLAGS |
| 136 | 8 | user RSP |
| 144 | 8 | user CS |
| 152 | 8 | user SS |

v1 uses fixed user selectors CS=0x23 and SS=0x1b. User RIP and RSP must lie in the lower canonical half; RSP must be 8-byte aligned. A syscall may occur with RSP at 8 modulo 16 under the ordinary x86-64 function-entry convention, so the kernel must not impose a 16-byte boundary here. RFLAGS bit 1 must be set and IOPL, NT and VM must remain clear.

## User memory

The lower user address space is the half-open interval [0, 0x0000800000000000). A buffer is range-valid only when addition does not overflow and the complete byte range stays inside this interval. This arithmetic check does not prove that a page is mapped, readable or writable.

Every syscall operation must validate its own argument lengths, access direction, quotas and object ownership. The kernel must copy untrusted input into kernel-owned memory or pin and validate pages before asynchronous use. Never trust a user pointer merely because it lies in the user range.

## Implementation gates

1. DuckOS provides an owned GDT/TSS, per-CPU kernel stack and user-return path.
2. A syscall entry stub preserves all registers, switches stacks before calling C and validates the return state before SYSRET.
3. The task model supplies PID, address space, handle table and capability grants from kernel-owned state.
4. The dispatcher validates operation-specific payloads, quotas, cancellation and status mapping.
5. QEMU tests enter ring 3, exercise valid calls, reject malformed state and prove that kernel addresses and ungranted operations are inaccessible.

This Reaper contract is not evidence that any of those DuckOS kernel gates are complete.
