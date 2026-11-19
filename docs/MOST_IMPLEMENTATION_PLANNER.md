# MOST implementation planner

`tools/most_plan.py` turns `language/features.json` into a deterministic,
dependency-aware work plan. It does not modify feature statuses or source files.

## Usage

```sh
python tools/most_plan.py
python tools/most_plan.py --target MOST-TYP-002
python tools/most_plan.py --target MOST-TYP-002 --target MOST-EFF-001 --format json
```

A target plan includes its transitive dependencies. Features in `implemented`
or `verified` state are treated as complete; every other selected feature is
listed in dependency order with explicit blockers and its acceptance gates.
The tool rejects unknown IDs, missing dependencies and dependency cycles via
the shared registry validator.

This is planning support, not an implementation claim: a feature becomes
complete only after its implementation and verification evidence are reviewed
and its registry status is deliberately updated.
