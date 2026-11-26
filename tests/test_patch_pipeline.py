import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "tools" / "reaper_patch.py"
SPEC = importlib.util.spec_from_file_location("reaper_patch", MODULE)
patcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patcher)


class PatchPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "REAPER tests")
        (self.root / "sample.txt").write_bytes(b"before\n")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        (self.root / "sample.txt").write_bytes(b"after\n")
        self.git("commit", "-qam", "change")
        self.head = self.git("rev-parse", "HEAD").strip()
        self.proposal = self.root / "proposal"
        patcher.create_proposal(self.root, self.base, self.head, self.proposal)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], text=True
        )

    def test_verify_apply_and_rollback(self):
        self.git("checkout", "-q", self.base)
        patcher.verify(self.root, self.proposal)
        patcher.apply(self.root, self.proposal)
        self.assertEqual((self.root / "sample.txt").read_bytes(), b"after\n")
        patcher.rollback(self.root, self.proposal)
        self.assertEqual((self.root / "sample.txt").read_bytes(), b"before\n")

    def test_crlf_base_hash_uses_exact_blob_bytes(self):
        path = self.root / "crlf.txt"
        path.write_bytes(b"before\r\n")
        self.git("add", "crlf.txt")
        self.git("commit", "-qm", "add CRLF file")
        base = self.git("rev-parse", "HEAD").strip()
        path.write_bytes(b"after\r\n")
        self.git("add", "crlf.txt")
        self.git("commit", "-qm", "change CRLF file")
        head = self.git("rev-parse", "HEAD").strip()
        proposal = self.root / "crlf-proposal"
        patcher.create_proposal(self.root, base, head, proposal)

        manifest = json.loads((proposal / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["files"][0]["base_sha256"], hashlib.sha256(b"before\r\n").hexdigest())
        self.git("checkout", "-q", base)
        patcher.verify(self.root, proposal)
        patcher.apply(self.root, proposal)
        self.assertEqual(path.read_bytes(), b"after\r\n")

    def test_binary_file_is_manifested_and_applied(self):
        path = self.root / "asset.bin"
        path.write_bytes(bytes([0, 1, 2, 255]))
        self.git("add", "asset.bin")
        self.git("commit", "-qm", "add binary")
        base = self.git("rev-parse", "HEAD").strip()
        path.write_bytes(bytes([0, 9, 2, 254]))
        self.git("add", "asset.bin")
        self.git("commit", "-qm", "change binary")
        head = self.git("rev-parse", "HEAD").strip()
        proposal = self.root / "binary-proposal"
        patcher.create_proposal(self.root, base, head, proposal)
        manifest = json.loads((proposal / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([item["path"] for item in manifest["files"]], ["asset.bin"])
        self.git("checkout", "-q", base)
        patcher.verify(self.root, proposal)
        patcher.apply(self.root, proposal)
        self.assertEqual(path.read_bytes(), bytes([0, 9, 2, 254]))

    def test_new_and_deleted_files_have_explicit_base_presence(self):
        added = self.root / "new.txt"
        added.write_bytes(b"new\n")
        self.git("add", "new.txt")
        self.git("commit", "-qm", "add file")
        base = self.git("rev-parse", "HEAD").strip()
        (self.root / "sample.txt").unlink()
        self.git("add", "-u")
        self.git("commit", "-qm", "delete file")
        head = self.git("rev-parse", "HEAD").strip()
        proposal = self.root / "create-delete-proposal"
        patcher.create_proposal(self.root, base, head, proposal)
        manifest = json.loads((proposal / "manifest.json").read_text(encoding="utf-8"))
        by_path = {item["path"]: item for item in manifest["files"]}
        self.assertTrue(by_path["sample.txt"]["base_exists"])
        self.assertFalse(by_path["new.txt"]["base_exists"])

    def test_tampered_patch_is_rejected(self):
        path = self.proposal / "proposal.patch"
        path.write_bytes(path.read_bytes() + b"# tamper\n")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            patcher.load_proposal(self.root, self.proposal)

    def test_manifest_cannot_omit_a_patch_section(self):
        manifest_path = self.proposal / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "manifest file list"):
            patcher.load_proposal(self.root, self.proposal)

    def test_base_drift_is_rejected(self):
        self.git("checkout", "-q", self.base)
        (self.root / "sample.txt").write_bytes(b"unexpected\n")
        with self.assertRaisesRegex(ValueError, "base content changed"):
            patcher.verify(self.root, self.proposal)

    def test_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsafe patch path"):
            patcher.safe_path("../outside.txt")
        with self.assertRaisesRegex(ValueError, "unsafe patch path"):
            patcher.safe_path(r"..\\outside.txt")

    def test_symlink_target_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir(exist_ok=True)
        link = self.root / "linked"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            patcher.ensure_no_symlink(self.root, "linked/escape.txt")


if __name__ == "__main__":
    unittest.main()
