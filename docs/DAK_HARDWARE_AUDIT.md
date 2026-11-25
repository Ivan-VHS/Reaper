# DAK hardware inventory integration

Reaper can verify the versioned read-only inventory emitted by DAK. The integration is a file-based contract: no daemon, network connection, driver loading or privileged helper is required.

## Collect on the host

From a DAK source checkout with its Python build tools installed:

```sh
python -m dak hardware-inventory --output hardware-inventory.json
```

The collector reads PCI and USB sysfs entries on Linux, or present Plug-and-Play device information through PowerShell on Windows. Device instance identifiers are reduced to keyed hashes using a fresh per-snapshot secret. The original identifiers are not written to the JSON file.

## Audit with Reaper

Install Reaper and run:

```sh
reaper-dak-audit hardware-inventory.json --output hardware-audit.json
```

The audit verifies the exact v1 field set, supported platform, per-device values, summary counts and canonical SHA-256 digest. It then reports devices without a bound driver and devices in a problem state. The bundled JSON Schema is available at `schemas/dak.hardware-inventory.v1.schema.json`.

## Trust and implementation boundary

Both commands are read-only. The Reaper report sets `execution_performed`, `disk_writes_performed` and `drivers_changed` to false. A missing driver is a diagnostic finding, not permission to download or install a driver. Before any later installation workflow exists, DAK still needs verified vendor provenance, signature validation, kernel-ABI and architecture matching, privilege separation, rollback and physical-device testing.

A passing file audit proves that the snapshot matches its declared contract. It does not prove that a driver is correct, that a device works, or that DAK has native kernel support.
