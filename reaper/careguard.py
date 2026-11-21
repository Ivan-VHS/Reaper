"""CareGuard v1: privacy-preserving engineering support primitives.

CareGuard evaluates project workload and language safety only. It does not
infer a person's mental state, store symptoms, diagnose conditions, prescribe
medication, or contact anyone.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Literal, Sequence

LoadStatus = Literal["normal", "watch", "pause"]
SupportPath = Literal["trusted_person", "peer_support", "professional", "urgent_human"]

@dataclass(frozen=True)
class WorkloadSnapshot:
    queued_items: int = 0
    failed_checks: int = 0
    alerts_per_hour: int = 0
    active_workers: int = 0
    worker_capacity: int = 1

    def __post_init__(self) -> None:
        for name in ("queued_items", "failed_checks", "alerts_per_hour", "active_workers", "worker_capacity"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.worker_capacity == 0:
            raise ValueError("worker_capacity must be greater than zero")

@dataclass(frozen=True)
class CareGuardAssessment:
    status: LoadStatus
    pressure_score: int
    findings: tuple[str, ...]
    reserve_percent: int
    available_worker_capacity: int

@dataclass(frozen=True)
class LanguageFinding:
    phrase: str
    suggestion: str

_STIGMA_PHRASES = {
    "weakness": "a request for support",
    "lazy": "a person may need support",
    "weakness": "a request for support",
    "lazy": "a person may need support",
    "слабость": "запрос о поддержке",
    "слабкість": "запит про підтримку",
    "ленивый": "человеку может требоваться помощь",
    "лінивий": "людині може бути потрібна підтримка",
    "attention seeking": "communicating a need or distress",
    "just snap out of it": "offer practical support without blame",
    "crazy": "describe the specific behaviour without a label",
}
_SENSITIVE_PROBES = ("depression", "депрессия", "депресія", "mental health", "психічне здоров'я")
_CLINICAL_ACTION_TERMS = (
    "diagnose", "diagnosis", "prescribe", "prescription", "medication",
    "antidepressant", "dosage", "назначить препарат", "поставить диагноз",
    "призначити препарат", "поставити діагноз",
)
_SUPPORT_PATHS = {
    "trusted_person", "peer_support", "professional", "urgent_human",
}
_ROLE_LABELS = {"maintainer", "reviewer", "contributor", "automation", "operator"}
_CONTEXT_EVENTS = {
    "project_paused", "human_review_requested", "capacity_rebalanced",
    "support_path_selected", "maintenance_window_opened",
}

def careguard_assess_project_load(snapshot: WorkloadSnapshot) -> CareGuardAssessment:
    """Score technical workload metrics; never accepts personal health data."""
    if not isinstance(snapshot, WorkloadSnapshot):
        raise TypeError("snapshot must be a WorkloadSnapshot")
    score = 0
    findings: list[str] = []
    if snapshot.queued_items >= 16:
        score += 25
        findings.append("work_queue_critical")
    elif snapshot.queued_items >= 8:
        score += 12
        findings.append("work_queue_growing")
    if snapshot.failed_checks >= 3:
        score += 30
        findings.append("repeated_check_failures")
    elif snapshot.failed_checks:
        score += 12
        findings.append("check_failure_present")
    if snapshot.alerts_per_hour >= 20:
        score += 30
        findings.append("alert_flood")
    elif snapshot.alerts_per_hour >= 8:
        score += 12
        findings.append("alert_rate_elevated")
    utilization = snapshot.active_workers / snapshot.worker_capacity
    if utilization >= 1.0:
        score += 25
        findings.append("capacity_exceeded")
    elif utilization >= 0.85:
        score += 12
        findings.append("capacity_near_limit")

    status: LoadStatus = "pause" if score >= 60 else "watch" if score >= 25 else "normal"
    reserve_percent = {"normal": 10, "watch": 20, "pause": 30}[status]
    reserve = math.ceil(snapshot.worker_capacity * reserve_percent / 100)
    available = max(0, snapshot.worker_capacity - reserve)
    return CareGuardAssessment(status, min(score, 100), tuple(findings), reserve_percent, available)

def careguard_review_language(text: str) -> tuple[LanguageFinding, ...]:
    """Return review suggestions; source text is never silently rewritten."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    folded = text.casefold()
    return tuple(
        LanguageFinding(phrase, suggestion)
        for phrase, suggestion in _STIGMA_PHRASES.items()
        if phrase in folded
    )

def careguard_probe_sensitive_handler(
    handler: Callable[[str], object],
    probes: Sequence[str] = _SENSITIVE_PROBES,
) -> tuple[str, ...]:
    """Smoke-test a caller-supplied text handler; return probes that raised."""
    if not callable(handler):
        raise TypeError("handler must be callable")
    failures: list[str] = []
    for probe in probes:
        if not isinstance(probe, str) or not probe:
            raise ValueError("probes must contain non-empty strings")
        try:
            handler(probe)
        except Exception:
            failures.append(probe)
    return tuple(failures)

def careguard_accept_help_request(message: str) -> bool:
    """A non-empty support request is valid input, never a weakness signal."""
    if not isinstance(message, str):
        raise TypeError("message must be a string")
    return bool(message.strip())

def careguard_select_support_path(path: SupportPath) -> dict[str, object]:
    """Return a user-selected route; this function never sends or escalates."""
    if path not in _SUPPORT_PATHS:
        raise ValueError(f"path must be one of: {', '.join(sorted(_SUPPORT_PATHS))}")
    return {"path": path, "mode": "manual_choice", "automatic_contact": False}

def careguard_review_contextual_claim(claim: str, evidence_ref: str | None) -> bool:
    """Only mark a claim as evidence-backed when a source reference is supplied."""
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("claim must be non-empty text")
    return isinstance(evidence_ref, str) and bool(evidence_ref.strip())

def careguard_check_clinical_boundary(action: str) -> bool:
    """Reject diagnosis/prescribing actions in this non-clinical application."""
    if not isinstance(action, str) or not action.strip():
        raise ValueError("action must be non-empty text")
    folded = action.casefold()
    return not any(term in folded for term in _CLINICAL_ACTION_TERMS)

def careguard_allocate_resilience_buffer(
    capacity_units: int, reserve_fraction: float = 0.20,
) -> tuple[int, int]:
    """Return (reserved_units, usable_units) with a bounded 0–50% reserve."""
    if isinstance(capacity_units, bool) or not isinstance(capacity_units, int) or capacity_units < 0:
        raise ValueError("capacity_units must be a non-negative integer")
    if isinstance(reserve_fraction, bool) or not isinstance(reserve_fraction, (int, float)):
        raise ValueError("reserve_fraction must be numeric")
    if not math.isfinite(reserve_fraction) or not 0.0 <= reserve_fraction <= 0.5:
        raise ValueError("reserve_fraction must be finite and between 0 and 0.5")
    reserved = math.ceil(capacity_units * reserve_fraction)
    return reserved, capacity_units - reserved

def careguard_record_context_event(actor: str, event_type: str, occurred_at: str) -> dict[str, str]:
    """Create a minimal allowlisted event; arbitrary personal details are not accepted."""
    for field, value in (("actor", actor), ("event_type", event_type), ("occurred_at", occurred_at)):
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise ValueError(f"{field} must be non-empty text of at most 128 characters")
    if actor.strip() not in _ROLE_LABELS:
        raise ValueError(f"actor must be one of: {\", \".join(sorted(_ROLE_LABELS))}")
    if event_type not in _CONTEXT_EVENTS:
        raise ValueError("event_type is not in the CareGuard allowlist")
    return {"actor": actor.strip(), "event_type": event_type, "occurred_at": occurred_at.strip()}
