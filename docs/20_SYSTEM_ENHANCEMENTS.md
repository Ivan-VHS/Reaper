# Reaper: 20-system engineering programme

The twenty tracks are represented as immutable engineering contracts. They are intentionally not marketed as twenty completed runtime features. Each track states a runtime-specific focus, a constraint, and an acceptance condition.

| Track | Reaper focus |
|---|---|
| Chrome Ironclad | Runtime reliability |
| Velocity Tempest | Repeatable performance measurement |
| Midnight Monolith | Lexer/parser/runtime modularity |
| Raven Vortex | Source-aware diagnostics |
| Circuit Cobalt | Value and operator semantics |
| Thunder Phantom | Cooperative bounded execution |
| Phantom Radiance | CLI and Python API |
| Velvet Gravitas | Developer experience |
| Obsidian Inferno | Typed error handling |
| Horizon Spectral | Python/platform portability |
| Crimson Overdrive | Future backend conformance |
| Voltage Citadel | Explicit host-effect security |
| Shadow Nemesis | Negative and boundary testing |
| Mirage Aether | Distributed execution contracts |
| Titanium Riptide | Resource limits |
| Eclipse Outlaw | Versioned extension points |
| Neutron Zenith | Profiling provenance |
| Scarlet Avalanche | CI automation |
| Quantum Paradox | Opt-in experimental features |
| Reactor Afterglow | Runtime observability |

## Safety and status

The registry is metadata only. It does not grant Reaper programs filesystem, network, subprocess, or native-code access. The interpreter's existing step, call-depth, collection, and text limits remain authoritative. Future backend or distributed features must preserve interpreter semantics and pass the same conformance tests before being exposed.

## Usage

Run `python -m reaper --systems` to print the catalogue. Run `python -m unittest discover -s tests -v` to validate it alongside the language suite.
