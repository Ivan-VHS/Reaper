# Reaper Aesthetic & Architecture Evolution Framework

The RAAEF framework family is documented in [frameworks/aesthetic/README.md](../frameworks/aesthetic/README.md). Its canonical public entry point is frameworks/aesthetic/all.rpr; discovery metadata is centralized in frameworks/catalog.v1.json.

RAAEF provides nominal tagged profile contracts, aesthetic HIR/MIR/LIR passes, a Reaper reference-runtime compiler adapter, architecture dependency validation, design quality assessment and bounded architecture/design/source change planning.

The design IR is a domain pipeline and must not be confused with the general Reaper compiler IR. The experimental native C17 backend remains a separate, limited scalar compilation path. The RAAEF profile compiler does not yet emit native object code or call a native renderer.

SOMO defaults to observation and proposal generation. Apply mode remains denied until repository grant validation, path-scope enforcement, patch application, isolated verification, immutable audit and tested rollback are integrated. No main-branch writes, merges or releases are performed by this framework foundation.
