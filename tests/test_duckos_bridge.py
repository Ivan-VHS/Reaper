from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reaper.duckos_bridge import (
    DuckOSInventoryError, REPORT_SCHEMA, audit_file, audit_snapshot, main,
)


def make_snapshot():
    devices = [
        {
            "identity_sha256": "1" * 64, "bus": "pci",
            "vendor_id": "0x10de", "device_id": "0x2f05",
            "device_class": "0x030000", "friendly_name": "Example display adapter",
            "driver": "example_gpu", "status": "driver_bound",
        },
        {
            "identity_sha256": "2" * 64, "bus": "usb",
            "vendor_id": "0x046d", "device_id": "0xc548",
            "device_class": "00", "friendly_name": "Example USB device",
            "driver": None, "status": "driver_missing",
        },
        {
            "identity_sha256": "3" * 64, "bus": "pnp",
            "vendor_id": None, "device_id": None,
            "device_class": "System", "friendly_name": "Example system device",
            "driver": None, "status": "device_problem",
        },
    ]
    snapshot = {
        "schema": "duckos.hardware-inventory.v1",
        "captured_utc": "2026-11-23T10:00:00Z",
        "source": {
            "provider": "duckos-host-inventory", "mode": "read_only",
            "platform": "windows", "architecture": "amd64",
        },
        "summary": {
            "total_devices": 3, "driver_bound": 1,
            "driver_missing": 1, "device_problem": 1,
        },
        "devices": devices,
    }
    snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return snapshot


class DuckOSBridgeTests(unittest.TestCase):
    def test_valid_snapshot_produces_read_only_audit_findings(self):
        report = audit_snapshot(make_snapshot())
        self.assertEqual(report["schema"], REPORT_SCHEMA)
        self.assertTrue(report["valid"])
        self.assertEqual(report["status"], "attention_required")
        self.assertEqual(report["summary"]["findings"], 2)
        self.assertEqual(
            {item["code"] for item in report["findings"]},
            {"DUCKOS-DRIVER-MISSING", "DUCKOS-DEVICE-PROBLEM"},
        )
        self.assertFalse(report["execution_performed"])
        self.assertFalse(report["disk_writes_performed"])
        self.assertFalse(report["drivers_changed"])

    def test_changed_content_is_rejected_by_snapshot_digest(self):
        snapshot = make_snapshot()
        snapshot["devices"][0]["driver"] = "untrusted_change"
        with self.assertRaisesRegex(DuckOSInventoryError, "SHA-256"):
            audit_snapshot(snapshot)

    def test_inconsistent_summary_is_rejected_even_with_resealed_hash(self):
        snapshot = make_snapshot()
        snapshot["summary"]["driver_bound"] = 2
        unsigned = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(DuckOSInventoryError, "summary.driver_bound"):
            audit_snapshot(snapshot)

    def test_bound_driver_cannot_be_missing_from_record(self):
        snapshot = make_snapshot()
        snapshot["devices"][0]["driver"] = None
        unsigned = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(DuckOSInventoryError, "bound driver"):
            audit_snapshot(snapshot)

    def test_cli_reads_snapshot_and_writes_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "inventory.json"
            output = Path(temporary) / "audit.json"
            source.write_text(json.dumps(make_snapshot()), encoding="utf-8")
            self.assertEqual(main([str(source), "--output", str(output)]), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["schema"], REPORT_SCHEMA)
            self.assertTrue(report["valid"])
            self.assertEqual(audit_file(source)["summary"]["total_devices"], 3)

    def test_cli_refuses_to_overwrite_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "inventory.json"
            source.write_text(json.dumps(make_snapshot()), encoding="utf-8")
            self.assertEqual(main([str(source), "--output", str(source)]), 2)

    def test_file_reader_rejects_duplicate_json_properties(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "duplicate.json"
            source.write_text(
                '{"schema":"duckos.hardware-inventory.v1","schema":"other"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DuckOSInventoryError, "duplicate JSON property"):
                audit_file(source)

    def test_file_reader_rejects_non_finite_json_constants(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "non-finite.json"
            source.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(DuckOSInventoryError, "non-finite"):
                audit_file(source)

    def test_file_reader_enforces_limit_during_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "oversized.json"
            source.write_bytes(b" " * 65)
            with patch("reaper.duckos_bridge.MAX_SNAPSHOT_BYTES", 64):
                with self.assertRaisesRegex(DuckOSInventoryError, "input limit"):
                    audit_file(source)

    def test_file_reader_rejects_symbolic_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "inventory.json"
            source.write_text(json.dumps(make_snapshot()), encoding="utf-8")
            link = Path(temporary) / "inventory-link.json"
            try:
                link.symlink_to(source)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(DuckOSInventoryError, "non-symlink"):
                audit_file(link)


if __name__ == "__main__":
    unittest.main()
