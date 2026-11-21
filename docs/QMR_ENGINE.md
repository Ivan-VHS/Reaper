# Reaper QMR — Quality, Cohesion and Cadence

## Purpose

The QMR diagnostic converts three engineering properties into bounded, explainable reports:

- **Quality:** caller-declared checks such as input bounds, typed edges and invariant preservation.
- **Cohesion:** observed compiler/workflow stages compared with an explicit ordered contract.
- **Cadence:** repeated phase durations analyzed for jitter, mean-period bias and first-half/second-half drift.

Cohesion means an end-to-end pipeline whose declared stages are present and correctly ordered. It does not mean merging the compiler into a single source file.

## Python API

`reaper.qmr` provides:

- `analyze_cadence(intervals, expected_interval, tolerance_ratio=0.1)`
- `audit_pipeline_cohesion(actual_stages, expected_stages)`
- `build_qmr_report(quality_checks, actual_stages, expected_stages, intervals, expected_interval)`

The score is descriptive. The caller owns the meaning of each quality check, expected stage sequence and timing observation. The analyzer never executes Reaper source or manufactures benchmark measurements.

## Cadence score

The 0–100 score penalizes coefficient of variation, relative mean-period bias and half-to-half drift. Inputs must be finite positive intervals; the sample count and pipeline size are bounded.

## Verification

Run `python -m unittest tests.test_qmr -v`. Tests cover stable and drifting timing, invalid values, pipeline gaps, duplicate/out-of-order stages and the combined report.
