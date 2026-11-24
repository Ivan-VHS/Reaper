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
        "requires": ["document.model", "storage.local", "localization.catalog"],
        "conflicts": [],
        "name_token": "Lexi",
        "single_name": "LexiDesk",
        "maturity": "specification_only",
    },
    "audio.editor": {
        "name": "Audio Editor",
        "domain": "media",
        "version": "1.0.0",
        "summary": "Audio asset organisation, timeline editing and non-destructive operations.",
        "provides": ["audio.asset", "audio.timeline", "audio.editing"],
        "requires": ["media.model", "timeline.model", "storage.local"],
        "conflicts": [],
        "name_token": "Tone",
        "single_name": "SonicLab",
        "maturity": "specification_only",
    },
    "translation.workspace": {
        "name": "Translator",
        "domain": "language",
        "version": "1.0.0",
        "summary": "Translation workspace, terminology, parallel text and locale review.",
        "provides": ["translation.workspace", "translation.terminology", "translation.review"],
        "requires": ["document.model", "localization.catalog", "translation.provider"],
        "conflicts": [],
        "name_token": "Lingua",
        "single_name": "LinguaDesk",
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


def _generated_name(component_ids: list[str]) -> str:
    if len(component_ids) == 1:
        return str(_COMPONENTS[component_ids[0]]["single_name"])
    first = str(_COMPONENTS[component_ids[0]]["name_token"])
    second = str(_COMPONENTS[component_ids[1]]["name_token"])
    suffix = f" {len(component_ids)}D" if len(component_ids) > 2 else ""
    return first + second + suffix


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
        "preferred_locale", "syntax_mode", "language_targets",
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

    custom_name = _text(request.get("name", ""), "name", 80, optional=True)
    display_name = custom_name or _generated_name(component_ids)
    if not _NAME_RE.fullmatch(display_name):
        raise JoraError("name contains unsupported characters")
    description = _text(request.get("description", ""), "description", 500, optional=True)

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
        "description": description or " + ".join(_COMPONENTS[item]["name"] for item in component_ids),
        "formula": {
            "expression": " + ".join(_COMPONENTS[item]["name"] for item in component_ids),
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
        lock = {
            "schema": "reaper.jora.lock.v1",
            "application_id": application["id"],
            "component_versions": {item["id"]: item["version"] for item in application["components"]},
            "dependency_versions": {item["id"]: item["version"] for item in application["dependencies"]},
            "dependency_order": application["dependency_order"],
            "generator": "Reaper Jora 1.0",
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
            "- jora.lock.json: resolved component and dependency versions.\n\n"
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
