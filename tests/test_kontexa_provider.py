from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

from kontexa.provider import OpenAICompatibleProvider, ProviderError


class ProviderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class StubHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                payload = {"choices": [{"message": {"content": "Перевод готов."}}]}
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_openai_compatible_contract(self):
        provider = OpenAICompatibleProvider(base_url=self.base_url, model="stub-model")
        text = provider.translate([{"role": "user", "content": "hello"}])
        self.assertEqual(text, "Перевод готов.")
        self.assertTrue(provider.endpoint.endswith("/v1/chat/completions"))

    def test_plain_http_is_rejected_for_non_loopback(self):
        with self.assertRaises(ProviderError):
            OpenAICompatibleProvider(base_url="http://example.com/v1", model="m")

    def test_https_remote_provider_is_accepted(self):
        provider = OpenAICompatibleProvider(base_url="https://api.example.com/v1", model="m")
        self.assertEqual(provider.endpoint, "https://api.example.com/v1/chat/completions")


if __name__ == "__main__":
    unittest.main()
