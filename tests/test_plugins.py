import unittest
from reaper.plugins import PluginError, PluginManager, list_plugins
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

if __name__ == "__main__":
    unittest.main()
