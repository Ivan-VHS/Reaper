from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.jora import (
    APPLICATION_NAME_POLICY, JoraError, REQUEST_SCHEMA, build_application, compose_application, list_components,
)


class JoraCompositionTests(unittest.TestCase):
    def request(self, **changes):
        value = {
            "schema": REQUEST_SCHEMA,
            "application_name_policy": APPLICATION_NAME_POLICY,
            "components": ["text.editor", "audio.editor", "translation.workspace"],
            "locales": ["en", "ru", "uk", "most"],
            "preferred_locale": "ru",
        }
        value.update(changes)
        return value

    def test_example_formula_and_dependency_closure(self):
        result = compose_application(self.request())
        self.assertEqual(result["formula"]["expression"], "Text Editor + Audio Editor + Translator → Documents, Media & Languages Workspace")
        self.assertEqual(result["formula"]["result"], "Documents, Media & Languages Workspace")
        self.assertEqual(result["name"], "Documents, Media & Languages Workspace")
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

    def test_single_component_gets_an_independent_default_name(self):
        result = compose_application(self.request(components=["text.editor"]))
        self.assertEqual(result["name"], "Documents Workspace")

    def test_application_names_are_independent_and_platform_name_is_rejected(self):
        legacy_request = self.request()
        legacy_request.pop("application_name_policy")
        self.assertEqual(compose_application(legacy_request)["naming"]["product_name_policy"], APPLICATION_NAME_POLICY)
        self.assertEqual(compose_application(self.request(name="Sonaris"))["name"], "Sonaris")
        with self.assertRaisesRegex(JoraError, "must not contain the platform name"):
            compose_application(self.request(name="Jora Audio"))
        with self.assertRaisesRegex(JoraError, "must not contain the platform name"):
            compose_application(self.request(name="Jora"))
        with self.assertRaisesRegex(JoraError, "must not contain the platform name"):
            compose_application(self.request(name="myjOrAapp"))
        with self.assertRaisesRegex(JoraError, "must not contain the platform name"):
            compose_application(self.request(name="ＪＯＲＡ Suite"))
        with self.assertRaisesRegex(JoraError, "application_name_policy"):
            compose_application(self.request(application_name_policy="allow_platform_brand"))

    def test_naming_variants_are_independent_product_descriptors(self):
        result = compose_application(self.request(name_style="balanced"))
        naming = result["naming"]
        self.assertEqual(naming["platform"], "Jora")
        self.assertEqual(naming["product_name_policy"], APPLICATION_NAME_POLICY)
        self.assertEqual(naming["version"], "jora-naming.v2")
        self.assertEqual(naming["selected"]["style"], "balanced")
        self.assertEqual(naming["selected"]["label"], "Documents, Media & Languages Workspace")
        compact = compose_application(self.request(name_style="compact"))
        self.assertEqual(compact["naming"]["selected"]["label"], "Docs / Audio / Translate Workspace")
        descriptive = compose_application(self.request(name_style="descriptive"))
        self.assertEqual(descriptive["naming"]["selected"]["label"], "Workspace for writing, audio editing & translation")
        self.assertGreaterEqual(len(naming["suggestions"]), 3)
        self.assertTrue(all("Jora" not in item["label"] for item in naming["suggestions"]))
        self.assertIn("Media", naming["descriptors"])

    def test_graph_variants_are_distinct_deterministic_and_well_formed(self):
        first = compose_application(self.request(graph={"topology": "auto", "seed": "demo", "variants": 4, "variation": 65}))
        second = compose_application(self.request(graph={"topology": "auto", "seed": "demo", "variants": 4, "variation": 65}))
        changed = compose_application(self.request(graph={"topology": "auto", "seed": "other", "variants": 4, "variation": 65}))
        graphs = first["graphs"]["variants"]
        selected = next(item for item in graphs if item["id"] == first["graphs"]["selected"])
        self.assertEqual(first["graphs"]["selection_policy"], "max_objective_score_then_compatibility_then_minimal_planned_nodes")
        self.assertEqual(selected["metrics"]["objective_score"], max(item["metrics"]["objective_score"] for item in graphs))
        self.assertEqual([item["signature"] for item in graphs],
                         [item["signature"] for item in second["graphs"]["variants"]])
        self.assertEqual(len({item["signature"] for item in graphs}), 4)
        self.assertNotEqual(first["graphs"]["variants"][0]["signature"],
                            changed["graphs"]["variants"][0]["signature"])
        for graph in graphs:
            node_ids = {node["id"] for node in graph["nodes"]}
            self.assertEqual(len(node_ids), len(graph["nodes"]))
            self.assertTrue(all(edge["from"] in node_ids and edge["to"] in node_ids for edge in graph["edges"]))
            self.assertGreaterEqual(graph["metrics"]["compatibility_score"], 0)

    def test_same_topology_variants_use_distinct_graph_rewrites(self):
        result = compose_application(self.request(
            graph={"topology": "pipeline", "seed": "repeatable", "variants": 6, "variation": 0}
        ))
        graphs = result["graphs"]["variants"]
        self.assertEqual(
            [item["layout_variant"] for item in graphs],
            ["direct", "domain_grouped", "capability_routed", "stateful", "validated", "extensible"],
        )
        node_sets = {tuple(sorted(node["id"] for node in item["nodes"])) for item in graphs}
        self.assertEqual(len(node_sets), 6)

    def test_plugin_mesh_connects_only_compatible_capabilities(self):
        result = compose_application(self.request(graph={"topology": "plugin_mesh", "variants": 1, "variation": 0}))
        edges = result["graphs"]["variants"][0]["edges"]
        self.assertIn({
            "from": "component:text.editor",
            "to": "component:translation.workspace",
            "relation": "capability:text.document",
        }, edges)
        self.assertFalse(any(
            edge["relation"].startswith("capability:")
            and edge["from"] == "component:audio.editor"
            for edge in edges
        ))

    def test_graph_objectives_expose_distinct_architecture_metrics(self):
        objectives = ["balanced", "low_latency", "modularity", "extensibility", "minimal_complexity"]
        for objective in objectives:
            result = compose_application(self.request(
                graph={"topology": "auto", "seed": "objective-test", "variants": 4, "variation": 75, "objective": objective}
            ))
            self.assertEqual(result["graphs"]["objective"], objective)
            for graph in result["graphs"]["variants"]:
                self.assertEqual(graph["objective"], objective)
                metrics = graph["metrics"]
                for metric in ("objective_score", "latency_score", "modularity_score",
                               "extensibility_score", "complexity_score", "longest_sync_path"):
                    self.assertIn(metric, metrics)
                    self.assertGreaterEqual(metrics[metric], 0)
            selected = next(item for item in result["graphs"]["variants"]
                            if item["id"] == result["graphs"]["selected"])
            self.assertEqual(selected["metrics"]["objective_score"],
                             max(item["metrics"]["objective_score"] for item in result["graphs"]["variants"]))

    def test_event_graph_marks_feedback_edges_as_async(self):
        result = compose_application(self.request(graph={"topology": "event_driven", "variants": 1, "variation": 0}))
        graph = result["graphs"]["variants"][0]
        self.assertEqual(graph["topology"], "event_driven")
        self.assertEqual(graph["cycle_policy"]["synchronous_edges"], "acyclic")
        self.assertIn("asynchronous", graph["cycle_policy"]["event_feedback"])
        self.assertTrue(any(edge.get("delivery") == "asynchronous" for edge in graph["edges"]))

    def test_pipeline_graph_respects_component_formula_order(self):
        result = compose_application(self.request(graph={"topology": "pipeline", "variants": 1, "variation": 0}))
        edges = result["graphs"]["variants"][0]["edges"]
        self.assertIn({
            "from": "component:text.editor",
            "to": "component:audio.editor",
            "relation": "workflow_next",
        }, edges)
        self.assertIn({
            "from": "component:audio.editor",
            "to": "component:translation.workspace",
            "relation": "workflow_next",
        }, edges)

    def test_invalid_graph_options_are_rejected(self):
        with self.assertRaisesRegex(JoraError, "unsupported graph topology"):
            compose_application(self.request(graph={"topology": "random_mesh"}))
        with self.assertRaisesRegex(JoraError, "graph.variants"):
            compose_application(self.request(graph={"variants": True}))
        with self.assertRaisesRegex(JoraError, "unknown graph fields"):
            compose_application(self.request(graph={"topology": "auto", "shell_command": "no"}))

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
            output = Path(directory) / "Sonaris"
            result = build_application(self.request(), output)
            self.assertTrue(result["ok"])
            self.assertFalse(result["installable"])
            self.assertFalse(result["source_executed"])
            self.assertEqual(result["validation"]["status"], "passed")
            self.assertEqual(result["validation"]["files_checked"], 4)
            self.assertTrue((output / "jora.graphs.json").is_file())
            graph_payload = json.loads((output / "jora.graphs.json").read_text(encoding="utf-8"))
            self.assertEqual(graph_payload["schema"], "reaper.jora.graph-set.v1")
            self.assertEqual(len(graph_payload["variants"]), 3)
            self.assertTrue((output / "graphs/variant-01.mmd").is_file())
            diagram = (output / "graphs/variant-01.mmd").read_text(encoding="utf-8")
            self.assertTrue(diagram.startswith("flowchart LR"))
            self.assertTrue((output / "src/main.rpr").is_file())
            self.assertTrue((output / "src/components/text_editor.rpr").is_file())
            self.assertTrue((output / "locales/en.json").is_file())
            self.assertTrue((output / "locales/most.json").is_file())
            manifest = json.loads((output / "jora.app.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["id"], result["application_id"])
            self.assertFalse(manifest["installable"])
            self.assertEqual(manifest["name"], "Documents, Media & Languages Workspace")
            self.assertEqual(manifest["naming"]["platform"], "Jora")
            self.assertNotIn("Jora", manifest["name"])
            lock = json.loads((output / "jora.lock.json").read_text(encoding="utf-8"))
            self.assertEqual(lock["name_style"], manifest["naming"]["style"])
            self.assertEqual(lock["naming_label"], manifest["naming"]["selected"]["label"])
            self.assertEqual(lock["graph_objective"], manifest["graphs"]["objective"])
            self.assertEqual(lock["selected_graph"], manifest["graphs"]["selected"])
            self.assertEqual(lock["selected_graph_score"], next(item["metrics"]["objective_score"] for item in manifest["graphs"]["variants"] if item["id"] == lock["selected_graph"]))
            self.assertEqual(lock["graph_signatures"], [item["signature"] for item in manifest["graphs"]["variants"]])

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
        legacy_ids = {
            "text.editor", "audio.editor", "translation.workspace",
            "subtitle.editor", "notes.workspace", "task.board", "calendar.scheduler",
            "speech.synthesis", "speech.recognition", "code.editor", "spreadsheet.editor",
            "image.editor", "video.editor", "presentation.editor", "file.manager",
            "api.client", "automation.engine", "data.visualizer", "database.manager",
            "archive.manager", "knowledge.graph",
        }
        harvest_ids = {
            "harvest.voxtrace", "harvest.cycleforge", "harvest.chronos",
            "harvest.lexigraph", "harvest.clashgraph", "harvest.resurgence",
            "harvest.culturefield", "harvest.narrativeforge", "harvest.factseal",
            "harvest.beatforge", "harvest.flowmetric", "harvest.rhymecore",
            "harvest.albumarch", "harvest.scenemap", "harvest.legacygraph",
            "harvest.engine",
        }
        self.assertEqual(len(items), 37)
        self.assertEqual({item["id"] for item in items}, legacy_ids | harvest_ids)


    def test_catalog_contains_sixteen_harvest_framework_contracts(self):
        items = [item for item in list_components() if item["id"].startswith("harvest.")]
        self.assertEqual(len(items), 16)
        self.assertTrue(all(item["source_status"] == "authored_unverified" for item in items))
        self.assertTrue(all(item["source_module"].endswith(".rpr") for item in items))
        self.assertTrue(all(item["input_schema"] and item["ir_schema"] and item["output_schema"] for item in items))

    def test_harvest_engine_resolves_every_framework_dependency(self):
        result = compose_application(self.request(components=["harvest.engine"]))
        bundle = result["source_bundle"]
        self.assertEqual(bundle["schema"], "harvest.jora.source-bundle.v1")
        self.assertEqual(bundle["status"], "authored_unverified")
        self.assertEqual(len(bundle["framework_ids"]), 16)
        self.assertEqual(bundle["framework_ids"][-1], "harvest.engine")
        self.assertIn("harvest.runtime", result["dependency_order"])
        self.assertIn("harvest.voxtrace", result["dependency_order"])
        self.assertIn("harvest.legacygraph", result["dependency_order"])
        self.assertEqual(result["implementation"]["canonical_language"], "reaper")
        self.assertFalse(result["installable"])

    def test_harvest_build_bundles_real_reaper_sources_and_schemas(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chronicle"
            result = build_application(self.request(
                components=["harvest.engine"],
                name="Chronicle Atlas",
            ), output)
            manifest = json.loads((output / "jora.app.json").read_text(encoding="utf-8"))
            main_source = (output / "src" / "main.rpr").read_text(encoding="utf-8")
            self.assertTrue((output / "src/harvest/core/storage.rpr").is_file())
            self.assertTrue((output / "src/harvest/frameworks/harvest_engine.rpr").is_file())
            self.assertTrue((output / "src/harvest/frameworks/voxtrace.rpr").is_file())
            self.assertTrue((output / "src/harvest/schemas/engine.ir.v1.schema.json").is_file())
            self.assertTrue((output / "src/harvest/registry/harvest.registry.v1.json").is_file())
            self.assertIn('import "harvest/core/jora_adapter.rpr" as harvest_app', main_source)
            self.assertIn('import "harvest/frameworks/harvest_engine.rpr" as harvest_harvest_engine', main_source)
            self.assertIn('make framework_ids := ["harvest.engine"]', main_source)
            self.assertEqual(manifest["source_bundle"]["status"], "authored_unverified")
            self.assertEqual(manifest["source_bundle"]["files_copied"], result["source_bundle"]["files_copied"])
            self.assertFalse(result["installable"])
            self.assertFalse(result["source_executed"])
            self.assertGreater(result["validation"]["files_checked"], 16)

    def test_catalog_contains_twenty_one_canonical_capability_packs(self):
        items = [item for item in list_components() if not item["id"].startswith("harvest.")]
        self.assertEqual(len(items), 21)
        ids = {item["id"] for item in items}
        self.assertTrue({
            "subtitle.editor", "notes.workspace", "task.board", "calendar.scheduler",
            "speech.synthesis", "speech.recognition", "code.editor", "spreadsheet.editor",
            "image.editor", "video.editor", "presentation.editor", "file.manager",
            "api.client", "automation.engine", "data.visualizer", "database.manager",
            "archive.manager", "knowledge.graph",
        }.issubset(ids))

    def test_thirteen_component_formula_uses_clustered_graph_and_auto_languages(self):
        component_ids = [
            "text.editor", "audio.editor", "translation.workspace", "subtitle.editor",
            "notes.workspace", "task.board", "calendar.scheduler", "speech.synthesis",
            "speech.recognition", "code.editor", "spreadsheet.editor", "image.editor",
            "video.editor",
        ]
        result = compose_application(self.request(
            components=component_ids,
            language_targets="auto",
            graph={"topology": "plugin_mesh", "variants": 3, "variation": 0},
        ))
        self.assertEqual(len(result["components"]), 13)
        self.assertTrue(all(graph["growth_policy"]["clustered"] for graph in result["graphs"]["variants"]))
        self.assertTrue(all(graph["clusters"] for graph in result["graphs"]["variants"]))
        targets = result["implementation"]["targets"]
        self.assertEqual(targets[0]["id"], "reaper")
        self.assertIn("python", [item["id"] for item in targets])
        self.assertIn("rust", [item["id"] for item in targets])
        self.assertTrue(all(item["status"] in {"generated", "adapter_pending"} for item in targets))
        self.assertTrue(all(graph["metrics"]["node_count"] <= 128 for graph in result["graphs"]["variants"]))
        self.assertTrue(all(graph["metrics"]["edge_count"] <= 512 for graph in result["graphs"]["variants"]))

    def test_all_twenty_one_components_compose_with_bounded_graph_budget(self):
        component_ids = [item["id"] for item in list_components() if not item["id"].startswith("harvest.")]
        result = compose_application(self.request(
            components=component_ids,
            language_targets="auto",
            graph={"topology": "hybrid", "variants": 2, "variation": 0},
        ))
        self.assertEqual(len(result["components"]), 21)
        self.assertLessEqual(len(result["name"]), 80)
        self.assertTrue(all(len(item["label"]) <= 80 for item in result["naming"]["suggestions"]))
        self.assertTrue(all("jora" not in item["label"].casefold() for item in result["naming"]["suggestions"]))
        self.assertTrue(all(graph["growth_policy"]["clustered"] for graph in result["graphs"]["variants"]))
        self.assertTrue(all(graph["metrics"]["node_count"] <= 128 for graph in result["graphs"]["variants"]))
        self.assertTrue(all(graph["metrics"]["edge_count"] <= 512 for graph in result["graphs"]["variants"]))


    def test_plugin_mesh_keeps_component_capability_edges_acyclic(self):
        component_ids = [
            "text.editor", "audio.editor", "translation.workspace", "subtitle.editor",
            "notes.workspace", "task.board", "calendar.scheduler", "speech.synthesis",
            "speech.recognition", "code.editor", "spreadsheet.editor", "image.editor",
            "video.editor",
        ]
        result = compose_application(self.request(
            components=component_ids,
            language_targets="auto",
            graph={"topology": "plugin_mesh", "variants": 1, "variation": 0},
        ))
        graph = result["graphs"]["variants"][0]
        adjacency = {}
        for edge in graph["edges"]:
            source = str(edge.get("source", edge.get("from", "")))
            target = str(edge.get("target", edge.get("to", "")))
            if source.startswith("component:") and target.startswith("component:"):
                adjacency.setdefault(source, []).append(target)
        self.assertTrue(adjacency, "the plugin-mesh graph should contain component capability edges")
        visiting = set()
        visited = set()

        def visit(node):
            if node in visiting:
                return False
            if node in visited:
                return True
            visiting.add(node)
            for target in adjacency.get(node, []):
                if not visit(target):
                    return False
            visiting.remove(node)
            visited.add(node)
            return True

        self.assertTrue(all(visit(node) for node in adjacency))


if __name__ == "__main__":
    unittest.main()
