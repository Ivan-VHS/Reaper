import unittest
from reaper.language_service import LanguageService, LanguagePluginRegistry
from reaper.lsp import LspServer

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.s=LanguageService()
        self.addCleanup(self.s.shutdown)
    def test_tolerant_parse_indexes_symbols_with_unclosed_expression(self):
        self.s.open("file:///x.rpr","craft greet(name) {\n emit name\nmake total := (1+2")
        a=self.s.analyze("file:///x.rpr")
        self.assertEqual([x.name for x in a.symbols],["greet","total"])
        self.assertTrue(any(x.code=="incomplete-delimiter" for x in a.diagnostics))
    def test_navigation_references_and_rename_validation(self):
        uri="file:///x.rpr"; self.s.open(uri,"make total := 1\nemit total"); self.s.analyze(uri)
        self.assertEqual(len(self.s.references(uri,"total")),2)
        self.assertEqual(len(self.s.rename(uri,"total","sum")),2)
        with self.assertRaises(ValueError): self.s.rename(uri,"total","when")
    def test_incremental_change_rejects_stale_version(self):
        uri="file:///x.rpr"; self.s.open(uri,"emit 1",1)
        self.s.change(uri,2,[{"range":{"start":{"line":0,"character":5},"end":{"line":0,"character":6}},"text":"2"}])
        old=self.s.change(uri,1,[{"text":"emit 99"}])
        self.assertEqual((old.version,old.text),(2,"emit 2"))
    def test_lazy_plugin_activation(self):
        registry=LanguagePluginRegistry(); made=[]
        registry.register("rpr",[".rpr"],lambda: made.append(1) or object())
        self.assertIsNone(registry.activate("a.txt")); self.assertEqual(made,[])
        self.assertIs(registry.activate("a.rpr"),registry.activate("b.rpr"))
    def test_lsp_capabilities(self):
        server=LspServer()
        r=server.dispatch({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        self.assertTrue(r["result"]["capabilities"]["definitionProvider"])
        server.service.shutdown()

if __name__=="__main__": unittest.main()
