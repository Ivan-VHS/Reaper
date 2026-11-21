"""ТЕЗИС — provenance-aware assertion ledger for Reaper / МОСТ.

The ledger stores claims, evidence links, review states and immutable revisions.
It does not decide political, historical, legal or factual truth automatically.
Opaque source and actor references are deliberate: personal identity is not part
of the interchange contract.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any

THESIS_SCHEMA = "reaper.thesis-ledger.v1"
MAX_CLAIMS = 10_000
MAX_EVIDENCE = 50_000
MAX_REVISIONS = 50_000
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RELATIONS = {"supports", "contradicts", "contextualizes"}
_SOURCE_KINDS = {"document", "dataset", "recording", "transcript", "measurement", "archive", "other"}
_SOURCE_CLASSES = {"primary", "secondary", "derived", "unknown"}
_CLAIM_STATES = {"proposed", "reviewed", "contested", "unresolved", "withdrawn"}


class ThesisLedgerError(ValueError):
    """Invalid claim, evidence, provenance reference or ledger transition."""


def _text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ThesisLedgerError(f"{field} must be text")
    value = value.strip()
    if not value or len(value) > maximum or "\x00" in value:
        raise ThesisLedgerError(f"{field} is empty or exceeds {maximum} characters")
    return value


def _opaque_ref(value: Any, prefix: str, field: str) -> str:
    result = _text(value, field, 68)
    expected = prefix + ":"
    if not result.startswith(expected) or not _ID_RE.fullmatch(result[len(expected):]):
        raise ThesisLedgerError(f"{field} must be an opaque {prefix}: identifier")
    return result


def _timestamp(value: Any, field: str) -> str:
    raw = _text(value, field, 64)
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError as error:
        raise ThesisLedgerError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ThesisLedgerError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value: Any, field: str) -> str:
    result = _text(value, field, 64).lower()
    if not _SHA256_RE.fullmatch(result):
        raise ThesisLedgerError(f"{field} must be a SHA-256 hex digest")
    return result


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ThesisLedgerError(f"{field} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ThesisLedgerError(f"{field} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class ThesisClaim:
    claim_id: str
    statement: str
    scope: str
    status: str
    created_at_utc: str
    period_start_utc: str | None
    period_end_utc: str | None
    metric_key: str | None
    quantity_value: float | None
    quantity_unit: str | None
    revision: int = 1


@dataclass(frozen=True, slots=True)
class ThesisEvidence:
    evidence_id: str
    claim_id: str
    relation: str
    source_ref: str
    source_kind: str
    source_class: str
    content_sha256: str
    locator: str
    captured_at_utc: str
    actor_ref: str | None


@dataclass(frozen=True, slots=True)
class ThesisRevision:
    claim_id: str
    revision: int
    previous_statement_sha256: str
    statement: str
    reason: str
    recorded_at_utc: str
    actor_ref: str | None


class ThesisLedger:
    """In-memory assertion/evidence graph with deterministic, auditable export.

    Status is always review-controlled. Adding supporting evidence never
    auto-promotes a claim to a truth/verified state. Contradictions remain
    attached to the same claim and are not silently resolved.
    """

    def __init__(self, audit_log: Any | None = None) -> None:
        if audit_log is not None and not callable(getattr(audit_log, "record", None)):
            raise ThesisLedgerError("audit_log must expose record(event, **details)")
        self._audit = audit_log
        self._claims: dict[str, ThesisClaim] = {}
        self._evidence: dict[str, ThesisEvidence] = {}
        self._revisions: list[ThesisRevision] = []

    def _audit_event(self, event: str, **details: Any) -> None:
        if self._audit is not None:
            self._audit.record(event, **details)

    def add_claim(
        self,
        claim_id: str,
        statement: str,
        scope: str,
        *,
        created_at_utc: str,
        period_start_utc: str | None = None,
        period_end_utc: str | None = None,
        metric_key: str | None = None,
        quantity_value: int | float | None = None,
        quantity_unit: str | None = None,
        status: str = "proposed",
    ) -> ThesisClaim:
        identifier = _opaque_ref(claim_id, "clm", "claim_id")
        if identifier in self._claims:
            raise ThesisLedgerError(f"claim already exists: {identifier}")
        if len(self._claims) >= MAX_CLAIMS:
            raise ThesisLedgerError(f"ledger exceeds MAX_CLAIMS={MAX_CLAIMS}")
        state = _text(status, "status", 32)
        if state not in _CLAIM_STATES:
            raise ThesisLedgerError(f"unsupported claim status: {state}")
        start = _timestamp(period_start_utc, "period_start_utc") if period_start_utc is not None else None
        end = _timestamp(period_end_utc, "period_end_utc") if period_end_utc is not None else None
        if (start is None) != (end is None):
            raise ThesisLedgerError("period_start_utc and period_end_utc must be supplied together")
        if start is not None and end is not None and start >= end:
            raise ThesisLedgerError("claim period must have positive duration")

        has_metric = metric_key is not None
        has_value = quantity_value is not None
        has_unit = quantity_unit is not None
        if len({has_metric, has_value, has_unit}) != 1:
            raise ThesisLedgerError("metric_key, quantity_value and quantity_unit must be supplied together")
        metric = _text(metric_key, "metric_key", 128) if has_metric else None
        value = _finite_number(quantity_value, "quantity_value") if has_value else None
        unit = _text(quantity_unit, "quantity_unit", 64) if has_unit else None

        claim = ThesisClaim(
            claim_id=identifier,
            statement=_text(statement, "statement", 4096),
            scope=_text(scope, "scope", 512),
            status=state,
            created_at_utc=_timestamp(created_at_utc, "created_at_utc"),
            period_start_utc=start,
            period_end_utc=end,
            metric_key=metric,
            quantity_value=value,
            quantity_unit=unit,
        )
        self._claims[identifier] = claim
        self._audit_event(
            "thesis_claim_added",
            claim_ref=identifier,
            statement_sha256=hashlib.sha256(claim.statement.encode("utf-8")).hexdigest(),
        )
        return claim

    def add_evidence(
        self,
        evidence_id: str,
        claim_id: str,
        *,
        relation: str,
        source_ref: str,
        source_kind: str,
        source_class: str,
        content_sha256: str,
        locator: str,
        captured_at_utc: str,
        actor_ref: str | None = None,
    ) -> ThesisEvidence:
        identifier = _opaque_ref(evidence_id, "evd", "evidence_id")
        target = _opaque_ref(claim_id, "clm", "claim_id")
        if target not in self._claims:
            raise ThesisLedgerError(f"unknown claim: {target}")
        if identifier in self._evidence:
            raise ThesisLedgerError(f"evidence already exists: {identifier}")
        if len(self._evidence) >= MAX_EVIDENCE:
            raise ThesisLedgerError(f"ledger exceeds MAX_EVIDENCE={MAX_EVIDENCE}")
        link = _text(relation, "relation", 32)
        if link not in _RELATIONS:
            raise ThesisLedgerError(f"unsupported evidence relation: {link}")
        kind = _text(source_kind, "source_kind", 32)
        if kind not in _SOURCE_KINDS:
            raise ThesisLedgerError(f"unsupported source_kind: {kind}")
        source_quality = _text(source_class, "source_class", 32)
        if source_quality not in _SOURCE_CLASSES:
            raise ThesisLedgerError(f"unsupported source_class: {source_quality}")
        actor = _opaque_ref(actor_ref, "anon", "actor_ref") if actor_ref is not None else None
        evidence = ThesisEvidence(
            evidence_id=identifier,
            claim_id=target,
            relation=link,
            source_ref=_opaque_ref(source_ref, "src", "source_ref"),
            source_kind=kind,
            source_class=source_quality,
            content_sha256=_digest(content_sha256, "content_sha256"),
            locator=_text(locator, "locator", 2048),
            captured_at_utc=_timestamp(captured_at_utc, "captured_at_utc"),
            actor_ref=actor,
        )
        self._evidence[identifier] = evidence
        self._audit_event(
            "thesis_evidence_linked",
            evidence_ref=identifier,
            claim_ref=target,
            relation=link,
            content_sha256=evidence.content_sha256,
        )
        return evidence

    def set_status(
        self,
        claim_id: str,
        status: str,
        *,
        reason: str,
        recorded_at_utc: str,
        actor_ref: str | None = None,
    ) -> ThesisClaim:
        target = _opaque_ref(claim_id, "clm", "claim_id")
        current = self._claims.get(target)
        if current is None:
            raise ThesisLedgerError(f"unknown claim: {target}")
        state = _text(status, "status", 32)
        if state not in _CLAIM_STATES:
            raise ThesisLedgerError(f"unsupported claim status: {state}")
        why = _text(reason, "reason", 1024)
        actor = _opaque_ref(actor_ref, "anon", "actor_ref") if actor_ref is not None else None
        updated = replace(current, status=state)
        self._claims[target] = updated
        self._audit_event(
            "thesis_status_changed",
            claim_ref=target,
            old_status=current.status,
            new_status=state,
            reason_sha256=hashlib.sha256(why.encode("utf-8")).hexdigest(),
            recorded_at_utc=_timestamp(recorded_at_utc, "recorded_at_utc"),
            actor_ref=actor,
        )
        return updated

    def revise_claim(
        self,
        claim_id: str,
        statement: str,
        *,
        reason: str,
        recorded_at_utc: str,
        actor_ref: str | None = None,
    ) -> ThesisClaim:
        target = _opaque_ref(claim_id, "clm", "claim_id")
        current = self._claims.get(target)
        if current is None:
            raise ThesisLedgerError(f"unknown claim: {target}")
        if len(self._revisions) >= MAX_REVISIONS:
            raise ThesisLedgerError(f"ledger exceeds MAX_REVISIONS={MAX_REVISIONS}")
        updated_statement = _text(statement, "statement", 4096)
        why = _text(reason, "reason", 1024)
        actor = _opaque_ref(actor_ref, "anon", "actor_ref") if actor_ref is not None else None
        revision = ThesisRevision(
            claim_id=target,
            revision=current.revision,
            previous_statement_sha256=hashlib.sha256(current.statement.encode("utf-8")).hexdigest(),
            statement=updated_statement,
            reason=why,
            recorded_at_utc=_timestamp(recorded_at_utc, "recorded_at_utc"),
            actor_ref=actor,
        )
        self._revisions.append(revision)
        updated = replace(current, statement=updated_statement, revision=current.revision + 1, status="proposed")
        self._claims[target] = updated
        self._audit_event(
            "thesis_claim_revised",
            claim_ref=target,
            revision=updated.revision,
            previous_statement_sha256=revision.previous_statement_sha256,
            statement_sha256=hashlib.sha256(updated_statement.encode("utf-8")).hexdigest(),
        )
        return updated

    def compare_quantitative_claims(
        self, left_id: str, right_id: str, *, tolerance: float = 0.0
    ) -> dict[str, Any]:
        left_key = _opaque_ref(left_id, "clm", "left_id")
        right_key = _opaque_ref(right_id, "clm", "right_id")
        if left_key not in self._claims or right_key not in self._claims:
            raise ThesisLedgerError("both claims must exist in the ledger")
        left, right = self._claims[left_key], self._claims[right_key]
        permitted_tolerance = _finite_number(tolerance, "tolerance")
        if permitted_tolerance < 0:
            raise ThesisLedgerError("tolerance cannot be negative")
        reasons: list[str] = []
        if left.metric_key is None or right.metric_key is None:
            reasons.append("claim is not quantitative")
        if left.scope != right.scope:
            reasons.append("scope differs")
        if left.metric_key != right.metric_key:
            reasons.append("metric differs")
        if left.quantity_unit != right.quantity_unit:
            reasons.append("unit differs")
        if (left.period_start_utc, left.period_end_utc) != (right.period_start_utc, right.period_end_utc):
            reasons.append("time window differs")
        if left.status == "withdrawn" or right.status == "withdrawn":
            reasons.append("a claim is withdrawn")
        if reasons:
            return {"comparable": False, "reasons": reasons}
        assert left.quantity_value is not None and right.quantity_value is not None
        delta = right.quantity_value - left.quantity_value
        return {
            "comparable": True,
            "metric_key": left.metric_key,
            "unit": left.quantity_unit,
            "delta": delta,
            "absolute_delta": abs(delta),
            "within_tolerance": abs(delta) <= permitted_tolerance,
            "tolerance": permitted_tolerance,
            "interpretation": "numerical comparison only; no truth or source-quality verdict",
        }

    def evidence_for(self, claim_id: str) -> list[ThesisEvidence]:
        target = _opaque_ref(claim_id, "clm", "claim_id")
        if target not in self._claims:
            raise ThesisLedgerError(f"unknown claim: {target}")
        return sorted(
            (item for item in self._evidence.values() if item.claim_id == target),
            key=lambda item: item.evidence_id,
        )

    def snapshot(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible snapshot with a content digest."""
        payload: dict[str, Any] = {
            "schema": THESIS_SCHEMA,
            "claims": [asdict(self._claims[key]) for key in sorted(self._claims)],
            "evidence": [asdict(self._evidence[key]) for key in sorted(self._evidence)],
            "revisions": [asdict(item) for item in self._revisions],
            "semantics": {
                "status_is_review_controlled": True,
                "evidence_does_not_auto_verify_claims": True,
                "identifiers_are_opaque_pseudonyms": True,
            },
        }
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        payload["snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()
        return payload

    def summary(self) -> dict[str, int]:
        statuses = {state: 0 for state in sorted(_CLAIM_STATES)}
        for claim in self._claims.values():
            statuses[claim.status] += 1
        without_evidence = sum(not any(
            evidence.claim_id == claim.claim_id for evidence in self._evidence.values()
        ) for claim in self._claims.values())
        return {
            "claims": len(self._claims),
            "evidence": len(self._evidence),
            "revisions": len(self._revisions),
            "claims_without_evidence": without_evidence,
            "contested_claims": statuses["contested"],
            "unresolved_claims": statuses["unresolved"],
        }
