from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from reaper.dak_bridge import (
    DAKInventoryError, REPORT_SCHEMA, audit_file, audit_snapshot, main,
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
        "schema": "dak.hardware-inventory.v1",
        "captured_utc": "2026-11-23T10:00:00Z",
        "source": {
            "provider": "dak-host-inventory", "mode": "read_only",
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


class DAKBridgeTests(unittest.TestCase):
    def test_valid_snapshot_produces_read_only_audit_findings(self):
        report = audit_snapshot(make_snapshot())
        self.assertEqual(report["schema"], REPORT_SCHEMA)
        self.assertTrue(report["valid"])
        self.assertEqual(report["status"], "attention_required")
        self.assertEqual(report["summary"]["findings"], 2)
        self.assertEqual(
            {item["code"] for item in report["findings"]},
            {"DAK-DRIVER-MISSING", "DAK-DEVICE-PROBLEM"},
        )
        self.assertFalse(report["execution_performed"])
        self.assertFalse(report["disk_writes_performed"])
        self.assertFalse(report["drivers_changed"])

    def test_changed_content_is_rejected_by_snapshot_digest(self):
        snapshot = make_snapshot()
        snapshot["devices"][0]["driver"] = "untrusted_change"
        with self.assertRaisesRegex(DAKInventoryError, "SHA-256"):
            audit_snapshot(snapshot)

    def test_inconsistent_summary_is_rejected_even_with_resealed_hash(self):
        snapshot = make_snapshot()
        snapshot["summary"]["driver_bound"] = 2
        unsigned = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(DAKInventoryError, "summary.driver_bound"):
            audit_snapshot(snapshot)

    def test_bound_driver_cannot_be_missing_from_record(self):
        snapshot = make_snapshot()
        snapshot["devices"][0]["driver"] = None
        unsigned = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(DAKInventoryError, "bound driver"):
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


if __name__ == "__main__":
    unittest.main()
