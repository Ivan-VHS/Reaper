# Python reference runtime

| Contract | Current limit/behavior |
|---|---|
| Source | UTF-8 .rpr; max 2 MB per module |
| Import depth | ≤64; cycles rejected |
| Heap accounting | default 64 MiB estimate |
| Open resources | default ≤64 handles |
| Execution | step and call-depth quotas |
| Effects | explicit file/console built-ins; no implicit network/shell/clock |
| Modules | exports only; relative canonical paths |

Heap byte counts are host-runtime estimates, not a process-RSS cap or security sandbox. Python is the compatibility reference; native C17 parity is incomplete.
