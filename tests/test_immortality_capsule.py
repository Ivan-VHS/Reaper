from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter
from reaper.capsule import (
    CapsuleIntegrityError,
    CapsuleNotFoundError,
    CapsuleStore,
    CapsuleStoreError,
)


class CapsuleStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = CapsuleStore(self.temporary.name, max_snapshot_bytes=4096, max_snapshots=3)

    def test_round_trip_and_metadata(self) -> None:
        saved = self.store.save("project-1", {"tracks": [1, 2], "name": "mix"})
        loaded = self.store.load("project-1")
        self.assertEqual(loaded.payload, {"tracks": [1, 2], "name": "mix"})
        self.assertEqual(saved.sha256, loaded.sha256)
        self.assertEqual(saved.revision, 1)
        self.assertFalse(loaded.recovered)

    def test_keeps_bounded_history(self) -> None:
        for value in range(5):
            self.store.save("session", {"value": value})
        directory = Path(self.temporary.name) / "session"
        self.assertEqual(len(list(directory.glob("snapshot-*.json"))), 3)
        self.assertEqual(self.store.load("session").payload, {"value": 4})

    def test_corrupt_head_snapshot_recovers_previous_revision(self) -> None:
        self.store.save("session", {"value": 1})
        latest = self.store.save("session", {"value": 2})
        directory = Path(self.temporary.name) / "session"
        (directory / latest.filename).write_text("{broken", encoding="utf-8")
        loaded = self.store.load("session")
        self.assertEqual(loaded.payload, {"value": 1})
        self.assertTrue(loaded.recovered)
        self.assertEqual(loaded.revision, 1)
        self.assertTrue(self.store.verify("session")["head_valid"])

    def test_payload_tampering_is_detected(self) -> None:
        saved = self.store.save("session", {"value": "original"})
        path = Path(self.temporary.name) / "session" / saved.filename
        envelope = json.loads(path.read_text(encoding="utf-8"))
        envelope["payload"]["value"] = "tampered"
        path.write_text(json.dumps(envelope), encoding="utf-8")
        with self.assertRaises(CapsuleIntegrityError):
            self.store.load("session")

    def test_corrupt_all_snapshots_fails_closed(self) -> None:
        snapshot = self.store.save("session", {"value": 1})
        (Path(self.temporary.name) / "session" / snapshot.filename).write_text("bad", encoding="utf-8")
        with self.assertRaises(CapsuleIntegrityError):
            self.store.load("session")

    def test_missing_capsule_is_reported(self) -> None:
        with self.assertRaises(CapsuleNotFoundError):
            self.store.load("missing")

    def test_ids_cannot_escape_root_or_use_windows_reserved_names(self) -> None:
        for capsule_id in ("../escape", "..", "CON", "NUL.txt", "bad/name", "ends.", ""):
            with self.subTest(capsule_id=capsule_id):
                with self.assertRaises(CapsuleStoreError):
                    self.store.save(capsule_id, {"ok": True})
        self.assertFalse((Path(self.temporary.name).parent / "escape").exists())

    def test_payload_accepts_only_finite_json_values(self) -> None:
        with self.assertRaises(CapsuleStoreError):
            self.store.save("nan", {"value": math.nan})
        with self.assertRaises(CapsuleStoreError):
            self.store.save("object", {"value": object()})
        with self.assertRaises(CapsuleStoreError):
            self.store.save("keys", {1: "not text"})

    def test_circular_payload_is_rejected(self) -> None:
        value = []
        value.append(value)
        with self.assertRaises(CapsuleStoreError):
            self.store.save("cycle", value)

    def test_payload_size_is_bounded(self) -> None:
        with self.assertRaises(CapsuleStoreError):
            self.store.save("large", {"content": "x" * 5000})

    def test_verify_reports_recoverable_revision_without_mutating_head(self) -> None:
        first = self.store.save("verify", {"value": 1})
        second = self.store.save("verify", {"value": 2})
        directory = Path(self.temporary.name) / "verify"
        (directory / second.filename).write_text("broken", encoding="utf-8")
        status = self.store.verify("verify")
        self.assertFalse(status["head_valid"])
        self.assertTrue(status["recoverable"])
        self.assertEqual(status["revision"], first.revision)
        self.assertTrue(self.store.load("verify").recovered)

    def test_list_only_includes_valid_capsules(self) -> None:
        self.store.save("valid", {"value": True})
        self.store.save("also-valid", [1, 2])
        self.assertEqual(
            [item["capsule_id"] for item in self.store.list_capsules()],
            ["also-valid", "valid"],
        )


class CapsuleRuntimeTests(unittest.TestCase):
    def test_capsule_builtins_are_disabled_without_host_storage_root(self) -> None:
        interpreter = Interpreter(output=lambda _line: None)
        with self.assertRaisesRegex(Exception, "capsule persistence is disabled"):
            interpreter.run("emit capsule_list()")

    def test_language_can_checkpoint_restore_verify_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output: list[str] = []
            interpreter = Interpreter(output=output.append, capsule_root=directory)
            interpreter.run(
                """
                emit capsule_checkpoint("studio", {"bpm": 93, "tracks": [1, 2]})
                emit capsule_restore("studio")
                emit capsule_load("studio")
                emit capsule_verify("studio")
                emit capsule_list()
                """
            )
        self.assertEqual(len(output), 5)
        self.assertIn("studio", output[0])
        self.assertIn("bpm", output[1])
        self.assertIn("bpm", output[2])
        self.assertIn("valid", output[3])
        self.assertIn("studio", output[4])


if __name__ == "__main__":
    unittest.main()
