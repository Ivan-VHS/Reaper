from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.checkpoint import SnapshotError, SnapshotStore, TransactionalStore


class CheckpointTests(unittest.TestCase):
    def test_snapshot_round_trip_and_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            snapshot = SnapshotStore(Path(directory) / "state.json")
            self.assertEqual(snapshot.save({"count": 4, "items": [1, 2]}), 1)
            restored = SnapshotStore(snapshot.path)
            self.assertEqual(restored.load(), {"count": 4, "items": [1, 2]})
            self.assertEqual(restored.revision, 1)

    def test_corrupt_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            snapshot = SnapshotStore(path)
            snapshot.save({"safe": True})
            data = json.loads(path.read_text(encoding="utf-8"))
            data["state"]["safe"] = False
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(SnapshotError, "checksum"):
                snapshot.load()

    def test_transaction_commits_atomically_and_rolls_back_on_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            snapshot = SnapshotStore(Path(directory) / "store.json")
            store = TransactionalStore(snapshot, {"counter": 1})
            with store.transaction() as state:
                state["counter"] = 2
            self.assertEqual(store.get("counter"), 2)
            with self.assertRaises(RuntimeError):
                with store.transaction() as state:
                    state["counter"] = 3
                    raise RuntimeError("abort")
            self.assertEqual(store.get("counter"), 2)
            restored = TransactionalStore(SnapshotStore(snapshot.path))
            self.assertEqual(restored.get("counter"), 2)

    def test_non_json_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            snapshot = SnapshotStore(Path(directory) / "state.json")
            with self.assertRaises(SnapshotError):
                snapshot.save({"not-json": object()})


if __name__ == "__main__":
    unittest.main()
