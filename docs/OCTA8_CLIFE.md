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

The 8 facets are: value kind, boundedness, schema version, deterministic encoding, validation, digest, failure reporting and adapter ownership. Counts in registries or catalogues are not interpreted as completed runtime features.
