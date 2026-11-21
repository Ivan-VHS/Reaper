import unittest

from reaper.ui_theme import PALETTES, contrast_ratio, palette_for


class UiThemeConstitutionTests(unittest.TestCase):
    def test_semantic_tokens_exist_in_both_palettes(self) -> None:
        required = {
            "bg", "surface", "elevated", "fg", "secondary", "muted",
            "blue", "blue_hover", "on_blue", "red", "red_hover", "on_red",
            "border", "focus", "selection", "selection_fg", "disabled",
        }
        for palette in PALETTES.values():
            self.assertTrue(required.issubset(palette))

    def test_primary_text_and_actions_have_readable_contrast(self) -> None:
        for palette in PALETTES.values():
            self.assertGreaterEqual(contrast_ratio(palette["fg"], palette["bg"]), 7.0)
            self.assertGreaterEqual(contrast_ratio(palette["on_blue"], palette["blue"]), 4.5)
            self.assertGreaterEqual(contrast_ratio(palette["on_red"], palette["red"]), 4.5)

    def test_atmospheric_profiles_are_resolved(self) -> None:
        self.assertEqual(palette_for("dawn")["bg"], "#F3F6FA")
        self.assertEqual(palette_for("sunset")["bg"], "#F5EFE8")
        self.assertEqual(palette_for("night")["bg"], "#081522")

    def test_invalid_color_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            contrast_ratio("blue", "#FFFFFF")

    def test_legacy_theme_resolution_remains_supported(self) -> None:
        self.assertEqual(palette_for("system", system_dark=True)["mode"], "dark")
        self.assertEqual(palette_for("system", system_dark=False)["mode"], "light")

    def test_focus_and_supporting_text_have_semantic_contrast(self) -> None:
        for palette in PALETTES.values():
            self.assertGreaterEqual(contrast_ratio(palette["focus"], palette["bg"]), 3.0)
            self.assertGreaterEqual(contrast_ratio(palette["muted"], palette["bg"]), 4.5)



if __name__ == "__main__":
    unittest.main()
