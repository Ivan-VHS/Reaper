from __future__ import annotations

import unittest

from reaper.careguard import (
    WorkloadSnapshot,
    careguard_accept_help_request,
    careguard_allocate_resilience_buffer,
    careguard_assess_project_load,
    careguard_check_clinical_boundary,
    careguard_probe_sensitive_handler,
    careguard_record_context_event,
    careguard_review_contextual_claim,
    careguard_review_language,
    careguard_select_support_path,
)

class CareGuardTests(unittest.TestCase):
    def test_empty_project_is_normal(self):
        result = careguard_assess_project_load(WorkloadSnapshot())
        self.assertEqual(result.status, "normal")
        self.assertGreaterEqual(result.reserve_percent, 10)

    def test_technical_pressure_can_recommend_pause(self):
        result = careguard_assess_project_load(
            WorkloadSnapshot(queued_items=20, failed_checks=4, alerts_per_hour=30,
                             active_workers=12, worker_capacity=10)
        )
        self.assertEqual(result.status, "pause")
        self.assertIn("alert_flood", result.findings)

    def test_language_review_suggests_but_does_not_rewrite(self):
        text = "Calling someone lazy is not useful."
        findings = careguard_review_language(text)
        self.assertTrue(any(item.phrase == "ленивый" for item in careguard_review_language("ленивый")))
        self.assertTrue(findings)
        self.assertEqual(text, "Calling someone lazy is not useful.")

    def test_sensitive_terms_do_not_crash_handler(self):
        self.assertEqual(careguard_probe_sensitive_handler(lambda value: value.casefold()), ())

    def test_help_request_is_not_classified_as_weakness(self):
        self.assertTrue(careguard_accept_help_request("I need help"))
        self.assertFalse(careguard_accept_help_request("   "))

    def test_support_route_is_manual(self):
        route = careguard_select_support_path("urgent_human")
        self.assertFalse(route["automatic_contact"])
        self.assertEqual(route["mode"], "manual_choice")

    def test_clinical_actions_are_blocked(self):
        self.assertFalse(careguard_check_clinical_boundary("prescribe antidepressant"))
        self.assertFalse(careguard_check_clinical_boundary("поставить диагноз"))
        self.assertTrue(careguard_check_clinical_boundary("pause project pipeline"))

    def test_claim_requires_evidence_reference(self):
        self.assertFalse(careguard_review_contextual_claim("The new handler is safe", None))
        self.assertTrue(careguard_review_contextual_claim("The test passed", "ci://run/123"))

    def test_resilience_buffer_is_bounded(self):
        self.assertEqual(careguard_allocate_resilience_buffer(10, 0.2), (2, 8))
        with self.assertRaises(ValueError):
            careguard_allocate_resilience_buffer(10, 0.9)

    def test_event_log_is_allowlisted_and_minimal(self):
        event = careguard_record_context_event("maintainer", "human_review_requested", "2026-11-21T20:00:00Z")
        self.assertEqual(set(event), {"actor", "event_type", "occurred_at"})
        with self.assertRaises(ValueError):
            careguard_record_context_event("maintainer", "symptom_recorded", "2026-11-21T20:00:00Z")

if __name__ == "__main__":
    unittest.main()
