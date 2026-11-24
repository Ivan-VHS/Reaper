# Reaper Toolchain Atlas — integrated environment inventory

Reaper Toolchain Atlas is a read-only environment inventory for the language and runtime domain represented by catalogue entries 251–310. It combines one declarative catalogue, bounded probes, deterministic aggregation and three report formats.

Examples:

    python tools/reaper_runtime_inventory.py
    python tools/reaper_runtime_inventory.py --family compiled --family proof --format markdown
    python tools/reaper_runtime_inventory.py --available-only --format json --output reports/toolchains.json
    python tools/reaper_runtime_inventory.py --workers 8 --timeout 3 --search-path "C:\Tools\bin"

The catalogue is descriptive metadata, not a bundled compiler distribution. Every probe uses a fixed argument vector, shell=False, closed standard input, a short timeout and a bounded worker pool. Results preserve catalogue order regardless of completion order. The application distinguishes missing tools from version-probe errors and timeouts; finding an executable does not imply that its full SDK or project build works.

The report schema is reaper.toolchain-atlas.v1. It contains a host summary, per-family counts, exact probe outcomes, executable paths and a policy record. The inventory does not compile, import, evaluate or execute a user's project.

This is an original Reaper-side environment workbench, not a clone or reimplementation of any language or compiler. It contains no bundled third-party binaries, source, logos, interface assets or copied trademarks. Copyright (c) 2026 Ivan-VHS. The repository Apache-2.0 LICENSE remains authoritative.

Test:

    python -m unittest discover -s tests -p "test_reaper_runtime_inventory.py" -v
