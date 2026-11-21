# Project stewardship

| Principle | Acceptance |
|---|---|
| Semantics first | user problems and tested language behavior before registry counts |
| Status honesty | implemented / partial / planned / not applicable |
| Authority | explicit owners for parser, runtime, compiler, FFI and security |
| Review | tests, compatibility, threat model and exact PR head |
| Continuity | migration notes, release procedures, reproducible issues |
| Incident | stabilize → assess → contain → communicate → recover → review |

Python is the reference runtime; native extensions are trusted in-process code, not a sandbox.
