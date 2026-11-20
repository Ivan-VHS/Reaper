from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper.audit import AuditLog
from reaper.governance import (
    MAX_CONSENT_TTL_SECONDS, ConsentAuthority, ConsentError,
)
from reaper.runtime import Builtin, Interpreter


class ConsentAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = ConsentAuthority(b"k" * 32)
        self.token = self.authority.issue(
            "local-user", "report-export", ["read-summary", "write-json"],
            3600, now=1_000,
        )

    def test_valid_grant_is_scoped_and_time_bounded(self) -> None:
        self.assertTrue(self.authority.verify(
            self.token, subject="local-user", purpose="report-export",
            scope="write-json", now=1_001,
        ))
        self.assertFalse(self.authority.verify(
            self.token, subject="other-user", purpose="report-export",
            scope="write-json", now=1_001,
        ))
        self.assertFalse(self.authority.verify(
            self.token, subject="local-user", purpose="marketing",
            scope="write-json", now=1_001,
        ))
        self.assertFalse(self.authority.verify(
            self.token, subject="local-user", purpose="report-export",
            scope="telemetry", now=1_001,
        ))

    def test_expired_not_yet_valid_tampered_and_unknown_grants_fail_closed(self) -> None:
        arguments = dict(subject="local-user", purpose="report-export", scope="write-json")
        self.assertFalse(self.authority.verify(self.token, **arguments, now=4_600))
        self.assertFalse(self.authority.verify(self.token, **arguments, now=999))
        changed = dict(self.token, expires_at=999_999)
        self.assertFalse(self.authority.verify(changed, **arguments, now=1_001))
        self.assertFalse(self.authority.verify(None, **arguments, now=1_001))

    def test_ttl_is_finite_and_bounded(self) -> None:
        with self.assertRaises(ConsentError):
            self.authority.issue("user", "purpose", ["scope"], 0, now=10)
        with self.assertRaises(ConsentError):
            self.authority.issue(
                "user", "purpose", ["scope"], MAX_CONSENT_TTL_SECONDS + 1,
                now=10,
            )

    def test_revoke_is_immediate_and_survives_restart_with_audit_log(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "governance.jsonl"
            first = ConsentAuthority(b"z" * 32, AuditLog(path))
            token = first.issue("user", "export", ["summary"], 60, now=100)
            self.assertTrue(first.verify(
                token, subject="user", purpose="export", scope="summary", now=101
            ))
            self.assertTrue(first.revoke(token))
            second = ConsentAuthority(b"z" * 32, AuditLog(path))
            self.assertFalse(second.verify(
                token, subject="user", purpose="export", scope="summary", now=101
            ))

    def test_wrong_key_cannot_verify_or_revoke(self) -> None:
        other = ConsentAuthority(b"x" * 32)
        self.assertFalse(other.verify(
            self.token, subject="local-user", purpose="report-export",
            scope="write-json", now=1_001,
        ))
        self.assertFalse(other.revoke(self.token))

    def test_runtime_exposes_host_controlled_consent_builtins(self) -> None:
        interpreter = Interpreter(consent_authority=self.authority)
        check = interpreter.globals.get("consent_check")
        revoke = interpreter.globals.get("consent_revoke")
        self.assertIsInstance(check, Builtin)
        self.assertIsInstance(revoke, Builtin)
        self.assertTrue(check.callback(
            self.token, "local-user", "report-export", "write-json"
        ))
        self.assertTrue(revoke.callback(self.token))
        self.assertFalse(check.callback(
            self.token, "local-user", "report-export", "write-json"
        ))

    def test_runtime_never_treats_missing_authority_as_allow(self) -> None:
        interpreter = Interpreter()
        check = interpreter.globals.get("consent_check")
        with self.assertRaisesRegex(Exception, "host-injected ConsentAuthority"):
            check.callback(self.token, "local-user", "report-export", "write-json")


if __name__ == "__main__":
    unittest.main()
