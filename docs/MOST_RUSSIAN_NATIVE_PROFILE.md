# МОСТ — Russian-native profile

МОСТ is exact lexical aliasing over Reaper, not a second language.

| Item | Count | State |
|---|---:|---|
| Total aliases | 54 | exact mapping |
| Executable in reference subset | 21 | runtime |
| Reserved for future grammar | 33 | lexer only |
| Parser/AST/runtime | 1 | canonical Reaper implementation |
| Morphology/synonym inference | 0 | unsupported |

Aliases normalize before parsing. No grammar fork, morphology engine or semantic resolver is permitted.
