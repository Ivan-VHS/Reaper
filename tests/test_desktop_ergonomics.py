from reaper.desktop import bounded_editor_font_size


def test_editor_font_size_stays_inside_accessible_limits():
    assert bounded_editor_font_size(11, 1) == 12
    assert bounded_editor_font_size(11, -1) == 10
    assert bounded_editor_font_size(24, 1) == 24
    assert bounded_editor_font_size(9, -1) == 9


def test_editor_font_size_handles_large_steps_without_overflow():
    assert bounded_editor_font_size(11, 50) == 24
    assert bounded_editor_font_size(11, -50) == 9
