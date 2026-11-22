from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tools.clife import ClifeError, snapshot, verify, restore

class ClifeSavepointTests(unittest.TestCase):
    def test_snapshot_verify_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            (source / "example.txt").write_text("CLife integrity", encoding="utf-8")
            archive = base / "snapshot.clife"
            result = snapshot(source, archive)
            self.assertEqual(result["schema"], "clife.snapshot.v1")
            self.assertTrue(verify(archive)["verified"])
            target = base / "recovered"
            restore(archive, target)
            self.assertEqual((target / "example.txt").read_text(encoding="utf-8"), "CLife integrity")

    def test_restore_never_overwrites_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            (source / "x").write_text("x", encoding="utf-8")
            archive = base / "snapshot.clife"
            snapshot(source, archive)
            target = base / "existing"
            target.mkdir()
            with self.assertRaises(ClifeError):
                restore(archive, target)

if __name__ == "__main__":
    unittest.main()
