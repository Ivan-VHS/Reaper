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

    def test_scenarios_and_registers_are_indexed_in_all_locales(self):
        uri = "file:///scenario-flow.rpr"
        self.service.open(uri, """
scenario operanda(value) { yield value }
reg total := 1
сценарий добуток(value) { повернути value }
регістр результат := 2
""")
        analysis = self.service.analyze(uri)
        self.assertEqual(
            [(item.name, item.kind) for item in analysis.symbols],
            [
                ("operanda", "function"),
                ("total", "variable"),
                ("добуток", "function"),
                ("результат", "variable"),
            ],
        )

        uri = "file:///typed.rpr"
        self.service.open(uri, 'emit "text" * 2')
        analysis = self.service.analyze(uri)
        diagnostic = next(item for item in analysis.diagnostics if item.code == "RPR-T0004")
        self.assertEqual(diagnostic.severity, "error")
        self.assertEqual(diagnostic.span.line, 0)

    def test_cross_document_definition_and_references(self):
        declaration_uri = "file:///project/model.rpr"
        usage_uri = "file:///project/main.rpr"
        self.service.open(declaration_uri, "make total := 7")
        self.service.open(usage_uri, "emit total")
        definitions = self.service.workspace_definitions("total")
        references = self.service.workspace_references("total")
        self.assertEqual([item.uri for item in definitions], [declaration_uri])
        self.assertEqual({uri for uri, _ in references}, {declaration_uri, usage_uri})
        self.assertEqual(len(references), 2)

    def test_workspace_symbol_query_is_bounded_and_case_insensitive(self):
        self.service.open("file:///a.rpr", "craft Render() { emit 1 }")
        self.service.open("file:///b.rpr", "craft render_more() { emit 2 }")
        self.assertEqual(
            [item.name for item in self.service.workspace_symbols("RENDER")],
            ["Render", "render_more"],
        )
        with self.assertRaises(ValueError):
            self.service.workspace_symbols("", limit=501)

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

    def test_workspace_symbols_and_cross_document_definition(self):
        declaration_uri = "file:///project/model.rpr"
        usage_uri = "file:///project/main.rpr"
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": declaration_uri, "version": 1,
                             "text": "make total := 7"}
        }})
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": usage_uri, "version": 1,
                             "text": "emit total"}
        }})
        symbols = self.server.dispatch({"jsonrpc": "2.0", "id": 20,
            "method": "workspace/symbol", "params": {"query": "tot"}})
        self.assertEqual(symbols["result"][0]["location"]["uri"], declaration_uri)

        definition = self.server.dispatch({"jsonrpc": "2.0", "id": 21,
            "method": "textDocument/definition",
            "params": {"textDocument": {"uri": usage_uri},
                       "position": {"line": 0, "character": 7}}})
        self.assertEqual(definition["result"][0]["uri"], declaration_uri)

        references = self.server.dispatch({"jsonrpc": "2.0", "id": 22,
            "method": "textDocument/references",
            "params": {"textDocument": {"uri": usage_uri},
                       "position": {"line": 0, "character": 7}}})
        self.assertEqual({item["uri"] for item in references["result"]},
                         {declaration_uri, usage_uri})

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

    def test_semantic_tokens_advertise_legend_and_classify_source(self):
        initialized = self.server.dispatch({
            "jsonrpc": "2.0", "id": 30, "method": "initialize"
        })
        provider = initialized["result"]["capabilities"]["semanticTokensProvider"]
        self.assertTrue(provider["full"])
        self.assertIn("function", provider["legend"]["tokenTypes"])
        self.assertIn("keyword", provider["legend"]["tokenTypes"])

        uri = "file:///semantic.rpr"
        source = 'craft hello(name) {\n make title := "😀"\n emit title\n}'
        self.server.dispatch({"method": "textDocument/didOpen", "params": {
            "textDocument": {"uri": uri, "version": 1, "text": source}
        }})
        response = self.server.dispatch({
            "jsonrpc": "2.0", "id": 31, "method": "textDocument/semanticTokens/full",
            "params": {"textDocument": {"uri": uri}},
        })
        data = response["result"]["data"]
        self.assertEqual(len(data) % 5, 0)

        token_types = provider["legend"]["tokenTypes"]
        seen = set()
        string_lengths = []
        declaration_modifiers = []
        line = 0
        start = 0
        for index in range(0, len(data), 5):
            delta_line, delta_start, length, token_type, modifiers = data[index:index + 5]
            line += delta_line
            start = start + delta_start if delta_line == 0 else delta_start
            kind = token_types[token_type]
            seen.add(kind)
            if kind == "string":
                string_lengths.append(length)
            if modifiers & 1:
                declaration_modifiers.append(kind)
        self.assertTrue({"keyword", "function", "variable", "string"} <= seen)
        self.assertEqual(string_lengths, [4])
        self.assertIn("function", declaration_modifiers)
        self.assertIn("variable", declaration_modifiers)

    def test_semantic_tokens_reject_closed_documents(self):
        response = self.server.dispatch({
            "jsonrpc": "2.0", "id": 32, "method": "textDocument/semanticTokens/full",
            "params": {"textDocument": {"uri": "file:///not-open.rpr"}},
        })
        self.assertEqual(response["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
