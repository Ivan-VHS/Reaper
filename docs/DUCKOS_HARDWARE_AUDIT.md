# DuckOS hardware inventory integration

Reaper can verify the versioned read-only inventory emitted by DuckOS. The integration is a file-based contract: no daemon, network connection, driver loading or privileged helper is required.

## Collect on the host

From a DuckOS source checkout with its Python build tools installed:

```sh
python -m duckos hardware-inventory --output hardware-inventory.json
```

The collector reads PCI and USB sysfs entries on Linux, or present Plug-and-Play device information through PowerShell on Windows. Device instance identifiers are reduced to keyed hashes using a fresh per-snapshot secret. The original identifiers are not written to the JSON file.

## Audit with Reaper

Install Reaper and run:

```sh
reaper-duckos-audit hardware-inventory.json --output hardware-audit.json
```

The audit verifies the exact v1 field set, supported platform, per-device values, summary counts and canonical SHA-256 digest. It then reports devices without a bound driver and devices in a problem state. The bundled JSON Schema is available at `schemas/duckos.hardware-inventory.v1.schema.json`.

## Trust and implementation boundary

Both commands are read-only. The Reaper report sets `execution_performed`, `disk_writes_performed` and `drivers_changed` to false. A missing driver is a diagnostic finding, not permission to download or install a driver. Before any later installation workflow exists, DuckOS still needs verified vendor provenance, signature validation, kernel-ABI and architecture matching, privilege separation, rollback and physical-device testing.

A passing file audit proves that the snapshot matches its declared contract. It does not prove that a driver is correct, that a device works, or that DuckOS has native kernel support.

## Reaper native target roadmap

The read-only hardware inventory audit remains a host-side file contract; it does not load drivers or provide kernel privileges. Reaper's longer-term obligations for DuckOS are specified in [the DuckOS Native Target Profile](DUCKOS_NATIVE_TARGET_PROFILE.md), while the cross-project architecture and migration stages are tracked in the [DuckOS migration blueprint](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/REAPER_DUCKOS_FULL_MIGRATION.md). Neither document changes the current audit's read-only behavior or implies a finished freestanding backend.
