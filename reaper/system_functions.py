"""Bounded, explicit system functions exposed to Reaper source programs.

These functions extend the Python reference runtime. They do not claim native-C17
compiler parity or operating-system isolation.
"""
from __future__ import annotations

import copy
import hashlib
import heapq
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Mapping
from typing import Any

from .errors import ReaperRuntimeError
from .lexer import Token


class SystemFunctionError(ReaperRuntimeError):
    """Invalid input or violated system-function contract."""


class WorkerBudgetExceeded(SystemFunctionError):
    """A cooperative Reaper worker crossed its time budget."""


class OverrideAuthority:
    """Host-owned, scoped, single-use override tokens.

    The authority is deliberately injected by the embedding host. Reaper source
    cannot mint its own approval tokens.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokens: dict[str, tuple[str, int]] = {}

    def issue(self, scope: str, ttl_ms: int = 30_000) -> str:
        if not isinstance(scope, str) or not scope or len(scope) > 128:
            raise ValueError("override scope must contain 1..128 characters")
        if isinstance(ttl_ms, bool) or not isinstance(ttl_ms, int) or not 1 <= ttl_ms <= 300_000:
            raise ValueError("override ttl_ms must be between 1 and 300000")
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._lock:
            self._tokens[digest] = (scope, time.monotonic_ns() + ttl_ms * 1_000_000)
        return token

    def consume(self, token: Any, scope: str) -> bool:
        if not isinstance(token, str) or not token:
            return False
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._lock:
            grant = self._tokens.pop(digest, None)
        if grant is None:
            return False
        granted_scope, expires_at = grant
        return hmac.compare_digest(granted_scope, scope) and time.monotonic_ns() <= expires_at


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SystemFunctionError(f"{label} must be a whole number >= {minimum}")
    return value


def _json_copy(value: Any, *, max_bytes: int = 4 * 1024 * 1024) -> Any:
    try:
        rendered = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        )
        encoded = rendered.encode("utf-8")
        if len(encoded) > max_bytes:
            raise SystemFunctionError(f"payload exceeds {max_bytes} bytes")
        return json.loads(rendered)
    except SystemFunctionError:
        raise
    except (TypeError, ValueError, RecursionError, UnicodeError) as error:
        raise SystemFunctionError(f"expected finite JSON-compatible data: {error}") from error


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise SystemFunctionError(f"{label} must be a list")
    return list(value)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise SystemFunctionError(f"{label} must be a mapping with text keys")
    return value


def _key_order(value: Any) -> tuple[str, str]:
    return type(value).__name__, repr(value)


class ReaperSystemFunctions:
    """Implementation backing the public functions in stdlib/system.rpr."""

    def __init__(self, interpreter: Any, override_authority: OverrideAuthority | None = None) -> None:
        self.interpreter = interpreter
        self.override_authority = override_authority
        self._revision = 0
        self._journal: deque[dict[str, Any]] = deque(maxlen=512)
        self._latencies: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=4096))

    def _invoke(self, function: Any, arguments: list[Any], name: str) -> Any:
        token = Token("BUILTIN", name, 1, 1)
        return self.interpreter._call(function, arguments, token)

    def contract_graph_check(self, contracts: Any) -> dict[str, Any]:
        """Validate ids, references, cycles and inherited field compatibility."""
        records = _list(contracts, "contracts")
        if len(records) > self.interpreter.max_collection_items:
            raise SystemFunctionError("contract count exceeds the interpreter collection limit")

        by_id: dict[str, Mapping[str, Any]] = {}
        errors: list[str] = []
        for index, raw in enumerate(records):
            record = _mapping(raw, f"contracts[{index}]")
            contract_id = record.get("id")
            if not isinstance(contract_id, str) or not contract_id.strip():
                errors.append(f"contracts[{index}]: id must be non-empty text")
                continue
            if contract_id in by_id:
                errors.append(f"duplicate contract id: {contract_id}")
                continue
            dependencies = record.get("depends_on", [])
            fields = record.get("fields", {})
            valid_dependencies = isinstance(dependencies, (list, tuple)) and all(
                isinstance(item, str) and item for item in dependencies
            )
            if not valid_dependencies:
                errors.append(f"{contract_id}: depends_on must be a list of contract ids")
            if not isinstance(fields, Mapping):
                errors.append(f"{contract_id}: fields must be a mapping")
            elif any(
                not isinstance(field_name, str) or not field_name
                or not isinstance(field_type, str) or not field_type
                for field_name, field_type in fields.items()
            ):
                errors.append(f"{contract_id}: fields must map non-empty names to non-empty type names")
            by_id[contract_id] = record

        graph: dict[str, list[str]] = {}
        for contract_id, record in by_id.items():
            dependencies = record.get("depends_on", [])
            if not isinstance(dependencies, (list, tuple)) or not all(
                isinstance(item, str) and item for item in dependencies
            ):
                graph[contract_id] = []
                continue
            graph[contract_id] = sorted(set(dependencies))
            for dependency in graph[contract_id]:
                if dependency not in by_id:
                    errors.append(f"{contract_id}: unknown dependency '{dependency}'")

        # Kahn ordering is iterative, deterministic and avoids Python recursion limits.
        pending = {
            contract_id: {dependency for dependency in dependencies if dependency in by_id}
            for contract_id, dependencies in graph.items()
        }
        dependents: dict[str, list[str]] = defaultdict(list)
        for contract_id, dependencies in pending.items():
            for dependency in dependencies:
                dependents[dependency].append(contract_id)
        ready = [contract_id for contract_id, dependencies in pending.items() if not dependencies]
        heapq.heapify(ready)
        order: list[str] = []
        while ready:
            contract_id = heapq.heappop(ready)
            order.append(contract_id)
            for dependent in sorted(dependents.get(contract_id, [])):
                pending[dependent].discard(contract_id)
                if not pending[dependent]:
                    heapq.heappush(ready, dependent)

        cyclic = sorted(contract_id for contract_id, dependencies in pending.items() if dependencies)
        if cyclic:
            errors.append("dependency cycle involving: " + ", ".join(cyclic[:32]))

        effective_fields: dict[str, dict[str, str]] = {}
        for contract_id in order:
            inherited: dict[str, str] = {}
            origins: dict[str, str] = {}
            for dependency in graph.get(contract_id, []):
                for field_name, field_type in effective_fields.get(dependency, {}).items():
                    if field_name in inherited and inherited[field_name] != field_type:
                        errors.append(
                            f"{contract_id}: inherited field '{field_name}' conflicts between "
                            f"'{origins[field_name]}' and '{dependency}'"
                        )
                    else:
                        inherited[field_name] = field_type
                        origins[field_name] = dependency
            own_fields = by_id[contract_id].get("fields", {})
            if isinstance(own_fields, Mapping):
                for field_name, field_type in own_fields.items():
                    if field_name in inherited and inherited[field_name] != field_type:
                        errors.append(
                            f"{contract_id}: field '{field_name}' conflicts with inherited "
                            f"type from '{origins[field_name]}'"
                        )
                    inherited[field_name] = field_type
                    origins[field_name] = contract_id
            effective_fields[contract_id] = inherited

        return {
            "ok": not errors,
            "order": order if not errors else [],
            "errors": errors,
            "contract_count": len(by_id),
            "phase": "runtime_preflight",
        }

    def arena_slot(self, function: Any, capacity_bytes: Any) -> dict[str, Any]:
        """Run a callback in a bounded tracked region and detach its result."""
        capacity = _integer(capacity_bytes, "capacity_bytes", 1)
        memory = self.interpreter.memory
        region = memory.begin_region(capacity)
        previous_environment = self.interpreter._current_environment
        try:
            value = self._invoke(function, [], "arena_slot")
            detached = _json_copy(value, max_bytes=capacity)
        except Exception:
            self.interpreter._current_environment = previous_environment
            try:
                memory.end_region(region, self.interpreter._memory_roots())
            except Exception:
                memory.promote_region(region)
            raise
        self.interpreter._current_environment = previous_environment
        try:
            reclaimed = memory.end_region(region, self.interpreter._memory_roots())
        except Exception as error:
            escaped = memory.promote_region(region)
            raise SystemFunctionError(
                f"arena_slot cannot close: {escaped} allocation(s) escaped the slot"
            ) from error
        return {
            "value": detached,
            "reclaimed_objects": reclaimed,
            "capacity_bytes": capacity,
        }

    def worker_budget(
        self, budget_ms: Any, memory_bytes: Any, function: Any,
        arguments: Any, state: Any = None,
    ) -> dict[str, Any]:
        """Run a cooperative callback under deadline and tracked-region limits.

        This is not a process sandbox: blocking host calls and untracked Python
        allocations cannot be pre-empted or accounted as hard OS resources.
        """
        milliseconds = _integer(budget_ms, "budget_ms", 1)
        memory_limit = _integer(memory_bytes, "memory_bytes", 1)
        args = _list(arguments, "worker arguments")
        if len(args) > 256:
            raise SystemFunctionError("worker argument count exceeds 256")
        started = time.monotonic_ns()
        deadline = started + milliseconds * 1_000_000
        start_steps = self.interpreter.steps
        frame = {"deadline_ns": deadline, "start_steps": start_steps, "budget_ms": milliseconds}
        region = self.interpreter.memory.begin_region(memory_limit)
        previous_environment = self.interpreter._current_environment
        self.interpreter._worker_budgets.append(frame)
        value: Any = None
        failure: str | None = None
        try:
            value = self._invoke(function, args, "worker_budget")
            if time.monotonic_ns() > deadline:
                raise WorkerBudgetExceeded(f"worker exceeded {milliseconds} ms")
            value = copy.deepcopy(value)
        except Exception as error:
            failure = f"{type(error).__name__}: {error}"
        finally:
            self.interpreter._worker_budgets.pop()
            self.interpreter._current_environment = previous_environment
            try:
                self.interpreter.memory.end_region(region, self.interpreter._memory_roots())
            except Exception as error:
                self.interpreter.memory.promote_region(region)
                if failure is None:
                    failure = f"worker state escaped its budget region: {error}"

        elapsed_ms = (time.monotonic_ns() - started) / 1_000_000
        try:
            state_dump = _json_copy(state, max_bytes=64 * 1024)
        except SystemFunctionError:
            state_dump = {"snapshot": repr(state)[:4096], "truncated": len(repr(state)) > 4096}
        return {
            "status": "completed" if failure is None else "halted",
            "value": value if failure is None else None,
            "reason": failure,
            "elapsed_ms": elapsed_ms,
            "steps": self.interpreter.steps - start_steps,
            "memory_budget_bytes": memory_limit,
            "state_dump": state_dump,
            "isolation": "cooperative_reference_runtime",
        }

    def diff_reconcile(self, before: Any, after: Any, key_field: Any) -> dict[str, Any]:
        old_rows = _list(before, "before snapshot")
        new_rows = _list(after, "after snapshot")
        if not isinstance(key_field, str) or not key_field:
            raise SystemFunctionError("key_field must be non-empty text")

        def index_rows(rows: list[Any], label: str) -> dict[Any, dict[str, Any]]:
            indexed: dict[Any, dict[str, Any]] = {}
            for position, raw in enumerate(rows):
                row = dict(_mapping(raw, f"{label}[{position}]"))
                key = row.get(key_field)
                if isinstance(key, bool) or not isinstance(key, (str, int)):
                    raise SystemFunctionError(f"{label}[{position}] has an invalid '{key_field}'")
                if key in indexed:
                    raise SystemFunctionError(f"{label} contains duplicate key {key!r}")
                indexed[key] = row
            return indexed

        old = index_rows(old_rows, "before")
        new = index_rows(new_rows, "after")
        operations: list[dict[str, Any]] = []
        for key in sorted(set(old) | set(new), key=_key_order):
            if key not in old:
                operations.append({"action": "upsert", "key": key, "value": new[key]})
            elif key not in new:
                operations.append({"action": "drop", "key": key})
            elif old[key] != new[key]:
                operations.append({"action": "upsert", "key": key, "value": new[key]})
            else:
                operations.append({"action": "noop", "key": key, "value": old[key]})
        target = [new[key] for key in sorted(new, key=_key_order)]
        rendered = json.dumps(target, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        checksum = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        return {
            "schema": "reaper.reconcile-plan.v1",
            "key_field": key_field,
            "operations": operations,
            "target_checksum": checksum,
            "operation_count": len(operations),
        }

    def reconcile_apply(self, current: Any, plan: Any, invariant: Any) -> dict[str, Any]:
        base = _list(current, "current snapshot")
        descriptor = _mapping(plan, "reconcile plan")
        if descriptor.get("schema") != "reaper.reconcile-plan.v1":
            raise SystemFunctionError("unsupported reconcile plan schema")
        key_field = descriptor.get("key_field")
        if not isinstance(key_field, str) or not key_field:
            raise SystemFunctionError("reconcile plan has no key field")
        rows: dict[Any, dict[str, Any]] = {}
        for index, raw in enumerate(base):
            row = dict(_mapping(raw, f"current[{index}]"))
            key = row.get(key_field)
            if isinstance(key, bool) or not isinstance(key, (str, int)):
                raise SystemFunctionError(f"current[{index}] has an invalid '{key_field}'")
            if key in rows:
                raise SystemFunctionError(f"current snapshot has duplicate key {key!r}")
            rows[key] = row

        seen: set[Any] = set()
        for index, raw in enumerate(_list(descriptor.get("operations"), "operations")):
            operation = _mapping(raw, f"operations[{index}]")
            action = operation.get("action")
            key = operation.get("key")
            if key in seen:
                raise SystemFunctionError(f"reconcile plan repeats key {key!r}")
            seen.add(key)
            if action == "drop":
                rows.pop(key, None)
            elif action == "upsert":
                value = dict(_mapping(operation.get("value"), "upsert value"))
                if value.get(key_field) != key:
                    raise SystemFunctionError(f"upsert key mismatch for {key!r}")
                rows[key] = value
            elif action == "noop":
                if key not in rows:
                    raise SystemFunctionError(f"noop references missing current key {key!r}")
            else:
                raise SystemFunctionError(f"unknown reconcile action: {action!r}")

        candidate = [rows[key] for key in sorted(rows, key=_key_order)]
        candidate = _json_copy(candidate)
        if self._invoke(invariant, [candidate], "reconcile_apply") is not True:
            raise SystemFunctionError("reconcile invariant rejected the candidate; no state was committed")
        rendered = json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        if descriptor.get("target_checksum") != digest:
            raise SystemFunctionError("reconcile candidate checksum does not match the plan")
        return {"committed": True, "snapshot": candidate, "checksum": digest}

    @staticmethod
    def ephemeral_match(left: Any, right: Any) -> bool:
        """Compare temporary SHA-256 digests and wipe the owned working copies."""
        def temporary(value: Any) -> bytearray:
            if isinstance(value, str):
                return bytearray(value.encode("utf-8"))
            if isinstance(value, (bytes, bytearray, memoryview)):
                return bytearray(value)
            raise SystemFunctionError("ephemeral_match accepts text or byte sequences")

        left_buffer: bytearray | None = None
        right_buffer: bytearray | None = None
        left_digest: bytes | None = None
        right_digest: bytes | None = None
        try:
            left_buffer = temporary(left)
            right_buffer = temporary(right)
            left_digest = hashlib.sha256(left_buffer).digest()
            right_digest = hashlib.sha256(right_buffer).digest()
            return hmac.compare_digest(left_digest, right_digest)
        finally:
            for buffer in (left_buffer, right_buffer):
                if buffer is not None:
                    buffer[:] = b"\0" * len(buffer)
            left_digest = None
            right_digest = None

    def guarded_mutation(
        self, current: Any, candidate: Any, mode: Any,
        validator: Any = None, token: Any = None,
    ) -> dict[str, Any]:
        before = _json_copy(current)
        after = _json_copy(candidate)
        if mode == "auto":
            if self._invoke(validator, [before, after], "guarded_mutation") is not True:
                raise SystemFunctionError("automatic mutation rejected by the strict validator")
        elif mode == "override":
            if self.override_authority is None or not self.override_authority.consume(token, "mutation:override"):
                raise SystemFunctionError("manual mutation requires a valid, unexpired, single-use override token")
        else:
            raise SystemFunctionError("mutation mode must be 'auto' or 'override'")

        rendered = json.dumps(after, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        self._revision += 1
        audit_id = f"rev-{self._revision:08d}"
        self._journal.append({
            "revision": self._revision,
            "audit_id": audit_id,
            "mode": mode,
            "digest": digest,
            "recorded_monotonic_ns": time.monotonic_ns(),
        })
        return {
            "state": after,
            "revision": self._revision,
            "audit_id": audit_id,
            "digest": digest,
            "mode": mode,
        }

    def revision_log(self) -> list[dict[str, Any]]:
        return [dict(event) for event in self._journal]

    @staticmethod
    def lease_window(start_ms: Any, days: Any, now_ms: Any) -> dict[str, Any]:
        start = _integer(start_ms, "start_ms")
        duration_days = _integer(days, "days", 1)
        now = _integer(now_ms, "now_ms")
        expires = start + duration_days * 86_400_000
        return {
            "active": now < expires and now >= start,
            "starts_at_ms": start,
            "expires_at_ms": expires,
            "remaining_ms": max(0, expires - now),
            "days": duration_days,
        }

    def latency_measure(self, label: Any, function: Any, arguments: Any) -> Any:
        if not isinstance(label, str) or not label or len(label) > 128:
            raise SystemFunctionError("latency label must contain 1..128 characters")
        args = _list(arguments, "latency arguments")
        started = time.perf_counter_ns()
        try:
            return self._invoke(function, args, "latency_measure")
        finally:
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            self._latencies[label].append(elapsed_ms)

    def latency_report(self) -> dict[str, Any]:
        def percentile(values: list[float], quantile: float) -> float:
            index = max(0, min(len(values) - 1, int((len(values) * quantile + 0.999999)) - 1))
            return values[index]

        rows: list[dict[str, Any]] = []
        for label in sorted(self._latencies):
            values = sorted(self._latencies[label])
            if not values:
                continue
            rows.append({
                "label": label,
                "count": len(values),
                "min_ms": values[0],
                "p95_ms": percentile(values, 0.95),
                "p99_ms": percentile(values, 0.99),
                "max_ms": values[-1],
            })
        return {"schema": "reaper.latency-profile.v1", "scope": "local_memory", "series": rows}

    def latency_reset(self) -> int:
        count = sum(len(values) for values in self._latencies.values())
        self._latencies.clear()
        return count

    @staticmethod
    def local_only_check(enabled: Any, effects: Any, imports: Any) -> dict[str, Any]:
        if not isinstance(enabled, bool):
            raise SystemFunctionError("local_only flag must be boolean")
        effect_items = _list(effects, "declared effects")
        import_items = _list(imports, "declared imports")
        denied_prefixes = (
            "network", "http", "https", "socket", "tcp", "udp", "dns",
            "web", "remote", "cloud", "grpc", "quic", "ws", "wss",
        )
        violations: list[str] = []
        if enabled:
            for category, items in (("effect", effect_items), ("import", import_items)):
                for raw in items:
                    if not isinstance(raw, str):
                        raise SystemFunctionError(f"{category} declarations must be text")
                    normalized = raw.strip().lower()
                    denied = normalized.startswith("net.") or any(
                        normalized == prefix
                        or normalized.startswith(prefix + ".")
                        or normalized.startswith(prefix + ":")
                        or normalized.startswith(prefix + "/")
                        for prefix in denied_prefixes
                    )
                    if denied:
                        violations.append(f"{category}:{raw}")
        return {"ok": not violations, "local_only": enabled, "violations": violations}

    def rollback_plan_check(self, migration: Any, rollback: Any, fixtures: Any) -> dict[str, Any]:
        cases = _list(fixtures, "rollback fixtures")
        failures: list[str] = []
        for index, raw in enumerate(cases):
            fixture = _mapping(raw, f"fixtures[{index}]")
            before = _json_copy(fixture.get("before"))
            expected = fixture.get("expected_after", None)
            after = self._invoke(migration, [copy.deepcopy(before)], "rollback_plan")
            after = _json_copy(after)
            if "expected_after" in fixture and after != _json_copy(expected):
                failures.append(f"fixture {index}: migration output differs from expected_after")
                continue
            restored = self._invoke(rollback, [copy.deepcopy(after)], "rollback_plan")
            if _json_copy(restored) != before:
                failures.append(f"fixture {index}: rollback did not restore the original state")
        return {
            "ok": not failures,
            "fixture_count": len(cases),
            "failures": failures,
            "phase": "pre_deployment_validation",
        }
