from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.polyglot import (
    PolyglotError,
    PolyglotStore,
    clean_subtitles,
    run_review,
    tokenize,
)


class PolyglotStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "polyglot.sqlite3"
        self.store = PolyglotStore(self.db)
        self.profile = self.store.create_profile(
            "English", "Russian", "A0", "everyday conversation", 45
        )

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_profiles_are_multi_language_and_selection_is_explicit(self) -> None:
        self.store.create_profile("日本語", "Russian", "A0", "travel", 30)
        self.assertEqual(len(self.store.list_profiles()), 2)
        with self.assertRaisesRegex(PolyglotError, "choose a target"):
            self.store.get_profile()
        self.assertEqual(self.store.get_profile("english")["id"], self.profile["id"])
        self.assertEqual(self.store.get_profile("日本語")["daily_minutes"], 30)

    def test_contextual_card_review_builds_known_term_coverage(self) -> None:
        content_id = self.store.add_content(
            self.profile, "Short dialogue", "hello world hello there",
            kind="dialogue", source="course lesson",
        )
        card_id = self.store.add_phrase(
            self.profile, "hello world", "привет мир",
            context="A greeting in a short dialogue", tags=("greeting",),
            content_id=content_id,
        )
        self.assertEqual(self.store.due_count(self.profile), 1)
        result = self.store.record_review(card_id, 4)
        self.assertEqual(result["repetitions"], 1)
        item = self.store.get_content(self.profile, content_id)
        self.assertEqual(item["coverage"], 0.75)
        self.assertTrue(item["in_comprehensible_band"])
        self.assertEqual(item["unknown_terms"], ["there"])

    def test_srs_lapse_resets_interval_and_tracks_history(self) -> None:
        card_id = self.store.add_phrase(self.profile, "good morning", "доброе утро")
        first = self.store.record_review(card_id, 5)
        self.assertEqual(first["interval_days"], 1)
        second = self.store.record_review(card_id, 5)
        self.assertEqual(second["interval_days"], 3)
        lapse = self.store.record_review(card_id, 1)
        self.assertEqual(lapse["interval_days"], 1)
        self.assertEqual(lapse["repetitions"], 0)
        self.assertEqual(lapse["lapses"], 1)
        self.assertEqual(len(self.store.connection.execute(
            "SELECT id FROM review_events WHERE phrase_id=?", (card_id,)
        ).fetchall()), 3)

    def test_new_cards_are_due_and_interactive_review_can_be_driven(self) -> None:
        card_id = self.store.add_phrase(
            self.profile, "How are you?", "Как дела?",
            context="A casual greeting", pronunciation="hau ar yu",
        )
        output: list[str] = []
        reviewed = run_review(self.store, self.profile, fixed_rating=5, output_fn=output.append)
        self.assertEqual(reviewed, 1)
        self.assertTrue(any("Ответ: How are you?" in line for line in output))
        self.assertEqual(self.store.due_count(self.profile), 0)
        self.assertEqual(self.store.list_phrases(self.profile)[0]["id"], card_id)

    def test_plan_allocates_all_minutes_and_increases_review_pressure(self) -> None:
        baseline = self.store.session_plan(self.profile)
        self.assertEqual(sum(task["minutes"] for task in baseline), 45)
        for index in range(20):
            self.store.add_phrase(self.profile, f"phrase {index}", f"перевод {index}")
        busy = self.store.session_plan(self.profile)
        self.assertEqual(sum(task["minutes"] for task in busy), 45)
        baseline_review = next(task["minutes"] for task in baseline if task["mode"] == "review")
        busy_review = next(task["minutes"] for task in busy if task["mode"] == "review")
        self.assertGreaterEqual(busy_review, baseline_review)

    def test_session_report_and_json_export(self) -> None:
        self.store.log_session(self.profile, 25, "listening", "Podcast with transcript", 4)
        self.store.log_session(self.profile, 10, "speaking", "Retold the story", 3)
        report = self.store.report(self.profile)
        self.assertEqual(report["last_7_days_minutes"], 35)
        self.assertEqual(report["last_7_days_sessions"], 2)
        exported = self.store.export_profile(self.profile)
        self.assertEqual(exported["schema_version"], 1)
        self.assertEqual(len(exported["sessions"]), 2)
        self.assertEqual(json.loads(json.dumps(exported))["profile"]["target_language"], "English")

    def test_duplicate_content_and_phrase_are_reported(self) -> None:
        self.store.add_content(self.profile, "Story", "Once upon a time.")
        with self.assertRaisesRegex(PolyglotError, "already imported"):
            self.store.add_content(self.profile, "Story", "Once upon a time.")
        self.store.add_phrase(self.profile, "thank you", "спасибо")
        with self.assertRaisesRegex(PolyglotError, "already exist"):
            self.store.add_phrase(self.profile, "thank you", "спасибо")

    def test_invalid_profile_and_session_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(PolyglotError, "level"):
            self.store.create_profile("French", "Russian", "C8")
        with self.assertRaisesRegex(PolyglotError, "between 5 and 240"):
            self.store.create_profile("French", "Russian", daily_minutes=2)
        with self.assertRaisesRegex(PolyglotError, "session mode"):
            self.store.log_session(self.profile, 10, "gaming")
        with self.assertRaisesRegex(PolyglotError, "rating"):
            self.store.record_review(999, 9)

    def test_cjk_tokenization_is_explicitly_character_approximate(self) -> None:
        self.assertTrue(tokenize("你好世界"))
        content_id = self.store.add_content(self.profile, "Japanese", "こんにちは世界")
        item = self.store.get_content(self.profile, content_id)
        self.assertIn("CJK", item["coverage_note"])


class PolyglotImportTests(unittest.TestCase):
    def test_subtitle_cleaning_removes_cues_and_preserves_text(self) -> None:
        source = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello there!\n\n2\n00:00:02,000 --> 00:00:03,000\nHow are you?\n"
        self.assertEqual(clean_subtitles(source), "Hello there!\nHow are you?")

    def test_utf8_file_import_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "lesson.txt"
            source.write_text("Привет, мир!", encoding="utf-8")
            with PolyglotStore(root / "store.sqlite3") as store:
                profile = store.create_profile("English", "Russian")
                body = source.read_text(encoding="utf-8-sig")
                item_id = store.add_content(profile, source.stem, body, source=str(source))
                self.assertEqual(store.get_content(profile, item_id)["body"], "Привет, мир!")


if __name__ == "__main__":
    unittest.main()
