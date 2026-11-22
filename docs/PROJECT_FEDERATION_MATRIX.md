# Four-project federation matrix

| Project | Owns | Reusable interface |
|---|---|---|
| Reaper | language, CLI, orchestration | bounded JSON workflows |
| Pytyliki | C11 processor, memory and metric core | C ABI v1 |
| OPlague | read-only device/driver diagnostics | versioned snapshots |
| VentuSample | independent desktop application | no Reaper runtime interface |

| Pair | Contract | Status |
|---|---|---|
| Reaper ↔ OPlague | device snapshot + comparison report | implemented |
| Reaper ↔ Pytyliki | explicit-path C ABI metrics | optional implemented |
| OPlague ↔ Pytyliki | explicit-path metric cross-check | optional implemented |
| VentuSample ↔ Reaper | no runtime integration | not applicable |

| VentuSample ↔ Pytyliki | direct adapter | planned |
| VentuSample ↔ OPlague | no useful coupling | not applicable |

Four independent apps; no shared monolithic runtime.
