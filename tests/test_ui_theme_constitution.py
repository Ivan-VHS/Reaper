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

    def test_shared_mora_tokens_are_used_for_light_and_dark(self) -> None:
        expected = {
            "light": {
                "bg": "#F5F3FA", "surface": "#FFFFFF", "elevated": "#ECE9F5",
                "fg": "#211F31", "secondary": "#4E4B63", "muted": "#66627A",
                "blue": "#5B43B5", "blue_hover": "#49359D", "red": "#A91F49",
                "border": "#D6D0E7", "selection": "#E6E0F7",
            },
            "dark": {
                "bg": "#10142A", "surface": "#191E39", "elevated": "#252B4B",
                "fg": "#F5F4FF", "secondary": "#D5D6EB", "muted": "#A8ADC8",
                "blue": "#A78BFA", "blue_hover": "#C1AEFF", "red": "#FF8EAC",
                "border": "#3B4262", "selection": "#353054",
            },
        }
        for mode, tokens in expected.items():
            palette = palette_for(mode)
            for token, value in tokens.items():
                self.assertEqual(palette[token], value, f"{mode}.{token}")

    def test_focus_and_supporting_text_have_semantic_contrast(self) -> None:
        for palette in PALETTES.values():
            self.assertGreaterEqual(contrast_ratio(palette["focus"], palette["bg"]), 3.0)
            self.assertGreaterEqual(contrast_ratio(palette["muted"], palette["bg"]), 4.5)



if __name__ == "__main__":
    unittest.main()
