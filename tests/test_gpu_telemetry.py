from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from reaper.gpu_telemetry import (
    OPLAGE_GPU_SCHEMA,
    load_oplage_gpu_snapshot,
    normalize_oplage_gpu_snapshot,
)


def gpu(**overrides):
    value = {
        "name": "NVIDIA GeForce RTX",
        "driver_version": "570.00",
        "temperature_c": 65,
        "utilization_pct": 75,
        "memory_used_mib": 4096,
        "memory_total_mib": 12288,
        "power_w": 180.5,
        "graphics_clock_mhz": 2400,
        "memory_clock_mhz": 9000,
    }
    value.update(overrides)
    return value


def snapshot(gpus=None, available=True, reason=None):
    value = {
        "schema": OPLAGE_GPU_SCHEMA,
        "snapshot_id": "00000000-0000-4000-8000-000000000001",
        "captured_at": "2026-11-25T12:00:00Z",
        "source": {"provider": "nvidia-smi", "mode": "read_only"},
        "available": available,
        "reason": reason,
        "controls_performed": False,
        "gpus": [gpu()] if gpus is None and available else (gpus or []),
    }
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    value["snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()
    return value


class OPlagueGpuTelemetryTests(unittest.TestCase):
    def test_normalizes_raw_v1_snapshot_for_dak_policy(self) -> None:
        result = normalize_oplage_gpu_snapshot(snapshot())
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], OPLAGE_GPU_SCHEMA)
        self.assertEqual(result[3:9], ["nvidia-smi", "read_only", True, "", False, True])
        self.assertEqual(
            result[9][0],
            ["NVIDIA GeForce RTX", "570.00", 65, 75, 4096, 12288, 180.5, 2400, 9000],
        )

    def test_null_sensors_remain_unknown_not_zero(self) -> None:
        raw = snapshot([gpu(
            temperature_c=None, utilization_pct=None, memory_used_mib=None,
            power_w=None, graphics_clock_mhz=None,
        )])
        result = normalize_oplage_gpu_snapshot(raw)
        self.assertEqual(
            result[9][0],
            ["NVIDIA GeForce RTX", "570.00", "unknown", "unknown", "unknown",
             12288, "unknown", "unknown", 9000],
        )

    def test_unavailable_provider_is_preserved_without_synthetic_gpu(self) -> None:
        raw = snapshot(gpus=[], available=False, reason="nvidia-smi unavailable")
        result = normalize_oplage_gpu_snapshot(raw)
        self.assertEqual(result[5], False)
        self.assertEqual(result[6], "nvidia-smi unavailable")
        self.assertEqual(result[9], [])

    def test_rejects_digest_tampering(self) -> None:
        raw = snapshot()
        raw["gpus"][0]["temperature_c"] = 42
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            normalize_oplage_gpu_snapshot(raw)

    def test_rejects_non_read_only_source_and_controls(self) -> None:
        raw = snapshot()
        raw["source"]["mode"] = "control"
        with self.assertRaisesRegex(ValueError, "read_only"):
            normalize_oplage_gpu_snapshot(raw)
        raw = snapshot()
        raw["controls_performed"] = True
        with self.assertRaisesRegex(ValueError, "must be false"):
            normalize_oplage_gpu_snapshot(raw)

    def test_rejects_extra_keys_bad_sensor_ranges_and_impossible_memory(self) -> None:
        raw = snapshot()
        raw["unexpected"] = True
        with self.assertRaisesRegex(ValueError, "fields are invalid"):
            normalize_oplage_gpu_snapshot(raw)
        raw = snapshot([gpu(utilization_pct=101)])
        with self.assertRaisesRegex(ValueError, "utilization_pct"):
            normalize_oplage_gpu_snapshot(raw)
        raw = snapshot([gpu(memory_used_mib=13000)])
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            normalize_oplage_gpu_snapshot(raw)

    def test_rejects_invalid_gpu_descriptors_and_device_limit(self) -> None:
        raw = snapshot([gpu(), gpu(driver_version="")])
        with self.assertRaisesRegex(ValueError, "driver_version"):
            normalize_oplage_gpu_snapshot(raw)
        raw = snapshot([gpu()] * 17)
        with self.assertRaisesRegex(ValueError, "at most 16"):
            normalize_oplage_gpu_snapshot(raw)

    def test_reads_only_an_explicit_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "gpu.json"
            source.write_text(json.dumps(snapshot()), encoding="utf-8")
            result = load_oplage_gpu_snapshot(source)
        self.assertEqual(result[0], OPLAGE_GPU_SCHEMA)
        self.assertEqual(result[8], True)


if __name__ == "__main__":
    unittest.main()
