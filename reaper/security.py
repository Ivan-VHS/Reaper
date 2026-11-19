"""Revocable capabilities for explicit host effects."""
from __future__ import annotations

import contextvars
import hashlib
import hmac
import secrets
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from typing import Iterator


class CapabilityError(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityToken:
    capability: str
    subject: str
    token_id: str
    signature: str


class CapabilityAuthority:
    """Issues process-local HMAC-authenticated capability tokens."""

    def __init__(self, secret: bytes | None = None) -> None:
        self._secret = secret or secrets.token_bytes(32)
        if len(self._secret) < 16:
            raise ValueError("capability secret must contain at least 16 bytes")
        self._issued: dict[str, tuple[str, str, str]] = {}
        self._revoked: set[str] = set()
        self._lock = RLock()

    def _signature(self, capability: str, subject: str, token_id: str) -> str:
        message = f"{capability}\0{subject}\0{token_id}".encode("utf-8")
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    def issue(self, capability: str, subject: str = "*") -> CapabilityToken:
        if not capability or not subject:
            raise ValueError("capability and subject must be non-empty")
        token_id = secrets.token_hex(16)
        signature = self._signature(capability, subject, token_id)
        with self._lock:
            self._issued[token_id] = (capability, subject, signature)
        return CapabilityToken(capability, subject, token_id, signature)

    def revoke(self, token: CapabilityToken) -> None:
        with self._lock:
            self._revoked.add(token.token_id)

    def verify(self, token: CapabilityToken, capability: str, subject: str = "*") -> bool:
        if not isinstance(token, CapabilityToken):
            return False
        with self._lock:
            issued = self._issued.get(token.token_id)
            if token.token_id in self._revoked or issued is None:
                return False
            expected = self._signature(token.capability, token.subject, token.token_id)
            return (
                issued == (token.capability, token.subject, token.signature)
                and hmac.compare_digest(token.signature, expected)
                and token.capability == capability
                and (token.subject == "*" or token.subject == subject)
            )


_ACTIVE_CAPABILITIES: contextvars.ContextVar[tuple[tuple[CapabilityAuthority, CapabilityToken], ...]] = (
    contextvars.ContextVar("reaper_active_capabilities", default=())
)


@contextmanager
def capability_scope(
    authority: CapabilityAuthority, *tokens: CapabilityToken
) -> Iterator[None]:
    for token in tokens:
        if not authority.verify(token, token.capability, token.subject):
            raise CapabilityError("cannot activate an invalid or revoked capability")
    current = _ACTIVE_CAPABILITIES.get()
    marker = _ACTIVE_CAPABILITIES.set(current + tuple((authority, token) for token in tokens))
    try:
        yield
    finally:
        _ACTIVE_CAPABILITIES.reset(marker)


def require_capability(capability: str, subject: str = "*") -> CapabilityToken:
    for authority, token in reversed(_ACTIVE_CAPABILITIES.get()):
        if authority.verify(token, capability, subject):
            return token
    raise CapabilityError(f"missing capability '{capability}' for subject '{subject}'")
