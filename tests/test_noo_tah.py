import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from reaper.noo_tah import Runtime, build_parser

class NooTahTests(unittest.TestCase):
    def test_explicit_node(self):
        with tempfile.TemporaryDirectory() as d:
            node=Path(d)/"node"; node.touch()
            with patch("reaper.noo_tah.shutil.which",return_value=None):
                self.assertEqual(Runtime.discover(str(node)).node,str(node.resolve()))
    def test_missing_node(self):
        with patch.dict(os.environ,{"NOO_TAH_NODE":""}), patch("reaper.noo_tah.shutil.which",return_value=None):
            with self.assertRaisesRegex(RuntimeError,"Node.js not found"): Runtime.discover()
    def test_run_arguments(self):
        a=build_parser().parse_args(["run","app.mjs","--","--port","3000"])
        self.assertEqual(a.args,["--","--port","3000"])
    def test_inspector_options(self):
        a=build_parser().parse_args(["inspect","--host","0.0.0.0","--port","9333","--brk","server.mjs"])
        self.assertTrue(a.brk); self.assertEqual(a.port,"9333")
    def test_project_command(self):
        a=build_parser().parse_args(["project","--cwd","/tmp"])
        self.assertEqual(a.action,"project")
    def test_runtime_command_never_shell(self):
        with tempfile.TemporaryDirectory() as d:
            node=Path(d)/"node"; node.touch()
            rt=Runtime(str(node),None,None)
            with patch("reaper.noo_tah.subprocess.run") as run:
                rt.command(["-e","process.exit(0)"])
                self.assertNotIn("shell",run.call_args.kwargs)
if __name__=="__main__": unittest.main()
