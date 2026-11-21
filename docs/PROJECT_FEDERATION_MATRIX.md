# Four-project federation matrix

| Project | Owns | Reusable interface |
|---|---|---|
| Reaper | language, CLI, orchestration | bounded JSON workflows |
| Pytyliki | C11 processor/memory/metric/DSP core | C ABI v1 |
| OPlague | read-only device/driver diagnostics | versioned snapshots |
| VentuSample | offline procedural audio | pack v1 manifest |

| Pair | Contract | Status |
|---|---|---|
| Reaper ↔ OPlague | device snapshot + comparison report | implemented |
| Reaper ↔ Pytyliki | explicit-path C ABI metrics | optional implemented |
| OPlague ↔ Pytyliki | explicit-path metric cross-check | optional implemented |
| VentuSample → Reaper | pack manifest, 22 descriptors | implemented |
| Reaper → VentuSample | render request | planned |
| VentuSample ↔ Pytyliki | direct adapter | planned |
| VentuSample ↔ OPlague | no useful coupling | not applicable |

Four independent apps; no shared monolithic runtime.
