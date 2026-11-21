"""Regression tests for REAPER IDE protocol cores."""
import io
import unittest
from reaper.dap import DebugSession
from reaper.lsp import LanguageService,read_message,write_message

class LanguageServiceTests(unittest.TestCase):
 def setUp(self):
  self.service=LanguageService(); self.uri="file:///workspace/main.rpr"
  self.service.handle("textDocument/didOpen",{"textDocument":{"uri":self.uri,"version":1,
   "text":"craft double(value) {\n    yield value * 2\n}\nmake answer := 4\nemit answer\n"}})
 def test_initialize_advertises_implemented_features(self):
  result,_=self.service.handle("initialize",{})
  self.assertTrue(result["capabilities"]["completionProvider"])
  self.assertTrue(result["capabilities"]["definitionProvider"])
  self.assertNotIn("semanticTokensProvider",result["capabilities"])
 def test_completion_and_hover(self):
  items,_=self.service.handle("textDocument/completion",{"textDocument":{"uri":self.uri},"position":{"line":0,"character":2}})
  self.assertIn("craft",[x["label"] for x in items])
  hover,_=self.service.handle("textDocument/hover",{"textDocument":{"uri":self.uri},"position":{"line":0,"character":2}})
  self.assertIn("Declare a function",hover["contents"]["value"])
 def test_symbols_and_references(self):
  symbols,_=self.service.handle("textDocument/documentSymbol",{"textDocument":{"uri":self.uri}})
  self.assertEqual([x["name"] for x in symbols],["double","answer"])
  refs,_=self.service.handle("textDocument/references",{"textDocument":{"uri":self.uri},"position":{"line":3,"character":7}})
  self.assertGreaterEqual(len(refs),2)
 def test_diagnostics_publish_for_invalid_source(self):
  _,notes=self.service.handle("textDocument/didChange",{"textDocument":{"uri":self.uri,"version":2},"contentChanges":[{"text":"make ="}]})
  self.assertEqual(notes[0]["method"],"textDocument/publishDiagnostics")
  self.assertEqual(notes[0]["params"]["diagnostics"][0]["severity"],1)
 def test_close_clears_document(self):
  _,notes=self.service.handle("textDocument/didClose",{"textDocument":{"uri":self.uri}})
  self.assertNotIn(self.uri,self.service.documents)
  self.assertEqual(notes[0]["params"]["diagnostics"],[])
 def test_content_length_roundtrip(self):
  stream=io.BytesIO(); write_message(stream,{"jsonrpc":"2.0","id":7,"result":"ok"}); stream.seek(0)
  self.assertEqual(read_message(stream),{"jsonrpc":"2.0","id":7,"result":"ok"})

class DebugAdapterTests(unittest.TestCase):
 def test_initialize_and_breakpoint_contract(self):
  stream=io.BytesIO(); session=DebugSession(stream)
  session.handle({"seq":1,"command":"initialize","arguments":{}})
  session.handle({"seq":2,"command":"setBreakpoints","arguments":{"breakpoints":[{"line":3},{"line":0}]}})
  payload=stream.getvalue().decode()
  self.assertIn("supportsConfigurationDoneRequest",payload)
  self.assertIn('"line":3',payload)
  self.assertNotIn('"line":0',payload)

if __name__=="__main__": unittest.main()
