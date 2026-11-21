"""Transport and debugger protocol regression tests for REAPER IDE."""
import io
import unittest
from reaper.dap import DebugSession
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
    def test_initialize_and_breakpoint_contract(self):
        stream = io.BytesIO()
        session = DebugSession(stream)
        session.handle({"seq": 1, "command": "initialize", "arguments": {}})
        session.handle({"seq": 2, "command": "setBreakpoints", "arguments": {
            "breakpoints": [{"line": 3}, {"line": 0}]
        }})
        payload = stream.getvalue().decode()
        self.assertIn("supportsConfigurationDoneRequest", payload)
        self.assertIn('"line":3', payload)
        self.assertNotIn('"line":0', payload)

if __name__ == "__main__":
    unittest.main()
