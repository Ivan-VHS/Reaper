from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "reaper_scripts" / "clife"


class ClifeReaScriptTests(unittest.TestCase):
    def test_three_standalone_reaper_actions_exist(self):
        files = sorted(SCRIPTS.glob("*.lua"))
        self.assertEqual(
            {path.name for path in files},
            {
                "CLife_Snapshot_Project.lua",
                "CLife_Verify_Latest.lua",
                "CLife_Restore_Latest.lua",
            },
        )
        for path in files:
            source = path.read_text(encoding="utf-8")
            self.assertIn("-- @description", source)
            self.assertIn("reaper.", source)
            self.assertNotIn("os.execute", source)
            self.assertNotIn("io.popen", source)
            self.assertNotIn("reaper.defer", source)

    def test_snapshot_is_rpp_only_and_writes_manifest(self):
        source = (SCRIPTS / "CLife_Snapshot_Project.lua").read_text(encoding="utf-8")
        self.assertIn("Main_SaveProject", source)
        self.assertIn(".clife", source)
        self.assertIn("snapshot_file=", source)
        self.assertIn("adler32=", source)
        self.assertIn("copy_and_fingerprint", source)

    def test_restore_never_replaces_active_project(self):
        source = (SCRIPTS / "CLife_Restore_Latest.lua").read_text(encoding="utf-8")
        self.assertIn("_CLife_Restored_", source)
        self.assertIn("will not be overwritten", source)
        self.assertIn("os.rename", source)
        self.assertNotIn("Main_openProject", source)
        self.assertNotIn("os.remove(project_file)", source)

    def test_integrity_check_is_explicitly_non_cryptographic(self):
        source = (SCRIPTS / "CLife_Verify_Latest.lua").read_text(encoding="utf-8")
        self.assertIn("adler32", source)
        self.assertIn("65521", source)
        self.assertIn("ok <= 0", source)


if __name__ == "__main__":
    unittest.main()
