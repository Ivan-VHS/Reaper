from __future__ import annotations

import unittest

from kontexa.engine import (
    MAX_DOCUMENT_CHARS,
    DEFAULT_CHUNK_CHARS,
    KontexaError,
    StructuralShield,
    analyze_document,
    semantic_chunk,
    extract_glossary_candidates,
    _check_protected_counts,
    _numeric_signature,
    translate_document,
)


class StructuralShieldTests(unittest.TestCase):
    def test_round_trip_preserves_markdown_code_templates_and_links(self):
        source = """# A heading

Text with `inline_code`, {{user.name}}, ${count}, %s and [link](https://example.com/path).

```python
value = {\"id\": 1}
```
"""
        shield = StructuralShield()
        protected = shield.protect(source)
        self.assertNotEqual(protected, source)
        restored, warnings = shield.restore(protected)
        self.assertEqual(restored, source)
        self.assertEqual(warnings, [])

    def test_missing_token_is_rejected(self):
        shield = StructuralShield()
        protected = shield.protect("Use `value` here")
        with self.assertRaisesRegex(KontexaError, "Missing protected token"):
            shield.restore(protected.replace("⟦KX000001⟧", "lost"))

    def test_chunk_token_validator_is_chunk_local(self):
        shield = StructuralShield()
        protected = shield.protect("`one` and `two`")
        chunks = semantic_chunk(protected, 800)
        self.assertTrue(_check_protected_counts(shield, protected))
        self.assertFalse(_check_protected_counts(shield, chunks[0].text.replace("⟦KX000002⟧", "missing")))


class SemanticChunkingTests(unittest.TestCase):
    def test_reconstructs_exact_source(self):
        source = "# Title\n\nFirst paragraph.\n\nSecond paragraph with detail.\n\n- item one\n- item two\n"
        chunks = semantic_chunk(source, 800)
        self.assertEqual("".join(chunk.text for chunk in chunks), source)
        self.assertTrue(all(len(chunk.text) <= 800 for chunk in chunks))

    def test_crlf_blank_lines_are_kept_as_semantic_boundaries(self):
        source = "# Title\r\n\r\nFirst section.\r\n\r\nSecond section.\r\n"
        chunks = semantic_chunk(source, 800)
        self.assertEqual("".join(chunk.text for chunk in chunks), source)
        self.assertEqual(chunks[0].text, source)

    def test_oversized_paragraph_is_split_without_loss(self):
        source = ("A sentence with a useful boundary. " * 120)
        chunks = semantic_chunk(source, 800)
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(chunk.text for chunk in chunks), source)
        self.assertTrue(all(len(chunk.text) <= 800 for chunk in chunks))

    def test_empty_document_has_no_chunks(self):
        self.assertEqual(semantic_chunk(""), [])

    def test_chunk_size_is_bounded(self):
        with self.assertRaises(KontexaError):
            semantic_chunk("hello", 100)
        with self.assertRaises(KontexaError):
            semantic_chunk("hello", 9000)


class DocumentAnalysisTests(unittest.TestCase):
    def test_exact_60000_character_limit_is_accepted(self):
        report = analyze_document("x" * MAX_DOCUMENT_CHARS)
        self.assertEqual(report["source_chars"], MAX_DOCUMENT_CHARS)

    def test_60001_characters_are_rejected(self):
        with self.assertRaisesRegex(KontexaError, "maximum is 60,000"):
            analyze_document("x" * (MAX_DOCUMENT_CHARS + 1))

    def test_large_document_graph_remains_valid_json_under_limit(self):
        sections = []
        for index in range(48):
            sections.append(f"# Section {index}\n\nAPI Gateway and DocumentContextGraph are used in this section.\n\n")
        text = ("".join(sections) + ("Additional content with stable context. " * 450))[:MAX_DOCUMENT_CHARS]
        report = analyze_document(text)
        self.assertGreater(report["graph_nodes"], 1)
        self.assertIsInstance(report["context_graph"]["edges"], list)

    def test_builds_document_graph_with_sections_terms_and_code(self):
        text = "# Overview\n\nThe API connects modules.\n\n## Runtime\n\n```python\nvalue = 1\n```\n"
        report = analyze_document(text)
        graph = report["context_graph"]
        node_types = {node["type"] for node in graph["nodes"]}
        relations = {edge["relation"] for edge in graph["edges"]}
        self.assertIn("document", node_types)
        self.assertIn("section", node_types)
        self.assertIn("term", node_types)
        self.assertIn("code_language", node_types)
        self.assertIn("contains", relations)
        self.assertIn("mentions", relations)

    def test_counts_unicode_code_points(self):
        text = "😀" * 10
        report = analyze_document(text)
        self.assertEqual(report["source_chars"], 10)

    def test_glossary_extracts_abbreviations_and_camel_case(self):
        terms = {item["source"] for item in extract_glossary_candidates("API Gateway and DocumentContextGraph with KONTEXA")}
        self.assertIn("API", terms)
        self.assertIn("DocumentContextGraph", terms)
        self.assertIn("KONTEXA", terms)

    def test_numeric_markers_are_stable(self):
        self.assertEqual(_numeric_signature("up to 60 000 chars, 99.5%, 20 MiB"), ["60000", "99.5%", "20MiB"])


class _MemoryCache:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value


class _EchoProvider:
    model = "test-model"
    endpoint = "http://127.0.0.1/test"

    def __init__(self, *, change_number=False, audit_risk="low"):
        self.calls = 0
        self.change_number = change_number
        self.audit_risk = audit_risk

    def translate(self, messages):
        import json
        self.calls += 1
        if "separate semantic audit pass" in messages[0]["content"]:
            return json.dumps({"risk": self.audit_risk, "back_translation": "original meaning", "tone_drift": "none", "register_score": 100, "issues": []})
        content = messages[1]["content"]
        start = content.find("<KONTEXA_SOURCE_SEGMENT>\n")
        end = content.find("\n</KONTEXA_SOURCE_SEGMENT>", start)
        if start < 0 or end < 0:
            raise AssertionError("Translation payload markers were not found")
        result = content[start + len("<KONTEXA_SOURCE_SEGMENT>\n"):end]
        if self.change_number:
            result = result.replace("60 000", "60 001")
        return result


class TranslationPipelineTests(unittest.TestCase):
    def test_translation_restores_protected_fragments_and_audits(self):
        source = "# Document\n\nKeep `code` and {{user_id}} unchanged. Limit: 60 000."
        provider = _EchoProvider()
        translated, report = translate_document(
            source, provider=provider, source_lang="English", target_lang="Ukrainian",
            semantic_audit=True,
        )
        self.assertEqual(translated, source)
        self.assertTrue(report.protected_integrity)
        self.assertTrue(report.numeric_markers_preserved)
        self.assertEqual(report.semantic_audit[0]["risk"], "low")
        self.assertEqual(report.status, "complete")
        self.assertEqual(provider.calls, 2)

    def test_contextual_cache_reuses_unchanged_segment(self):
        source = "One short paragraph.\n\nSecond short paragraph."
        provider = _EchoProvider()
        cache = _MemoryCache()
        first, first_report = translate_document(
            source, provider=provider, source_lang="English", target_lang="Ukrainian", cache=cache,
        )
        calls_after_first = provider.calls
        second, second_report = translate_document(
            source, provider=provider, source_lang="English", target_lang="Ukrainian", cache=cache,
        )
        self.assertEqual(first, second)
        self.assertEqual(second_report.cache_hits, second_report.chunk_count)
        self.assertEqual(provider.calls, calls_after_first)

    def test_numeric_mismatch_requires_review(self):
        source = "The limit is 60 000 characters."
        translated, report = translate_document(
            source, provider=_EchoProvider(change_number=True), source_lang="English", target_lang="Ukrainian",
        )
        self.assertIn("60 001", translated)
        self.assertFalse(report.numeric_markers_preserved)
        self.assertEqual(report.status, "needs_review")

    def test_hard_lock_requires_a_target(self):
        with self.assertRaisesRegex(KontexaError, "approved target"):
            translate_document(
                "Kontexa", provider=_EchoProvider(), source_lang="English", target_lang="Ukrainian",
                glossary=[{"source": "Kontexa", "target": "", "mode": "hard_lock"}],
            )

    def test_invalid_unicode_surrogate_is_rejected(self):
        with self.assertRaisesRegex(KontexaError, "invalid Unicode surrogate"):
            analyze_document("bad\ud800text")


if __name__ == "__main__":
    unittest.main()
