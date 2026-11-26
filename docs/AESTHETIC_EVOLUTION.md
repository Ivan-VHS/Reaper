# Reaper Aesthetic & Architecture Evolution Framework

The RAAEF framework family is documented in [frameworks/aesthetic/README.md](../frameworks/aesthetic/README.md). Its canonical public entry point is frameworks/aesthetic/all.rpr; discovery metadata is centralized in frameworks/catalog.v1.json.

RAAEF provides nominal tagged profile contracts, aesthetic HIR/MIR/LIR passes, a Reaper reference-runtime compiler adapter, current-versus-proposed architecture graph validation and comparison, dependency-edge consistency and cycle checks, design quality assessment, and bounded architecture/design/source change planning. Observe returns assessments and architecture deltas without creating a patch plan; propose emits a bounded plan after PLAGUE policy approval and risk/benefit gates.

The design IR is a domain pipeline and must not be confused with the general Reaper compiler IR. The experimental native C17 backend remains a separate, limited scalar compilation path. The RAAEF profile compiler does not yet emit native object code or call a native renderer.

SOMO consults the PLAGUE v1 action-policy module before planning: observation requires read/analysis/report actions, and proposal mode additionally requires the declared plan capability. This is policy integration, not an authenticated repository grant or path-level authorization system.

SOMO defaults to observation and proposal generation. Apply remains blocked even where the PLAGUE policy matrix recognizes the apply mode: repository-grant validation, per-path scope enforcement, revision pinning, patch application, isolated verification, immutable audit and tested rollback are still missing. No main-branch writes, merges or releases are performed by this framework foundation.
