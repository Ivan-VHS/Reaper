# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import subprocess
import unittest
from unittest.mock import patch
from reaper_runtime_inventory import (
    ProbeResult, Toolchain, _version_text, build_report, inventory, probe_toolchain, render_markdown,
)

class RuntimeInventoryTests(unittest.TestCase):
    def test_version_text_prefers_first_nonempty_line(self):
        self.assertEqual(_version_text("\nGo version go1.25 linux/amd64\nmore", "warning"), "Go version go1.25 linux/amd64")
        self.assertIsNone(_version_text("", "  "))

    @patch("reaper_runtime_inventory.shutil.which", return_value=None)
    def test_missing_toolchain_is_reported_without_execution(self, which):
        result = probe_toolchain(Toolchain("Demo", "demo", ("--version",), "compiled"))
        self.assertFalse(result.available)
        self.assertEqual(result.status, "missing")
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
        self.assertEqual(result.status, "ok")

    @patch("reaper_runtime_inventory.shutil.which", return_value=None)
    def test_inventory_preserves_catalogue_order(self, _which):
        entries = [Toolchain("First", "first", ("--version",), "runtime"),
                   Toolchain("Second", "second", ("--version",), "proof")]
        results = inventory(entries, workers=2)
        self.assertEqual([item.language for item in results], ["First", "Second"])

    def test_report_is_versioned_and_groups_toolchains(self):
        results = [
            ProbeResult("Go", "go", "compiled", "compiler", True, "/usr/bin/go", "go version", "ok", 2.0, 0),
            ProbeResult("Rust", "rustc", "compiled", "compiler", False, None, None, "missing", None),
        ]
        report = build_report(results)
        self.assertEqual(report["schema"], "reaper.toolchain-atlas.v1")
        self.assertEqual(report["summary"]["available"], 1)
        self.assertEqual(report["families"]["compiled"]["ok"], 1)
        self.assertIn("Reaper Toolchain Atlas", render_markdown(report))

    def test_timeout_and_worker_limits_are_explicit(self):
        with self.assertRaises(ValueError):
            inventory([], workers=0)
        with self.assertRaises(ValueError):
            inventory([], timeout=20)

if __name__ == "__main__":
    unittest.main()
