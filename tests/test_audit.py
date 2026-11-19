from __future__ import annotations
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from reaper.audit import AuditLog, AuditLogError, verify_audit_log
from reaper.cli import main

class AuditLogTests(unittest.TestCase):
    def test_append_and_verify_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            audit = AuditLog(path)
            first = audit.record("execution_started", source_sha256="a" * 64)
            second = audit.record("execution_completed", output_lines=2)
            summary = verify_audit_log(path)
        self.assertNotEqual(first, second)
        self.assertEqual(summary.records, 2)
        self.assertEqual(summary.last_hash, second)

    def test_tampered_record_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            AuditLog(path).record("execution_started", source_sha256="b" * 64)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["details"]["source_sha256"] = "c" * 64
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AuditLogError, "digest mismatch"):
                verify_audit_log(path)

    def test_broken_previous_hash_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            audit = AuditLog(path)
            audit.record("one")
            audit.record("two")
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[1]["previous_hash"] = "f" * 64
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AuditLogError, "broken hash link"):
                verify_audit_log(path)

    def test_new_writer_refuses_corrupted_existing_log(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            path.write_text("not-json\n", encoding="utf-8")
            with self.assertRaises(AuditLogError):
                AuditLog(path)

    def test_cli_records_execution_without_capturing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main(["examples/hello.rpr", "--audit-log", str(path)])
            summary = verify_audit_log(path)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(result, 0)
        self.assertIn("hello", stdout.getvalue().lower())
        self.assertEqual(summary.records, 3)
        self.assertEqual([row["event"] for row in rows],
                         ["source_loaded", "execution_started", "execution_completed"])
        self.assertNotIn("hello", path.read_text(encoding="utf-8"))

    def test_cli_verification_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            AuditLog(path).record("manual_check")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main(["--verify-audit-log", str(path)])
        self.assertEqual(result, 0)
        self.assertIn("1 record(s)", stdout.getvalue())

if __name__ == "__main__":
    unittest.main()
