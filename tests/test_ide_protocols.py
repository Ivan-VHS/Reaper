"""Transport and debugger protocol regression tests for REAPER IDE."""
import io
import unittest

from reaper.dap import DebugSession, evaluate_read_only
from reaper.debugger import DebugSnapshot, RuntimeDebugger
from reaper.lsp import LspServer, read_message, write_message


class LspTransportTests(unittest.TestCase):
    def test_content_length_roundtrip(self):
        stream = io.BytesIO()
        write_message(stream, {"jsonrpc": "2.0", "id": 7, "result": "ok"})
        stream.seek(0)
        self.assertEqual(read_message(stream), {"jsonrpc": "2.0", "id": 7, "result": "ok"})

    def test_open_emits_protocol_notification(self):
        server = LspServer()
        try:
            server.dispatch({"method": "textDocument/didOpen", "params": {
                "textDocument": {"uri": "file:///x.rpr", "version": 1, "text": "emit 1"}
            }})
            messages = server.drain_notifications()
            self.assertEqual(messages[0]["method"], "textDocument/publishDiagnostics")
        finally:
            server.service.shutdown()


class DebugAdapterTests(unittest.TestCase):
    def test_initialize_advertises_implemented_capabilities(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.handle({"seq": 1, "command": "initialize", "arguments": {}})
        payload = stream.getvalue().decode()
        self.assertIn('"supportsConditionalBreakpoints":true', payload)
        self.assertIn('"supportsHitConditionalBreakpoints":true', payload)
        self.assertIn('"supportsLogPoints":true', payload)
        self.assertIn('"supportsStepOut":true', payload)
        self.assertIn('"supportsEvaluateForHovers":true', payload)

    def test_breakpoint_fields_and_hit_conditions(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.handle({"seq": 1, "command": "setBreakpoints", "arguments": {
            "breakpoints": [
                {"line": 3, "condition": "counter > 5", "hitCondition": ">=2"},
                {"line": 4, "logMessage": "counter={counter}"},
                {"line": 0},
            ]
        }})
        payload = stream.getvalue().decode()
        self.assertIn('"verified":true,"line":3', payload)
        self.assertIn('"verified":true,"line":4', payload)
        self.assertEqual(session.breakpoints, {3, 4})
        self.assertFalse(session._hit_condition_matches(">=2", 1))
        self.assertTrue(session._hit_condition_matches(">=2", 2))
        self.assertTrue(session._hit_condition_matches("%3", 6))
        self.assertFalse(session._hit_condition_matches("%3", 5))

    def test_condition_skips_breakpoint_and_logpoint_does_not_pause(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.breakpoint_specs = {
            7: {"line": 7, "condition": "counter > 10"},
            8: {"line": 8, "logMessage": "seen {counter}"},
        }
        session.pause_hook(DebugSnapshot("test.rpr", 7, 1, ["main"], {"counter": 2}))
        self.assertIsNone(session.snapshot)
        session.pause_hook(DebugSnapshot("test.rpr", 8, 1, ["main"], {"counter": 2}))
        self.assertFalse(session.waiting)
        self.assertIn("seen 2", stream.getvalue().decode())

    def test_read_only_evaluate_supports_values_and_rejects_calls(self):
        self.assertEqual(evaluate_read_only("counter * 2 + 1", {"counter": 20}), 41)
        self.assertEqual(evaluate_read_only("items[1]", {"items": [4, 9, 16]}), 9)
        self.assertTrue(evaluate_read_only("ready AND count >= 3", {"ready": True, "count": 3}))
        with self.assertRaises(ValueError):
            evaluate_read_only("emit(1)", {})
        with self.assertRaises(ValueError):
            evaluate_read_only("missing + 1", {})

    def test_step_out_waits_for_the_calling_frame(self):
        stopped = []
        debugger = RuntimeDebugger(pause_hook=stopped.append)
        debugger.last_snapshot = DebugSnapshot("test.rpr", 5, 1, ["outer", "inner"], {})
        debugger.step_out()
        debugger.before_statement(type("Token", (), {"line": 6, "column": 1})(), None, ["outer", "inner"], "test.rpr")
        self.assertEqual(stopped, [])
        debugger.before_statement(type("Token", (), {"line": 12, "column": 1})(), None, ["outer"], "test.rpr")
        self.assertEqual(len(stopped), 1)
        self.assertEqual(stopped[0].line, 12)


if __name__ == "__main__":
    unittest.main()
