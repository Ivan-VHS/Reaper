# CLife Immortality Pod — Reaper adapter

CLife applies the "second life" metaphor to project data, not people or consciousness.
For Reaper, a checkpoint is a bounded, versioned copy of caller-supplied project bytes.

Implemented: SHA-256 snapshots; atomic temp-file + fsync + replace writes; strict schema,
size, project binding and checksum verification; four recovery branches; bounded 256-step
transition interpolation.

Commands:
python -m reaper.clife capture project.rpr .clife/project.json --project-id my-project --generation 1
python -m reaper.clife verify .clife/project.json
python -m reaper.clife restore .clife/project.json recovered/project.rpr --project-id my-project
python -m unittest tests.test_clife -v

Restore exports bytes to a selected path; it does not execute recovered Reaper source.
The 64 MiB payload limit applies. Keep credentials, tokens and private keys out of snapshots.
SHA-256 is an integrity checksum, not a signature or creator-authentication mechanism.
Recovered source must pass normal parsing, testing and review before execution.
