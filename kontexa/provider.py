"""OpenAI-compatible provider adapter and local translation cache."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
import threading
import urllib.error
import urllib.request
from urllib.parse import urlparse
from typing import Any

from .engine import KontexaError


class ProviderError(RuntimeError):
    """Provider network, configuration or response error."""


class OpenAICompatibleProvider:
    """Small stdlib-only adapter for hosted and local OpenAI-compatible APIs."""

    def __init__(self, *, base_url: str, model: str, api_key: str = "", timeout: int = 150, temperature: float = 0.15):
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.api_key = api_key
        self.timeout = max(15, min(int(timeout), 300))
        self.temperature = max(0.0, min(float(temperature), 1.0))
        parsed = urlparse(self.base_url)
        loopback_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and (parsed.hostname or "").casefold() in loopback_hosts):
            raise ProviderError("Provider URL must use HTTPS or a loopback HTTP address.")
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ProviderError("Provider URL must contain a host/path only; credentials, query strings and fragments are not accepted.")
        if not self.model:
            raise ProviderError("Provider model is required.")

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return self.base_url + "/chat/completions"
        return self.base_url + "/v1/chat/completions"

    def translate(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise ProviderError("Provider response exceeded the 8 MiB safety limit.")
        except urllib.error.HTTPError as error:
            detail = error.read(2048).decode("utf-8", errors="replace")
            raise ProviderError(f"Provider returned HTTP {error.code}: {detail[:500]}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise ProviderError(f"Could not reach translation provider: {error}") from error
        try:
            document = json.loads(raw.decode("utf-8"))
            content = document["choices"][0]["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise ProviderError("Provider response does not match the OpenAI-compatible chat-completions shape.") from error
        if isinstance(content, list):
            # Some providers return text as typed content blocks.
            content = "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Provider returned no text content.")
        return content


class TranslationCache:
    """SQLite cache keyed by source, context neighbours and translation settings."""

    MAX_ENTRIES = 10_000
    MAX_TRANSLATED_CHARS = 64_000_000
    PRUNE_BATCH = 1_000

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.RLock()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS translations (cache_key TEXT PRIMARY KEY, translated TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        self.connection.commit()
        try:
            for suffix in ("-wal", "-shm"):
                sidecar = Path(str(self.path) + suffix)
                if sidecar.exists():
                    os.chmod(sidecar, 0o600)
        except OSError:
            pass

    def get(self, key: str) -> str | None:
        with self._lock:
            row = self.connection.execute("SELECT translated FROM translations WHERE cache_key = ?", (key,)).fetchone()
            return str(row[0]) if row else None

    def set(self, key: str, translated: str) -> None:
        with self._lock:
            self.connection.execute(
                "INSERT INTO translations(cache_key, translated) VALUES(?, ?) "
                "ON CONFLICT(cache_key) DO UPDATE SET translated=excluded.translated, created_at=CURRENT_TIMESTAMP",
                (key, translated),
            )
            self.connection.commit()
            count, total_chars = self.connection.execute(
                "SELECT COUNT(*), COALESCE(SUM(length(translated)), 0) FROM translations"
            ).fetchone()
            if count > self.MAX_ENTRIES or total_chars > self.MAX_TRANSLATED_CHARS:
                self.connection.execute(
                    "DELETE FROM translations WHERE cache_key IN ("
                    "SELECT cache_key FROM translations ORDER BY created_at ASC, rowid ASC LIMIT ?)"
                    , (self.PRUNE_BATCH,)
                )
                self.connection.commit()

    def clear(self) -> None:
        with self._lock:
            self.connection.execute("DELETE FROM translations")
            self.connection.commit()

    def count(self) -> int:
        with self._lock:
            return int(self.connection.execute("SELECT COUNT(*) FROM translations").fetchone()[0])

    def close(self) -> None:
        with self._lock:
            self.connection.close()
