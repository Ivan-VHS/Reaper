from __future__ import annotations

import copy
import unittest

from reaper.gaming_policy_contract import (
    GamingTaskPlanError,
    build_gaming_task_plan,
    validate_gaming_task_plan,
)


class GamingTaskPlanTests(unittest.TestCase):
    def profile(self):
        return {
            "schema": "duckos.gaming-session-profile.v1",
            "game_id": "sample-game",
            "engine": "directx12",
            "worker_count": 8,
            "multithreaded": True,
            "audio_enabled": True,
        }

    def test_builds_bounded_role_plan_without_host_side_effects(self):
        plan = build_gaming_task_plan(self.profile())
        self.assertTrue(validate_gaming_task_plan(plan))
        self.assertEqual([task["role"] for task in plan["tasks"]],
                         ["main", "render", "audio", "worker", "background"])
        self.assertEqual(plan["tasks"][3]["count"], 8)
        self.assertFalse(plan["host_application"]["process_created"])
        self.assertFalse(plan["host_application"]["cpu_affinity_assigned"])
        self.assertFalse(plan["execution_performed"])

    def test_respects_single_threaded_and_silent_profiles(self):
        profile = self.profile()
        profile.update(multithreaded=False, audio_enabled=False)
        plan = build_gaming_task_plan(profile)
        roles = {task["role"] for task in plan["tasks"]}
        self.assertNotIn("worker", roles)
        self.assertNotIn("audio", roles)

    def test_rejects_invalid_input_and_unbounded_workers(self):
        profile = self.profile()
        profile["worker_count"] = 100000
        with self.assertRaises(GamingTaskPlanError):
            build_gaming_task_plan(profile)
        profile = self.profile()
        profile["game_id"] = "../escape"
        with self.assertRaises(GamingTaskPlanError):
            build_gaming_task_plan(profile)

    def test_validator_rejects_attempt_to_turn_hints_into_execution(self):
        plan = build_gaming_task_plan(self.profile())
        unsafe = copy.deepcopy(plan)
        unsafe["host_application"]["os_priority_changed"] = True
        with self.assertRaises(GamingTaskPlanError):
            validate_gaming_task_plan(unsafe)

    def test_validator_rejects_duplicate_roles(self):
        plan = build_gaming_task_plan(self.profile())
        duplicate = copy.deepcopy(plan)
        duplicate["tasks"].append(copy.deepcopy(duplicate["tasks"][0]))
        with self.assertRaises(GamingTaskPlanError):
            validate_gaming_task_plan(duplicate)


if __name__ == "__main__":
    unittest.main()
