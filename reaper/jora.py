"""Jora: deterministic composition of Reaper-first application projects.

Jora generates reproducible Reaper projects from a closed catalogue of
capability contracts and may bundle explicitly versioned first-party source
packs. Bundled source is validated but never executed or installed.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

REQUEST_SCHEMA = "reaper.jora.request.v1"
APPLICATION_SCHEMA = "reaper.jora.application.v1"
APPLICATION_NAME_POLICY = "no_platform_brand_in_application_name"
MAX_REQUEST_BYTES = 1_048_576
MAX_COMPONENTS = 24
MAX_LOCALES = 8
MAX_OUTPUT_FILES = 160
MAX_GRAPH_VARIANTS = 6
MAX_GRAPH_NODES = 128
MAX_GRAPH_EDGES = 512
GRAPH_TOPOLOGIES = (
    "layered", "pipeline", "hub_spoke", "plugin_mesh", "event_driven", "hybrid",
)
GRAPH_OBJECTIVES = ("balanced", "low_latency", "modularity", "extensibility", "minimal_complexity")
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
    "productivity": "Productivity",
    "runtime": "Runtime",
    "audio": "Speech",
    "development": "Development",
    "data": "Data",
    "visual": "Visual",
    "video": "Video",
    "system": "System",
    "network": "Network",
    "automation": "Automation",
    "analytics": "Analytics",
    "knowledge": "Knowledge",
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
        "preferred_languages": ["python"],
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
        "preferred_languages": ["rust"],
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
        "preferred_languages": ["python"],
        "maturity": "specification_only",
    },
    "subtitle.editor": {
        "name": "Subtitle Editor", "domain": "language", "version": "1.0.0",
        "summary": "Timed subtitle authoring, validation and export.",
        "provides": ["subtitle.document", "subtitle.timing", "subtitle.export"],
        "consumes": ["text.document", "audio.timeline"],
        "requires": ["document.model", "timeline.model", "localization.catalog"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
    "notes.workspace": {
        "name": "Notes Workspace", "domain": "productivity", "version": "1.0.0",
        "summary": "Linked notes, tags, references and project annotations.",
        "provides": ["notes.collection", "notes.links", "notes.annotations"],
        "consumes": ["text.document"],
        "requires": ["document.model", "storage.local"],
        "conflicts": [], "preferred_languages": [], "maturity": "specification_only",
    },
    "task.board": {
        "name": "Task Board", "domain": "productivity", "version": "1.0.0",
        "summary": "Tasks, workflow states, priorities and project queues.",
        "provides": ["tasks.board", "tasks.workflow"],
        "consumes": ["calendar.events"],
        "requires": ["document.model", "storage.local"],
        "conflicts": [], "preferred_languages": [], "maturity": "specification_only",
    },
    "calendar.scheduler": {
        "name": "Calendar Scheduler", "domain": "productivity", "version": "1.0.0",
        "summary": "Calendar events, deadlines, schedules and reminders.",
        "provides": ["calendar.events", "scheduling.deadlines"],
        "consumes": [],
        "requires": ["time.model", "storage.local"],
        "conflicts": [], "preferred_languages": [], "maturity": "specification_only",
    },
    "speech.synthesis": {
        "name": "Speech Synthesis", "domain": "audio", "version": "1.0.0",
        "summary": "Text-to-speech jobs, voice profiles and speech assets.",
        "provides": ["speech.audio", "speech.voice"],
        "consumes": ["text.document", "translation.workspace"],
        "requires": ["media.model", "speech.provider"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
    "speech.recognition": {
        "name": "Speech Recognition", "domain": "audio", "version": "1.0.0",
        "summary": "Speech-to-text, transcription and speaker segmentation.",
        "provides": ["speech.transcription", "speech.diarization"],
        "consumes": ["audio.asset"],
        "requires": ["media.model", "speech.provider"],
        "conflicts": [], "preferred_languages": ["python", "rust"], "maturity": "specification_only",
    },
    "code.editor": {
        "name": "Code Editor", "domain": "development", "version": "1.0.0",
        "summary": "Source editing, diagnostics, project structure and code search.",
        "provides": ["code.workspace", "code.diagnostics", "code.search"],
        "consumes": [],
        "requires": ["code.model", "storage.local", "localization.catalog"],
        "conflicts": [], "preferred_languages": ["rust"], "maturity": "specification_only",
    },
    "spreadsheet.editor": {
        "name": "Spreadsheet Editor", "domain": "data", "version": "1.0.0",
        "summary": "Tabular data, formulas, sorting and data transformations.",
        "provides": ["data.table", "data.formula", "data.filter"],
        "consumes": [],
        "requires": ["data.model", "storage.local"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
    "image.editor": {
        "name": "Image Editor", "domain": "visual", "version": "1.0.0",
        "summary": "Image assets, layers, masks and visual export.",
        "provides": ["image.asset", "image.layers", "image.export"],
        "consumes": [],
        "requires": ["image.model", "storage.local"],
        "conflicts": [], "preferred_languages": ["rust"], "maturity": "specification_only",
    },
    "video.editor": {
        "name": "Video Editor", "domain": "video", "version": "1.0.0",
        "summary": "Video assets, sequences, timeline editing and rendering jobs.",
        "provides": ["video.asset", "video.timeline", "video.render"],
        "consumes": ["audio.asset", "subtitle.document"],
        "requires": ["video.model", "timeline.model", "storage.local"],
        "conflicts": [], "preferred_languages": ["rust"], "maturity": "specification_only",
    },
    "presentation.editor": {
        "name": "Presentation Editor", "domain": "documents", "version": "1.0.0",
        "summary": "Slide decks, speaker notes, layouts and document export.",
        "provides": ["presentation.deck", "presentation.slides"],
        "consumes": ["text.document", "image.asset"],
        "requires": ["document.model", "image.model", "storage.local"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
    "file.manager": {
        "name": "File Manager", "domain": "system", "version": "1.0.0",
        "summary": "File navigation, metadata, collections and workspace paths.",
        "provides": ["files.navigation", "files.metadata"],
        "consumes": [],
        "requires": ["files.provider", "storage.local"],
        "conflicts": [], "preferred_languages": ["rust"], "maturity": "specification_only",
    },
    "api.client": {
        "name": "API Client", "domain": "network", "version": "1.0.0",
        "summary": "HTTP API requests, response schemas and request collections.",
        "provides": ["api.requests", "api.schemas", "network.http"],
        "consumes": [],
        "requires": ["api.transport", "storage.local"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
    "automation.engine": {
        "name": "Automation Engine", "domain": "automation", "version": "1.0.0",
        "summary": "Triggers, rules, scheduled workflows and event actions.",
        "provides": ["automation.workflows", "automation.events"],
        "consumes": ["tasks.workflow", "calendar.events", "api.requests"],
        "requires": ["event.bus", "storage.local"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
    "data.visualizer": {
        "name": "Data Visualizer", "domain": "analytics", "version": "1.0.0",
        "summary": "Charts, dashboards, aggregates and interactive data views.",
        "provides": ["charts.render", "analytics.dashboard"],
        "consumes": ["data.table"],
        "requires": ["data.model"],
        "conflicts": [], "preferred_languages": ["python", "typescript"], "maturity": "specification_only",
    },
    "database.manager": {
        "name": "Database Manager", "domain": "data", "version": "1.0.0",
        "summary": "Database schemas, queries, migrations and table inspection.",
        "provides": ["database.schema", "database.queries"],
        "consumes": [],
        "requires": ["database.provider", "storage.local"],
        "conflicts": [], "preferred_languages": ["rust"], "maturity": "specification_only",
    },
    "archive.manager": {
        "name": "Archive Manager", "domain": "system", "version": "1.0.0",
        "summary": "Archive inspection, extraction, packaging and integrity checks.",
        "provides": ["archive.read", "archive.write", "archive.index"],
        "consumes": ["files.navigation"],
        "requires": ["archive.provider", "storage.local"],
        "conflicts": [], "preferred_languages": ["rust"], "maturity": "specification_only",
    },
    "knowledge.graph": {
        "name": "Knowledge Graph", "domain": "knowledge", "version": "1.0.0",
        "summary": "Knowledge entities, relations, backlinks and semantic references.",
        "provides": ["knowledge.entities", "knowledge.relations", "knowledge.index"],
        "consumes": ["text.document", "notes.collection"],
        "requires": ["knowledge.index", "document.model", "storage.local"],
        "conflicts": [], "preferred_languages": ["python"], "maturity": "specification_only",
    },
}

_DEPENDENCIES: dict[str, dict[str, Any]] = {
    "document.model": {"version": "1.0.0", "maturity": "contract_only", "requires": []},
    "media.model": {"version": "1.0.0", "maturity": "contract_only", "requires": []},
    "timeline.model": {"version": "1.0.0", "maturity": "contract_only", "requires": ["media.model"]},
    "storage.local": {"version": "1.0.0", "maturity": "host_adapter_required", "requires": []},
    "localization.catalog": {"version": "1.0.0", "maturity": "generated", "requires": []},
    "translation.provider": {"version": "1.0.0", "maturity": "provider_required", "requires": []},
    "time.model": {"version": "1.0.0", "maturity": "contract_only", "requires": []},
    "speech.provider": {"version": "1.0.0", "maturity": "provider_required", "requires": ["media.model"]},
    "code.model": {"version": "1.0.0", "maturity": "contract_only", "requires": ["document.model"]},
    "data.model": {"version": "1.0.0", "maturity": "contract_only", "requires": ["storage.local"]},
    "image.model": {"version": "1.0.0", "maturity": "contract_only", "requires": ["media.model"]},
    "video.model": {"version": "1.0.0", "maturity": "contract_only", "requires": ["media.model", "timeline.model"]},
    "files.provider": {"version": "1.0.0", "maturity": "host_adapter_required", "requires": ["storage.local"]},
    "api.transport": {"version": "1.0.0", "maturity": "provider_required", "requires": []},
    "event.bus": {"version": "1.0.0", "maturity": "contract_only", "requires": []},
    "database.provider": {"version": "1.0.0", "maturity": "provider_required", "requires": ["storage.local"]},
    "archive.provider": {"version": "1.0.0", "maturity": "provider_required", "requires": ["storage.local"]},
    "knowledge.index": {"version": "1.0.0", "maturity": "contract_only", "requires": ["storage.local"]},
}


# HARVEST is a bundled, source-only Reaper capability pack. The archive is
# decoded and inspected without extracting files or executing source.
_HARVEST_BUNDLE_DIR = Path(__file__).resolve().parents[1] / "harvest" / "bundle"
_HARVEST_ARCHIVE_LIMIT = 4 * 1024 * 1024
_HARVEST_FILES_LIMIT = 128
_HARVEST_ARCHIVE_EXPECTED_SHA256 = "64d8b6738f27a4d03ba9e10537effc28d781c1c9efb9390004451bba40ae520a"
_HARVEST_COMPONENTS: dict[str, dict[str, Any]] = {}
_HARVEST_ARCHIVE_BYTES: bytes | None = None
_HARVEST_ARCHIVE_SHA256: str | None = None


def _read_harvest_pack() -> dict[str, Any] | None:
    global _HARVEST_ARCHIVE_BYTES, _HARVEST_ARCHIVE_SHA256
    parts = sorted(_HARVEST_BUNDLE_DIR.glob("chunk-*.b64"))
    if not parts:
        return None
    expected = [f"chunk-{index:03d}.b64" for index in range(1, 17)]
    if [path.name for path in parts] != expected:
        raise JoraError("HARVEST source bundle is incomplete or has unexpected segments")
    encoded_parts: list[str] = []
    for path in parts:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 3000:
            raise JoraError(f"invalid HARVEST archive segment: {path.name}")
        encoded = path.read_text(encoding="ascii").strip()
        if not encoded or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for char in encoded):
            raise JoraError(f"invalid base64 in HARVEST archive segment: {path.name}")
        encoded_parts.append(encoded)
    try:
        archive_bytes = base64.b64decode("".join(encoded_parts), validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise JoraError(f"HARVEST source bundle is not valid base64: {error}") from error
    if not archive_bytes or len(archive_bytes) > _HARVEST_ARCHIVE_LIMIT:
        raise JoraError("HARVEST source archive exceeds its configured size limit")

    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > _HARVEST_FILES_LIMIT:
                raise JoraError("HARVEST source archive contains too many files")
            names: set[str] = set()
            total_size = 0
            for member in members:
                member_path = PurePosixPath(member.name)
                if member_path.is_absolute() or ".." in member_path.parts or "\\" in member.name:
                    raise JoraError(f"unsafe path in HARVEST source archive: {member.name}")
                if member.name in names:
                    raise JoraError(f"duplicate path in HARVEST source archive: {member.name}")
                names.add(member.name)
                if member.isdir():
                    continue
                if not member.isfile():
                    raise JoraError(f"unsupported archive entry type: {member.name}")
                if not (member.name.startswith("harvest/") or member.name == "docs/HARVEST_ARCHITECTURE.md"):
                    raise JoraError(f"unexpected path in HARVEST source archive: {member.name}")
                total_size += member.size
                if total_size > _HARVEST_ARCHIVE_LIMIT:
                    raise JoraError("HARVEST uncompressed source exceeds its configured size limit")
            pack_member = archive.extractfile("harvest/jora/components.v1.json")
            if pack_member is None:
                raise JoraError("HARVEST archive does not contain its Jora component manifest")
            pack = json.loads(pack_member.read().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, tarfile.TarError) as error:
        raise JoraError(f"cannot inspect HARVEST source archive: {error}") from error

    if not isinstance(pack, dict) or pack.get("schema") != "harvest.jora.pack.v1":
        raise JoraError("HARVEST component manifest has an unsupported schema")
    components = pack.get("components")
    if pack.get("pack_id") != "harvest.frameworks" or pack.get("version") != "1.0.0":
        raise JoraError("HARVEST pack identity or version is unsupported")
    if not isinstance(components, list) or len(components) != 16:
        raise JoraError("HARVEST pack must declare exactly 16 framework components")

    seen: set[str] = set()
    for spec in components:
        if not isinstance(spec, dict):
            raise JoraError("HARVEST component entries must be objects")
        identifier = spec.get("id")
        source_module = spec.get("source_module")
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"harvest\.[a-z0-9_]{1,40}", identifier)
            or identifier in seen
        ):
            raise JoraError(f"invalid or duplicate HARVEST component id: {identifier!r}")
        if not isinstance(source_module, str) or not re.fullmatch(r"[a-z0-9_]{1,48}\.rpr", source_module):
            raise JoraError(f"invalid HARVEST source module for {identifier}")
        for field in ("name", "domain", "version", "summary", "input_schema", "ir_schema", "output_schema", "ir_schema_file"):
            if not isinstance(spec.get(field), str) or not spec[field]:
                raise JoraError(f"HARVEST component {identifier} is missing {field}")
        for field in ("provides", "consumes", "requires"):
            if not isinstance(spec.get(field), list) or not all(isinstance(item, str) and item for item in spec[field]):
                raise JoraError(f"HARVEST component {identifier} has invalid {field}")
        seen.add(identifier)
        _HARVEST_COMPONENTS[identifier] = copy.deepcopy(spec)

    for filename in pack.get("core_files", []):
        if not isinstance(filename, str) or not re.fullmatch(r"[a-z0-9_]{1,48}\.rpr", filename):
            raise JoraError("HARVEST core file list contains an invalid path")
        if "harvest/core/" + filename not in names:
            raise JoraError(f"HARVEST core module is missing: {filename}")
    for filename in pack.get("schema_files", []):
        if not isinstance(filename, str) or not re.fullmatch(r"[a-z0-9_.-]{1,96}\.schema\.json", filename):
            raise JoraError("HARVEST schema file list contains an invalid path")
        if "harvest/schemas/" + filename not in names:
            raise JoraError(f"HARVEST schema file is missing: {filename}")
    if "harvest/registry/" + str(pack.get("registry_file", "")) not in names:
        raise JoraError("HARVEST registry file is missing")
    for spec in components:
        if "harvest/frameworks/" + spec["source_module"] not in names:
            raise JoraError(f"HARVEST source module is missing: {spec['source_module']}")

    _HARVEST_ARCHIVE_BYTES = archive_bytes
    _HARVEST_ARCHIVE_SHA256 = hashlib.sha256(archive_bytes).hexdigest()
    if _HARVEST_ARCHIVE_SHA256 != _HARVEST_ARCHIVE_EXPECTED_SHA256:
        raise JoraError("HARVEST source archive checksum does not match the pinned release")
    return pack


_HARVEST_PACK = _read_harvest_pack()
if _HARVEST_PACK is not None:
    _DEPENDENCIES["harvest.runtime"] = {
        "version": _HARVEST_PACK["version"],
        "maturity": "partial",
        "requires": [],
    }
    for _harvest_id, _harvest_spec in _HARVEST_COMPONENTS.items():
        _COMPONENTS[_harvest_id] = {
            "name": _harvest_spec["name"],
            "domain": _harvest_spec["domain"],
            "version": _harvest_spec["version"],
            "summary": _harvest_spec["summary"],
            "provides": list(_harvest_spec["provides"]),
            "consumes": list(_harvest_spec["consumes"]),
            "requires": list(_harvest_spec["requires"]),
            "conflicts": [],
            "preferred_languages": [],
            "maturity": _harvest_spec.get("maturity", "partial"),
            "source_module": _harvest_spec["source_module"],
            "input_schema": _harvest_spec["input_schema"],
            "ir_schema": _harvest_spec["ir_schema"],
            "output_schema": _harvest_spec["output_schema"],
            "ir_schema_file": _harvest_spec["ir_schema_file"],
        }
        _DEPENDENCIES[_harvest_id] = {
            "version": _harvest_spec["version"],
            "maturity": _harvest_spec.get("maturity", "partial"),
            "requires": list(_harvest_spec["requires"]),
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
_NAME_RE = re.compile(r"^[A-Za-z0-9\u0400-\u04ff\u4e00-\u9fff][A-Za-z0-9\u0400-\u04ff\u4e00-\u9fff .,_&+/\-]{0,79}$")


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


def _validate_application_name(value: str) -> str:
    """Reject the platform brand in every generated or supplied product name."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    if "jora" in normalized:
        raise JoraError("application name must be independent and must not contain the platform name Jora")
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
    allowed = {"topology", "objective", "seed", "variants", "variation"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise JoraError("unknown graph fields: " + ", ".join(unknown))
    topology = _text(value.get("topology", "auto"), "graph.topology", 32).casefold()
    if topology != "auto" and topology not in GRAPH_TOPOLOGIES:
        raise JoraError(
            "unsupported graph topology; choose auto or: " + ", ".join(GRAPH_TOPOLOGIES)
        )
    objective = _text(value.get("objective", "balanced"), "graph.objective", 32).casefold()
    if objective not in GRAPH_OBJECTIVES:
        raise JoraError("graph.objective must be one of: " + ", ".join(GRAPH_OBJECTIVES))
    seed = _text(value.get("seed", ""), "graph.seed", 64, optional=True)
    variants = value.get("variants", 3)
    variation = value.get("variation", 50)
    if isinstance(variants, bool) or not isinstance(variants, int) or not 1 <= variants <= MAX_GRAPH_VARIANTS:
        raise JoraError(f"graph.variants must be an integer from 1 to {MAX_GRAPH_VARIANTS}")
    if isinstance(variation, bool) or not isinstance(variation, int) or not 0 <= variation <= 100:
        raise JoraError("graph.variation must be an integer from 0 to 100")
    return {
        "topology": topology,
        "objective": objective,
        "seed": seed,
        "variants": variants,
        "variation": variation,
    }


def _join_naming_terms(values: list[str]) -> str:
    if len(values) <= 1:
        return values[0] if values else "Workspace"
    if len(values) == 2:
        return values[0] + " & " + values[1]
    return ", ".join(values[:-1]) + " & " + values[-1]


def _naming_profile(component_ids: list[str], style: str) -> dict[str, Any]:
    terms = {
        "text.editor": {
            "short": "Docs",
            "domain": "Documents",
            "action": "Writing",
            "formula": "Text",
        },
        "audio.editor": {
            "short": "Audio",
            "domain": "Media",
            "action": "Audio Editing",
            "formula": "Audio",
        },
        "translation.workspace": {
            "short": "Translate", "domain": "Languages", "action": "Translation", "formula": "Translation",
        },
        "subtitle.editor": {"short": "Captions", "domain": "Media", "action": "Subtitle Editing", "formula": "Subtitles"},
        "notes.workspace": {"short": "Notes", "domain": "Productivity", "action": "Note Taking", "formula": "Notes"},
        "task.board": {"short": "Tasks", "domain": "Productivity", "action": "Task Management", "formula": "Tasks"},
        "calendar.scheduler": {"short": "Calendar", "domain": "Productivity", "action": "Scheduling", "formula": "Calendar"},
        "speech.synthesis": {"short": "Voice", "domain": "Audio", "action": "Speech Synthesis", "formula": "Voice"},
        "speech.recognition": {"short": "Speech", "domain": "Audio", "action": "Speech Recognition", "formula": "Transcription"},
        "code.editor": {"short": "Code", "domain": "Development", "action": "Code Editing", "formula": "Code"},
        "spreadsheet.editor": {"short": "Sheets", "domain": "Data", "action": "Spreadsheet Editing", "formula": "Sheets"},
        "image.editor": {"short": "Images", "domain": "Visual", "action": "Image Editing", "formula": "Images"},
        "video.editor": {"short": "Video", "domain": "Media", "action": "Video Editing", "formula": "Video"},
        "presentation.editor": {"short": "Slides", "domain": "Documents", "action": "Presentation Design", "formula": "Slides"},
        "file.manager": {"short": "Files", "domain": "System", "action": "File Management", "formula": "Files"},
        "api.client": {"short": "API", "domain": "Development", "action": "API Integration", "formula": "API"},
        "automation.engine": {"short": "Flow", "domain": "Automation", "action": "Workflow Automation", "formula": "Automation"},
        "data.visualizer": {"short": "Charts", "domain": "Analytics", "action": "Data Visualization", "formula": "Charts"},
        "database.manager": {"short": "Database", "domain": "Data", "action": "Database Management", "formula": "Database"},
        "archive.manager": {"short": "Archive", "domain": "System", "action": "Archive Management", "formula": "Archive"},
        "knowledge.graph": {"short": "Knowledge", "domain": "Knowledge", "action": "Knowledge Mapping", "formula": "Knowledge"},
    }
    for component_id in component_ids:
        if component_id not in terms:
            spec = _COMPONENTS[component_id]
            short = re.sub(r"[^A-Za-z0-9]+", "", str(spec["name"]))[:16] or "Research"
            terms[component_id] = {
                "short": short,
                "domain": DOMAIN_LABELS.get(str(spec["domain"]), str(spec["domain"]).title()),
                "action": str(spec["summary"])[:60],
                "formula": short,
            }
    short_terms = list(dict.fromkeys(terms[item]["short"] for item in component_ids))
    descriptors = list(dict.fromkeys(terms[item]["domain"] for item in component_ids))
    action_terms = list(dict.fromkeys(terms[item]["action"] for item in component_ids))
    formula_terms = list(dict.fromkeys(terms[item]["formula"] for item in component_ids))
    natural_domains = _join_naming_terms(descriptors)
    natural_actions = _join_naming_terms(action_terms)
    compact = " / ".join(short_terms) + " Workspace"
    balanced = natural_domains + " Workspace"
    descriptive = "Workspace for " + natural_actions.lower()
    formula = " + ".join(formula_terms) + " Workspace"

    def bounded_label(candidate: str) -> str:
        if len(candidate) <= 80:
            return candidate
        # Large compositions need a readable independent name within the
        # public 80-character contract. Keep a deterministic compact identity.
        for count in range(len(short_terms), 0, -1):
            compact_candidate = " / ".join(short_terms[:count]) + " Workspace"
            if len(compact_candidate) <= 80:
                return compact_candidate
        return "Workspace"

    suggestions = [
        {"id": "jora.compact", "label": bounded_label(compact), "style": "compact"},
        {"id": "jora.balanced", "label": bounded_label(balanced), "style": "balanced"},
        {"id": "jora.descriptive", "label": bounded_label(descriptive), "style": "descriptive"},
        {"id": "jora.formula", "label": bounded_label(formula), "style": "formula"},
    ]
    preferred = next((item for item in suggestions if item["style"] == style), None)
    if preferred is None:
        preferred = suggestions[1]
    for candidate in suggestions:
        _validate_application_name(candidate["label"])
    return {
        "version": "jora-naming.v2",
        "platform": "Jora",
        "product_name_policy": APPLICATION_NAME_POLICY,
        "style": style,
        "descriptors": descriptors,
        "selected": preferred,
        "suggestions": suggestions,
        "rule": "Application names are independent product identities and must not contain the platform name Jora.",
    }


def _build_graph_variant(
    component_ids: list[str],
    dependency_order: list[str],
    locales: list[str],
    topology: str,
    seed: str,
    variation: int,
    objective: str,
    variant_index: int,
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    def add_node(node_id: str, kind: str, label: str, maturity: str = "contract") -> None:
        if node_id in node_ids:
            return
        if len(nodes) >= MAX_GRAPH_NODES:
            raise JoraError(f"generated graph exceeds {MAX_GRAPH_NODES} nodes")
        node_ids.add(node_id)
        nodes.append({"id": node_id, "kind": kind, "label": label, "maturity": maturity})

    def add_edge(source: str, target: str, relation: str, *, async_edge: bool = False) -> None:
        if source not in node_ids or target not in node_ids:
            raise JoraError(f"graph edge references an unknown node: {source} -> {target}")
        record = {"from": source, "to": target, "relation": relation}
        if async_edge:
            record["delivery"] = "asynchronous"
        if record in edges:
            return
        if len(edges) >= MAX_GRAPH_EDGES:
            raise JoraError(f"generated graph exceeds {MAX_GRAPH_EDGES} edges")
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
    # Large formulae route through bounded domain gateways. Direct pairwise meshes
    # are not materialized for N > 12, keeping integration graph growth linear.
    domain_clusters: dict[str, str] = {}
    if len(component_ids) > 12:
        for component_id in component_ids:
            domain = str(_COMPONENTS[component_id]["domain"])
            gateway_id = "cluster:" + domain
            if domain not in domain_clusters:
                domain_clusters[domain] = gateway_id
                add_node(gateway_id, "domain_gateway", DOMAIN_LABELS.get(domain, domain.title()) + " Gateway", "planned")
                add_edge("ui:shell", gateway_id, "routes_domain")
            add_edge(gateway_id, "component:" + component_id, "routes_component")
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
        providers_by_capability: dict[str, list[str]] = {}
        for provider_id in component_ids:
            for capability in _COMPONENTS[provider_id]["provides"]:
                providers_by_capability.setdefault(capability, []).append(provider_id)
        matches: list[tuple[str, str, str]] = []
        component_order = {identifier: index for index, identifier in enumerate(component_ids)}
        for consumer_id in component_ids:
            consumed = sorted(set(_COMPONENTS[consumer_id].get("consumes", [])))
            for capability in consumed:
                # Keep the nearest deterministic provider set bounded. Orient
                # every synchronous capability route from earlier to later
                # components so even reciprocal contracts cannot create cycles.
                for provider_id in providers_by_capability.get(capability, [])[:4]:
                    if component_order[provider_id] < component_order[consumer_id]:
                        matches.append((provider_id, consumer_id, capability))
        if variant_index % 3 == 0:
            for provider_id, consumer_id, capability in matches:
                add_edge(
                    "component:" + provider_id,
                    "component:" + consumer_id,
                    "capability:" + capability,
                )
        elif variant_index % 3 == 1 and matches:
            for provider_id, consumer_id, capability in matches:
                broker_id = (
                    "capability:broker:"
                    + provider_id.replace(".", "_") + ":"
                    + consumer_id.replace(".", "_") + ":"
                    + capability.replace(".", "_")
                )
                add_node(broker_id, "capability_broker", capability + " Broker", "planned")
                add_edge("component:" + provider_id, broker_id, "provides_to_broker:" + capability)
                add_edge(broker_id, "component:" + consumer_id, "routes_to_consumer:" + capability)
        else:
            for provider_id, consumer_id, capability in matches:
                channel_id = (
                    "capability:channel:"
                    + provider_id.replace(".", "_") + ":"
                    + consumer_id.replace(".", "_") + ":"
                    + capability.replace(".", "_")
                )
                add_node(channel_id, "capability_channel", capability + " Channel", "planned")
                add_edge("component:" + provider_id, channel_id, "publishes_capability")
                add_edge(channel_id, "component:" + consumer_id, "consumes_capability")
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
        providers_by_capability: dict[str, list[str]] = {}
        for provider_id in component_ids:
            for capability in _COMPONENTS[provider_id]["provides"]:
                providers_by_capability.setdefault(capability, []).append(provider_id)
        for consumer_id in component_ids:
            for capability in sorted(set(_COMPONENTS[consumer_id].get("consumes", []))):
                for provider_id in providers_by_capability.get(capability, [])[:4]:
                    if provider_id != consumer_id:
                        add_edge("component:" + provider_id, "component:" + consumer_id, "capability:" + capability)

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
        "objective": objective,
        "layout_variant": layout_variant,
        "domain_clusters": domain_clusters,
        "nodes": nodes,
        "edges": edges,
    }
    signature = hashlib.sha256(
        json.dumps(canonical_graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    dependency_edges = sum(edge["relation"] == "requires" for edge in edges)
    capability_edges = sum("capability" in edge["relation"] for edge in edges)
    planned_nodes = sum(node["maturity"] == "planned" for node in nodes)
    complexity_penalty = max(0, (len(edges) - len(nodes) + 1) // 8)
    compatibility_score = max(0, min(100, 100 + min(10, capability_edges * 2) - planned_nodes * 3 - complexity_penalty))

    path_cache: dict[str, int] = {}
    def longest_path(node_id: str) -> int:
        if node_id not in path_cache:
            path_cache[node_id] = 1 + max(
                (longest_path(target) for target in dependency_graph[node_id]),
                default=0,
            )
        return path_cache[node_id]

    longest_sync_path = max((longest_path(node_id) for node_id in dependency_graph), default=0)
    event_nodes = sum(node["kind"] in {"event_bus", "event_channel"} for node in nodes)
    router_nodes = sum(node["kind"] in {"capability_router", "capability_broker", "capability_channel"} for node in nodes)
    registry_nodes = sum(node["kind"] == "extension_registry" for node in nodes)
    modular_nodes = sum(node["kind"] in {"domain_layer", "domain_orchestrator", "layout_group", "capability_channel"} for node in nodes)

    latency_score = max(0, min(100, 100 - max(0, longest_sync_path - 3) * 12 - event_nodes * 6 - router_nodes * 3))
    modularity_score = max(0, min(100, 55 + modular_nodes * 8 + capability_edges * 5))
    extensibility_score = max(0, min(100, 40 + registry_nodes * 25 + router_nodes * 8 + event_nodes * 8))
    complexity_score = max(0, min(100, 100 - planned_nodes * 7 - max(0, len(edges) - len(nodes) + 1) * 2))
    objective_scores = {
        "balanced": round(0.40 * compatibility_score + 0.20 * latency_score + 0.20 * modularity_score + 0.20 * extensibility_score),
        "low_latency": round(0.75 * latency_score + 0.25 * compatibility_score),
        "modularity": round(0.75 * modularity_score + 0.25 * compatibility_score),
        "extensibility": round(0.75 * extensibility_score + 0.25 * compatibility_score),
        "minimal_complexity": round(0.75 * complexity_score + 0.25 * compatibility_score),
    }
    objective_score = objective_scores[objective]
    return {
        "id": "jora-graph-" + signature,
        "label": "Jora · " + GRAPH_LABELS[topology] + " · " + layout_variant,
        "topology": topology,
        "objective": objective,
        "layout_variant": layout_variant,
        "seed": seed,
        "variation": variation,
        "signature": signature,
        "nodes": nodes,
        "edges": edges,
        "clusters": domain_clusters,
        "growth_policy": {
            "component_count": len(component_ids),
            "clustered": len(component_ids) > 12,
            "max_direct_provider_neighbors": 4,
            "topology": "cluster-gateway-and-bounded-local-capability-edges" if len(component_ids) > 12 else "selected-graph-topology",
        },
        "metrics": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "dependency_edges": dependency_edges,
            "capability_connections": capability_edges,
            "planned_nodes": planned_nodes,
            "compatibility_score": compatibility_score,
            "objective_score": objective_score,
            "latency_score": latency_score,
            "modularity_score": modularity_score,
            "extensibility_score": extensibility_score,
            "complexity_score": complexity_score,
            "longest_sync_path": longest_sync_path,
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
            options["variation"], options["objective"], index,
        ))
    selected_graph = max(
        variants,
        key=lambda item: (
            item["metrics"]["objective_score"],
            item["metrics"]["compatibility_score"],
            item["metrics"]["capability_connections"],
            -item["metrics"]["planned_nodes"],
            -item["metrics"]["edge_count"],
            item["signature"],
        ),
    )
    return {
        "schema": "reaper.jora.graph-set.v1",
        "selected": selected_graph["id"],
        "selection_policy": "max_objective_score_then_compatibility_then_minimal_planned_nodes",
        "topology_mode": options["topology"],
        "objective": options["objective"],
        "seed": base_seed,
        "variant_count": len(variants),
        "variants": variants,
    }


def _generated_name(component_ids: list[str], requested_name: str = "", style: str = "balanced") -> str:
    """Resolve an independent application name; Jora is only the platform."""
    if requested_name:
        name = _text(requested_name, "name", 80)
    else:
        name = _naming_profile(component_ids, style)["selected"]["label"]
    _validate_application_name(name)
    if not _NAME_RE.fullmatch(name):
        raise JoraError("name contains unsupported characters")
    return name


def _safe_slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.casefold()).strip("-")
    return normalized or "application"


def list_components() -> list[dict[str, Any]]:
    """Return the public catalogue as detached records."""
    return [{"id": identifier, **copy.deepcopy(spec)} for identifier, spec in _COMPONENTS.items()]


def compose_application(request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise JoraError("request must be a JSON object")
    if request.get("schema", REQUEST_SCHEMA) != REQUEST_SCHEMA:
        raise JoraError(f"expected request schema {REQUEST_SCHEMA}")
    name_policy = request.get("application_name_policy", APPLICATION_NAME_POLICY)
    if name_policy != APPLICATION_NAME_POLICY:
        raise JoraError(f"application_name_policy must be {APPLICATION_NAME_POLICY!r}")

    allowed = {
        "schema", "application_name_policy", "name", "description", "components", "locales",
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

    requested_name = _text(request.get("name", ""), "name", 80, optional=True)
    name_style = _text(request.get("name_style", "balanced"), "name_style", 24).casefold()
    if name_style not in {"compact", "balanced", "descriptive", "formula"}:
        raise JoraError("name_style must be compact, balanced, descriptive or formula")
    display_name = _generated_name(component_ids, requested_name, name_style)
    naming = _naming_profile(component_ids, name_style)
    description = _text(request.get("description", ""), "description", 500, optional=True)
    graph_options = _normalize_graph_options(request.get("graph"))

    raw_targets = request.get("language_targets", "auto")
    target_reasons: dict[str, list[str]] = {}
    if raw_targets == "auto":
        target_ids = ["reaper"]
        for component_id in component_ids:
            for language_id in _COMPONENTS[component_id].get("preferred_languages", []):
                if language_id not in _LANGUAGE_TARGETS or language_id == "reaper":
                    continue
                target_reasons.setdefault(language_id, []).append(component_id)
        for language_id in ("python", "rust", "typescript", "c", "java", "kotlin"):
            if language_id in target_reasons:
                target_ids.append(language_id)
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
        "application_name_policy": APPLICATION_NAME_POLICY,
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
            "generated_unit": (
                "src/harvest/frameworks/" + spec["source_module"]
                if spec.get("source_module")
                else "src/components/" + component_id.replace(".", "_") + ".rpr"
            ),
            **({
                "source_module": spec["source_module"],
                "input_schema": spec["input_schema"],
                "ir_schema": spec["ir_schema"],
                "output_schema": spec["output_schema"],
                "ir_schema_file": spec["ir_schema_file"],
                "source_status": "authored_unverified",
            } if spec.get("source_module") else {}),
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

    harvest_framework_ids = [
        identifier for identifier in dependency_order
        if identifier in _HARVEST_COMPONENTS
    ]
    source_bundle = None
    if harvest_framework_ids:
        source_bundle = {
            "schema": "harvest.jora.source-bundle.v1",
            "pack_id": _HARVEST_PACK["pack_id"],
            "version": _HARVEST_PACK["version"],
            "archive_sha256": _HARVEST_ARCHIVE_SHA256,
            "runtime": _HARVEST_PACK["runtime"],
            "framework_ids": harvest_framework_ids,
            "core_files": list(_HARVEST_PACK["core_files"]),
            "schema_files": list(_HARVEST_PACK["schema_files"]),
            "registry_file": _HARVEST_PACK["registry_file"],
            "status": "authored_unverified",
        }

    language_targets = []
    for target_id in target_ids:
        generated = target_id == "reaper"
        selected_by = target_reasons.get(target_id, [])
        language_targets.append({
            "id": target_id,
            "language": _LANGUAGE_TARGETS[target_id],
            "status": "generated" if generated else "adapter_pending",
            "selection": "canonical_core" if generated else ("automatic" if raw_targets == "auto" else "explicit"),
            "selected_for_components": selected_by,
            "reason": (
                "Canonical Reaper source is generated from the validated application request."
                if generated else
                ("Automatically selected from component capability preferences; adapter implementation remains pending for: "
                 + ", ".join(selected_by) + ".")
                if raw_targets == "auto" else
                "Explicitly requested; no Jora code-generation backend is integrated for this target."
            ),
            "toolchain": (
                "available" if generated or target_id == "python" or shutil.which({"rust": "rustc", "typescript": "tsc", "c": "cc", "java": "javac", "kotlin": "kotlinc"}.get(target_id, "")) else "not_detected"
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
            "expression": " + ".join(_COMPONENTS[item]["name"] for item in component_ids) + " → " + display_name,
            "result": display_name,
            "components": component_ids,
        },
        "components": components,
        "dependency_order": dependency_order,
        "dependencies": dependencies,
        "source_bundle": source_bundle,
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
            "Non-HARVEST catalogue packs remain versioned specifications; their feature implementations are not bundled.",
            "The generated Reaper entry point remains a project scaffold; HARVEST source maturity is authored_unverified until runtime and integration checks pass.",
            "Additional programming-language targets remain adapter_pending until a tested backend is delivered.",
            "Jora does not install, execute, or grant permissions to generated projects.",
            *(
                ["HARVEST snapshot storage has a single-writer concurrency contract; no cross-process lock or compare-and-swap is provided."]
                if source_bundle is not None else []
            ),
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



def _copy_harvest_bundle(staging: Path, source_bundle: dict[str, Any] | None) -> dict[str, Any] | None:
    if source_bundle is None:
        return None
    if _HARVEST_ARCHIVE_BYTES is None or _HARVEST_ARCHIVE_SHA256 is None or _HARVEST_PACK is None:
        raise JoraError("HARVEST source bundle is unavailable")
    if source_bundle.get("archive_sha256") != _HARVEST_ARCHIVE_SHA256:
        raise JoraError("HARVEST source bundle checksum does not match the composed request")

    written: list[str] = []
    total_bytes = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(_HARVEST_ARCHIVE_BYTES), mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > _HARVEST_FILES_LIMIT:
                raise JoraError("HARVEST source archive contains too many files")
            for member in members:
                if member.isdir():
                    continue
                if not member.isfile():
                    raise JoraError(f"unsupported HARVEST archive entry type: {member.name}")
                relative = PurePosixPath(member.name)
                if relative.is_absolute() or ".." in relative.parts or "\\" in member.name:
                    raise JoraError(f"unsafe path in HARVEST source archive: {member.name}")
                if member.name.startswith("harvest/"):
                    destination_relative = Path("src") / Path(*relative.parts)
                elif member.name == "docs/HARVEST_ARCHITECTURE.md":
                    destination_relative = Path(*relative.parts)
                else:
                    raise JoraError(f"unexpected HARVEST archive member: {member.name}")
                target = staging / destination_relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() or target.is_symlink():
                    raise JoraError(f"HARVEST file would overwrite an existing generated path: {destination_relative}")
                stream = archive.extractfile(member)
                if stream is None:
                    raise JoraError(f"cannot read HARVEST archive member: {member.name}")
                payload = stream.read()
                if len(payload) != member.size:
                    raise JoraError(f"HARVEST archive member size mismatch: {member.name}")
                total_bytes += len(payload)
                if total_bytes > _HARVEST_ARCHIVE_LIMIT:
                    raise JoraError("HARVEST extracted source exceeds its configured size limit")
                try:
                    payload.decode("utf-8")
                except UnicodeError as error:
                    raise JoraError(f"HARVEST source is not UTF-8: {member.name}") from error
                target.write_bytes(payload)
                written.append(str(destination_relative).replace("\\", "/"))
    except (OSError, tarfile.TarError) as error:
        raise JoraError(f"cannot copy HARVEST source pack: {error}") from error

    required = {
        "src/harvest/core/" + filename for filename in _HARVEST_PACK["core_files"]
    }
    required.update(
        "src/harvest/schemas/" + filename for filename in _HARVEST_PACK["schema_files"]
    )
    required.add("src/harvest/registry/" + _HARVEST_PACK["registry_file"])
    required.update(
        "src/harvest/frameworks/" + _HARVEST_COMPONENTS[identifier]["source_module"]
        for identifier in source_bundle["framework_ids"]
    )
    missing = sorted(required - set(written))
    if missing:
        raise JoraError("HARVEST source bundle is missing required output files: " + ", ".join(missing[:8]))
    source_bundle["files_copied"] = len(written)
    source_bundle["bytes_copied"] = total_bytes
    return {
        "schema": "harvest.jora.build-result.v1",
        "archive_sha256": _HARVEST_ARCHIVE_SHA256,
        "files_copied": len(written),
        "bytes_copied": total_bytes,
        "framework_ids": list(source_bundle["framework_ids"]),
        "status": "authored_unverified",
    }


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
        harvest_build = _copy_harvest_bundle(staging, application.get("source_bundle"))
        if harvest_build is not None:
            application["source_bundle"].update({
                "files_copied": harvest_build["files_copied"],
                "bytes_copied": harvest_build["bytes_copied"],
                "archive_sha256": harvest_build["archive_sha256"],
            })
            framework_imports = []
            for framework_id in application["source_bundle"]["framework_ids"]:
                module = _HARVEST_COMPONENTS[framework_id]["source_module"]
                alias = "harvest_" + module[:-4]
                framework_imports.append(
                    f'import "harvest/frameworks/{module}" as {alias}'
                )
            selected_framework_ids = [
                item["id"] for item in application["components"]
                if item.get("source_module")
            ]
            main_source = "\n".join([
                'import "harvest/core/jora_adapter.rpr" as harvest_app',
                *framework_imports,
                "",
                f'make framework_ids := {json.dumps(selected_framework_ids, ensure_ascii=False)}',
                f'make application_plan := harvest_app["application_plan"]("{application["id"]}", "{application["name"]}", framework_ids, "{application["preferred_locale"]}")',
                'make application_ir := harvest_app["application_ir"](application_plan)',
                f'emit "Application: {application["name"]}"',
                f'emit "HARVEST frameworks: {len(selected_framework_ids)}"',
                'emit application_plan',
                'emit application_ir',
                'emit "Sources and schemas were bundled; runtime verification remains a separate gate."',
                "",
            ])
        else:
            main_source = (
                f'emit "Jora application: {application["name"]}"\n'
                f'emit "Composed from: {application["formula"]["expression"]}"\n'
                'emit "Scaffold only: capability packs require implementation."\n'
            )
        _write_text(staging, "src/main.rpr", main_source)

        for component in application["components"]:
            if component.get("source_module"):
                continue
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
            "graph_objective": application["graphs"]["objective"],
            "selected_graph": application["graphs"]["selected"],
            "selected_graph_score": next(item["metrics"]["objective_score"] for item in application["graphs"]["variants"] if item["id"] == application["graphs"]["selected"]),
            "graph_signatures": [item["signature"] for item in application["graphs"]["variants"]],
            "generator": "Reaper Jora 2.0",
            "harvest_source_bundle": application.get("source_bundle"),
        }
        _write_text(staging, "jora.lock.json", json.dumps(lock, ensure_ascii=False, indent=2) + "\n")

        readme = (
            f"# {application['name']}\n\n"
            f"Jora formula: {application['formula']['expression']}\n\n"
            f"{application['description']}\n\n"
            "## Project contents\n\n"
            "- src/main.rpr: Reaper entry-point scaffold.\n"
            "- src/components/: contract stubs for non-HARVEST specification packs.\n"
            "- src/harvest/: bundled HARVEST Reaper modules and versioned JSON schemas when selected.\n"
            "- locales/: generated EN/RU/UK/MOST interface dictionaries.\n"
            "- jora.app.json: versioned application manifest.\n"
            "- jora.lock.json: resolved component, dependency, naming and graph versions.\n"
            "- jora.graphs.json: reproducible graph variants, nodes, typed edges and compatibility metrics.\n"
            "- graphs/variant-*.mmd: readable Mermaid diagrams for each graph alternative.\n\n"
            "## Maturity\n\n"
            "This directory is a reproducible scaffold, not an installable application. "
            "Non-HARVEST catalogue packs remain specification-only. Storage, translation and "
            "audio host adapters need separate implementations. No source was executed.\n"
            + (
                "\n## HARVEST source bundle\n\n"
                "Selected HARVEST Reaper modules and their versioned schemas are included under src/harvest/. "
                "Their maturity is authored_unverified until Reaper parser, typechecker and integration checks pass. "
                "Jora bundles but does not install or execute the source.\n"
                if harvest_build is not None else ""
            )
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
        "source_bundle": harvest_build,
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
