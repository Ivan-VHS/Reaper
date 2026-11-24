from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.jora import (
    JoraError, REQUEST_SCHEMA, build_application, compose_application, list_components,
)


class JoraCompositionTests(unittest.TestCase):
    def request(self, **changes):
        value = {
            "schema": REQUEST_SCHEMA,
            "components": ["text.editor", "audio.editor", "translation.workspace"],
            "locales": ["en", "ru", "uk", "most"],
            "preferred_locale": "ru",
        }
        value.update(changes)
        return value

    def test_example_formula_and_dependency_closure(self):
        result = compose_application(self.request())
        self.assertEqual(result["formula"]["expression"], "Text Editor + Audio Editor + Translator = Jora")
        self.assertEqual(result["formula"]["result"], "Jora")
        self.assertEqual(result["name"], "Jora")
        self.assertEqual(result["locales"], ["en", "ru", "uk", "most"])
        self.assertEqual(result["preferred_locale"], "ru")
        self.assertEqual(result["implementation"]["canonical_language"], "reaper")
        self.assertEqual(result["implementation"]["targets"][0]["status"], "generated")
        self.assertFalse(result["installable"])
        self.assertEqual(result["executable_capabilities"], [])
        self.assertLess(result["dependency_order"].index("media.model"),
                        result["dependency_order"].index("timeline.model"))
        self.assertIn("storage.local", result["dependency_order"])

    def test_composition_is_deterministic_and_order_sensitive(self):
        first = compose_application(self.request())
        second = compose_application(self.request())
        reverse = compose_application(self.request(
            components=["translation.workspace", "audio.editor", "text.editor"]
        ))
        self.assertEqual(first["id"], second["id"])
        self.assertNotEqual(first["id"], reverse["id"])

    def test_single_component_is_still_named_jora(self):
        result = compose_application(self.request(components=["text.editor"]))
        self.assertEqual(result["name"], "Jora")

    def test_component_combinations_never_create_separate_product_names(self):
        with self.assertRaisesRegex(JoraError, "fixed application name"):
            compose_application(self.request(name="LexiTone"))
        self.assertEqual(compose_application(self.request(name="Jora"))["name"], "Jora")

    def test_auto_locales_and_aliases(self):
        result = compose_application(self.request(locales="auto", preferred_locale="uk-UA"))
        self.assertEqual(result["locales"], ["en", "ru", "uk", "most"])
        self.assertEqual(result["preferred_locale"], "uk")

    def test_additional_language_target_is_never_misreported(self):
        result = compose_application(self.request(language_targets=["java", "kotlin"]))
        targets = result["implementation"]["targets"]
        self.assertEqual([item["id"] for item in targets], ["reaper", "java", "kotlin"])
        self.assertEqual([item["status"] for item in targets],
                         ["generated", "adapter_pending", "adapter_pending"])

    def test_unknown_duplicate_component_and_duplicate_locale_are_rejected(self):
        with self.assertRaisesRegex(JoraError, "unknown component"):
            compose_application(self.request(components=["text.editor", "game.engine"]))
        with self.assertRaisesRegex(JoraError, "duplicate component"):
            compose_application(self.request(components=["text.editor", "text.editor"]))
        with self.assertRaisesRegex(JoraError, "duplicate locale"):
            compose_application(self.request(locales=["ru", "ru"]))

    def test_unknown_fields_and_unsupported_syntax_are_rejected(self):
        with self.assertRaisesRegex(JoraError, "unknown request fields"):
            compose_application(self.request(shell_command="unexpected"))
        with self.assertRaisesRegex(JoraError, "only the 'flow'"):
            compose_application(self.request(syntax_mode="classic"))

    def test_build_writes_project_manifest_and_locales(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "Jora"
            result = build_application(self.request(), output)
            self.assertTrue(result["ok"])
            self.assertFalse(result["installable"])
            self.assertFalse(result["source_executed"])
            self.assertEqual(result["validation"]["status"], "passed")
            self.assertEqual(result["validation"]["files_checked"], 4)
            self.assertTrue((output / "src/main.rpr").is_file())
            self.assertTrue((output / "src/components/text_editor.rpr").is_file())
            self.assertTrue((output / "locales/en.json").is_file())
            self.assertTrue((output / "locales/most.json").is_file())
            manifest = json.loads((output / "jora.app.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["id"], result["application_id"])
            self.assertFalse(manifest["installable"])

    def test_existing_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(JoraError, "already exists"):
                build_application(self.request(), output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_symlink_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / "actual"
            actual.mkdir()
            link = root / "link"
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are unavailable")
            with self.assertRaisesRegex(JoraError, "symbolic link"):
                build_application(self.request(), link)

    def test_catalog_records_do_not_mutate_internal_component_contracts(self):
        items = list_components()
        items[0]["provides"].append("tampered.capability")
        refreshed = next(item for item in list_components() if item["id"] == "text.editor")
        self.assertNotIn("tampered.capability", refreshed["provides"])

    def test_catalog_is_closed_and_first_party(self):
        items = list_components()
        self.assertEqual({item["id"] for item in items},
                         {"text.editor", "audio.editor", "translation.workspace"})


if __name__ == "__main__":
    unittest.main()
