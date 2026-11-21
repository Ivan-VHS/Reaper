# Data and workflow composition

Reaper composes values with `::`, while modules expose explicitly exported bindings.

| Layer | Contract |
|---|---|
| Collections | bounded map/keep/fold |
| Modules | UTF-8 .rpr, canonical relative paths |
| Imports | exports only; cycle detection |
| Composition | deterministic input order |
| Effects | explicit; no implicit host access |

This is language-level composition, not an always-on distributed service.
