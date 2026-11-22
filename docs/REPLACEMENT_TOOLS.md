# Original replacement tools

The new tools/reaper_runtime_inventory.py utility is an independently written inventory for the programming-language and toolchain domain represented by entries 251-310 in the source catalogue. It checks whether selected compilers and runtimes are present on PATH and asks each installed tool only for a version string.

Run:

    python tools/reaper_runtime_inventory.py
    python tools/reaper_runtime_inventory.py --available-only --json

The catalogue is descriptive metadata, not a bundled compiler distribution. Probes use fixed argument lists, shell=False, closed standard input and a short timeout. The tool never compiles, imports, evaluates or executes a user project. A failed or timed-out probe is reported rather than treated as proof that a toolchain is broken. Tools without a safe, non-interactive version query are deliberately omitted from this first catalogue revision.

This is not a clone or reimplementation of Go, Rust, .NET, Java, Swift, Deno or any other named language runtime. It provides an original Reaper-side inventory layer and does not reuse third-party source code, logos, interface assets or trademarks. Names are used only to identify detected tools.

The new source and tests are original Reaper contributions, copyright (c) 2026 Ivan-VHS, under Apache License 2.0. The repository LICENSE remains authoritative.

Test:

    python -m unittest discover -s tests -p "test_reaper_runtime_inventory.py" -v
