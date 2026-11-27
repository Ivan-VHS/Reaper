import os
import tempfile
import unittest
from unittest.mock import patch

from reaper.ui_motion import (
    DURATIONS_MS, MotionPreferences, Spring1D, PADDLE_EASING, WATER_EASING,
    drapery_fold_offset, duration_for, ease_out,
    load_preferences, reduced_motion_enabled, save_preferences,
)


class MotionTests(unittest.TestCase):
    def test_easing_is_clamped_and_monotonic(self):
        self.assertEqual(ease_out(-1), 0.0)
        self.assertEqual(ease_out(0), 0.0)
        self.assertEqual(ease_out(1), 1.0)
        self.assertEqual(ease_out(2), 1.0)
        values = [ease_out(i / 20) for i in range(21)]
        self.assertEqual(values, sorted(values))

    def test_shared_paddle_and_water_motion_tokens_are_stable(self):
        self.assertEqual(PADDLE_EASING, "cubic-bezier(0.22, 1.18, 0.36, 1)")
        self.assertEqual(WATER_EASING, "cubic-bezier(0.37, 0, 0.63, 1)")

    def test_drapery_fold_offsets_are_finite_and_bounded(self):
        self.assertAlmostEqual(drapery_fold_offset(0.0, 0.0, 2.0), 0.0)
        self.assertLessEqual(abs(drapery_fold_offset(2.4, 8.0, 20.0)), 4.0)
        self.assertEqual(drapery_fold_offset(1.0, 2.0, -1.0), 0.0)
        with self.assertRaises(ValueError):
            drapery_fold_offset(float("nan"), 0.0, 1.0)

    def test_duration_tokens_follow_motion_budget(self):
        with patch("reaper.ui_motion.reduced_motion_enabled", return_value=False):
            self.assertEqual(DURATIONS_MS["instant"], 0)
            self.assertEqual(DURATIONS_MS["micro"], 100)
            self.assertLessEqual(duration_for("spatial", MotionPreferences(reduce_motion=True)), 80)
            self.assertLessEqual(duration_for("emphasis", MotionPreferences(eco_visuals=True)), 80)

    def test_expressive_mode_scales_but_bounds_motion(self):
        with patch("reaper.ui_motion.reduced_motion_enabled", return_value=False):
            normal = duration_for("spatial", MotionPreferences())
            expressive = duration_for("spatial", MotionPreferences(expressive_motion=True))
            reduced = duration_for("spatial", MotionPreferences(True, False, False, True))
            self.assertGreater(expressive, normal)
            self.assertLessEqual(expressive, 380)
            self.assertLessEqual(reduced, 80)

    def test_spring_converges_and_rejects_non_finite_targets(self):
        spring = Spring1D(0.0, 240.0, 22.0, 1.0)
        spring.set_target(1.0)
        for _ in range(240):
            spring.step(1 / 60)
        self.assertTrue(spring.settled)
        self.assertAlmostEqual(spring.value, 1.0, places=3)
        with self.assertRaises(ValueError):
            spring.set_target(float("nan"))

    def test_explicit_reduced_motion_override(self):
        previous = os.environ.get("UI_REDUCED_MOTION")
        try:
            os.environ["UI_REDUCED_MOTION"] = "1"
            self.assertTrue(reduced_motion_enabled())
            os.environ["UI_REDUCED_MOTION"] = "true"
            self.assertTrue(reduced_motion_enabled())
        finally:
            if previous is None:
                os.environ.pop("UI_REDUCED_MOTION", None)
            else:
                os.environ["UI_REDUCED_MOTION"] = previous

    def test_preferences_are_persisted_without_losing_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            old_appdata = os.environ.get("APPDATA")
            os.environ["APPDATA"] = folder
            try:
                expected = MotionPreferences(True, True, False, True)
                save_preferences("motion-tests", expected)
                self.assertEqual(load_preferences("motion-tests"), expected)
            finally:
                if old_appdata is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = old_appdata


if __name__ == "__main__":
    unittest.main()
