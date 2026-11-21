"""Regression tests for the transcript-grounded wellbeing reference."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from reaper.wellbeing import (
    RESOURCE_PATH,
    WellbeingReferenceError,
    format_catalog,
    get_topic,
    load_reference,
)


class WellbeingReferenceTests(unittest.TestCase):
    def test_source_and_partial_transcript_are_preserved(self):
        payload = load_reference()
        self.assertEqual(payload["source"]["published_at"], "2025-11-23")
        self.assertTrue(payload["transcript_coverage"]["missing_middle"])
        self.assertEqual(
            payload["transcript_coverage"]["available_segments"],
            [{"start_seconds": 0, "end_seconds": 475},
             {"start_seconds": 4636, "end_seconds": 4793}],
        )

    def test_antidepressant_myths_are_not_fabricated(self):
        topic = get_topic("antidepressant-myths")
        self.assertEqual(topic["evidence_status"], "insufficient_transcript")
        self.assertEqual(topic["timestamps_seconds"], [])

    def test_personal_experience_is_not_a_clinical_rule(self):
        topic = get_topic("personal-experiences")
        self.assertEqual(topic["evidence_status"], "transcript_excerpt")
        self.assertIn("особист", topic["summary"].casefold())

    def test_catalog_displays_safety_limit(self):
        output = format_catalog(load_reference())
        self.assertIn("middle unavailable", output)
        self.assertIn("no diagnosis", output)

    def test_duplicate_topic_ids_are_rejected(self):
        payload = load_reference()
        payload["topics"].append(copy.deepcopy(payload["topics"][0]))
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "bundle.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(WellbeingReferenceError):
                load_reference(candidate)

    def test_missing_middle_flag_cannot_be_removed(self):
        payload = load_reference()
        payload["transcript_coverage"]["missing_middle"] = False
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "bundle.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(WellbeingReferenceError):
                load_reference(candidate)

    def test_default_resource_is_repository_local(self):
        self.assertTrue(RESOURCE_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
