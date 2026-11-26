from __future__ import annotations

import unittest

from reaper.lsp import LspServer


class LspFormattingTests(unittest.TestCase):
    def setUp(self):
        self.server = LspServer()
        self.addCleanup(self.server.service.shutdown)

    def test_document_formatting_returns_single_utf16_range_edit(self):
        uri = "file:///format.rpr"
        source = 'craft greet() {\n emit "😀"   \n}\n'
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": uri, "version": 1, "text": source}
        }})
        self.server.drain_notifications()
        initialize = self.server.dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertTrue(initialize["result"]["capabilities"]["documentFormattingProvider"])
        response = self.server.dispatch({"jsonrpc": "2.0", "id": 2,
            "method": "textDocument/formatting",
            "params": {"textDocument": {"uri": uri}, "options": {"tabSize": 4, "insertSpaces": True}}})
        edit = response["result"][0]
        self.assertEqual(edit["newText"], 'craft greet() {\n    emit "😀"\n}\n')
        self.assertEqual(edit["range"]["start"], {"line": 0, "character": 0})
        self.assertEqual(edit["range"]["end"], {"line": 3, "character": 0})

    def test_closed_document_is_rejected(self):
        response = self.server.dispatch({"jsonrpc": "2.0", "id": 3,
            "method": "textDocument/formatting",
            "params": {"textDocument": {"uri": "file:///closed.rpr"}, "options": {"tabSize": 4}}})
        self.assertEqual(response["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
