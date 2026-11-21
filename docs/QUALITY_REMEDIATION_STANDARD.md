# Quality remediation

`quality-remediation.v1.json` retains the 20×3 correction/coverage/defect matrix.

| Step | Evidence |
|---:|---|
| 1 | reproduce |
| 2 | isolate root cause |
| 3 | patch with rollback |
| 4 | add regression test |
| 5 | run build/CTest/CI |
| 6 | review exact PR head |

Run `python tools/quality_remediation.py --format json`. Broad coverage does not mean unbounded resources.
