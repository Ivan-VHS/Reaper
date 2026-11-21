# МОСТ — 66 Russian-native principles

The 66 rules govern exact aliasing, token identity, parser equivalence, diagnostics, compatibility and honest implementation status.

| Invariant | Requirement |
|---|---|
| One language | same Reaper token stream and AST |
| Exact aliases | no stemming or synonym guesses |
| Reserved words | no implied grammar/runtime support |
| Diagnostics | canonical source positions |
| Compatibility | changes versioned and tested |

This is a profile, not a second compiler or runtime.
