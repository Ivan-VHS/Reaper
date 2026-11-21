# Clinical Systems Reliability — CSR-120

Engineering analogy and telemetry rule catalogue; **not a medical or clinical diagnostic product**.

| Item | Count |
|---|---:|
| Versioned principles | 120 |
| Domains | 8 |
| Executable checks | 36 |
| JSON contract | csr-120/v1 |
| Exit codes | 0 healthy/catalog · 1 findings · 2 invalid/error |

| IDs | Domain |
|---|---|
| 001–015 | Transport |
| 016–030 | Signals |
| 031–045 | Homeostasis |
| 046–060 | Defense |
| 061–075 | Dosing |
| 076–090 | Lifecycle |
| 091–105 | Diagnostics |
| 106–120 | Operator |

Run `python tools/clinical_systems.py --catalog --pretty` or pass a JSON telemetry file. Principles without a matching executable check are design concepts, not live detectors.
