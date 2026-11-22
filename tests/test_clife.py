from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("clife_under_test", ROOT / "tools" / "clife.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load tools/clife.py")
CLIFE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIFE)

class ClifeSavepointTests(unittest.TestCase):
    def test_snapshot_verify_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            (source / "example.txt").write_text("CLife integrity", encoding="utf-8")
            archive = base / "snapshot.clife"
            result = CLIFE.snapshot(source, archive)
            self.assertEqual(result["schema"], "clife.snapshot.v1")
            self.assertTrue(CLIFE.verify(archive)["verified"])
            target = base / "recovered"
            CLIFE.restore(archive, target)
            self.assertEqual((target / "example.txt").read_text(encoding="utf-8"), "CLife integrity")

    def test_restore_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            (source / "x").write_text("x", encoding="utf-8")
            archive = base / "snapshot.clife"
            CLIFE.snapshot(source, archive)
            target = base / "existing"
            target.mkdir()
            with self.assertRaises(CLIFE.ClifeError):
                CLIFE.restore(archive, target)

if __name__ == "__main__":
    unittest.main()
