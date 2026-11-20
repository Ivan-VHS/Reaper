from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from reaper.audit import AuditLog, verify_audit_log
from reaper.thesis import ThesisLedger, ThesisLedgerError, THESIS_SCHEMA


class ThesisLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = ThesisLedger()
        self.claim = self.ledger.add_claim(
            "clm:incident-count-a",
            "The reported count for one defined interval is 12.",
            "case:sample",
            created_at_utc="2026-11-20T10:00:00Z",
            period_start_utc="2026-11-01T00:00:00Z",
            period_end_utc="2026-11-08T00:00:00Z",
            metric_key="event.count",
            quantity_value=12,
            quantity_unit="events",
        )

    def add_source(self, evidence_id: str, relation: str = "supports") -> None:
        self.ledger.add_evidence(
            evidence_id, self.claim.claim_id,
            relation=relation, source_ref="src:archive-a",
            source_kind="document", source_class="primary",
            content_sha256="a" * 64, locator="page:4/paragraph:2",
            captured_at_utc="2026-11-20T10:05:00+00:00",
            actor_ref="anon:reviewer-01",
        )

    def test_evidence_preserves_relation_and_never_auto_verifies(self) -> None:
        self.add_source("evd:source-a")
        self.add_source("evd:source-b", "contradicts")
        self.assertEqual(self.ledger.snapshot()["claims"][0]["status"], "proposed")
        evidence = self.ledger.evidence_for("clm:incident-count-a")
        self.assertEqual([item.relation for item in evidence], ["supports", "contradicts"])
        self.assertEqual(evidence[0].actor_ref, "anon:reviewer-01")

    def test_quantitative_comparison_requires_matching_scope_unit_and_window(self) -> None:
        self.ledger.add_claim(
            "clm:incident-count-b", "A second estimate is 15.",
            "case:sample", created_at_utc="2026-11-20T10:00:00Z",
            period_start_utc="2026-11-01T00:00:00Z",
            period_end_utc="2026-11-08T00:00:00Z",
            metric_key="event.count", quantity_value=15, quantity_unit="events",
        )
        result = self.ledger.compare_quantitative_claims(
            "clm:incident-count-a", "clm:incident-count-b", tolerance=2
        )
        self.assertTrue(result["comparable"])
        self.assertEqual(result["delta"], 3)
        self.assertFalse(result["within_tolerance"])

        self.ledger.add_claim(
            "clm:incompatible-window", "A count from another interval is 15.",
            "case:sample", created_at_utc="2026-11-20T10:00:00Z",
            period_start_utc="2026-11-08T00:00:00Z",
            period_end_utc="2026-11-15T00:00:00Z",
            metric_key="event.count", quantity_value=15, quantity_unit="events",
        )
        mismatch = self.ledger.compare_quantitative_claims(
            "clm:incident-count-a", "clm:incompatible-window"
        )
        self.assertFalse(mismatch["comparable"])
        self.assertIn("time window differs", mismatch["reasons"])

    def test_revision_is_append_only_and_resets_review_state(self) -> None:
        self.ledger.set_status(
            self.claim.claim_id, "reviewed", reason="manual review",
            recorded_at_utc="2026-11-20T11:00:00Z",
            actor_ref="anon:reviewer-01",
        )
        updated = self.ledger.revise_claim(
            self.claim.claim_id, "The corrected reported count is 13.",
            reason="source transcription corrected",
            recorded_at_utc="2026-11-20T12:00:00Z",
            actor_ref="anon:reviewer-01",
        )
        self.assertEqual(updated.revision, 2)
        self.assertEqual(updated.status, "proposed")
        snapshot = self.ledger.snapshot()
        self.assertEqual(snapshot["revisions"][0]["revision"], 1)
        self.assertEqual(
            snapshot["revisions"][0]["previous_statement_sha256"],
            hashlib.sha256(self.claim.statement.encode()).hexdigest(),
        )

    def test_direct_names_are_rejected_in_identity_fields(self) -> None:
        with self.assertRaisesRegex(ThesisLedgerError, "opaque anon"):
            self.ledger.add_evidence(
                "evd:bad-actor", self.claim.claim_id,
                relation="supports", source_ref="src:archive-a",
                source_kind="document", source_class="primary",
                content_sha256="a" * 64, locator="page:1",
                captured_at_utc="2026-11-20T10:00:00Z",
                actor_ref="John Smith",
            )

    def test_invalid_hash_timestamp_status_and_unknown_target_fail_closed(self) -> None:
        with self.assertRaisesRegex(ThesisLedgerError, "SHA-256"):
            self.ledger.add_evidence(
                "evd:bad-hash", self.claim.claim_id,
                relation="supports", source_ref="src:archive-a",
                source_kind="document", source_class="primary",
                content_sha256="not-a-hash", locator="page:1",
                captured_at_utc="2026-11-20T10:00:00Z",
            )
        with self.assertRaisesRegex(ThesisLedgerError, "timezone"):
            self.ledger.add_claim(
                "clm:naive-date", "A statement", "case:sample",
                created_at_utc="2026-11-20T10:00:00",
            )
        with self.assertRaisesRegex(ThesisLedgerError, "unknown claim"):
            self.ledger.add_evidence(
                "evd:orphan", "clm:missing",
                relation="supports", source_ref="src:archive-a",
                source_kind="document", source_class="unknown",
                content_sha256="a" * 64, locator="page:1",
                captured_at_utc="2026-11-20T10:00:00Z",
            )
        with self.assertRaisesRegex(ThesisLedgerError, "unsupported claim status"):
            self.ledger.set_status(
                self.claim.claim_id, "verified", reason="not permitted",
                recorded_at_utc="2026-11-20T10:00:00Z",
            )

    def test_snapshot_is_deterministic_and_reports_coverage(self) -> None:
        self.add_source("evd:source-a")
        first = self.ledger.snapshot()
        second = self.ledger.snapshot()
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], THESIS_SCHEMA)
        self.assertEqual(len(first["snapshot_sha256"]), 64)
        self.assertEqual(self.ledger.summary()["claims_without_evidence"], 0)

    def test_optional_audit_log_records_metadata_not_statement_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "thesis-audit.jsonl"
            ledger = ThesisLedger(AuditLog(path))
            ledger.add_claim(
                "clm:audited",
                "private claim text must not enter audit details",
                "case:a", created_at_utc="2026-11-20T10:00:00Z",
            )
            summary = verify_audit_log(path)
            self.assertEqual(summary.records, 1)
            self.assertNotIn("private claim text", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
