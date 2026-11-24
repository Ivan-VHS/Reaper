"""Object-capability primitives for Reaper's trusted extension host.

Requests are parsed into immutable, refined values. Grants are opaque in-process
objects authenticated with HMAC-SHA-256, scoped to one resource subtree and a
finite action set, bounded by expiry, and revocable under a thread-safe authority.
This is an application-level authorization boundary, not an operating-system sandbox.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from contextlib import contextmanager
import unicodedata
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")
_REFINEMENT_PROOF = object()
_MAX_ACTIONS = 64
_MAX_PRINCIPAL = 128
_MAX_RESOURCE = 512
_MAX_ACTION_LENGTH = 80
_CLOCK_SKEW_NS = 5_000_000_000


class CapabilityError(ValueError):
    """Invalid capability request or authority configuration."""


class CapabilityDenied(PermissionError):
    """A capability is missing, invalid, expired, out of scope or revoked."""


@dataclass(frozen=True, slots=True, repr=False)
class TaintedValue(Generic[T]):
    """Value entering from a boundary which has not yet been refined."""

    value: T = field(repr=False)
    source: str = "untrusted boundary"

    def __repr__(self) -> str:
        return f"TaintedValue(source={self.source!r}, value=<redacted>)"


@dataclass(frozen=True, slots=True, init=False, repr=False)
class RefinedValue(Generic[R]):
    """Immutable value produced only through an explicit refinement parser."""

    value: R = field(repr=False)
    refinement: str

    def __init__(self, value: R, refinement: str, *, _proof: object | None = None) -> None:
        if _proof is not _REFINEMENT_PROOF:
            raise TypeError("RefinedValue must be created by refine_tainted()")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "refinement", refinement)

    def __repr__(self) -> str:
        return f"RefinedValue(refinement={self.refinement!r}, value=<redacted>)"


def refine_tainted(
    value: TaintedValue[T],
    parser: Callable[[T], R],
    *,
    refinement: str,
) -> RefinedValue[R]:
    """Parse untrusted input once and return an immutable refined value."""
    if not isinstance(value, TaintedValue):
        raise TypeError("refinement requires a TaintedValue")
    if not isinstance(refinement, str) or not refinement.strip() or len(refinement) > 100:
        raise CapabilityError("refinement label must be non-empty bounded text")
    try:
        parsed = parser(value.value)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CapabilityError(f"{refinement} refinement failed") from exc
    return RefinedValue(parsed, refinement.strip(), _proof=_REFINEMENT_PROOF)


def _clean_text(value: Any, *, name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise CapabilityError(f"{name} must be text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized or len(normalized) > maximum:
        raise CapabilityError(f"{name} must contain 1..{maximum} characters")
    if any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in normalized):
        raise CapabilityError(f"{name} contains a control or hidden Unicode character")
    return normalized


def _parse_principal(value: Any) -> str:
    text = _clean_text(value, name="principal", maximum=_MAX_PRINCIPAL)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}", text):
        raise CapabilityError("principal contains unsupported characters")
    return text.casefold()


def _parse_resource(value: Any) -> str:
    text = _clean_text(value, name="resource", maximum=_MAX_RESOURCE)
    if "\\" in text or text.startswith("/") or text.endswith("/") or "//" in text:
        raise CapabilityError("resource must be a canonical relative scope")
    components = text.split("/")
    if any(part in {"", ".", ".."} for part in components):
        raise CapabilityError("resource cannot contain empty, dot or parent path segments")
    if any(not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", part) for part in components):
        raise CapabilityError("resource contains unsupported path characters")
    return "/".join(part.casefold() for part in components)


def _parse_action(value: Any) -> str:
    text = _clean_text(value, name="action", maximum=_MAX_ACTION_LENGTH)
    normalized = re.sub(r"[\s_]+", "-", text.casefold())
    normalized = re.sub(r"-{2,}", "-", normalized)
    if not re.fullmatch(r"[a-z0-9][a-z0-9.:-]{0,79}", normalized):
        raise CapabilityError("action must be a specific name; wildcards are forbidden")
    return normalized


@dataclass(frozen=True, slots=True, init=False, repr=False)
class CapabilityRequest:
    """Parsed request; raw mappings never reach the authority."""

    principal: str
    resource: str
    actions: tuple[str, ...]
    ttl_seconds: int

    def __init__(
        self,
        principal: str,
        resource: str,
        actions: tuple[str, ...],
        ttl_seconds: int,
        *,
        _proof: object | None = None,
    ) -> None:
        if _proof is not _REFINEMENT_PROOF:
            raise TypeError("CapabilityRequest must be created by parse()")
        object.__setattr__(self, "principal", principal)
        object.__setattr__(self, "resource", resource)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "ttl_seconds", ttl_seconds)

    @classmethod
    def parse(
        cls,
        raw: Mapping[str, Any],
        *,
        max_ttl_seconds: int = 3_600,
    ) -> "CapabilityRequest":
        if not isinstance(raw, Mapping):
            raise CapabilityError("capability request must be a mapping")
        allowed = {"principal", "resource", "actions", "ttl_seconds"}
        unknown = set(raw) - allowed
        if unknown:
            raise CapabilityError(f"unsupported capability request field(s): {', '.join(sorted(map(str, unknown)))}")
        required = {"principal", "resource", "actions"}
        missing = required - set(raw)
        if missing:
            raise CapabilityError(f"missing capability request field(s): {', '.join(sorted(missing))}")

        principal = refine_tainted(
            TaintedValue(raw["principal"], "capability principal"),
            _parse_principal,
            refinement="principal",
        ).value
        resource = refine_tainted(
            TaintedValue(raw["resource"], "capability resource"),
            _parse_resource,
            refinement="resource",
        ).value
        raw_actions = raw["actions"]
        if isinstance(raw_actions, (str, bytes)) or not isinstance(raw_actions, (list, tuple, set, frozenset)):
            raise CapabilityError("actions must be a list or set of specific action names")
        if not 1 <= len(raw_actions) <= _MAX_ACTIONS:
            raise CapabilityError(f"actions must contain 1..{_MAX_ACTIONS} entries")
        actions = tuple(sorted({
            refine_tainted(
                TaintedValue(item, "capability action"),
                _parse_action,
                refinement="action",
            ).value
            for item in raw_actions
        }))
        ttl = raw.get("ttl_seconds", 900)
        if isinstance(ttl, bool) or not isinstance(ttl, int):
            raise CapabilityError("ttl_seconds must be an integer")
        if not isinstance(max_ttl_seconds, int) or isinstance(max_ttl_seconds, bool) or max_ttl_seconds < 1:
            raise CapabilityError("authority maximum TTL is invalid")
        if not 1 <= ttl <= max_ttl_seconds:
            raise CapabilityError(f"ttl_seconds must be within 1..{max_ttl_seconds}")
        return cls(principal, resource, actions, ttl, _proof=_REFINEMENT_PROOF)

    def __repr__(self) -> str:
        return (
            f"CapabilityRequest(principal={self.principal!r}, resource={self.resource!r}, "
            f"actions={self.actions!r}, ttl_seconds={self.ttl_seconds})"
        )


@dataclass(frozen=True, slots=True, repr=False)
class CapabilityToken:
    """Opaque signed grant. Its signature is deliberately omitted from repr."""

    token_id: str
    authority_id: str
    principal: str
    resource: str
    actions: tuple[str, ...]
    issued_at_ns: int
    expires_at_ns: int
    _signature: bytes = field(repr=False)

    def __repr__(self) -> str:
        return (
            f"CapabilityToken(id={self.token_id!r}, principal={self.principal!r}, "
            f"resource={self.resource!r}, actions={self.actions!r}, "
            f"expires_at_ns={self.expires_at_ns}, signature=<redacted>)"
        )

    def __reduce_ex__(self, protocol: int) -> Any:
        raise TypeError("capability tokens are intentionally non-serializable")


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    principal: str
    resource: str
    action: str
    token_id: str
    expires_at_ns: int


class CapabilityAuthority:
    """Thread-safe HMAC authority with expiry, scope checks and revocation."""

    __slots__ = (
        "_key", "_authority_id", "_clock_ns", "_max_ttl_seconds",
        "_max_active_tokens", "_issued", "_lock", "_closed",
    )

    def __init__(
        self,
        secret: bytes | None = None,
        *,
        max_ttl_seconds: int = 3_600,
        max_active_tokens: int = 10_000,
        clock_ns: Callable[[], int] | None = None,
    ) -> None:
        if secret is not None and (not isinstance(secret, bytes) or len(secret) < 32):
            raise CapabilityError("capability authority secret must contain at least 32 bytes")
        if isinstance(max_ttl_seconds, bool) or not isinstance(max_ttl_seconds, int) or not 1 <= max_ttl_seconds <= 86_400:
            raise CapabilityError("max_ttl_seconds must be within 1..86400")
        if isinstance(max_active_tokens, bool) or not isinstance(max_active_tokens, int) or not 1 <= max_active_tokens <= 100_000:
            raise CapabilityError("max_active_tokens must be within 1..100000")
        self._key = secret if secret is not None else secrets.token_bytes(32)
        self._authority_id = secrets.token_urlsafe(18)
        self._clock_ns = clock_ns or time.time_ns
        self._max_ttl_seconds = max_ttl_seconds
        self._max_active_tokens = max_active_tokens
        self._issued: dict[str, tuple[str, int]] = {}
        self._lock = threading.RLock()
        self._closed = False

    @property
    def max_ttl_seconds(self) -> int:
        return self._max_ttl_seconds

    def _ensure_open(self) -> None:
        if self._closed:
            raise CapabilityDenied("capability authority is closed")

    def _purge_expired_locked(self, now: int) -> None:
        expired = [token_id for token_id, (_, expires) in self._issued.items() if now >= expires]
        for token_id in expired:
            self._issued.pop(token_id, None)

    @staticmethod
    def _canonical_payload(
        authority_id: str,
        token_id: str,
        principal: str,
        resource: str,
        actions: tuple[str, ...],
        issued_at_ns: int,
        expires_at_ns: int,
    ) -> bytes:
        payload = {
            "v": 1,
            "authority": authority_id,
            "id": token_id,
            "principal": principal,
            "resource": resource,
            "actions": list(actions),
            "issued_at_ns": issued_at_ns,
            "expires_at_ns": expires_at_ns,
        }
        return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")

    def _signature(self, token: CapabilityToken) -> bytes:
        payload = self._canonical_payload(
            token.authority_id, token.token_id, token.principal, token.resource,
            token.actions, token.issued_at_ns, token.expires_at_ns,
        )
        return hmac.new(self._key, payload, hashlib.sha256).digest()

    def issue(self, request: CapabilityRequest) -> CapabilityToken:
        if not isinstance(request, CapabilityRequest):
            raise CapabilityError("issue() requires a parsed CapabilityRequest")
        if request.ttl_seconds > self._max_ttl_seconds:
            raise CapabilityError("request TTL exceeds this authority's configured maximum")
        with self._lock:
            self._ensure_open()
            now = self._clock_ns()
            self._purge_expired_locked(now)
            if len(self._issued) >= self._max_active_tokens:
                raise CapabilityError("authority active-token limit reached")
            token_id = secrets.token_urlsafe(24)
            unsigned = CapabilityToken(
                token_id=token_id,
                authority_id=self._authority_id,
                principal=request.principal,
                resource=request.resource,
                actions=request.actions,
                issued_at_ns=now,
                expires_at_ns=now + request.ttl_seconds * 1_000_000_000,
                _signature=b"",
            )
            token = CapabilityToken(
                token_id=unsigned.token_id,
                authority_id=unsigned.authority_id,
                principal=unsigned.principal,
                resource=unsigned.resource,
                actions=unsigned.actions,
                issued_at_ns=unsigned.issued_at_ns,
                expires_at_ns=unsigned.expires_at_ns,
                _signature=self._signature(unsigned),
            )
            self._issued[token.token_id] = (token.principal, token.expires_at_ns)
            return token

    @staticmethod
    def _resource_contains(granted: str, requested: str) -> bool:
        return requested == granted or requested.startswith(granted + "/")

    def verify(
        self,
        token: CapabilityToken,
        *,
        principal: str,
        resource: str,
        action: str,
    ) -> AuthorizationDecision:
        if not isinstance(token, CapabilityToken):
            raise CapabilityDenied("no valid capability token supplied")
        try:
            expected_principal = _parse_principal(principal)
            requested_resource = _parse_resource(resource)
            requested_action = _parse_action(action)
        except CapabilityError as exc:
            raise CapabilityDenied("authorization request did not pass refinement") from exc

        with self._lock:
            self._ensure_open()
            now = self._clock_ns()
            self._purge_expired_locked(now)
            issued = self._issued.get(token.token_id)
            if token.authority_id != self._authority_id or issued is None:
                raise CapabilityDenied("capability was not issued by this authority or has been revoked")
            if issued != (token.principal, token.expires_at_ns):
                raise CapabilityDenied("capability registry state does not match the grant")
            if now < token.issued_at_ns - _CLOCK_SKEW_NS:
                raise CapabilityDenied("capability issue time is in the future")
            if now >= token.expires_at_ns or token.expires_at_ns <= token.issued_at_ns:
                raise CapabilityDenied("capability has expired or has an invalid lifetime")
            if token.expires_at_ns - token.issued_at_ns > self._max_ttl_seconds * 1_000_000_000:
                raise CapabilityDenied("capability lifetime exceeds authority policy")
            if not isinstance(token._signature, bytes) or len(token._signature) != hashlib.sha256().digest_size:
                raise CapabilityDenied("capability signature has an invalid representation")
            if not hmac.compare_digest(token._signature, self._signature(token)):
                raise CapabilityDenied("capability signature is invalid")
            if token.principal != expected_principal:
                raise CapabilityDenied("capability principal mismatch")
            if not self._resource_contains(token.resource, requested_resource):
                raise CapabilityDenied("requested resource is outside the granted scope")
            if requested_action not in token.actions:
                raise CapabilityDenied("requested action is not granted")
            return AuthorizationDecision(
                principal=expected_principal,
                resource=requested_resource,
                action=requested_action,
                token_id=token.token_id,
                expires_at_ns=token.expires_at_ns,
            )

    @contextmanager
    def authorized(
        self,
        token: CapabilityToken,
        *,
        principal: str,
        resource: str,
        action: str,
    ) -> Iterator[AuthorizationDecision]:
        """Hold the authority lock across a protected operation.

        Revocation waits for an in-flight authorized operation to finish. Once
        revoke() returns, that grant cannot start or continue another operation.
        """
        self._lock.acquire()
        try:
            decision = self.verify(
                token,
                principal=principal,
                resource=resource,
                action=action,
            )
            yield decision
        finally:
            self._lock.release()

    def revoke(self, token: CapabilityToken) -> bool:
        if not isinstance(token, CapabilityToken) or token.authority_id != self._authority_id:
            return False
        with self._lock:
            self._ensure_open()
            issued = self._issued.get(token.token_id)
            if issued is None or issued != (token.principal, token.expires_at_ns):
                return False
            if not isinstance(token._signature, bytes) or len(token._signature) != hashlib.sha256().digest_size:
                return False
            if not hmac.compare_digest(token._signature, self._signature(token)):
                return False
            self._issued.pop(token.token_id, None)
            return True

    def revoke_principal(self, principal: str) -> int:
        try:
            normalized = _parse_principal(principal)
        except CapabilityError as exc:
            raise CapabilityError("principal could not be refined for revocation") from exc
        with self._lock:
            self._ensure_open()
            targets = [token_id for token_id, (owner, _) in self._issued.items() if owner == normalized]
            for token_id in targets:
                self._issued.pop(token_id, None)
            return len(targets)

    def revoke_all(self) -> int:
        with self._lock:
            self._ensure_open()
            count = len(self._issued)
            self._issued.clear()
            return count

    @property
    def active_count(self) -> int:
        with self._lock:
            if self._closed:
                return 0
            self._purge_expired_locked(self._clock_ns())
            return len(self._issued)

    def close(self) -> None:
        with self._lock:
            self._issued.clear()
            self._key = bytes(len(self._key))
            self._closed = True

    def __enter__(self) -> "CapabilityAuthority":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


__all__ = [
    "AuthorizationDecision",
    "CapabilityAuthority",
    "CapabilityDenied",
    "CapabilityError",
    "CapabilityRequest",
    "CapabilityToken",
    "RefinedValue",
    "TaintedValue",
    "refine_tainted",
]
