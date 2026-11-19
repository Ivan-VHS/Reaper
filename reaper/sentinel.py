"""In-process health observation and advisory recovery decisions."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HealthSample:
    cpu_load: float
    memory_pressure: float
    error_rate: float
    latency_ms: float
    mailbox_depth: int = 0


@dataclass(frozen=True, slots=True)
class SentinelPolicy:
    cpu_warning: float = 0.85
    cpu_critical: float = 0.97
    memory_warning: float = 0.85
    memory_critical: float = 0.97
    error_warning: float = 0.02
    error_critical: float = 0.10
    latency_warning_ms: float = 500.0
    latency_critical_ms: float = 2_000.0
    mailbox_warning: int = 1_000
    mailbox_critical: int = 10_000
    sustained_critical_samples: int = 3

    def __post_init__(self) -> None:
        ratios = (self.cpu_warning, self.cpu_critical, self.memory_warning,
                  self.memory_critical, self.error_warning, self.error_critical)
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in ratios):
            raise ValueError("ratio thresholds must be finite values between 0 and 1")
        if self.cpu_warning > self.cpu_critical or self.memory_warning > self.memory_critical:
            raise ValueError("warning thresholds cannot exceed critical thresholds")
        if self.error_warning > self.error_critical:
            raise ValueError("error warning threshold cannot exceed critical threshold")
        if self.latency_warning_ms < 0 or self.latency_critical_ms < self.latency_warning_ms:
            raise ValueError("latency thresholds are invalid")
        if self.mailbox_warning < 0 or self.mailbox_critical < self.mailbox_warning:
            raise ValueError("mailbox thresholds are invalid")
        if self.sustained_critical_samples < 1:
            raise ValueError("sustained_critical_samples must be positive")


@dataclass(frozen=True, slots=True)
class SentinelReport:
    sequence: int
    severity: str
    action: str
    reasons: tuple[str, ...]
    consecutive_critical: int


class VanguardSentinel:
    """Classifies supplied samples; it never restarts processes or scales services."""

    def __init__(self, policy: SentinelPolicy | None = None) -> None:
        self.policy = policy or SentinelPolicy()
        self.sequence = 0
        self._consecutive_critical = 0

    def observe(self, sample: HealthSample) -> SentinelReport:
        if not isinstance(sample, HealthSample):
            raise TypeError("sample must be a HealthSample")
        ratios = (sample.cpu_load, sample.memory_pressure, sample.error_rate)
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in ratios):
            raise ValueError("CPU, memory and error rates must be finite values between 0 and 1")
        if not math.isfinite(sample.latency_ms) or sample.latency_ms < 0:
            raise ValueError("latency_ms must be a finite non-negative number")
        if isinstance(sample.mailbox_depth, bool) or not isinstance(sample.mailbox_depth, int) or sample.mailbox_depth < 0:
            raise ValueError("mailbox_depth must be a non-negative integer")

        p = self.policy
        warning: list[str] = []
        critical: list[str] = []
        for value, warn, hard, label in (
            (sample.cpu_load, p.cpu_warning, p.cpu_critical, "cpu"),
            (sample.memory_pressure, p.memory_warning, p.memory_critical, "memory"),
            (sample.error_rate, p.error_warning, p.error_critical, "error_rate"),
            (sample.latency_ms, p.latency_warning_ms, p.latency_critical_ms, "latency_ms"),
            (sample.mailbox_depth, p.mailbox_warning, p.mailbox_critical, "mailbox_depth"),
        ):
            if value >= hard:
                critical.append(label)
            elif value >= warn:
                warning.append(label)

        self.sequence += 1
        if critical:
            self._consecutive_critical += 1
            severity = "critical"
            action = "review-restart-or-scale" if self._consecutive_critical >= p.sustained_critical_samples else "investigate"
            reasons = tuple(critical + warning)
        elif warning:
            self._consecutive_critical = 0
            severity, action, reasons = "warning", "investigate", tuple(warning)
        else:
            self._consecutive_critical = 0
            severity, action, reasons = "healthy", "none", ()
        return SentinelReport(self.sequence, severity, action, reasons, self._consecutive_critical)
