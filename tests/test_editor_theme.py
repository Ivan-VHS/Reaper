from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
EXTENSION = ROOT / "editors" / "vscode"


class EditorThemeTests(unittest.TestCase):
    def test_package_declares_existing_light_theme(self) -> None:
        package = json.loads((EXTENSION / "package.json").read_text(encoding="utf-8"))
        themes = package["contributes"]["themes"]
        self.assertEqual(len(themes), 1)
        self.assertEqual(themes[0]["uiTheme"], "vs")
        self.assertTrue((EXTENSION / themes[0]["path"].removeprefix("./")).is_file())

    def test_theme_uses_white_red_blue_accessible_tokens(self) -> None:
        theme = json.loads(
            (EXTENSION / "themes" / "most-white-red-blue-color-theme.json").read_text(
                encoding="utf-8"
            )
        )
        colors = theme["colors"]
        self.assertEqual(colors["editor.background"], "#FAFCFF")
        self.assertEqual(colors["editorCursor.foreground"], "#235EA8")
        self.assertEqual(colors["errorForeground"], "#B82C37")
        self.assertEqual(colors["button.foreground"], "#FFFFFF")
        self.assertTrue(theme["tokenColors"])


if __name__ == "__main__":
    unittest.main()
