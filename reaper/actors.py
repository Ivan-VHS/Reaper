"""Deterministic mailbox actors with integrity-checked, JSON-safe snapshots."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any


class ActorError(RuntimeError):
    """Base class for actor lifecycle and message errors."""


class ActorHibernatedError(ActorError):
    """Raised when messages are sent to or state is read from a hibernated actor."""


def _canonical_json(value: Any) -> bytes:
    try:
        text = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"actor state and messages must be JSON-compatible: {error}") from error
    return text.encode("utf-8")


def _clone_json(value: Any) -> Any:
    return json.loads(_canonical_json(value).decode("utf-8"))


class SovereignUnit:
    """Single-threaded actor with a bounded FIFO mailbox and durable state snapshot.

    Handlers should be deterministic and avoid external side effects: state changes
    are committed only after the handler returns a JSON-compatible next state.
    """

    SNAPSHOT_VERSION = 1

    def __init__(
        self,
        unit_id: str,
        state: Any,
        handler: Callable[[Any, Any], Any],
        *,
        max_mailbox: int = 10_000,
    ) -> None:
        if not isinstance(unit_id, str) or not unit_id.strip():
            raise ValueError("unit_id must be a non-empty string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if isinstance(max_mailbox, bool) or not isinstance(max_mailbox, int) or max_mailbox < 1:
            raise ValueError("max_mailbox must be a positive integer")
        self.unit_id = unit_id
        self.handler = handler
        self.max_mailbox = max_mailbox
        self._state = _clone_json(state)
        self._mailbox: list[Any] = []
        self._hibernated = False

    @property
    def state(self) -> Any:
        self._ensure_awake()
        return _clone_json(self._state)

    @property
    def mailbox_size(self) -> int:
        return len(self._mailbox)

    @property
    def hibernated(self) -> bool:
        return self._hibernated

    def send(self, message: Any) -> None:
        self._ensure_awake()
        if len(self._mailbox) >= self.max_mailbox:
            raise ActorError(f"mailbox limit ({self.max_mailbox}) exceeded")
        self._mailbox.append(_clone_json(message))

    def drain(self, *, max_messages: int | None = None) -> int:
        self._ensure_awake()
        if max_messages is not None and (
            isinstance(max_messages, bool) or not isinstance(max_messages, int) or max_messages < 1
        ):
            raise ValueError("max_messages must be a positive integer")
        processed = 0
        while self._mailbox and (max_messages is None or processed < max_messages):
            message = self._mailbox[0]
            working_state = _clone_json(self._state)
            working_message = _clone_json(message)
            next_state = self.handler(working_state, working_message)
            committed_state = _clone_json(next_state)
            self._state = committed_state
            del self._mailbox[0]
            processed += 1
        return processed

    def hibernate(self) -> bytes:
        self._ensure_awake()
        payload = {
            "version": self.SNAPSHOT_VERSION,
            "unit_id": self.unit_id,
            "state": self._state,
            "mailbox": self._mailbox,
        }
        digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
        snapshot = _canonical_json({"payload": payload, "sha256": digest})
        self._state = None
        self._mailbox = []
        self._hibernated = True
        return snapshot

    def wake(self, snapshot: bytes) -> None:
        if not self._hibernated:
            raise ActorError("actor must be hibernated before wake")
        if not isinstance(snapshot, bytes):
            raise TypeError("snapshot must be bytes")
        try:
            envelope = json.loads(snapshot.decode("utf-8"))
            if not isinstance(envelope, dict):
                raise TypeError("snapshot envelope must be an object")
            payload = envelope["payload"]
            supplied_digest = envelope["sha256"]
            if not isinstance(payload, dict):
                raise TypeError("snapshot payload must be an object")
        except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ActorError("snapshot is malformed") from error
        expected_digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
        if not isinstance(supplied_digest, str) or supplied_digest != expected_digest:
            raise ActorError("snapshot integrity check failed")
        if payload.get("version") != self.SNAPSHOT_VERSION:
            raise ActorError("unsupported snapshot version")
        if payload.get("unit_id") != self.unit_id:
            raise ActorError("snapshot belongs to a different actor")
        mailbox = payload.get("mailbox")
        if not isinstance(mailbox, list) or len(mailbox) > self.max_mailbox:
            raise ActorError("snapshot mailbox is invalid or exceeds configured limit")
        restored_state = _clone_json(payload.get("state"))
        restored_mailbox = _clone_json(mailbox)
        self._state = restored_state
        self._mailbox = restored_mailbox
        self._hibernated = False

    def _ensure_awake(self) -> None:
        if self._hibernated:
            raise ActorHibernatedError(f"actor '{self.unit_id}' is hibernated")
