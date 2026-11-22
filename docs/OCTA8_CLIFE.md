# OCTA-8 + CLife federation

Reaper is the control language and reference implementation. OCTA-8 provides eight portable value kinds: null, boolean, signed 64-bit integer, finite number, UTF-8 text, bytes, sequence and record. The JSON envelope is versioned as `ivan-vhs.octa8.v1`.

## Reaper language surface

The reference runtime exposes `octa8_kind`, `octa8_pack`, `octa8_validate`, `octa8_unpack`, `octa8_digest`, `octa8_assert_kind` and `octa8_map`. They are ordinary callables and compose with `::`. The implementation enforces finite numbers, signed-i64 integers, 64 levels of nesting, 100000 aggregate nodes, 1 MiB text and 16 MiB byte values.

```reaper
make source := [1, 2, 3]
make wire := source :: octa8_pack()
assert(octa8_validate(wire), "OCTA-8 envelope failed")
make restored := wire :: octa8_unpack()
emit text(wire :: octa8_digest())
```

## CLife savepoints

`python tools/clife.py snapshot .` creates a bounded ZIP savepoint with a SHA-256 manifest. `verify` checks every stored file; `restore --to PATH` restores into a new directory and refuses to overwrite an existing destination. Build outputs, dependency caches, VCS metadata and previous .clife archives are excluded.

## Federation rule

Reaper owns language semantics and orchestration. Pytyliki remains C11, OPlague remains a read-only Python workbench, and VentuSample remains C++20. They share the OCTA-8 JSON envelope and CLife snapshot contract; native engines are not replaced by Reaper and no automatic code or plugin loading is introduced.

The machine-readable contracts are [OCTA-8](../schemas/octa8.v1.schema.json) and [CLife snapshots](../schemas/clife.snapshot.v1.schema.json). Run `python -m unittest tests.test_octa8 tests.test_clife -v` for the focused reference-runtime/savepoint checks. The eight *value kinds* are distinct from the eight engineering facets: boundedness, versioning, deterministic encoding, validation, digest, failure reporting, adapter ownership and explicit lifecycle control. Registry counts are not interpreted as completed runtime features.
