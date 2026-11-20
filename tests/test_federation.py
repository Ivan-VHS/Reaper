from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from reaper.federation import (
    OPLAGE_SNAPSHOT_SCHEMA,
    REAPER_COMPARISON_SCHEMA,
    compare_oplage_snapshots,
    oplage_metrics,
    read_json,
    write_json,
)
from reaper import Interpreter, ReaperRuntimeError


def snapshot(metrics: dict[str, float], digest: str) -> dict[str, object]:
    values = {
        "device_ok_ratio": 0.0,
        "device_problem_free_ratio": 0.0,
        "device_class_coverage_ratio": 0.0,
        "device_identity_coverage_ratio": 0.0,
        "package_integrity_ratio": 0.0,
        "package_audit_coverage_ratio": 0.0,
    }
    values.update(metrics)
    result: dict[str, object] = {
        "schema": OPLAGE_SNAPSHOT_SCHEMA,
        "captured_utc": "2026-11-20T00:00:00Z",
        "source": {"provider": f"test-{digest}", "mode": "read_only"},
        "identity_protection": {
            "algorithm": "HMAC-SHA-256", "key_scope": "snapshot_ephemeral",
        },
        "summary": {
            "total_devices": 0, "ok_devices": 0, "problem_devices": 0,
            "other_status_devices": 0, "devices_with_class": 0,
            "devices_with_identity": 0, "audited_packages": 0, "valid_packages": 0,
        },
        "metrics": values,
        "devices": [],
        "packages": [],
    }
    canonical = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    result["snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


def reseal_snapshot(value: dict[str, object]) -> dict[str, object]:
    payload = dict(value)
    payload.pop("snapshot_sha256", None)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    value["snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()
    return value


class FederationJsonTests(unittest.TestCase):
    def test_json_round_trip_and_atomic_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            value = {"nested": {"ok": True}, "numbers": [0.25, 1.0]}
            self.assertEqual(write_json(path, value), str(path))
            self.assertEqual(read_json(path), value)
            self.assertFalse(list(Path(directory).glob("*.tmp")))

    def test_rejects_duplicate_keys_non_finite_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                read_json(path)
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                read_json(path)
            link = Path(directory) / "link.json"
            try:
                link.symlink_to(path)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                read_json(link)

    def test_write_rejects_non_finite_and_non_json_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output.json"
            with self.assertRaisesRegex(ValueError, "finite JSON"):
                write_json(path, {"bad": float("nan")})
            with self.assertRaisesRegex(ValueError, "finite JSON"):
                write_json(path, {"bad": object()})


class OPlagueContractTests(unittest.TestCase):
    def test_extracts_sorted_normalized_metric_map(self) -> None:
        result = oplage_metrics(snapshot({"z": 0.5, "a": 1}, "x"))
        self.assertEqual(list(result), sorted(result))
        self.assertEqual(result["a"], 1.0)
        self.assertEqual(result["z"], 0.5)
        self.assertEqual(len(result), 8)

    def test_rejects_wrong_schema_invalid_values_and_bool(self) -> None:
        with self.assertRaisesRegex(ValueError, "schema"):
            oplage_metrics({"schema": "other", "metrics": {"x": 0.5}})
        for invalid in (True, -0.1, 1.1, float("inf"), "0.5"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    oplage_metrics(snapshot({"x": invalid}, "x"))

    def test_compares_snapshots_and_exposes_component_contributions(self) -> None:
        left = snapshot({"cpu": 0.8, "memory": 0.5}, "left")
        right = snapshot({"cpu": 0.6, "memory": 1.0}, "right")
        result = compare_oplage_snapshots(left, right)
        self.assertEqual(result["schema"], REAPER_COMPARISON_SCHEMA)
        self.assertEqual(result["mode"], "read_only")
        self.assertAlmostEqual(result["euclidean_distance"], (0.2**2 + 0.5**2) ** 0.5)
        self.assertAlmostEqual(result["components"]["memory"]["difference"], 0.5)
        self.assertEqual(result["distance_backend"], "reaper-python")

    def test_rejects_tampered_snapshot_fingerprint(self) -> None:
        value = snapshot({"device_ok_ratio": 0.5}, "tampered")
        value["metrics"]["device_ok_ratio"] = 0.25
        with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
            oplage_metrics(value)

    def test_rejects_dimension_drift(self) -> None:
        with self.assertRaisesRegex(ValueError, "dimensions differ"):
            compare_oplage_snapshots(snapshot({"cpu": 0.8}, "a"), snapshot({"gpu": 0.8}, "b"))


class FederationLanguageTests(unittest.TestCase):
    def test_rpr_can_load_snapshot_extract_metrics_and_write_report(self) -> None:
        source = """
        make baseline := read_json("baseline.json")
        make current := read_json("current.json")
        make metrics := oplage_metrics(current)
        make report := oplage_compare(baseline, current)
        emit report["schema"]
        emit report["distance_backend"]
        emit text(metrics["device_ok_ratio"])
        write_json("audit.json", report)
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "baseline.json", snapshot({"device_ok_ratio": 1.0}, "old"))
            write_json(root / "current.json", snapshot({"device_ok_ratio": 0.5}, "new"))
            original = Path.cwd()
            try:
                import os
                os.chdir(root)
                output: list[str] = []
                Interpreter(output=output.append).run(source, "federation.rpr")
                saved = read_json(root / "audit.json")
            finally:
                os.chdir(original)
        self.assertEqual(output, [REAPER_COMPARISON_SCHEMA, "reaper-python", "0.5"])
        self.assertAlmostEqual(saved["euclidean_distance"], 0.5)

    def test_rpr_rejects_invalid_snapshot_with_source_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "invalid.json").write_text(
                json.dumps({"schema": "wrong", "metrics": {"cpu": 0.5}}),
                encoding="utf-8",
            )
            original = Path.cwd()
            try:
                import os
                os.chdir(root)
                interpreter = Interpreter(output=lambda _line: None)
                with self.assertRaisesRegex(ReaperRuntimeError, r"oplage_metrics\(\).*schema"):
                    interpreter.run('make invalid := read_json("invalid.json")\nemit oplage_metrics(invalid)')
            finally:
                os.chdir(original)



if __name__ == "__main__":
    unittest.main()
