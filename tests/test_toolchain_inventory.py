from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from reaper.toolchain_inventory import (
    create_lock, discover_toolchain, verify_lock, ToolchainError, TOOLS,
)


class ToolchainInventoryTests(unittest.TestCase):
    def test_inventory_does_not_execute_programs(self):
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "cmake"
            executable.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            executable.chmod(0o755)
            report = discover_toolchain(folder)
            cmake = next(item for item in report["tools"] if item["id"] == "cmake")
            self.assertTrue(cmake["available"])
            self.assertEqual(cmake["version"], "not-probed")
            self.assertEqual(cmake["path"], str(executable.resolve()))

    def test_lock_and_verify_detect_binary_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "cmake"
            executable.write_bytes(b"first binary")
            executable.chmod(0o755)
            inventory = discover_toolchain(folder)
            lock = create_lock(inventory)
            self.assertTrue(verify_lock(lock, folder)["valid"])
            executable.write_bytes(b"changed binary")
            self.assertFalse(verify_lock(lock, folder)["valid"])

    def test_rejects_incomplete_inventory(self):
        with self.assertRaises(ToolchainError):
            create_lock({"schema": "wrong", "tools": []})
        self.assertEqual(len(discover_toolchain("")[ "tools"]), len(TOOLS))


if __name__ == "__main__":
    unittest.main()
