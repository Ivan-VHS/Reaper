import json
import tempfile
import unittest
from pathlib import Path

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

    def test_manifest_discovery_is_metadata_only_and_execution_requires_trust(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "hello-world"
            package.mkdir()
            (package / "plugin.json").write_text(json.dumps({
                "schema": "ivan-vhs.plugin.v1",
                "id": "hello-world",
                "name": "Hello World",
                "version": "1.2.0",
                "api_version": 1,
                "host": {"id": "reaper"},
                "domain": "examples",
                "description": "Test extension package.",
                "capabilities": ["commands"],
                "entrypoint": "plugin.py:create_plugin",
            }), encoding="utf-8")
            (package / "plugin.py").write_text(
                """class Extension:
    def __init__(self, api): self.api = api
    def on_load(self, context): self.api.log('loaded')
    def run(self, operation, arguments):
        return {'host': self.api.context.host_id, 'value': arguments.get('value')}
    def on_event(self, event, payload): return {'event': event, **payload}
    def on_unload(self, context): pass
def create_plugin(api): return Extension(api)
""",
                encoding="utf-8",
            )

            manager = PluginManager(plugin_dirs=[temporary])
            spec = manager.get_plugin("hello-world")
            self.assertEqual(spec.source, "external")
            self.assertFalse(manager.is_enabled("hello-world"))
            self.assertFalse(manager.is_loaded("hello-world"))
            self.assertTrue(Path(spec.manifest_path).is_file())

            manager.set_enabled("hello-world", True)
            with self.assertRaisesRegex(PluginError, "trusted=True"):
                manager.load("hello-world")
            with self.assertRaisesRegex(PluginError, "not loaded"):
                manager.run("hello-world", value=7)

            manager.load("hello-world", trusted=True)
            self.assertTrue(manager.is_loaded("hello-world"))
            self.assertEqual(manager.run("hello-world", value=7),
                             {"host": "reaper", "value": 7})
            self.assertEqual(manager.emit("project_saved", {"project": "demo"}),
                             {"hello-world": {"event": "project_saved", "project": "demo"}})
            manager.unload("hello-world")
            self.assertFalse(manager.is_loaded("hello-world"))

    def test_manifest_rejects_unsupported_api_and_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "bad"
            package.mkdir()
            base = {
                "schema": "ivan-vhs.plugin.v1", "id": "bad-extension",
                "name": "Bad Extension", "version": "1.0.0", "api_version": 99,
                "host": {"id": "reaper"}, "domain": "test", "description": "bad",
                "capabilities": [], "entrypoint": "../escape.py:create_plugin",
            }
            (package / "plugin.json").write_text(json.dumps(base), encoding="utf-8")
            manager = PluginManager(plugin_dirs=[temporary])
            self.assertGreaterEqual(len(manager.discovery_errors), 1)
            with self.assertRaisesRegex(PluginError, "unknown"):
                manager.get_plugin("bad-extension")


if __name__ == "__main__":
    unittest.main()
