from __future__ import annotations

import unittest

from reaper.systems import TRACKS, format_tracks, validate_registry


class SystemRegistryTests(unittest.TestCase):
    def test_registry_has_twenty_unique_sequential_tracks(self) -> None:
        validate_registry()
        self.assertEqual(len(TRACKS), 20)
        self.assertEqual([track.id for track in TRACKS], list(range(1, 21)))
        self.assertEqual(len({track.name for track in TRACKS}), 20)

    def test_each_track_has_an_acceptance_contract(self) -> None:
        for track in TRACKS:
            with self.subTest(track=track.name):
                self.assertTrue(track.focus)
                self.assertTrue(track.runtime_contract)
                self.assertTrue(track.acceptance)

    def test_registry_is_immutable(self) -> None:
        with self.assertRaises((AttributeError, TypeError)):
            TRACKS[0].name = "changed"

    def test_terminal_report_is_stable_and_complete(self) -> None:
        report = format_tracks()
        self.assertIn("Chrome Ironclad", report)
        self.assertIn("Reactor Afterglow", report)
        self.assertEqual(report.count("Contract:"), 20)
        self.assertEqual(report.count("Accept:"), 20)


if __name__ == "__main__":
    unittest.main()
