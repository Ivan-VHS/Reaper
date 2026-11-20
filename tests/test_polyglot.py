from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from reaper.cli import main
from reaper.polyglot import PolyglotError, PolyglotWorkspace, detect_script


class PolyglotProfileTests(unittest.TestCase):
    def workspace(self, directory: str, **kwargs: object) -> PolyglotWorkspace:
        return PolyglotWorkspace.create(
            Path(directory) / "polyglot.json",
            target_language=str(kwargs.pop("target_language", "Spanish")),
            language_code=str(kwargs.pop("language_code", "es")),
            on_date=date(2026, 1, 1),
            **kwargs,
        )

    def test_profile_detects_tonal_language_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.workspace(
                directory,
                target_language="Mandarin",
                language_code="zh",
                daily_minutes=30,
            )
            self.assertEqual(workspace.profile["script_family"], "han")
            self.assertTrue(workspace.profile["tonal_language"])
            self.assertTrue(workspace.profile["romanization_bridge"])
            self.assertIn("tones", workspace.profile["phonetic_focus"])

    def test_script_detection_handles_supported_writing_systems(self) -> None:
        self.assertEqual(detect_script("Привіт, світе"), "cyrillic")
        self.assertEqual(detect_script("مرحبا بالعالم"), "arabic")
        self.assertEqual(detect_script("こんにちは世界"), "japanese")
        self.assertEqual(detect_script("안녕하세요"), "hangul")
        self.assertEqual(detect_script("สวัสดี"), "thai")


class ComprehensibleInputTests(unittest.TestCase):
    def test_spaced_language_coverage_and_difficulty_band(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            workspace.add_phrase("hola", "hello")
            workspace.add_phrase("mundo", "world")
            analysis = workspace.analyze_text("Hola, mundo, nuevo amigo.")
            self.assertEqual(analysis["known_units"], 2)
            self.assertEqual(analysis["total_units"], 4)
            self.assertEqual(analysis["coverage"], 0.5)
            self.assertEqual(analysis["band"], "too_hard")
            self.assertTrue(analysis["is_heuristic"])

    def test_compact_script_uses_character_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(
                directory,
                target_language="Chinese",
                language_code="zh",
            )
            workspace.add_phrase("你好", "hello")
            analysis = workspace.analyze_text("你好世界")
            self.assertEqual(analysis["script_family"], "han")
            self.assertEqual(analysis["known_units"], 2)
            self.assertEqual(analysis["total_units"], 4)
            self.assertEqual(analysis["coverage"], 0.5)

    def test_add_content_persists_comprehension_estimate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            workspace.add_phrase("good morning", "good morning")
            item = workspace.add_content(
                "Short greeting",
                "Good morning",
                source="lesson 1",
                audio_ref="audio/greeting.mp3",
            )
            self.assertEqual(item["comprehension_band"], "too_easy")
            self.assertEqual(item["audio_ref"], "audio/greeting.mp3")


class PhraseAndReviewTests(unittest.TestCase):
    def test_contextual_card_and_duplicate_protection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            phrase = workspace.add_phrase(
                "¿Qué tal?",
                "How are you?",
                context="A casual greeting between friends.",
                pronunciation="keh tal",
                personal_example="¿Qué tal estuvo tu día?",
                tags=["greeting", "conversation"],
            )
            self.assertEqual(phrase["id"], "phrase-000001")
            self.assertEqual(phrase["context"], "A casual greeting between friends.")
            self.assertEqual(phrase["tags"], ["conversation", "greeting"])
            with self.assertRaisesRegex(PolyglotError, "already exists"):
                workspace.add_phrase("¿Qué tal?", "How are you?")

    def test_spaced_repetition_schedule_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            phrase = workspace.add_phrase("buenos días", "good morning", on_date="2026-01-01")
            self.assertEqual(len(workspace.due_phrases("2026-01-01")), 1)

            first = workspace.review_phrase(phrase["id"], "good", on_date="2026-01-01")
            self.assertEqual(first["interval_days"], 1)
            self.assertEqual(first["due_on"], "2026-01-02")
            self.assertEqual(workspace.due_phrases("2026-01-01"), [])

            second = workspace.review_phrase(phrase["id"], "good", on_date="2026-01-02")
            self.assertEqual(second["interval_days"], 6)
            self.assertEqual(second["due_on"], "2026-01-08")
            self.assertEqual(second["review_count"], 2)

    def test_again_resets_repetition_streak_and_keeps_minimum_ease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            phrase = workspace.add_phrase("gracias", "thank you")
            result = workspace.review_phrase(phrase["id"], "again", on_date="2026-01-01")
            self.assertEqual(result["repetitions"], 0)
            self.assertEqual(result["interval_days"], 1)
            self.assertEqual(result["ease_factor"], 2.3)

    def test_review_rejects_unknown_card_and_rating(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            with self.assertRaisesRegex(PolyglotError, "unknown phrase"):
                workspace.review_phrase("phrase-999999", "good")
            phrase = workspace.add_phrase("hola", "hello")
            with self.assertRaisesRegex(PolyglotError, "rating"):
                workspace.review_phrase(phrase["id"], "perfect")


class StudyPlanningTests(unittest.TestCase):
    def test_profile_can_be_reconfigured_as_the_learner_progresses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory, daily_minutes=30)
            updated = workspace.configure(
                level="A2",
                daily_minutes=50,
                comprehension_target=0.85,
                romanization_bridge=False,
                goal="Travel and conversation",
            )
            self.assertEqual(updated["level"], "A2")
            self.assertEqual(updated["daily_minutes"], 50)
            self.assertEqual(updated["comprehension_target"], 0.85)
            self.assertFalse(updated["romanization_bridge"])
            self.assertEqual(updated["goal"], "Travel and conversation")

    def test_daily_plan_has_four_pillars_and_exact_time_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory, daily_minutes=45)
            plan = workspace.daily_plan("2026-01-01")
            self.assertEqual(plan["total_minutes"], 45)
            self.assertEqual(len(plan["tasks"]), 4)
            self.assertEqual(sum(item["minutes"] for item in plan["tasks"]), 45)
            self.assertEqual(
                {item["pillar"] for item in plan["tasks"]},
                {"audio_visual", "contextual_reading", "spaced_repetition", "speaking_feedback"},
            )

    def test_session_logging_and_phase_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            workspace.log_session(
                "audio_visual", 30, comprehension=0.82, on_date="2026-01-01"
            )
            workspace.log_session(
                "speaking_feedback", 35, oral_confidence=3,
                notes="Retold a short story; fix past tense.", on_date="2026-01-01"
            )
            status = workspace.status("2026-01-01")
            self.assertEqual(status["study_minutes"], 65)
            self.assertEqual(status["phase"], "sound_foundation")
            self.assertEqual(status["average_session_comprehension"], 0.82)
            self.assertEqual(status["session_count"], 2)

    def test_session_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = PolyglotProfileTests().workspace(directory)
            with self.assertRaisesRegex(PolyglotError, "minutes"):
                workspace.log_session("audio_visual", 0)
            with self.assertRaisesRegex(PolyglotError, "comprehension"):
                workspace.log_session("audio_visual", 10, comprehension=1.2)
            with self.assertRaisesRegex(PolyglotError, "pillar"):
                workspace.log_session("grammar", 10)


class PersistenceAndCliTests(unittest.TestCase):
    def test_save_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "polyglot.json"
            workspace = PolyglotWorkspace.create(
                path, target_language="French", language_code="fr"
            )
            workspace.add_phrase("bonjour", "hello", context="A daytime greeting")
            workspace.log_session("contextual_reading", 20, comprehension=0.76)
            workspace.save()

            loaded = PolyglotWorkspace.load(path)
            self.assertEqual(loaded.profile["target_language"], "French")
            self.assertEqual(loaded.data["phrases"][0]["text"], "bonjour")
            self.assertEqual(loaded.status()["study_minutes"], 20)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_init_refuses_to_overwrite_existing_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "polyglot.json"
            PolyglotWorkspace.create(path, target_language="German")
            with self.assertRaisesRegex(PolyglotError, "refusing to overwrite"):
                PolyglotWorkspace.create(path, target_language="Spanish")

    def test_cli_init_add_phrase_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "polyglot.json"
            code = main([
                "polyglot", "init", "--target-language", "Spanish", "--code", "es",
                "--store", str(path), "--json",
            ])
            self.assertEqual(code, 0)
            code = main([
                "polyglot", "add-phrase", "--store", str(path), "--json",
                "--text", "hola", "--meaning", "hello", "--context", "A greeting",
            ])
            self.assertEqual(code, 0)
            code = main(["polyglot", "status", "--store", str(path), "--json"])
            self.assertEqual(code, 0)

    def test_cli_analyze_reads_text_argument(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "polyglot.json"
            PolyglotWorkspace.create(path, target_language="Spanish")
            workspace = PolyglotWorkspace.load(path)
            workspace.add_phrase("hola", "hello")
            workspace.save()
            code = main([
                "polyglot", "analyze", "--store", str(path),
                "--text", "hola mundo", "--json",
            ])
            self.assertEqual(code, 0)

    def test_load_rejects_invalid_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema_version": 99}', encoding="utf-8")
            with self.assertRaisesRegex(PolyglotError, "schema"):
                PolyglotWorkspace.load(path)


if __name__ == "__main__":
    unittest.main()
