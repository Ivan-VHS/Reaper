"""Declarative CPU-workload hints for DuckOS gaming sessions.

The adapter describes relative task roles. It never creates threads, changes
OS priorities, pins CPUs, changes timers or calls a host scheduler.
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "reaper.gaming-task-plan.v1"
INPUT_SCHEMA = "duckos.gaming-session-profile.v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ROLES = {
    "main": {"weight": 5, "deadline_class": "frame_cycle", "migratable": False},
    "render": {"weight": 5, "deadline_class": "frame_cycle", "migratable": False},
    "audio": {"weight": 4, "deadline_class": "audio_period", "migratable": False},
    "worker": {"weight": 3, "deadline_class": "throughput", "migratable": True},
    "background": {"weight": 1, "deadline_class": "deferred", "migratable": True},
}
MAX_WORKERS = 64


class GamingTaskPlanError(ValueError):
    """Raised when an untrusted gaming profile cannot be represented safely."""


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise GamingTaskPlanError(f"{field} must be a safe identifier")
    return value


def _worker_count(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_WORKERS:
        raise GamingTaskPlanError(f"worker_count must be between 1 and {MAX_WORKERS}")
    return value


def build_gaming_task_plan(profile: dict[str, Any]) -> dict[str, Any]:
    """Validate a DuckOS session profile and return advisory thread-role hints."""
    if not isinstance(profile, dict) or profile.get("schema") != INPUT_SCHEMA:
        raise GamingTaskPlanError(f"expected a {INPUT_SCHEMA} object")
    game_id = _identifier(profile.get("game_id"), "game_id")
    engine = _identifier(profile.get("engine", "unknown"), "engine")
    worker_count = _worker_count(profile.get("worker_count", 4))
    multithreaded = profile.get("multithreaded", True)
    audio_enabled = profile.get("audio_enabled", True)
    if not isinstance(multithreaded, bool) or not isinstance(audio_enabled, bool):
        raise GamingTaskPlanError("multithreaded and audio_enabled must be booleans")

    tasks = []
    for role, settings in ROLES.items():
        if role == "audio" and not audio_enabled:
            continue
        if role == "worker" and not multithreaded:
            continue
        count = worker_count if role == "worker" else 1
        tasks.append({
            "role": role,
            "count": count,
            "relative_weight": settings["weight"],
            "deadline_class": settings["deadline_class"],
            "migratable": settings["migratable"],
        })

    return {
        "schema": SCHEMA,
        "game_id": game_id,
        "engine": engine,
        "tasks": tasks,
        "scheduler_hints": {
            "protect_frame_cycle": True,
            "protect_audio_period": audio_enabled,
            "reduce_unnecessary_migration": True,
            "respect_cpu_topology_when_reported": True,
            "never_assign_affinity_without_host_policy": True,
        },
        "source_rules": ["GPR-13", "GPR-14", "GPR-15", "GPR-16", "GPR-21", "GPR-22", "GPR-23", "GPR-24"],
        "host_application": {
            "process_created": False,
            "os_priority_changed": False,
            "cpu_affinity_assigned": False,
            "timer_resolution_changed": False,
            "requires_trusted_host_executor": True,
        },
        "execution_performed": False,
    }


def validate_gaming_task_plan(plan: dict[str, Any]) -> bool:
    """Check the generated plan's bounded, declarative execution invariants."""
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        raise GamingTaskPlanError(f"expected a {SCHEMA} object")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks or len(tasks) > len(ROLES):
        raise GamingTaskPlanError("tasks must contain between 1 and 5 role entries")
    seen: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict) or task.get("role") not in ROLES:
            raise GamingTaskPlanError("task contains an unknown role")
        if task["role"] in seen:
            raise GamingTaskPlanError("task roles must be unique")
        seen.add(task["role"])
        expected = ROLES[task["role"]]
        if task.get("relative_weight") != expected["weight"]:
            raise GamingTaskPlanError("task weight differs from the bounded role policy")
        if task.get("deadline_class") != expected["deadline_class"]:
            raise GamingTaskPlanError("task deadline class differs from the role policy")
        if task.get("migratable") is not expected["migratable"]:
            raise GamingTaskPlanError("task migration hint differs from the role policy")
        count = task.get("count")
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_WORKERS:
            raise GamingTaskPlanError("task count is outside the configured bound")
    host = plan.get("host_application")
    required = {
        "process_created": False,
        "os_priority_changed": False,
        "cpu_affinity_assigned": False,
        "timer_resolution_changed": False,
        "requires_trusted_host_executor": True,
    }
    if host != required or plan.get("execution_performed") is not False:
        raise GamingTaskPlanError("host application must remain declarative and non-executing")
    return True
