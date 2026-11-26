# Reaper evolution engine

The engine is a governed proposal lifecycle, not an unrestricted autonomous agent.

| State | Gate |
|---|---|
| Observe | test/build evidence |
| Diagnose | root cause |
| Plan | measurable acceptance |
| Implement | scoped branch |
| Verify | regression and compatibility |
| Review | human maintainer |
| Promote | protected merge |

Native execution, plugin loading and external side effects require independent capability controls.

## Framework Family 66

The native C17 core registers 66 specialized framework profiles. Each profile
declares a Latin-only identifier, domain, specialization, expected deliverable
and required evidence flags. The registry is exposed through
`reaper_framework_catalog_*`, `reaper_framework_find` and
`reaper_framework_assess`; CLI discovery is available with
`reaper-c --frameworks` and `reaper-c --framework NAME`.

Assessment is intentionally conservative: missing evidence produces
`blocked`; complete evidence produces `review-required`, never an approval.
The profiles do not yet imply 66 independent scanners or source mutators.
Future adapters must be implemented and verified separately within the
existing Observe → Diagnose → Plan → Implement → Verify → Review → Promote
lifecycle.
