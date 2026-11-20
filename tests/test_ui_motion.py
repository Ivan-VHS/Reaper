import os
import unittest

from reaper.ui_motion import DURATIONS_MS, ease_out, reduced_motion_enabled


class MotionTests(unittest.TestCase):
    def test_easing_is_clamped_and_monotonic(self):
        self.assertEqual(ease_out(-1), 0.0)
        self.assertEqual(ease_out(0), 0.0)
        self.assertEqual(ease_out(1), 1.0)
        self.assertEqual(ease_out(2), 1.0)
        values = [ease_out(i / 20) for i in range(21)]
        self.assertEqual(values, sorted(values))

    def test_duration_tokens_are_bounded(self):
        self.assertEqual(DURATIONS_MS["instant"], 0)
        self.assertLessEqual(DURATIONS_MS["micro"], DURATIONS_MS["fast"])
        self.assertLess(DURATIONS_MS["fast"], DURATIONS_MS["spatial"])

    def test_reduced_motion_override(self):
        previous = os.environ.get("UI_REDUCED_MOTION")
        try:
            os.environ["UI_REDUCED_MOTION"] = "1"
            self.assertTrue(reduced_motion_enabled())
            os.environ["UI_REDUCED_MOTION"] = "false"
            self.assertFalse(reduced_motion_enabled() if os.name != "nt" else True)
        finally:
            if previous is None:
                os.environ.pop("UI_REDUCED_MOTION", None)
            else:
                os.environ["UI_REDUCED_MOTION"] = previous


if __name__ == "__main__":
    unittest.main()
