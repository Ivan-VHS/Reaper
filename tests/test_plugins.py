import unittest
from reaper.plugins import (
    PluginError, PluginExecutionPolicy, PluginManager, list_plugins,
)
from reaper.products import PRODUCTS

class PluginHostTests(unittest.TestCase):
    def test_all_products_are_registered(self):
        plugins = list_plugins()
        self.assertEqual(len(plugins), 18)
        self.assertEqual({p["name"] for p in plugins}, {p.name for p in PRODUCTS})
        self.assertEqual(len({p["plugin_id"] for p in plugins}), 18)
        self.assertTrue(all(p["enabled"] for p in plugins))

    def test_names_and_ids_resolve(self):
        manager = PluginManager()
        self.assertEqual(manager.get_plugin("Dropaul"), manager.get_plugin("dropaul"))
        self.assertEqual(manager.get_plugin("keel-koh").name, "Keel Koh")

    def test_enable_disable_blocks_dispatch(self):
        manager = PluginManager()
        self.assertFalse(manager.set_enabled("Dropaul", False))
        with self.assertRaisesRegex(PluginError, "disabled"):
            manager.run("Dropaul", steps=[])
        self.assertTrue(manager.set_enabled("Dropaul", True))

    def test_dropaul_dispatches_to_safe_service(self):
        result = PluginManager().run("Dropaul", steps=[
            {"id": "compile", "depends_on": []},
            {"id": "test", "depends_on": ["compile"]},
        ])
        self.assertEqual(result["execution_order"], ["compile", "test"])
        self.assertTrue(result["dry_run"])

    def test_unknown_plugin_is_rejected(self):
        with self.assertRaisesRegex(PluginError, "unknown"):
            PluginManager().get_plugin("NotAPlugin")

    def test_plugin_policy_bounds_inputs_outputs_and_configuration(self):
        with self.assertRaises(PluginError):
            PluginExecutionPolicy(max_concurrent_per_plugin=True)
        limited_input = PluginManager(policy=PluginExecutionPolicy(max_input_bytes=8))
        with self.assertRaisesRegex(PluginError, "input exceeds"):
            limited_input.run("Dropaul", steps=[{"id": "a", "depends_on": []}])

        limited_output = PluginManager(policy=PluginExecutionPolicy(max_output_bytes=8))
        with self.assertRaisesRegex(PluginError, "output exceeds"):
            limited_output.run("Dropaul", steps=[])

    def test_plugin_health_reports_readiness_and_execution_metrics(self):
        manager = PluginManager()
        result = manager.run("Dropaul", steps=[
            {"id": "compile", "depends_on": []},
            {"id": "test", "depends_on": ["compile"]},
        ])
        self.assertTrue(result["dry_run"])
        health = manager.health()
        self.assertEqual(health["schema"], "reaper.plugin-health.v1")
        self.assertTrue(health["ready"])
        self.assertEqual(health["plugins"]["dropaul"]["invocations"], 1)
        self.assertEqual(health["plugins"]["dropaul"]["successes"], 1)
        self.assertEqual(health["plugins"]["dropaul"]["in_flight"], 0)

    def test_plugin_concurrency_is_bounded_per_plugin(self):
        manager = PluginManager(policy=PluginExecutionPolicy(max_concurrent_per_plugin=1))
        semaphore = manager._semaphores["dropaul"]
        self.assertTrue(semaphore.acquire(blocking=False))
        try:
            with self.assertRaisesRegex(PluginError, "concurrency limit"):
                manager.run("Dropaul", steps=[])
        finally:
            semaphore.release()

if __name__ == "__main__":
    unittest.main()
