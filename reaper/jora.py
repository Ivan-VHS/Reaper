"""Jora: deterministic composition of Reaper-first application projects.

The first increment generates reproducible project scaffolds and localization
bundles from a closed catalogue of capability contracts. It never claims that
specification-only packs are executable applications.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REQUEST_SCHEMA = "reaper.jora.request.v1"
APPLICATION_SCHEMA = "reaper.jora.application.v1"
MAX_REQUEST_BYTES = 1_048_576
MAX_COMPONENTS = 24
MAX_LOCALES = 8
MAX_OUTPUT_FILES = 64
MAX_GRAPH_VARIANTS = 6
GRAPH_TOPOLOGIES = (
    "layered", "pipeline", "hub_spoke", "plugin_mesh", "event_driven", "hybrid",
)
GRAPH_LABELS = {
    "layered": "Layered Composition",
    "pipeline": "Sequential Workflow",
    "hub_spoke": "Shared Orchestrator",
    "plugin_mesh": "Capability Mesh",
    "event_driven": "Event-Driven",
    "hybrid": "Hybrid Composition",
}
DOMAIN_LABELS = {
    "documents": "Documents",
    "media": "Audio",
    "language": "Languages",
}

LOCALES: dict[str, dict[str, str]] = {
    "en": {
        "language_name": "English",
        "app_title": "Application workspace",
        "app_description": "A combined workspace generated from selected capability packs.",
        "status": "Project scaffold generated; feature adapters require implementation.",
        "compose": "Compose application",
        "export": "Export build request",
        "modules": "Included modules",
        "pending": "Specification only",
    },
    "ru": {
        "language_name": "Русский",
        "app_title": "Рабочее пространство приложения",
        "app_description": "Объединённое приложение, собранное из выбранных функциональных модулей.",
        "status": "Каркас проекта создан; функциональные адаптеры требуют реализации.",
        "compose": "Собрать приложение",
        "export": "Экспортировать запрос сборки",
        "modules": "Подключённые модули",
        "pending": "Только спецификация",
    },
    "uk": {
        "language_name": "Українська",
        "app_title": "Робочий простір застосунку",
        "app_description": "Об’єднаний застосунок, зібраний із вибраних функціональних модулів.",
        "status": "Каркас проєкту створено; функціональні адаптери потребують реалізації.",
        "compose": "Скомпонувати застосунок",
        "export": "Експортувати запит збірки",
        "modules": "Підключені модулі",
        "pending": "Лише специфікація",
    },
    "most": {
        "language_name": "MOST · русский языковой профиль",
        "app_title": "Рабочее пространство приложения",
        "app_description": "Объединённое приложение, собранное из выбранных функциональных модулей.",
        "status": "Каркас проекта создан; функциональные адаптеры требуют реализации.",
        "compose": "Собрать приложение",
        "export": "Экспортировать запрос сборки",
        "modules": "Подключённые модули",
        "pending": "Только спецификация",
    },
}

# First-party capability contracts. These records are not executable plugins.
_COMPONENTS: dict[str, dict[str, Any]] = {
    "text.editor": {
        "name": "Text Editor",
        "domain": "documents",
        "version": "1.0.0",
        "summary": "Structured text editing, search, formatting and document history.",
        "provides": ["text.document", "text.search", "text.formatting", "text.history"],
        "consumes": [],
        "requires": ["document.model", "storage.local", "localization.catalog"],
        "conflicts": [],
        "maturity": "specification_only",
    },
    "audio.editor": {
        "name": "Audio Editor",
        "domain": "media",
        "version": "1.0.0",
        "summary": "Audio asset organisation, timeline editing and non-destructive operations.",
        "provides": ["audio.asset", "audio.timeline", "audio.editing"],
        "consumes": [],
        "requires": ["media.model", "timeline.model", "storage.local"],
        "conflicts": [],
        "maturity": "specification_only",
    },
    "translation.workspace": {
        "name": "Translator",
        "domain": "language",
        "version": "1.0.0",
        "summary": "Translation workspace, terminology, parallel text and locale review.",
        "provides": ["translation.workspace", "translation.terminology", "translation.review"],
        "consumes": ["text.document"],
        "requires": ["document.model", "localization.catalog", "translation.provider"],
        "conflicts": [],
        "maturity": "specification_only",
    },
}

_DEPENDENCIES: dict[str, dict[str, Any]] = {
    "document.model": {"version": "1.0.0", "maturity": "contract_only", "requires": []},
    "media.model": {"version": "1.0.0", "maturity": "contract_only", "requires": []},
    "timeline.model": {"version": "1.0.0", "maturity": "contract_only", "requires": ["media.model"]},
    "storage.local": {"version": "1.0.0", "maturity": "host_adapter_required", "requires": []},
    "localization.catalog": {"version": "1.0.0", "maturity": "generated", "requires": []},
    "translation.provider": {"version": "1.0.0", "maturity": "provider_required", "requires": []},
}

_LOCALE_ALIASES = {
    "en": "en", "en-us": "en", "ru": "ru", "ru-ru": "ru",
    "uk": "uk", "uk-ua": "uk", "ua": "uk", "most": "most",
}
_LANGUAGE_TARGETS = {
    "reaper": "Reaper",
    "java": "Java",
    "kotlin": "Kotlin",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
    "c": "C",
}
_NAME_RE = re.compile(r"^[A-Za-z0-9\u0400-\u04ff\u4e00-\u9fff][A-Za-z0-9\u0400-\u04ff\u4e00-\u9fff ._-]{0,79}$")


class JoraError(ValueError):
    """Invalid Jora request, composition or build operation."""


def _text(value: Any, field: str, maximum: int, *, optional: bool = False) -> str:
    if value is None and optional:
        return ""
    if not isinstance(value, str):
        raise JoraError(f"{field} must be text")
    value = value.strip()
    if not value and not optional:
        raise JoraError(f"{field} must not be empty")
    if len(value) > maximum:
        raise JoraError(f"{field} exceeds {maximum} characters")
    return value


def _normalize_locales(value: Any) -> list[str]:
    if value is None or value == "auto":
        return ["en", "ru", "uk", "most"]
    if not isinstance(value, list) or not value or len(value) > MAX_LOCALES:
        raise JoraError(f"locales must be a non-empty list of at most {MAX_LOCALES} values")
    result: list[str] = []
    for raw in value:
        code = _text(raw, "locale", 16).casefold()
        normalized = _LOCALE_ALIASES.get(code)
        if normalized is None:
            raise JoraError(f"unsupported locale {raw!r}; available: {', '.join(LOCALES)}")
        if normalized in result:
            raise JoraError(f"duplicate locale: {normalized}")
        result.append(normalized)
    return result


def _normalize_components(value: Any) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > MAX_COMPONENTS:
        raise JoraError(f"components must be a non-empty list of at most {MAX_COMPONENTS} ids")
    result: list[str] = []
    for raw in value:
        identifier = _text(raw, "component id", 80).casefold()
        if identifier not in _COMPONENTS:
            raise JoraError(f"unknown component {identifier!r}; available: {', '.join(_COMPONENTS)}")
        if identifier in result:
            raise JoraError(f"duplicate component: {identifier}")
        result.append(identifier)
    return result


def _resolve_dependencies(component_ids: list[str]) -> list[str]:
    """Return a stable dependency-first order and reject cycles or unknown edges."""
    ordered: list[str] = []
    active: set[str] = set()
    complete: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in complete:
            return
        if identifier in active:
            raise JoraError(f"dependency cycle detected at {identifier}")
        active.add(identifier)
        if identifier in _COMPONENTS:
            dependencies = _COMPONENTS[identifier]["requires"]
        elif identifier in _DEPENDENCIES:
            dependencies = _DEPENDENCIES[identifier]["requires"]
        else:
            raise JoraError(f"dependency is not registered: {identifier}")
        for dependency in dependencies:
            visit(dependency)
        active.remove(identifier)
        complete.add(identifier)
        ordered.append(identifier)

    for component_id in component_ids:
        visit(component_id)
    return ordered


def _normalize_graph_options(value: Any) -> dict[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise JoraError("graph must be an object")
    allowed = {"topology", "seed", "variants", "variation"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise JoraError("unknown graph fields: " + ", ".join(unknown))
    topology = _text(value.get("topology", "auto"), "graph.topology", 32).casefold()
    if topology != "auto" and topology not in GRAPH_TOPOLOGIES:
        raise JoraError(
            "unsupported graph topology; choose auto or: " + ", ".join(GRAPH_TOPOLOGIES)
        )
    seed = _text(value.get("seed", ""), "graph.seed", 64, optional=True)
    variants = value.get("variants", 3)
    variation = value.get("variation", 50)
    if isinstance(variants, bool) or not isinstance(variants, int) or not 1 <= variants <= MAX_GRAPH_VARIANTS:
        raise JoraError(f"graph.variants must be an integer from 1 to {MAX_GRAPH_VARIANTS}")
    if isinstance(variation, bool) or not isinstance(variation, int) or not 0 <= variation <= 100:
        raise JoraError("graph.variation must be an integer from 0 to 100")
    return {
        "topology": topology,
        "seed": seed,
        "variants": variants,
        "variation": variation,
    }


def _naming_profile(component_ids: list[str], style: str) -> dict[str, Any]:
    domains = sorted(
        {_COMPONENTS[item]["domain"] for item in component_ids},
        key=lambda item: ({"documents": 0, "media": 1, "language": 2}.get(item, 99), item),
    )
    descriptors = [DOMAIN_LABELS.get(domain, domain.replace("_", " ").title()) for domain in domains]
    if not descriptors:
        descriptors = ["Workspace"]
    joined = " · ".join(descriptors)
    plus_joined = " + ".join(descriptors)
    natural = " & ".join(descriptors)
    suggestions = [
        {"id": "jora.compact", "label": f"Jora · {joined}", "style": "compact"},
        {"id": "jora.balanced", "label": f"Jora — {natural} Workspace", "style": "balanced"},
        {"id": "jora.descriptive", "label": f"Jora | Workspace for {natural}", "style": "descriptive"},
        {"id": "jora.formula", "label": f"Jora — {plus_joined}", "style": "formula"},
    ]
    preferred = next((item for item in suggestions if item["style"] == style), None)
    if preferred is None:
        preferred = suggestions[1]
    return {
        "version": "jora-naming.v2",
        "brand": "Jora",
        "canonical_name": "Jora",
        "style": style,
        "descriptors": descriptors,
        "selected": preferred,
        "suggestions": suggestions,
        "rule": "All suggestions retain Jora as the only product name; suffixes describe the selected capability composition and are not independent brands.",
    }


def _build_graph_variant(
    component_ids: list[str],
    dependency_order: list[str],
    locales: list[str],
    topology: str,
    seed: str,
    variation: int,
    variant_index: int,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    def add_node(node_id: str, kind: str, label: str, maturity: str = "contract") -> None:
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        nodes.append({"id": node_id, "kind": kind, "label": label, "maturity": maturity})

    def add_edge(source: str, target: str, relation: str, *, async_edge: bool = False) -> None:
        if source not in node_ids or target not in node_ids:
            raise JoraError(f"graph edge references an unknown node: {source} -> {target}")
        record = {"from": source, "to": target, "relation": relation}
        if async_edge:
            record["delivery"] = "asynchronous"
        if record not in edges:
            edges.append(record)

    add_node("app:jora", "application", "Jora", "scaffold")
    add_node("ui:shell", "interface", "Jora Interface", "planned")
    add_node("runtime:reaper", "runtime", "Reaper Runtime", "available")
    for locale in locales:
        add_node("locale:" + locale, "locale", locale.upper(), "generated")
    for component_id in component_ids:
        spec = _COMPONENTS[component_id]
        add_node(
            "component:" + component_id,
            "component",
            str(spec["name"]),
            str(spec["maturity"]),
        )
    for dependency_id in dependency_order:
        if dependency_id in _DEPENDENCIES:
            spec = _DEPENDENCIES[dependency_id]
            add_node(
                "service:" + dependency_id,
                "service",
                dependency_id,
                str(spec["maturity"]),
            )

    add_edge("app:jora", "runtime:reaper", "executes_on")
    add_edge("app:jora", "ui:shell", "exposes")
    for locale in locales:
        add_edge("ui:shell", "locale:" + locale, "localizes_with")
    for component_id in component_ids:
        component_node = "component:" + component_id
        for dependency in _COMPONENTS[component_id]["requires"]:
            if dependency in _DEPENDENCIES:
                add_edge(component_node, "service:" + dependency, "requires")
    for dependency_id in dependency_order:
        if dependency_id not in _DEPENDENCIES:
            continue
        for dependency in _DEPENDENCIES[dependency_id]["requires"]:
            if dependency in _DEPENDENCIES:
                add_edge("service:" + dependency_id, "service:" + dependency, "requires")

    if topology == "layered":
        if variant_index % 2 == 0:
            for component_id in component_ids:
                add_edge("ui:shell", "component:" + component_id, "mounts")
        else:
            domain_nodes: dict[str, str] = {}
            for component_id in component_ids:
                domain = str(_COMPONENTS[component_id]["domain"])
                layer_id = "layer:" + domain
                if domain not in domain_nodes:
                    domain_nodes[domain] = layer_id
                    add_node(layer_id, "domain_layer", domain.title() + " Layer", "planned")
                    add_edge("ui:shell", layer_id, "contains_layer")
                add_edge(layer_id, "component:" + component_id, "mounts")
    elif topology == "pipeline":
        if component_ids:
            add_edge("ui:shell", "component:" + component_ids[0], "starts_workflow")
        for left, right in zip(component_ids, component_ids[1:]):
            add_edge("component:" + left, "component:" + right, "workflow_next")
        if variant_index % 3 == 1:
            add_node("workflow:state", "workflow_state", "Jora Workflow State", "planned")
            for component_id in component_ids:
                add_edge("component:" + component_id, "workflow:state", "updates_workflow_state")
        elif variant_index % 3 == 2:
            for index, component_id in enumerate(component_ids):
                validator_id = "workflow:validator:" + component_id.replace(".", "_")
                add_node(validator_id, "workflow_validator", "Jora Validator · " + component_id, "planned")
                add_edge("component:" + component_id, validator_id, "validates_output")
                if index + 1 < len(component_ids):
                    add_edge(validator_id, "component:" + component_ids[index + 1], "releases_stage")
    elif topology == "hub_spoke":
        if variant_index % 2 == 0:
            add_node("orchestrator:jora", "orchestrator", "Jora Orchestrator", "planned")
            add_edge("ui:shell", "orchestrator:jora", "dispatches_to")
            for component_id in component_ids:
                add_edge("orchestrator:jora", "component:" + component_id, "routes_to")
        else:
            domain_hubs: dict[str, str] = {}
            for component_id in component_ids:
                domain = str(_COMPONENTS[component_id]["domain"])
                hub_id = "orchestrator:" + domain
                if domain not in domain_hubs:
                    domain_hubs[domain] = hub_id
                    add_node(hub_id, "domain_orchestrator", domain.title() + " Coordinator", "planned")
                    add_edge("ui:shell", hub_id, "dispatches_to")
                add_edge(hub_id, "component:" + component_id, "routes_to")
    elif topology == "plugin_mesh":
        for component_id in component_ids:
            add_edge("ui:shell", "component:" + component_id, "mounts")
        matches: list[tuple[str, str, str]] = []
        for consumer_id in component_ids:
            consumed = set(_COMPONENTS[consumer_id].get("consumes", []))
            for provider_id in component_ids:
                if provider_id == consumer_id:
                    continue
                for capability in sorted(consumed & set(_COMPONENTS[provider_id]["provides"])):
                    matches.append((provider_id, consumer_id, capability))
        if variant_index % 3 == 0:
            for provider_id, consumer_id, capability in matches:
                add_edge(
                    "component:" + provider_id,
                    "component:" + consumer_id,
                    "capability:" + capability,
                )
        elif variant_index % 3 == 1 and matches:
            add_node("capability:broker", "capability_broker", "Jora Capability Broker", "planned")
            for provider_id, consumer_id, capability in matches:
                add_edge("component:" + provider_id, "capability:broker", "provides_to_broker:" + capability)
                add_edge("capability:broker", "component:" + consumer_id, "routes_to_consumer:" + capability)
        else:
            brokers: dict[str, str] = {}
            for provider_id, consumer_id, capability in matches:
                broker_id = "capability:" + capability.replace(".", "_")
                if capability not in brokers:
                    brokers[capability] = broker_id
                    add_node(broker_id, "capability_channel", capability + " Channel", "planned")
                add_edge("component:" + provider_id, broker_id, "publishes_capability")
                add_edge(broker_id, "component:" + consumer_id, "consumes_capability")
    elif topology == "event_driven":
        if variant_index % 2 == 0:
            add_node("events:jora", "event_bus", "Jora Event Bus", "planned")
            add_edge("ui:shell", "events:jora", "dispatches_events")
            for component_id in component_ids:
                component_node = "component:" + component_id
                add_edge(component_node, "events:jora", "publishes", async_edge=True)
                add_edge("events:jora", component_node, "subscribes", async_edge=True)
        else:
            domain_buses: dict[str, str] = {}
            for component_id in component_ids:
                domain = str(_COMPONENTS[component_id]["domain"])
                bus_id = "events:" + domain
                if domain not in domain_buses:
                    domain_buses[domain] = bus_id
                    add_node(bus_id, "event_channel", domain.title() + " Event Channel", "planned")
                    add_edge("ui:shell", bus_id, "dispatches_events")
                component_node = "component:" + component_id
                add_edge(component_node, bus_id, "publishes", async_edge=True)
                add_edge(bus_id, component_node, "subscribes", async_edge=True)
    elif topology == "hybrid":
        if variant_index % 2 == 0:
            add_node("orchestrator:jora", "orchestrator", "Jora Orchestrator", "planned")
            add_edge("ui:shell", "orchestrator:jora", "dispatches_to")
            for component_id in component_ids:
                add_edge("orchestrator:jora", "component:" + component_id, "routes_to")
        else:
            domain_hubs: dict[str, str] = {}
            for component_id in component_ids:
                domain = str(_COMPONENTS[component_id]["domain"])
                hub_id = "orchestrator:" + domain
                if domain not in domain_hubs:
                    domain_hubs[domain] = hub_id
                    add_node(hub_id, "domain_orchestrator", domain.title() + " Coordinator", "planned")
                    add_edge("ui:shell", hub_id, "dispatches_to")
                add_edge(hub_id, "component:" + component_id, "routes_to")
        for consumer_id in component_ids:
            consumed = set(_COMPONENTS[consumer_id].get("consumes", []))
            for provider_id in component_ids:
                if provider_id == consumer_id:
                    continue
                for capability in sorted(consumed & set(_COMPONENTS[provider_id]["provides"])):
                    add_edge(
                        "component:" + provider_id,
                        "component:" + consumer_id,
                        "capability:" + capability,
                    )

    layout_modes = (
        "direct", "domain_grouped", "capability_routed",
        "stateful", "validated", "extensible",
    )
    layout_variant = layout_modes[variant_index % len(layout_modes)]
    if layout_variant == "domain_grouped":
        grouped: dict[str, str] = {}
        for component_id in component_ids:
            domain = str(_COMPONENTS[component_id]["domain"])
            group_id = "layout:domain:" + domain
            if domain not in grouped:
                grouped[domain] = group_id
                add_node(group_id, "layout_group", domain.title() + " Group", "planned")
                add_edge("ui:shell", group_id, "groups_domain")
            add_edge(group_id, "component:" + component_id, "contains_component")
    elif layout_variant == "capability_routed":
        add_node("layout:capability-router", "capability_router", "Jora Capability Router", "planned")
        add_edge("ui:shell", "layout:capability-router", "routes_capabilities")
        for component_id in component_ids:
            add_edge("layout:capability-router", "component:" + component_id, "routes_module")
    elif layout_variant == "stateful":
        add_node("layout:workflow-context", "workflow_context", "Jora Shared Workflow Context", "planned")
        for component_id in component_ids:
            add_edge("component:" + component_id, "layout:workflow-context", "contributes_context")
    elif layout_variant == "validated":
        add_node("layout:validation-gate", "validation_gate", "Jora Composition Validation", "planned")
        add_edge("app:jora", "layout:validation-gate", "validates_graph")
        add_edge("layout:validation-gate", "ui:shell", "approves_graph")
    elif layout_variant == "extensible":
        add_node("layout:extension-registry", "extension_registry", "Jora Extension Registry", "planned")
        add_edge("ui:shell", "layout:extension-registry", "discovers_extensions")
        for component_id in component_ids:
            add_edge("layout:extension-registry", "component:" + component_id, "registers_module")

    # Deterministic optional architecture augmentations create real graph variety
    # without pretending that these planned contracts are already executable.
    roll = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % 100
    if variation and roll < variation:
        add_node("extension:jora", "extension_registry", "Jora Extension Registry", "planned")
        add_edge("ui:shell", "extension:jora", "discovers_extensions")
        for component_id in component_ids:
            add_edge("extension:jora", "component:" + component_id, "registers")
    gate_roll = int(hashlib.sha256((seed + ":gate").encode("utf-8")).hexdigest()[:8], 16) % 100
    if variation >= 50 and gate_roll < variation:
        add_node("gate:jora", "validation_gate", "Jora Compatibility Gate", "planned")
        add_edge("app:jora", "gate:jora", "validates_composition")
        add_edge("gate:jora", "ui:shell", "approves_layout")

    # Every synchronous control/data edge must be acyclic. Event-mediated feedback
    # loops are explicit asynchronous edges and are excluded from startup ordering.
    dependency_graph: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        if edge.get("delivery") != "asynchronous":
            dependency_graph[edge["from"]].append(edge["to"])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise JoraError(f"generated graph contains a dependency cycle at {node_id}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for target in dependency_graph[node_id]:
            visit(target)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(dependency_graph):
        visit(node_id)

    canonical_graph = {
        "topology": topology,
        "seed": seed,
        "variation": variation,
        "layout_variant": layout_variant,
        "nodes": nodes,
        "edges": edges,
    }
    signature = hashlib.sha256(
        json.dumps(canonical_graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    dependency_edges = sum(edge["relation"] == "requires" for edge in edges)
    capability_edges = sum("capability" in edge["relation"] for edge in edges)
    planned_nodes = sum(node["maturity"] == "planned" for node in nodes)
    return {
        "id": "jora-graph-" + signature,
        "label": "Jora · " + GRAPH_LABELS[topology] + " · " + layout_variant,
        "topology": topology,
        "layout_variant": layout_variant,
        "seed": seed,
        "variation": variation,
        "signature": signature,
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "dependency_edges": dependency_edges,
            "capability_connections": capability_edges,
            "planned_nodes": planned_nodes,
            "compatibility_score": max(0, 100 - planned_nodes * 3),
        },
        "cycle_policy": {
            "synchronous_edges": "acyclic",
            "event_feedback": "asynchronous and mediated by the Jora event bus"
            if topology == "event_driven" else "not used",
        },
    }


def _build_graph_variants(
    component_ids: list[str],
    dependency_order: list[str],
    locales: list[str],
    options: dict[str, Any],
    fallback_seed: str,
) -> dict[str, Any]:
    base_seed = options["seed"] or fallback_seed[:24]
    if options["topology"] == "auto":
        start = int(hashlib.sha256(base_seed.encode("utf-8")).hexdigest()[:8], 16) % len(GRAPH_TOPOLOGIES)
        topologies = [
            GRAPH_TOPOLOGIES[(start + index) % len(GRAPH_TOPOLOGIES)]
            for index in range(options["variants"])
        ]
    else:
        topologies = [options["topology"]] * options["variants"]
    variants = []
    for index, topology in enumerate(topologies):
        variant_seed = f"{base_seed}:{index}:{topology}"
        variants.append(_build_graph_variant(
            component_ids, dependency_order, locales, topology, variant_seed,
            options["variation"], index,
        ))
    return {
        "schema": "reaper.jora.graph-set.v1",
        "selected": variants[0]["id"],
        "topology_mode": options["topology"],
        "seed": base_seed,
        "variant_count": len(variants),
        "variants": variants,
    }


def _generated_name() -> str:
    """Every application composed by this unified product is named Jora."""
    return "Jora"


def _safe_slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.casefold()).strip("-")
    return normalized or "jora-app"


def list_components() -> list[dict[str, Any]]:
    """Return the public catalogue as detached records."""
    return [{"id": identifier, **copy.deepcopy(spec)} for identifier, spec in _COMPONENTS.items()]


def compose_application(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise JoraError("request must be a JSON object")
    if request.get("schema", REQUEST_SCHEMA) != REQUEST_SCHEMA:
        raise JoraError(f"expected request schema {REQUEST_SCHEMA}")

    allowed = {
        "schema", "name", "description", "components", "locales",
        "preferred_locale", "syntax_mode", "language_targets", "name_style", "graph",
    }
    unknown = sorted(set(request) - allowed)
    if unknown:
        raise JoraError("unknown request fields: " + ", ".join(unknown))

    component_ids = _normalize_components(request.get("components"))
    locales = _normalize_locales(request.get("locales", "auto"))
    preferred = _text(request.get("preferred_locale", locales[0]), "preferred_locale", 16).casefold()
    preferred = _LOCALE_ALIASES.get(preferred, preferred)
    if preferred not in locales:
        raise JoraError("preferred_locale must be included in locales")

    syntax_mode = _text(request.get("syntax_mode", "flow"), "syntax_mode", 32).casefold()
    if syntax_mode != "flow":
        raise JoraError("the current generated Reaper source supports only the 'flow' syntax profile")

    requested_name = _text(request.get("name", "Jora"), "name", 80, optional=True)
    if requested_name and requested_name != "Jora":
        raise JoraError("Jora is the fixed application name; component formulas do not create separately named products")
    display_name = _generated_name()
    name_style = _text(request.get("name_style", "balanced"), "name_style", 24).casefold()
    if name_style not in {"compact", "balanced", "descriptive", "formula"}:
        raise JoraError("name_style must be compact, balanced, descriptive or formula")
    naming = _naming_profile(component_ids, name_style)
    description = _text(request.get("description", ""), "description", 500, optional=True)
    graph_options = _normalize_graph_options(request.get("graph"))

    raw_targets = request.get("language_targets", "auto")
    if raw_targets == "auto":
        target_ids = ["reaper"]
    elif isinstance(raw_targets, list) and raw_targets:
        target_ids = []
        for raw in raw_targets:
            target_id = _text(raw, "language target", 32).casefold()
            if target_id not in _LANGUAGE_TARGETS:
                raise JoraError(f"unknown language target: {target_id}")
            if target_id in target_ids:
                raise JoraError(f"duplicate language target: {target_id}")
            target_ids.append(target_id)
        if "reaper" not in target_ids:
            target_ids.insert(0, "reaper")
    else:
        raise JoraError("language_targets must be 'auto' or a non-empty list")

    dependency_order = _resolve_dependencies(component_ids)
    selected = set(component_ids)
    for component_id in component_ids:
        conflicts = sorted(set(_COMPONENTS[component_id]["conflicts"]) & selected)
        if conflicts:
            raise JoraError(f"{component_id} conflicts with: {', '.join(conflicts)}")

    canonical = {
        "components": component_ids,
        "locales": locales,
        "preferred_locale": preferred,
        "syntax_mode": syntax_mode,
        "name": display_name,
        "language_targets": target_ids,
        "name_style": name_style,
        "graph": graph_options,
    }
    digest = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    application_id = _safe_slug(display_name)[:48] + "-" + digest

    components = []
    for component_id in component_ids:
        spec = _COMPONENTS[component_id]
        components.append({
            "id": component_id,
            "name": spec["name"],
            "version": spec["version"],
            "domain": spec["domain"],
            "summary": spec["summary"],
            "provides": list(spec["provides"]),
            "consumes": list(spec.get("consumes", [])),
            "requires": list(spec["requires"]),
            "maturity": spec["maturity"],
            "generated_unit": "src/components/" + component_id.replace(".", "_") + ".rpr",
        })

    dependencies = []
    for dependency_id in dependency_order:
        if dependency_id in _DEPENDENCIES:
            spec = _DEPENDENCIES[dependency_id]
            dependencies.append({
                "id": dependency_id,
                "version": spec["version"],
                "maturity": spec["maturity"],
                "requires": list(spec["requires"]),
            })

    graphs = _build_graph_variants(
        component_ids,
        dependency_order,
        locales,
        graph_options,
        hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8")).hexdigest(),
    )

    language_targets = []
    for target_id in target_ids:
        generated = target_id == "reaper"
        language_targets.append({
            "id": target_id,
            "language": _LANGUAGE_TARGETS[target_id],
            "status": "generated" if generated else "adapter_pending",
            "reason": (
                "Canonical Reaper source is generated from the validated application request."
                if generated else
                "No Jora code-generation backend is integrated for this target."
            ),
        })

    return {
        "schema": APPLICATION_SCHEMA,
        "version": 1,
        "id": application_id,
        "name": display_name,
        "naming": naming,
        "graphs": graphs,
        "description": description or " + ".join(_COMPONENTS[item]["name"] for item in component_ids),
        "formula": {
            "expression": " + ".join(_COMPONENTS[item]["name"] for item in component_ids) + " = Jora",
            "result": "Jora",
            "components": component_ids,
        },
        "components": components,
        "dependency_order": dependency_order,
        "dependencies": dependencies,
        "locales": locales,
        "preferred_locale": preferred,
        "syntax": {"mode": syntax_mode, "status": "implemented"},
        "implementation": {
            "canonical_language": "reaper",
            "targets": language_targets,
            "runtime": "reaper-reference",
            "maturity": "scaffold_only",
        },
        "installable": False,
        "executable_capabilities": [],
        "limitations": [
            "Component packs are versioned specifications; their feature implementations are not yet bundled.",
            "The generated Reaper entry point is a project scaffold, not a completed editor or translation engine.",
            "Additional programming-language targets remain adapter_pending until a tested backend is delivered.",
            "Jora does not install, execute, or grant permissions to generated projects.",
        ],
    }


def _write_text(root: Path, relative_path: str, content: str) -> None:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise JoraError(f"refusing to write through a symbolic link: {relative_path}")
    target.write_text(content, encoding="utf-8", newline="\n")


def _validate_generated_sources(root: Path) -> dict[str, Any]:
    """Parse and statically type-check every generated Reaper source file."""
    from .parser import parse
    from .typecheck import TypeChecker

    checked_files = 0
    warnings = 0
    for source_path in sorted(root.rglob("*.rpr")):
        source = source_path.read_text(encoding="utf-8")
        try:
            tree = parse(source, str(source_path))
            result = TypeChecker(str(source_path)).check(tree)
        except Exception as error:
            raise JoraError(
                f"generated Reaper source could not be parsed or checked: {error}"
            ) from error
        errors = [item for item in result.diagnostics if item.severity == "error"]
        if errors:
            details = "; ".join(
                f"{item.code}: {item.message}" for item in errors[:5]
            )
            raise JoraError(f"generated Reaper source failed static validation: {details}")
        warnings += sum(item.severity == "warning" for item in result.diagnostics)
        checked_files += 1
    if checked_files == 0:
        raise JoraError("Jora did not generate any Reaper source files")
    return {
        "status": "passed",
        "mode": "static-typecheck",
        "files_checked": checked_files,
        "warnings": warnings,
    }


def _mermaid_node_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", value)
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return "node_" + safe[:40] + "_" + suffix


def _render_mermaid_graph(graph: dict[str, Any]) -> str:
    """Render a graph variant as a deterministic Mermaid flowchart."""
    lines = [
        "flowchart LR",
        f'  %% {graph["label"]} · {graph["signature"]}',
    ]
    for node in graph["nodes"]:
        label = str(node["label"]).replace('"', "'").replace("\n", " ")
        maturity = str(node["maturity"]).replace('"', "'")
        lines.append(
            f'  {_mermaid_node_id(node["id"])}["{label} · {maturity}"]'
        )
    for edge in graph["edges"]:
        relation = re.sub(r"[^A-Za-z0-9 _:-]", "", str(edge["relation"])).strip()
        if edge.get("delivery") == "asynchronous":
            relation += " · async"
        lines.append(
            f'  {_mermaid_node_id(edge["from"])} -->|{relation}| '
            f'{_mermaid_node_id(edge["to"])}'
        )
    return "\n".join(lines) + "\n"


def build_application(request: dict[str, Any], output: str | Path) -> dict[str, Any]:
    application = compose_application(request)
    raw_output = Path(output).expanduser()
    if raw_output.name in {"", ".", ".."}:
        raise JoraError("output must name a new project directory")
    if raw_output.is_symlink():
        raise JoraError("output directory must not be a symbolic link")
    parent = raw_output.parent.resolve()
    if not parent.is_dir():
        raise JoraError("output parent directory must already exist")
    destination = parent / raw_output.name
    if destination.exists() or destination.is_symlink():
        raise JoraError("output path already exists; choose a new directory (Jora never overwrites projects)")

    staging = Path(tempfile.mkdtemp(prefix=".jora-build-", dir=parent))
    try:
        component_names = [item["name"] for item in application["components"]]
        main_source = (
            f'emit "Jora application: {application["name"]}"\n'
            f'emit "Composed from: {application["formula"]["expression"]}"\n'
            'emit "Scaffold only: capability packs require implementation."\n'
        )
        _write_text(staging, "src/main.rpr", main_source)

        for component in application["components"]:
            source_name = component["id"].replace(".", "_") + ".rpr"
            component_source = (
                f'emit "Jora component contract: {component["id"]}"\n'
                f'emit "Maturity: {component["maturity"]}"\n'
            )
            _write_text(staging, "src/components/" + source_name, component_source)

        for locale in application["locales"]:
            locale_payload = {
                "schema": "reaper.jora.locale.v1",
                "locale": locale,
                **LOCALES[locale],
                "app_name": application["name"],
                "component_names": component_names,
            }
            encoded = json.dumps(locale_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            _write_text(staging, "locales/" + locale + ".json", encoded)

        _write_text(
            staging,
            "jora.app.json",
            json.dumps(application, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        _write_text(
            staging,
            "jora.graphs.json",
            json.dumps(application["graphs"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        for index, graph in enumerate(application["graphs"]["variants"], start=1):
            diagram_path = f"graphs/variant-{index:02d}.mmd"
            _write_text(staging, diagram_path, _render_mermaid_graph(graph))
        lock = {
            "schema": "reaper.jora.lock.v1",
            "application_id": application["id"],
            "component_versions": {item["id"]: item["version"] for item in application["components"]},
            "dependency_versions": {item["id"]: item["version"] for item in application["dependencies"]},
            "dependency_order": application["dependency_order"],
            "naming_version": application["naming"]["version"],
            "name_style": application["naming"]["style"],
            "naming_label": application["naming"]["selected"]["label"],
            "graph_set": application["graphs"]["schema"],
            "selected_graph": application["graphs"]["selected"],
            "graph_signatures": [item["signature"] for item in application["graphs"]["variants"]],
            "generator": "Reaper Jora 2.0",
        }
        _write_text(staging, "jora.lock.json", json.dumps(lock, ensure_ascii=False, indent=2) + "\n")

        readme = (
            f"# {application['name']}\n\n"
            f"Jora formula: {application['formula']['expression']}\n\n"
            f"{application['description']}\n\n"
            "## Project contents\n\n"
            "- src/main.rpr: Reaper entry-point scaffold.\n"
            "- src/components/: one contract stub per selected component.\n"
            "- locales/: generated EN/RU/UK/MOST interface dictionaries.\n"
            "- jora.app.json: versioned application manifest.\n"
            "- jora.lock.json: resolved component, dependency, naming and graph versions.\n"
            "- jora.graphs.json: reproducible graph variants, nodes, typed edges and compatibility metrics.\n"
            "- graphs/variant-*.mmd: readable Mermaid diagrams for each graph alternative.\n\n"
            "## Maturity\n\n"
            "This directory is a reproducible scaffold, not an installable application. "
            "The selected feature packs are specification-only. Storage, translation and "
            "audio host adapters need separate implementations. No source was executed.\n"
        )
        _write_text(staging, "README.md", readme)

        validation = _validate_generated_sources(staging)
        files = sorted(
            str(path.relative_to(staging)).replace("\\", "/")
            for path in staging.rglob("*")
            if path.is_file()
        )
        if len(files) > MAX_OUTPUT_FILES:
            raise JoraError(f"generated output exceeds {MAX_OUTPUT_FILES} files")
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return {
        "schema": "reaper.jora.build-result.v1",
        "ok": True,
        "status": "scaffold_generated",
        "application_id": application["id"],
        "name": application["name"],
        "output": str(destination),
        "files": files,
        "validation": validation,
        "installable": False,
        "source_executed": False,
    }


def _read_request(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise JoraError("request must be an existing regular JSON file, not a symbolic link")
    if path.stat().st_size > MAX_REQUEST_BYTES:
        raise JoraError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise JoraError(f"cannot read request JSON: {error}") from error
    if not isinstance(payload, dict):
        raise JoraError("request JSON must contain an object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reaper jora", description="Compose Reaper-first application projects.")
    commands = parser.add_subparsers(dest="command", required=True)

    catalog = commands.add_parser("catalog", help="list registered application capability packs")
    catalog.add_argument("--json", action="store_true")

    compose = commands.add_parser("compose", help="resolve a request into an application specification")
    compose.add_argument("--request", type=Path, required=True)
    compose.add_argument("--json", action="store_true")

    build = commands.add_parser("build", help="generate a Reaper project scaffold")
    build.add_argument("--request", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            result: Any = {"schema": "reaper.jora.component-catalog.v1", "components": list_components()}
        else:
            request = _read_request(args.request)
            result = compose_application(request) if args.command == "compose" else build_application(request, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (JoraError, OSError, TypeError, ValueError) as error:
        print(f"Jora: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
