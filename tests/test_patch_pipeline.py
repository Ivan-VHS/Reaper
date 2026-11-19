import importlib.util, subprocess, tempfile, unittest
from pathlib import Path
MODULE = Path(__file__).parents[1] / "tools" / "reaper_patch.py"
SPEC = importlib.util.spec_from_file_location("reaper_patch", MODULE)
patcher = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(patcher)

class PatchPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.git("init", "-q"); self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "REAPER tests")
        (self.root / "sample.txt").write_text("before\n", encoding="utf-8")
        self.git("add", "sample.txt"); self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        (self.root / "sample.txt").write_text("after\n", encoding="utf-8")
        self.git("commit", "-qam", "change"); self.head = self.git("rev-parse", "HEAD").strip()
        self.proposal = self.root / "proposal"
        patcher.create_proposal(self.root, self.base, self.head, self.proposal)
    def tearDown(self): self.temp.cleanup()
    def git(self, *args): return subprocess.check_output(["git", "-C", str(self.root), *args], text=True)
    def test_verify_apply_and_rollback(self):
        self.git("checkout", "-q", self.base); patcher.verify(self.root, self.proposal)
        patcher.apply(self.root, self.proposal)
        self.assertEqual((self.root / "sample.txt").read_text(), "after\n")
        patcher.rollback(self.root, self.proposal)
        self.assertEqual((self.root / "sample.txt").read_text(), "before\n")
    def test_tampered_patch_is_rejected(self):
        path = self.proposal / "proposal.patch"; path.write_text(path.read_text() + "# tamper\n")
        with self.assertRaisesRegex(ValueError, "digest mismatch"): patcher.load_proposal(self.root, self.proposal)
    def test_base_drift_is_rejected(self):
        self.git("checkout", "-q", self.base); (self.root / "sample.txt").write_text("unexpected\n")
        with self.assertRaisesRegex(ValueError, "base content changed"): patcher.verify(self.root, self.proposal)
    def test_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsafe patch path"): patcher.safe_path("../outside.txt")

    def test_windows_path_forms_are_rejected(self):
        for path in (
            r"..\\outside.txt",
            r"C:\\outside.txt",
            "C:relative.txt",
            r"\\\\server\\share\\outside.txt",
            "src/file.txt:alternate-stream",
            ".GIT/config",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    patcher.safe_path(path)
    def test_symlink_target_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir(exist_ok=True)
        link = self.root / "linked"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink path component"):
            patcher.ensure_no_symlink(self.root, "linked/escape.txt")

if __name__ == "__main__": unittest.main()
