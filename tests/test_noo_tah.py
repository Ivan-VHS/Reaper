import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper.noo_tah import Runtime, build_parser


class RuntimeDiscoveryTests(unittest.TestCase):
    def test_explicit_node_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            node = Path(directory) / "node"
            node.touch()
            with patch("reaper.noo_tah.shutil.which", side_effect=lambda name: "/usr/bin/npm" if name == "npm" else None):
                runtime = Runtime.discover(str(node))
            self.assertEqual(runtime.node, str(node.resolve()))
            self.assertEqual(runtime.npm, "/usr/bin/npm")

    def test_missing_node_is_actionable(self):
        with patch.dict(os.environ, {"NOO_TAH_NODE": ""}):
            with patch("reaper.noo_tah.shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "Node.js was not found"):
                    Runtime.discover()

    def test_cli_contract(self):
        args = build_parser().parse_args(["run", "app.mjs", "--", "one"])
        self.assertEqual(args.action, "run")
        self.assertEqual(args.file, "app.mjs")
        self.assertEqual(args.args, ["--", "one"])


if __name__ == "__main__":
    unittest.main()
