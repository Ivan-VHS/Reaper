"""Tests for versioned REAPER language services and the LSP adapter."""
import unittest
from reaper.language_service import LanguageService, LanguagePluginRegistry, _offset
from reaper.lsp import LspServer

class LanguageServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = LanguageService()
        self.addCleanup(self.service.shutdown)

    def test_tolerant_index_and_parser_diagnostics(self):
        uri = "file:///x.rpr"
        self.service.open(uri, "craft greet(name) {\n emit name\nmake total := (1+2")
        analysis = self.service.analyze(uri)
        self.assertEqual([symbol.name for symbol in analysis.symbols], ["greet", "total"])
        self.assertTrue(any(item.code == "RPR-W0001" for item in analysis.diagnostics))
        self.assertTrue(any(item.code == "RPR-E0013" for item in analysis.diagnostics))

    def test_navigation_references_and_rename_validation(self):
        uri = "file:///x.rpr"
        self.service.open(uri, "make total := 1\nemit total")
        self.service.analyze(uri)
        self.assertEqual(len(self.service.references(uri, "total")), 2)
        self.assertEqual(len(self.service.rename(uri, "total", "sum_value")), 2)
        with self.assertRaises(ValueError):
            self.service.rename(uri, "total", "when")

    def test_incremental_change_rejects_stale_version(self):
        uri = "file:///x.rpr"
        self.service.open(uri, "emit 1", 1)
        updated = self.service.change(uri, 2, [{
            "range": {"start": {"line": 0, "character": 5}, "end": {"line": 0, "character": 6}},
            "text": "2",
        }])
        stale = self.service.change(uri, 1, [{"text": "emit 99"}])
        self.assertEqual((updated.version, updated.text), (2, "emit 2"))
        self.assertEqual((stale.version, stale.text), (2, "emit 2"))

    def test_utf16_position_maps_to_python_index(self):
        self.assertEqual(_offset('emit "😀"', {"line": 0, "character": 8}), 7)

    def test_most_function_alias_is_indexed_as_function(self):
        uri = "file:///most.most"
        self.service.open(uri, "функция привет(имя) {\n вернуть имя\n}")
        analysis = self.service.analyze(uri)
        self.assertEqual([(item.name, item.kind) for item in analysis.symbols],
                         [("привет", "function")])

    def test_lazy_plugin_activation(self):
        registry = LanguagePluginRegistry()
        created = []
        registry.register("reaper", [".rpr"], lambda: created.append(True) or object())
        self.assertIsNone(registry.activate("notes.txt"))
        self.assertEqual(created, [])
        self.assertIs(registry.activate("a.rpr"), registry.activate("b.rpr"))
        self.assertEqual(created, [True])

class LspAdapterTests(unittest.TestCase):
    def setUp(self):
        self.server = LspServer()
        self.addCleanup(self.server.service.shutdown)

    def test_ranges_use_utf16_columns(self):
        from reaper.language_service import Span
        self.assertEqual(self.server._range('emit "😀"', Span(0, 6, 7)), {
            "start": {"line": 0, "character": 6},
            "end": {"line": 0, "character": 8},
        })

    def test_initialize_advertises_incremental_sync(self):
        result = self.server.dispatch({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        capabilities = result["result"]["capabilities"]
        self.assertEqual(capabilities["textDocumentSync"]["change"], 2)
        self.assertTrue(capabilities["definitionProvider"])

    def test_open_publishes_diagnostics_and_symbols(self):
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": "file:///x.rpr", "version": 1, "text": "make value := ("}
        }})
        notifications = self.server.drain_notifications()
        self.assertEqual(notifications[0]["method"], "textDocument/publishDiagnostics")
        self.assertEqual(notifications[0]["params"]["version"], 1)
        self.assertTrue(notifications[0]["params"]["diagnostics"])

    def test_incremental_change_updates_version_and_completion(self):
        uri = "file:///x.rpr"
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": uri, "version": 1, "text": "make total := 1\nemit tot"}
        }})
        self.server.drain_notifications()
        self.server.dispatch({"method": "textDocument/didChange", "params": {
            "textDocument": {"uri": uri, "version": 2},
            "contentChanges": [{"range": {
                "start": {"line": 1, "character": 5}, "end": {"line": 1, "character": 8}
            }, "text": "total"}],
        }})
        notification = self.server.drain_notifications()[0]
        self.assertEqual(notification["params"]["version"], 2)
        response = self.server.dispatch({"jsonrpc": "2.0", "id": 2,
            "method": "textDocument/completion",
            "params": {"textDocument": {"uri": uri}, "position": {"line": 1, "character": 8}}})
        self.assertIn("total", [item["label"] for item in response["result"]["items"]])

    def test_stale_change_does_not_publish_new_version(self):
        uri = "file:///x.rpr"
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": uri, "version": 3, "text": "emit 1"}
        }})
        self.server.drain_notifications()
        self.server.dispatch({"method": "textDocument/didChange", "params": {
            "textDocument": {"uri": uri, "version": 2}, "contentChanges": [{"text": "emit 2"}]
        }})
        self.assertEqual(self.server.drain_notifications(), [])

    def test_close_clears_diagnostics(self):
        uri = "file:///x.rpr"
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": uri, "version": 1, "text": "emit 1"}
        }})
        self.server.drain_notifications()
        self.server.dispatch({"method": "textDocument/didClose", "params": {
            "textDocument": {"uri": uri}
        }})
        self.assertEqual(self.server.drain_notifications()[0]["params"]["diagnostics"], [])

if __name__ == "__main__":
    unittest.main()
