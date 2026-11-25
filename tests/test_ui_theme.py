from reaper.ui_theme import (
    PALETTES, palette_contrast_issues, palette_for,
)


def test_light_and_dark_palettes_are_distinct_and_complete():
    light = palette_for("light")
    dark = palette_for("dark")
    assert light["page"] != dark["page"]
    assert light["accent"] and dark["accent"]
    assert light["editor_text"] and dark["editor_text"]


def test_system_mode_can_be_resolved_deterministically():
    assert palette_for("system", system_dark=True)["mode"] == "dark"
    assert palette_for("system", system_dark=False)["mode"] == "light"


def test_unknown_theme_is_rejected():
    try:
        palette_for("neon")
    except ValueError as error:
        assert "system" in str(error)
    else:
        raise AssertionError("unknown themes must be rejected")


def test_every_palette_meets_stage_0_1_text_contrast():
    required_status_tokens = {"success", "warning", "error", "info"}
    for name, palette in PALETTES.items():
        assert required_status_tokens.issubset(palette), name
        assert palette_contrast_issues(palette) == [], name
