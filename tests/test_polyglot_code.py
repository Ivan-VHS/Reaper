from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from reaper.polyglot_code import (
    FAMILIES,
    PolyglotCodeError,
    PolyglotCodeStore,
    infer_family,
    main,
)


class PolyglotCodeStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "polyglot-code.sqlite3"
        self.store = PolyglotCodeStore(self.db)
        self.profile = self.store.create_profile(
            "Rust", ["C", "C++"], "working", "auto",
            "Understand ownership and idiomatic systems code", 60,
        )

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_profiles_infer_families_and_require_explicit_selection(self) -> None:
        self.assertEqual(self.profile["family"], "ownership")
        self.store.create_profile("Python", ["C"], "novice", "auto", "", 30)
        self.assertEqual(self.store.get_profile("python")["family"], "dynamic")
        with self.assertRaisesRegex(PolyglotCodeError, "select one"):
            self.store.get_profile()
        self.assertEqual(len(self.store.list_profiles()), 2)

    def test_concept_progress_and_cross_language_comparison_are_persistent(self) -> None:
        self.store.update_concept(
            self.profile, "memory", "understood",
            "Borrowing prevents aliases from mutating shared state.",
            "Implemented a slice API and explained its lifetime.",
        )
        self.store.save_comparison(
            self.profile, "memory", "C++",
            "References and RAII with ownership conventions",
            "Borrow checker validates ownership and borrowing statically",
            "More explicit lifetime constraints in exchange for stronger guarantees.",
        )
        concept = next(item for item in self.store.list_concepts(self.profile)
                       if item["key"] == "memory")
        self.assertEqual(concept["status"], "understood")
        self.assertIn("borrow", concept["notes"].lower())
        comparisons = self.store.list_comparisons(self.profile)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0]["known_language"], "C++")

    def test_katas_idioms_and_error_journal(self) -> None:
        self.store.complete_kata(
            self.profile, "sem-01", 5, "Observed moves and borrowed references.",
            "experiments/value-semantics.rs",
        )
        kata = next(item for item in self.store.list_katas(self.profile)
                    if item["id"] == "sem-01")
        self.assertEqual(kata["status"], "completed")
        self.assertEqual(kata["score"], 5)

        self.store.add_idiom(
            self.profile, "Result propagation", "? operator",
            "Nested match ladders that discard error context",
            "Propagate expected failures and add context at abstraction boundaries.",
            "The Rust book",
        )
        idioms = self.store.list_idioms(self.profile)
        self.assertEqual(idioms[0]["name"], "Result propagation")

        self.store.add_error(
            self.profile, "Borrow after move", "value used after it was moved",
            "Ownership transferred into a consuming function",
            "Borrow the value or clone only when the ownership contract requires it",
            "Check parameter ownership before choosing a call signature",
            "stable",
        )
        error = self.store.list_errors(self.profile)[0]
        self.assertIn("ownership", error["cause"].lower())
        self.assertIn("parameter ownership", error["lesson"])

    def test_daily_plan_uses_exact_budget_and_adapts_to_profile(self) -> None:
        novice = self.store.daily_plan(self.profile, 37)
        self.assertEqual(sum(item["minutes"] for item in novice), 37)
        self.assertTrue(any("время жизни" in item["task"] for item in novice))
        self.assertTrue(all(item["minutes"] >= 0 for item in novice))
        for item in self.store.list_concepts(self.profile):
            self.store.update_concept(self.profile, item["key"], "understood")
        advanced_profile = dict(self.profile)
        advanced_profile["current_level"] = "advanced"
        advanced = self.store.daily_plan(advanced_profile, 37)
        self.assertEqual(sum(item["minutes"] for item in advanced), 37)
        self.assertEqual(advanced[0]["mode"], "reading")

    def test_session_report_and_json_export(self) -> None:
        self.store.log_session(self.profile, 25, "coding", "Implemented a parser", 4)
        self.store.log_session(self.profile, 10, "testing", "Boundary tests", 5)
        report = self.store.report(self.profile)
        self.assertEqual(report["last_7_days_sessions"], 2)
        self.assertEqual(report["last_7_days_minutes"], 35)
        self.assertEqual(report["concepts_total"], 16)
        exported = self.store.export_profile(self.profile)
        self.assertEqual(exported["schema_version"], 1)
        self.assertEqual(len(exported["sessions"]), 2)
        self.assertEqual(json.loads(json.dumps(exported))["profile"]["target_language"], "Rust")

    def test_validation_rejects_unknown_concepts_katas_and_bad_values(self) -> None:
        with self.assertRaisesRegex(PolyglotCodeError, "unknown concept"):
            self.store.update_concept(self.profile, "invented", "understood")
        with self.assertRaisesRegex(PolyglotCodeError, "unknown kata"):
            self.store.complete_kata(self.profile, "fake-kata")
        with self.assertRaisesRegex(PolyglotCodeError, "between 5 and 240"):
            self.store.create_profile("Go", level="novice", daily_minutes=2)
        with self.assertRaisesRegex(PolyglotCodeError, "from 0 to 5"):
            self.store.log_session(self.profile, 10, "coding", score=9)
        with self.assertRaisesRegex(PolyglotCodeError, "positive"):
            self.store.list_errors(self.profile, 0)
        self.assertIn(infer_family("Haskell"), FAMILIES)


class PolyglotCodeCliTests(unittest.TestCase):
    def test_cli_profile_plan_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "cli.sqlite3")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([
                    "--db", db, "init", "Go", "--known", "Python",
                    "--level", "novice", "--minutes", "30",
                ]), 0)
                self.assertEqual(main(["--db", db, "plan"]), 0)
                self.assertEqual(main(["--db", db, "report"]), 0)
            rendered = output.getvalue()
            self.assertIn("Профиль готов: Go", rendered)
            self.assertIn("План: Go", rendered)
            self.assertIn("Концепции:", rendered)

    def test_roadmap_is_readable_without_creating_a_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "unused.sqlite3"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["--db", str(db), "roadmap", "--stage", "2"]), 0)
            self.assertIn("Этап 2: Semantics", output.getvalue())
            self.assertTrue(db.exists())


if __name__ == "__main__":
    unittest.main()
