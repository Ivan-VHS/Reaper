# Reaper processor/kernel control model v1

**Status:** executable Reaper reference-runtime contracts; not a native scheduler or privileged kernel backend.  
**Scope:** deterministic state transitions, timer arithmetic, pressure response, cooperative quota decisions, bounded trace retention, memory-range admission and verified update staging.

## Architecture

The model separates six concerns that the Embedded C sketch originally placed in one loop:

1. **Core lifecycle:** `boot → idle → active`, with explicit diagnostic, degraded and terminal halted states. Recovery from degraded requires a healthy profile and no active fault. A halted core cannot restart through this policy.
2. **Timebase:** 32-bit counter wrap is calculated modulo (2^{32}). Intervals above the half-range are marked ambiguous; callers must sample often enough to remain within that bound. Jitter is the absolute difference between observed and expected durations.
3. **Pressure governor:** weighted pressure requests observation, diagnostic throttling, degraded operation or a safe stop. It never slows a hard real-time interrupt or silently changes the CPU clock.
4. **Cooperative quotas:** a task may run while budget remains, then yields and receives bounded breath ticks. This is a scheduling decision, not a context switch.
5. **Memory and trace:** memory spans use subtraction-based bounds checks; the trace is a bounded FIFO that reports dropped entries instead of allocating.
6. **Update staging:** checksum, signature and ABI checks precede any commit decision. A commit is deferred until a safe point with no active IRQ and no device-owned DMA buffers. The contract only authorizes an inactive-bank policy decision; it does not write or execute code.

## Executable contract

The source is `selfhost/processor_kernel.rpr`. Its assertions are executed by the Reaper reference runtime through `tests/test_self_hosting.py`. The public contract is deliberately deterministic and uses fixed-capacity inputs.

## Integration rules

- Reaper's MMIO descriptor and DMA ownership contracts remain the authority for device access and DMA lifecycle.
- Atomics and barriers must be implemented by a target backend. `volatile` alone is not a concurrency primitive.
- ISR paths must stay bounded and non-blocking. Telemetry collection may be deferred; it must not delay a hard deadline.
- A trace ring with one writer and multiple readers still requires an explicitly specified atomic publication protocol. The pure contract does not claim lock-free thread safety.
- CRC/checksum detects accidental corruption; update authorization requires a trusted signature verifier and protected key policy.
- Target-specific cache maintenance, timer source stability, interrupt routing, context switches and privilege transitions remain backend responsibilities.

## Acceptance

The self-host test checks legal and illegal lifecycle transitions, saturation, timer wrap, ambiguous intervals, jitter, pressure thresholds, quota exhaustion, range bounds, trace overflow and update deferral for unsafe conditions. The module is a reference semantic contract; native compiler parity is a separate gate.
