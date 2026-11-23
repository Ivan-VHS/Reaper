from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from reaper.backend import BackendConfig, BackendServer
from reaper.backend_store import BackendStore, BackendStoreError
from reaper.backend_service import BackendService


async def send_request(
    server: BackendServer,
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    token: str | None = None,
    idempotency_key: str | None = None,
) -> tuple[int, dict[str, str], dict]:
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Host": "127.0.0.1",
        "Connection": "close",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key

    lines = [f"{method} {path} HTTP/1.1"]
    lines.extend(f"{name}: {value}" for name, value in headers.items())
    request = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body

    reader, writer = await asyncio.open_connection(*server.address)
    writer.write(request)
    await writer.drain()
    raw_headers = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=3)
    header_lines = raw_headers.decode("latin-1").split("\r\n")
    status = int(header_lines[0].split(" ")[1])
    response_headers = {}
    for line in header_lines[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            response_headers[name.lower()] = value.strip()
    response_body = await asyncio.wait_for(
        reader.readexactly(int(response_headers["content-length"])),
        timeout=3,
    )
    writer.close()
    await writer.wait_closed()
    return status, response_headers, json.loads(response_body.decode("utf-8"))


class BackendServiceTests(unittest.TestCase):
    def test_json_result_serializer_handles_nested_values_and_non_finite_numbers(self) -> None:
        result = BackendService._json_safe({"items": [1, 2], "invalid": float("nan")})
        self.assertEqual(result["items"], [1, 2])
        self.assertIsNone(result["invalid"])

    def test_json_result_serializer_enforces_a_total_item_budget(self) -> None:
        result = BackendService._json_safe([[0] * 10_000 for _ in range(3)])
        self.assertIsInstance(result, list)
        self.assertEqual(result[2], {"type": "item_limit"})


class BackendStoreTests(unittest.TestCase):
    def test_idempotency_replay_and_payload_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backend.sqlite3"
            store = BackendStore(path)
            fingerprint = "a" * 64
            claim = store.reserve("check", "request-1", fingerprint)
            self.assertEqual(claim.state, "claimed")
            store.complete(
                "check",
                "request-1",
                fingerprint,
                claim.owner or "",
                200,
                {"ok": True, "diagnostics": []},
            )

            replay = store.reserve("check", "request-1", fingerprint)
            conflict = store.reserve("check", "request-1", "b" * 64)
            store.close()

            self.assertEqual(replay.state, "cached")
            self.assertEqual(replay.status_code, 200)
            self.assertEqual(replay.response, {"ok": True, "diagnostics": []})
            self.assertEqual(conflict.state, "conflict")

    def test_pending_claim_is_not_granted_twice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = BackendStore(Path(directory) / "backend.sqlite3")
            first = store.reserve("run", "same-key", "c" * 64)
            second = store.reserve("run", "same-key", "c" * 64)
            store.abandon("run", "same-key", first.owner or "")
            third = store.reserve("run", "same-key", "c" * 64)
            store.close()

            self.assertEqual(first.state, "claimed")
            self.assertEqual(second.state, "pending")
            self.assertEqual(third.state, "claimed")

    def test_backup_is_atomically_published_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = BackendStore(root / "backend.sqlite3")
            claim = store.reserve("check", "backup-key", "d" * 64)
            store.complete("check", "backup-key", "d" * 64, claim.owner or "", 200, {"ok": True})
            backup = store.backup(root / "backup.sqlite3")
            self.assertTrue(backup.is_file())
            store.close()

            restored = BackendStore(backup)
            self.assertEqual(restored.integrity_check(), "ok")
            self.assertEqual(
                restored.reserve("check", "backup-key", "d" * 64).state,
                "cached",
            )
            restored.close()


class BackendServerTests(unittest.TestCase):
    def test_backend_refuses_non_loopback_binding(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            BackendConfig(host="0.0.0.0")

    def test_http_api_auth_idempotency_metrics_and_restricted_run(self) -> None:
        async def exercise(root: Path) -> None:
            token = "t" * 48
            config = BackendConfig(
                host="127.0.0.1",
                port=0,
                database=root / "backend.sqlite3",
                token=token,
                allow_execution=True,
                max_workers=2,
                queue_depth=2,
                max_body_bytes=8192,
                max_source_bytes=4096,
            )
            server = BackendServer(config)
            await server.start()
            try:
                status, _headers, body = await send_request(server, "GET", "/healthz")
                self.assertEqual(status, 200)
                self.assertEqual(body["status"], "alive")

                status, _headers, _body = await send_request(
                    server,
                    "GET",
                    "/v1/info",
                )
                self.assertEqual(status, 401)

                source = "make answer := 42\nsay(answer)\n"
                status, headers, result = await send_request(
                    server,
                    "POST",
                    "/v1/check",
                    payload={"source": source},
                    token=token,
                    idempotency_key="check-1",
                )
                self.assertEqual(status, 200)
                self.assertTrue(result["ok"])
                self.assertIn("request_id", result)

                replay_status, replay_headers, replay = await send_request(
                    server,
                    "POST",
                    "/v1/check",
                    payload={"source": source},
                    token=token,
                    idempotency_key="check-1",
                )
                self.assertEqual(replay_status, 200)
                self.assertEqual(replay_headers["idempotency-replayed"], "true")
                self.assertEqual(replay["diagnostics"], result["diagnostics"])

                conflict_status, _headers, conflict = await send_request(
                    server,
                    "POST",
                    "/v1/check",
                    payload={"source": "make other := 7\n"},
                    token=token,
                    idempotency_key="check-1",
                )
                self.assertEqual(conflict_status, 409)
                self.assertEqual(conflict["error"]["code"], "idempotency_conflict")

                run_status, _headers, run_result = await send_request(
                    server,
                    "POST",
                    "/v1/run",
                    payload={"source": source},
                    token=token,
                    idempotency_key="run-1",
                )
                self.assertEqual(run_status, 200)
                self.assertEqual(run_result["output"], ["42"])
                self.assertTrue(run_result["ok"])

                replay_run_status, replay_run_headers, replay_run = await send_request(
                    server,
                    "POST",
                    "/v1/run",
                    payload={"source": source},
                    token=token,
                    idempotency_key="run-1",
                )
                self.assertEqual(replay_run_status, 200)
                self.assertEqual(replay_run_headers["idempotency-replayed"], "true")
                self.assertEqual(replay_run["output"], run_result["output"])

                import_status, _headers, import_result = await send_request(
                    server,
                    "POST",
                    "/v1/run",
                    payload={"source": 'import "other.rpr"\n'},
                    token=token,
                    idempotency_key="run-import",
                )
                self.assertEqual(import_status, 422)
                self.assertEqual(import_result["error"]["code"], "restricted_effect")

                blocked_json_path = root / "backend-must-not-create.json"
                for index, restricted_source in enumerate((
                    f'write_json("{blocked_json_path.as_posix()}", [1, 2, 3])\\n',
                    f'read_json("{blocked_json_path.as_posix()}")\\n',
                    'oplage_compare(1, 2, "untrusted-native-library.so")\\n',
                    'pytyliki_embedded_profiles("untrusted-native-library.so")\\n',
                )):
                    restricted_status, _headers, _restricted_result = await send_request(
                        server,
                        "POST",
                        "/v1/run",
                        payload={"source": restricted_source},
                        token=token,
                        idempotency_key=f"restricted-{index}",
                    )
                    self.assertEqual(restricted_status, 422)

                self.assertFalse(blocked_json_path.exists())

                metrics_status, _headers, metrics = await send_request(
                    server,
                    "GET",
                    "/v1/metrics",
                    token=token,
                )
                self.assertEqual(metrics_status, 200)
                self.assertGreaterEqual(metrics["requests"]["total"], 7)
                self.assertIn("p95", metrics["latency_ms"])
                self.assertIn("active", metrics["workers"])
                self.assertIn("cpu_seconds", metrics["process"])
                self.assertIn("max_rss_bytes", metrics["process"])
                self.assertIn("sqlite_bytes", metrics["storage"])
                self.assertIn("received", metrics["network_bytes"])

                ready_status, _headers, ready = await send_request(server, "GET", "/readyz")
                self.assertEqual(ready_status, 200)
                self.assertEqual(ready["status"], "ready")
            finally:
                await server.close()

        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(exercise(Path(directory)))

    def test_run_is_disabled_by_default(self) -> None:
        async def exercise(root: Path) -> None:
            token = "u" * 48
            server = BackendServer(
                BackendConfig(
                    port=0,
                    database=root / "backend.sqlite3",
                    token=token,
                    max_body_bytes=8192,
                    max_source_bytes=4096,
                )
            )
            await server.start()
            try:
                status, _headers, body = await send_request(
                    server,
                    "POST",
                    "/v1/run",
                    payload={"source": "say(1)\n"},
                    token=token,
                    idempotency_key="disabled-run",
                )
                self.assertEqual(status, 403)
                self.assertEqual(body["error"]["code"], "execution_disabled")
            finally:
                await server.close()

        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(exercise(Path(directory)))


if __name__ == "__main__":
    unittest.main()
