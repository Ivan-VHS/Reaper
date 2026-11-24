import unittest
from pathlib import Path
from unittest.mock import patch
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


    def test_plugin_enablement_issues_and_revokes_scoped_capability(self):
        from reaper.capabilities import CapabilityAuthority
        authority = CapabilityAuthority()
        manager = PluginManager(enabled=["Dropaul"], authority=authority)
        self.assertEqual(authority.active_count, 1)
        self.assertTrue(manager.is_enabled("Dropaul"))
        self.assertFalse(manager.set_enabled("Dropaul", False))
        self.assertEqual(authority.active_count, 0)
        with self.assertRaisesRegex(PluginError, "disabled"):
            manager.run("Dropaul", steps=[])
        self.assertTrue(manager.set_enabled("Dropaul", True))
        self.assertEqual(authority.active_count, 1)
        manager.close()
        self.assertEqual(authority.active_count, 0)
        authority.close()

    def test_external_revocation_fails_closed(self):
        from reaper.capabilities import CapabilityAuthority
        authority = CapabilityAuthority()
        manager = PluginManager(enabled=["Dropaul"], authority=authority)
        self.assertEqual(authority.revoke_all(), 1)
        with self.assertRaisesRegex(PluginError, "capability grant"):
            manager.run("Dropaul", steps=[])
        self.assertFalse(manager.is_enabled("Dropaul"))
        manager.close()
        authority.close()

    def test_plugin_scope_does_not_authorize_another_plugin(self):
        from reaper.capabilities import CapabilityAuthority, CapabilityDenied
        authority = CapabilityAuthority()
        manager = PluginManager(enabled=["Dropaul"], authority=authority)
        token = manager._grants["dropaul"]
        with self.assertRaises(CapabilityDenied):
            authority.verify(
                token,
                principal="reaper-plugin:dropaul",
                resource="plugins/professiya",
                action="invoke",
            )
        manager.close()
        authority.close()

    def test_kali_dispatches_to_unified_java_reaper_bav(self):
        report = {"schema": "bav.security.report.v1", "verdict": "clear"}
        manager = PluginManager(enabled=["Kali"])
        try:
            with patch("reaper.bav.scan", return_value=report) as bav_scan:
                result = manager.run("Kali", path=Path.cwd())
            self.assertEqual(result, report)
            bav_scan.assert_called_once_with(Path.cwd().resolve())
        finally:
            manager.close()

    def test_unknown_plugin_is_rejected(self):
        with self.assertRaisesRegex(PluginError, "unknown"):
            PluginManager().get_plugin("NotAPlugin")

if __name__ == "__main__":
    unittest.main()
