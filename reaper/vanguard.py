"""Explicit health inspection and bounded recovery hooks.

VanguardSentinel never starts background threads and never changes application
state during inspection. A host must call recover() explicitly after reviewing
a report; recovery callbacks are local and bounded by a per-watch budget.
"""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class SentinelFinding:
    subject: str
    state: str
    detail: str
    recoveries: int = 0
    recovery_limit: int = 0


@dataclass(frozen=True, slots=True)
class SentinelReport:
    findings: tuple[SentinelFinding, ...]

    @property
    def healthy(self) -> bool:
        return all(item.state in {"healthy", "stopped"} for item in self.findings)

    @property
    def unhealthy(self) -> tuple[SentinelFinding, ...]:
        return tuple(item for item in self.findings if item.state in {"degraded", "critical"})


@dataclass(slots=True)
class _Watch:
    probe: Callable[[], bool]
    recovery: Callable[[], Any] | None
    recovery_limit: int
    recoveries: int = 0


class VanguardSentinel:
    """Collect local health reports and expose explicitly invoked recovery.

    Probes must return bool. Exceptions and invalid return values are reported
    as critical findings. Actor status dictionaries may be supplied using the
    shape returned by reaper.concurrency.ActorSystem.status().
    """

    def __init__(self, max_watches: int = 256) -> None:
        if max_watches < 1:
            raise ValueError("max_watches must be positive")
        self.max_watches = max_watches
        self._watches: dict[str, _Watch] = {}
        self._latest: dict[str, SentinelFinding] = {}
        self._lock = RLock()

    def watch(
        self,
        name: str,
        probe: Callable[[], bool],
        recovery: Callable[[], Any] | None = None,
        *,
        max_recoveries: int = 0,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("watch name must be a non-empty string")
        if not callable(probe):
            raise TypeError("probe must be callable")
        if recovery is not None and not callable(recovery):
            raise TypeError("recovery must be callable or None")
        if max_recoveries < 0:
            raise ValueError("max_recoveries cannot be negative")
        if recovery is None and max_recoveries:
            raise ValueError("max_recoveries requires a recovery callback")
        with self._lock:
            if name in self._watches:
                raise ValueError(f"watch '{name}' is already registered")
            if len(self._watches) >= self.max_watches:
                raise ValueError(f"watch limit ({self.max_watches}) exceeded")
            self._watches[name] = _Watch(probe, recovery, max_recoveries)

    def unwatch(self, name: str) -> bool:
        with self._lock:
            self._latest.pop(name, None)
            return self._watches.pop(name, None) is not None

    def inspect(
        self,
        *,
        actors: Iterable[Mapping[str, Any]] = (),
    ) -> SentinelReport:
        with self._lock:
            watches = tuple(self._watches.items())

        findings: list[SentinelFinding] = []
        for name, watch in watches:
            try:
                result = watch.probe()
                if type(result) is not bool:
                    raise TypeError("health probe must return bool")
                state = "healthy" if result else "critical"
                detail = "probe passed" if result else "probe reported unhealthy"
            except Exception as error:
                state = "critical"
                detail = f"{type(error).__name__}: {error}"
            findings.append(SentinelFinding(
                name, state, detail, watch.recoveries, watch.recovery_limit
            ))

        for actor in actors:
            if not isinstance(actor, Mapping):
                raise TypeError("actor statuses must be mappings")
            name = str(actor.get("name", "<unnamed>"))
            subject = f"actor:{name}"
            failed = bool(actor.get("failed", False))
            restarts = actor.get("restarts", 0)
            failure = actor.get("failure")
            if failed:
                state = "critical"
                detail = str(failure or "actor supervisor reports failure")
            elif isinstance(restarts, int) and not isinstance(restarts, bool) and restarts > 0:
                state = "degraded"
                detail = f"actor restarted {restarts} time(s)"
            elif bool(actor.get("done", False)):
                state = "stopped"
                detail = "actor task has stopped"
            else:
                state = "healthy"
                detail = "actor task is running"
            findings.append(SentinelFinding(subject, state, detail))

        with self._lock:
            self._latest = {finding.subject: finding for finding in findings}
            enriched: list[SentinelFinding] = []
            for finding in findings:
                watch = self._watches.get(finding.subject)
                if watch is not None:
                    finding = SentinelFinding(
                        finding.subject, finding.state, finding.detail,
                        watch.recoveries, watch.recovery_limit,
                    )
                enriched.append(finding)
        return SentinelReport(tuple(enriched))

    def recover(self, name: str) -> bool:
        """Run one registered recovery callback for the latest unhealthy finding.

        Returns False when no unhealthy finding, callback, or recovery budget
        exists. Callback exceptions propagate to the caller.
        """
        with self._lock:
            watch = self._watches.get(name)
            finding = self._latest.get(name)
            if (
                watch is None
                or finding is None
                or finding.state not in {"degraded", "critical"}
                or watch.recovery is None
                or watch.recoveries >= watch.recovery_limit
            ):
                return False
            watch.recoveries += 1
            callback = watch.recovery
        callback()
        return True
