"""Tests for REAPER's DAP adapter."""
import io
import unittest
from reaper.dap import DebugSession

class DebugAdapterTests(unittest.TestCase):
    def test_initialize_advertises_only_supported_controls(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.handle({"seq": 1, "command": "initialize", "arguments": {}})
        payload = stream.getvalue().decode()
        self.assertIn("supportsConfigurationDoneRequest", payload)
        self.assertIn('"supportsConditionalBreakpoints":false', payload)
        self.assertIn('"supportsStepBack":false', payload)

    def test_breakpoint_lines_are_positive_and_sorted(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.handle({"seq": 2, "command": "setBreakpoints", "arguments": {
            "breakpoints": [{"line": 9}, {"line": 0}, {"line": 3}]}})
        payload = stream.getvalue().decode()
        self.assertIn('"line":3', payload)
        self.assertIn('"line":9', payload)
        self.assertNotIn('"line":0', payload)

    def test_launch_rejects_missing_program(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.handle({"seq": 3, "command": "launch", "arguments": {"program": "/no/such/file.rpr"}})
        self.assertIn('"success":false', stream.getvalue().decode())

if __name__ == "__main__":
    unittest.main()
