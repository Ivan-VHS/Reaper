# MOST implementation status

| Surface | Count | State |
|---|---:|---|
| Exact aliases | 54 | 31 executable, 23 reserved |
| Semantic grammar | 1 | shared Reaper grammar |
| Parser/AST/runtime | 1 | Python reference interpreter and VM |
| Morphology/synonym resolver | 0 | not supported |

Reserved lexemes do not imply parser or runtime behavior. C17 native parity is tracked separately and is not inferred from Python runtime support.
