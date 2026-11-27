from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper.game_launch_contract import GameLaunchContractError, build_game_launch_task


class GameLaunchContractTests(unittest.TestCase):
    def profile(self):
        return {
            "schema": "dakos.game-launch-profile.v1",
            "id": "classic-title",
            "name": "Classic Title",
            "executable": "game.exe",
            "working_directory": ".",
            "arguments": ["-window", "-console"],
            "runtime": {"backend": "wine", "executable": "wine", "prefix": "prefix"},
            "compatibility": {"windows_version": "windows-xp", "service_pack": 3},
            "environment": {"WINEDEBUG": "-all"},
        }

    def test_builds_argv_task_without_process_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "game.exe").write_bytes(b"MZ-not-parsed-by-this-contract")
            (root / "prefix").mkdir()
            task = build_game_launch_task(self.profile(), root)
            self.assertEqual(task["schema"], "reaper.game-launch-task.v1")
            self.assertEqual(task["argv"][1], str(root / "game.exe"))
            self.assertEqual(task["argv"][-2:], ["-window", "-console"])
            self.assertEqual(task["working_directory"], str(root))
            self.assertEqual(task["environment_overrides"]["WINEPREFIX"], str(root / "prefix"))
            self.assertFalse(task["shell"])
            self.assertFalse(task["process_created"])
            self.assertTrue(task["requires_trusted_host_executor"])

    def test_rejects_unknown_environment_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "game.exe").touch()
            (root / "prefix").mkdir()
            profile = self.profile()
            profile["environment"] = {"LD_PRELOAD": "/tmp/override.so"}
            with self.assertRaises(GameLaunchContractError):
                build_game_launch_task(profile, root)

    def test_rejects_relative_escape_and_shell_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "game.exe").touch()
            (root / "prefix").mkdir()
            profile = self.profile()
            profile["working_directory"] = "../"
            with self.assertRaises(GameLaunchContractError):
                build_game_launch_task(profile, root)
            profile = self.profile()
            profile["runtime"]["backend"] = "shell"
            with self.assertRaises(GameLaunchContractError):
                build_game_launch_task(profile, root)

    def test_rejects_null_byte_in_argument(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "game.exe").touch()
            (root / "prefix").mkdir()
            profile = self.profile()
            profile["arguments"] = ["safe", "bad\x00arg"]
            with self.assertRaises(GameLaunchContractError):
                build_game_launch_task(profile, root)


if __name__ == "__main__":
    unittest.main()
