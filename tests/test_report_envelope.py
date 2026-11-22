from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "report_envelope.py"
SPEC = importlib.util.spec_from_file_location("report_envelope", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
report_envelope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report_envelope)

class ReportEnvelopeTests(unittest.TestCase):
    def test_preserves_result_and_adds_shared_metadata(self):
        result = {"audit_events": 3}
        report = report_envelope.build_envelope(
            tool="reaper", version="0.8.0", commit="ABCDEF012345678",
            result=result, created="2026-11-22T06:00:00Z",
            os_name="linux", architecture="x86_64")
        self.assertEqual(report["envelope"], "ivan-vhs.report.v1")
        self.assertEqual(report["tool"]["commit"], "abcdef012345678")
        self.assertEqual(report["result"], result)
        self.assertIn("not an operating-system sandbox", report["limitations"])

    def test_hashes_input_without_disclosing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.bin"
            path.write_bytes(b"input bytes")
            digest = report_envelope.sha256_file(path)
            report = report_envelope.build_envelope(
                tool="oplague", version="1", commit=None, result={},
                input_kind="file", input_sha256=digest,
                created="2026-11-22T06:00:00Z")
        self.assertEqual(report["input"]["sha256"], digest)
        self.assertNotIn("private.bin", json.dumps(report))

    def test_rejects_invalid_hashes_and_timestamps(self):
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(tool="reaper", version="1", commit="bad", result={})
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(tool="reaper", version="1", commit=None, result={}, input_sha256="123")
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(tool="reaper", version="1", commit=None, result={},
                                           created="2026-11-22T08:00:00+02:00")

    def test_limitations_are_deduplicated(self):
        report = report_envelope.build_envelope(
            tool="reaper", version="1", commit=None, result={},
            limitations=["the runtime is not an operating-system sandbox", "local review"])
        self.assertEqual(report["limitations"].count("the runtime is not an operating-system sandbox"), 1)
        self.assertIn("local review", report["limitations"])

if __name__ == "__main__":
    unittest.main()
