"""Resolve task dependencies into a deterministic topological execution plan."""
from __future__ import annotations

import heapq
from typing import Any

from .common import ApplicationInputError, require_array, require_object, require_text


def run(payload: dict[str, Any]) -> dict[str, Any]:
    raw_tasks = require_array(payload, "tasks")
    tasks: dict[str, list[str]] = {}
    for index, item in enumerate(raw_tasks):
        task = require_object(item, f"tasks[{index}]")
        task_id = require_text(task.get("id"), f"tasks[{index}].id")
        if task_id in tasks:
            raise ApplicationInputError(f"duplicate_task_id: {task_id}")
        raw_deps = task.get("deps", [])
        if not isinstance(raw_deps, list):
            raise ApplicationInputError(f"tasks[{index}].deps must be an array")
        deps = [require_text(dep, f"tasks[{index}].deps[]") for dep in raw_deps]
        if len(set(deps)) != len(deps):
            raise ApplicationInputError(f"tasks[{index}].deps contains duplicates")
        tasks[task_id] = deps

    for task_id, deps in tasks.items():
        missing = sorted(set(deps) - tasks.keys())
        if missing:
            raise ApplicationInputError(f"task {task_id} depends on unknown task(s): {', '.join(missing)}")

    indegree = {task_id: len(deps) for task_id, deps in tasks.items()}
    dependents: dict[str, list[str]] = {task_id: [] for task_id in tasks}
    for task_id, deps in tasks.items():
        for dep in deps:
            dependents[dep].append(task_id)
    ready = [task_id for task_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[str] = []
    levels: list[list[str]] = []
    completed: set[str] = set()

    while ready:
        current_level = sorted(ready)
        ready = []
        levels.append(current_level)
        for task_id in current_level:
            order.append(task_id)
            completed.add(task_id)
        for task_id in current_level:
            for dependent in sorted(dependents[task_id]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heapq.heappush(ready, dependent)

    if len(order) != len(tasks):
        cycle_nodes = sorted(set(tasks) - completed)
        raise ApplicationInputError("dependency_cycle: " + ", ".join(cycle_nodes))

    return {
        "order": order,
        "parallel_levels": levels,
        "task_count": len(tasks),
        "execution_performed": False,
    }
