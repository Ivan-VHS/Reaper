# QCS 1.0 frontend

| Stage | Contract |
|---|---|
| Lexer | UTF-8 source and source spans |
| Parser | domain/contour expressions and bounded frames |
| AST | JSON-serializable nodes |
| Validation | syntax, metadata and handoff markers |
| Excluded | driver verification, firmware and hardware execution |

Run `reaper-qcs check examples/qcs_irq.qcs`.


## Relationship to the systems language

QCS remains a separate validation frontend until its grammar and AST can be migrated into the canonical Reaper parser and typed IR without breaking existing QCS files. Its current parser does not read/write MMIO, install drivers, execute firmware, register interrupts or allocate DMA buffers. The shared target architecture and staged convergence plan are in [HARDWARE_LANGUAGE.md](HARDWARE_LANGUAGE.md).