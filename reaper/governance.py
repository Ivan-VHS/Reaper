"""Host-issued, HMAC-authenticated consent grants for sensitive runtime operations.

This is an application-level authorization primitive, not a healthcare compliance
engine or a replacement for identity proofing, legal review, or a secure key store.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Mapping, Sequence
from typing import Any

from .audit import AuditLog, verify_audit_log

CONSENT_SCHEMA = "reaper.consent.v1"
MAX_CONSENT_TTL_SECONDS = 365 * 24 * 60 * 60
_REQUIRED_FIELDS = {
    "schema", "subject", "purpose", "scopes", "issued_at",
    "expires_at", "nonce", "signature",
}


class ConsentError(ValueError):
    """Invalid consent grant, signing configuration, or revocation log."""


def _text(value: Any, field: str, limit: int = 256) -> str:
    if not isinstance(value, str):
        raise ConsentError(f"{field} must be text")
    value = value.strip()
    if not value or len(value) > limit or "\x00" in value:
        raise ConsentError(f"{field} is empty or outside the permitted length")
    return value


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


class ConsentAuthority:
    """Issue and verify scoped, expiring consent tokens using a host-held key.

    The signing key must be supplied by the embedding application. It is never
    generated implicitly, persisted, exported, or exposed to Reaper programs.
    Revocations are kept in memory and, when an AuditLog is supplied, restored
    from its verified hash-chained journal at startup.
    """

    def __init__(self, secret: bytes, audit_log: AuditLog | None = None) -> None:
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ConsentError("consent signing key must contain at least 32 bytes")
        if audit_log is not None and not isinstance(audit_log, AuditLog):
            raise ConsentError("audit_log must be an AuditLog instance")
        self._secret = bytes(secret)
        self._audit = audit_log
        self._revoked: set[str] = set()
        if self._audit is not None:
            self._load_revocations()

    @staticmethod
    def _scope_list(scopes: Sequence[str]) -> list[str]:
        if isinstance(scopes, (str, bytes)) or not isinstance(scopes, (list, tuple, set, frozenset)):
            raise ConsentError("scopes must be a sequence of scope names")
        normalized = sorted({_text(scope, "scope", 128) for scope in scopes})
        if not normalized or len(normalized) > 64:
            raise ConsentError("consent must grant between 1 and 64 scopes")
        return normalized

    def _signature(self, payload: Mapping[str, Any]) -> str:
        return hmac.new(self._secret, _canonical(payload), hashlib.sha256).hexdigest()

    def issue(
        self, subject: str, purpose: str, scopes: Sequence[str],
        ttl_seconds: int, *, now: int | None = None,
    ) -> dict[str, Any]:
        """Create a host-side grant with a finite TTL (maximum 365 days)."""
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
            raise ConsentError("ttl_seconds must be a whole number")
        if not 1 <= ttl_seconds <= MAX_CONSENT_TTL_SECONDS:
            raise ConsentError("consent TTL must be between 1 second and 365 days")
        issued = self._now(now)
        payload: dict[str, Any] = {
            "schema": CONSENT_SCHEMA,
            "subject": _text(subject, "subject"),
            "purpose": _text(purpose, "purpose", 128),
            "scopes": self._scope_list(scopes),
            "issued_at": issued,
            "expires_at": issued + ttl_seconds,
            "nonce": secrets.token_urlsafe(24),
        }
        token = dict(payload)
        token["signature"] = self._signature(payload)
        if self._audit is not None:
            self._audit.record(
                "consent_issued",
                nonce_sha256=hashlib.sha256(token["nonce"].encode("utf-8")).hexdigest(),
                expires_at=token["expires_at"],
            )
        return token

    @staticmethod
    def _now(value: int | None) -> int:
        import time
        result = int(time.time()) if value is None else value
        if isinstance(result, bool) or not isinstance(result, int) or result < 0:
            raise ConsentError("current time must be a non-negative epoch integer")
        return result

    def _verified_payload(self, token: Any) -> dict[str, Any] | None:
        if not isinstance(token, Mapping) or set(token) != _REQUIRED_FIELDS:
            return None
        payload = {key: token[key] for key in _REQUIRED_FIELDS if key != "signature"}
        if payload.get("schema") != CONSENT_SCHEMA:
            return None
        try:
            _text(payload.get("subject"), "subject")
            _text(payload.get("purpose"), "purpose", 128)
            _text(payload.get("nonce"), "nonce", 128)
            scopes = self._scope_list(payload.get("scopes"))
        except ConsentError:
            return None
        if scopes != payload.get("scopes"):
            return None
        issued, expires = payload.get("issued_at"), payload.get("expires_at")
        if (isinstance(issued, bool) or not isinstance(issued, int)
                or isinstance(expires, bool) or not isinstance(expires, int)
                or issued < 0 or expires <= issued
                or expires - issued > MAX_CONSENT_TTL_SECONDS):
            return None
        signature = token.get("signature")
        if not isinstance(signature, str) or len(signature) != 64:
            return None
        try:
            expected = self._signature(payload)
        except (TypeError, ValueError):
            return None
        if not hmac.compare_digest(signature, expected):
            return None
        return payload

    def verify(
        self, token: Any, *, subject: str, purpose: str, scope: str,
        now: int | None = None,
    ) -> bool:
        """Return False unless signature, identity, purpose, scope, TTL and revocation pass."""
        try:
            current = self._now(now)
            expected_subject = _text(subject, "subject")
            expected_purpose = _text(purpose, "purpose", 128)
            expected_scope = _text(scope, "scope", 128)
        except ConsentError:
            return False
        payload = self._verified_payload(token)
        if payload is None:
            return False
        nonce_hash = hashlib.sha256(payload["nonce"].encode("utf-8")).hexdigest()
        return (
            payload["subject"] == expected_subject
            and payload["purpose"] == expected_purpose
            and expected_scope in payload["scopes"]
            and payload["issued_at"] <= current < payload["expires_at"]
            and nonce_hash not in self._revoked
        )

    def revoke(self, token: Any) -> bool:
        """Revoke a correctly signed token; repeat calls are idempotent."""
        payload = self._verified_payload(token)
        if payload is None:
            return False
        nonce_hash = hashlib.sha256(payload["nonce"].encode("utf-8")).hexdigest()
        if nonce_hash in self._revoked:
            return True
        if self._audit is not None:
            self._audit.record("consent_revoked", nonce_sha256=nonce_hash)
        self._revoked.add(nonce_hash)
        return True

    def _load_revocations(self) -> None:
        assert self._audit is not None
        path = self._audit.path
        summary = verify_audit_log(path)
        if summary.records == 0:
            return
        try:
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    record = json.loads(line)
                    if record.get("event") == "consent_revoked":
                        digest = record.get("details", {}).get("nonce_sha256")
                        if isinstance(digest, str) and len(digest) == 64:
                            self._revoked.add(digest)
        except (OSError, ValueError, TypeError) as error:
            raise ConsentError(f"cannot restore revocation state: {error}") from error
