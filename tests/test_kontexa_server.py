from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from kontexa.server import Handler, KontexaServer, _parse_alternatives
from kontexa.provider import ProviderError


class LocalServerTests(unittest.TestCase):
    def test_alternative_response_schema_is_validated(self):
        payload = json.dumps({"alternatives": [
            {"text": "Bank (financial institution)", "nuance": "A monetary institution", "when_to_use": "When the source refers to money"},
            {"text": "River bank", "nuance": "A river edge", "when_to_use": "When the surrounding topic is geography"},
        ]})
        result = _parse_alternatives(payload)
        self.assertEqual(len(result), 2)
        with self.assertRaises(ProviderError):
            _parse_alternatives('{"alternatives": []}')

    @classmethod
    def setUpClass(cls):
        cls.server = KontexaServer(("127.0.0.1", 0), Handler)
        cls.server.jobs = SimpleNamespace()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_and_workspace_are_served(self):
        with urllib.request.urlopen(self.base + "/api/health", timeout=2) as response:
            health = json.load(response)
        self.assertEqual(health["app"], "Kontexa")
        self.assertEqual(health["max_chars"], 60_000)
        with urllib.request.urlopen(self.base + "/", timeout=2) as response:
            page = response.read().decode("utf-8")
        self.assertIn("Context Translation Workspace", page)

    def test_document_preflight_api(self):
        request = urllib.request.Request(
            self.base + "/api/analyze",
            data=json.dumps({"text": "# Kontexa\n\nA protected `code` value."}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.load(response)
        self.assertEqual(payload["source_chars"], len("# Kontexa\n\nA protected `code` value."))
        self.assertGreater(payload["protected_count"], 0)

    def test_ambiguity_alternatives_endpoint_uses_configured_provider(self):
        class FakeProvider:
            def __init__(self, **kwargs):
                self.model = kwargs["model"]

            def translate(self, messages):
                return json.dumps({"alternatives": [
                    {"text": "банк", "nuance": "Финансовое учреждение", "when_to_use": "В финансовом контексте"},
                    {"text": "берег", "nuance": "Край водоёма", "when_to_use": "В географическом контексте"},
                ]}, ensure_ascii=False)

        payload = {
            "term": "bank", "snippet": "The bank was closed.",
            "context": "The character needed to withdraw cash.",
            "source_lang": "English", "target_lang": "Russian",
            "style": "Neutral", "domain": "General",
        }
        request = urllib.request.Request(
            self.base + "/api/alternatives",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with patch("kontexa.server.load_config", return_value={
            "base_url": "http://127.0.0.1:11434/v1", "model": "test-model",
            "api_key": "", "timeout": 15,
        }), patch("kontexa.server.OpenAICompatibleProvider", FakeProvider):
            with urllib.request.urlopen(request, timeout=2) as response:
                result = json.load(response)
        self.assertEqual(result["model"], "test-model")
        self.assertEqual([item["text"] for item in result["alternatives"]], ["банк", "берег"])

    def test_cross_origin_requests_are_rejected(self):
        request = urllib.request.Request(
            self.base + "/api/health", headers={"Origin": "https://evil.example"}
        )
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request, timeout=2)
        self.assertEqual(error.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
