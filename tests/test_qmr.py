from __future__ import annotations

import math
import unittest

from reaper.qmr import (
    analyze_cadence,
    audit_pipeline_cohesion,
    build_qmr_report,
)


class QualityCohesionCadenceTests(unittest.TestCase):
    def test_stable_cadence_scores_maximum(self) -> None:
        result = analyze_cadence([1.0, 1.0, 1.0, 1.0], 1.0)
        self.assertEqual(result["schema"], "reaper.qmr-cadence.v1")
        self.assertEqual(result["cadence_score"], 100.0)
        self.assertEqual(result["relative_drift"], 0.0)

    def test_cadence_detects_bias_and_drift(self) -> None:
        result = analyze_cadence([1.0, 1.0, 1.08, 1.08], 1.0, 0.1)
        self.assertGreater(result["relative_drift"], 0.0)
        self.assertLess(result["cadence_score"], 100.0)

    def test_cadence_rejects_non_finite_and_invalid_bounds(self) -> None:
        with self.assertRaises(ValueError):
            analyze_cadence([1.0, math.nan], 1.0)
        with self.assertRaises(ValueError):
            analyze_cadence([1.0], 1.0)
        with self.assertRaises(ValueError):
            analyze_cadence([1.0, 1.0], 0.0)
        with self.assertRaises(ValueError):
            analyze_cadence([1.0, 1.0], 1.0, 0.0)
        with self.assertRaises(TypeError):
            analyze_cadence([1.0, True], 1.0)

    def test_pipeline_cohesion_identifies_missing_order_and_duplicates(self) -> None:
        result = audit_pipeline_cohesion(
            ["parse", "lex", "parse", "emit"],
            ["lex", "parse", "lower", "emit"],
        )
        self.assertEqual(result["missing_stages"], ["lower"])
        self.assertEqual(result["duplicate_stages"], ["parse"])
        self.assertEqual(result["order_inversions"], 1)
        self.assertFalse(result["cohesive"])
        self.assertLess(result["cohesion_score"], 100.0)

    def test_perfect_pipeline_is_cohesive(self) -> None:
        stages = ["lex", "parse", "lower", "optimize", "emit"]
        result = audit_pipeline_cohesion(stages, stages)
        self.assertTrue(result["cohesive"])
        self.assertEqual(result["cohesion_score"], 100.0)

    def test_combined_qmr_report(self) -> None:
        stages = ["lex", "parse", "lower"]
        result = build_qmr_report(
            {"bounded_input": True, "typed_edges": True},
            stages,
            stages,
            [0.5, 0.5, 0.5, 0.5],
            0.5,
        )
        self.assertEqual(result["schema"], "reaper.qmr-report.v1")
        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["quality"]["score"], 100.0)
        self.assertTrue(result["cohesion"]["cohesive"])


if __name__ == "__main__":
    unittest.main()
