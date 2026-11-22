# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import subprocess
import unittest
from unittest.mock import patch
from reaper_runtime_inventory import Toolchain, _version_text, inventory, probe_toolchain

class RuntimeInventoryTests(unittest.TestCase):
    def test_version_text_prefers_first_nonempty_line(self):
        self.assertEqual(_version_text("\nGo version go1.25 linux/amd64\nmore", "warning"), "Go version go1.25 linux/amd64")
        self.assertIsNone(_version_text("", "  "))

    @patch("reaper_runtime_inventory.shutil.which", return_value=None)
    def test_missing_toolchain_is_reported_without_execution(self, which):
        result = probe_toolchain(Toolchain("Demo", "demo", ("--version",), "compiled"))
        self.assertFalse(result.available)
        self.assertIsNone(result.version)
        which.assert_called_once()

    @patch("reaper_runtime_inventory.subprocess.run")
    @patch("reaper_runtime_inventory.shutil.which", return_value="/tools/demo")
    def test_probe_runs_only_fixed_version_arguments(self, which, run):
        run.return_value = subprocess.CompletedProcess(["/tools/demo"], 0, "demo 1.2.3\n", "")
        result = probe_toolchain(Toolchain("Demo", "demo", ("--version",), "compiled"))
        self.assertTrue(result.available)
        self.assertEqual(result.version, "demo 1.2.3")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["/tools/demo", "--version"])
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)

    @patch("reaper_runtime_inventory.shutil.which", return_value=None)
    def test_inventory_preserves_catalogue_order(self, _which):
        entries = [Toolchain("First", "first", ("--version",), "runtime"), Toolchain("Second", "second", ("--version",), "proof")]
        results = inventory(entries)
        self.assertEqual([item.language for item in results], ["First", "Second"])

if __name__ == "__main__":
    unittest.main()
