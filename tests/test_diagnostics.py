from __future__ import annotations
import unittest
from reaper.diagnostic_catalog import diagnose_exception, diagnostic_definitions, explain_diagnostic
from reaper.errors import LexError, ParseError, ExecutionLimitError

class DiagnosticCatalogTests(unittest.TestCase):
    def test_registry_codes_are_unique_and_stable(self):
        definitions = diagnostic_definitions()
        codes = [item["code"] for item in definitions]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(code.startswith("RPR-") for code in codes))

    def test_explain_returns_actionable_help(self):
        item = explain_diagnostic("RPR-E0013")
        self.assertIsNotNone(item)
        self.assertIn("delimiter", item["help"])
        self.assertIsNone(explain_diagnostic("RPR-E9999"))

    def test_parse_diagnostic_preserves_source_range(self):
        item = diagnose_exception(ParseError("examples/flow.rpr:7:12: expected a closing brace"), "fallback.rpr")
        payload = item.to_dict()
        self.assertEqual(payload["code"], "RPR-E0013")
        self.assertEqual(payload["file"], "examples/flow.rpr")
        self.assertEqual(payload["range"]["start"], {"line":6,"character":11})
        self.assertEqual(payload["range"]["end"], {"line":6,"character":12})
        self.assertIn("closing brace", payload["message"])

    def test_lexer_and_budget_errors_have_distinct_codes(self):
        self.assertEqual(diagnose_exception(LexError("bad token")).code, "RPR-E0001")
        self.assertEqual(diagnose_exception(ExecutionLimitError("step limit")).code, "RPR-E0101")

if __name__ == "__main__":
    unittest.main()
