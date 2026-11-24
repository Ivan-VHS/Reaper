"""Validate the versioned Reaper system target profiles without third-party packages."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "language" / "targets" / "duckos-kernel.v1.json"
DEFAULT_SCHEMA = ROOT / "schemas" / "system-target.v1.schema.json"


class TargetProfileError(ValueError):
    pass


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TargetProfileError(f"{name} must be an object")
    return value


def validate_profile(profile: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    if profile.get("schema") != "reaper.system-target.v1" or profile.get("version") != 1:
        raise TargetProfileError("unsupported system target schema or version")
    if not isinstance(profile.get("target_id"), str) or not profile["target_id"]:
        raise TargetProfileError("target_id must be non-empty text")
    if profile.get("maturity") not in {"planned", "experimental", "available"}:
        raise TargetProfileError("invalid target maturity")

    target = _object(profile.get("target"), "target")
    required_target_fields = {
        "architecture", "triple", "abi", "boot_protocol",
        "endianness", "pointer_width_bits", "decision_status",
    }
    if set(target) != required_target_fields:
        raise TargetProfileError("target must declare exactly the versioned target decision fields")
    if target.get("decision_status") != "approved":
        if any(target.get(key) is not None for key in (
            "architecture", "triple", "abi", "boot_protocol", "endianness", "pointer_width_bits"
        )):
            raise TargetProfileError("unapproved target and ABI values must remain unset")

    toolchain = _object(profile.get("current_toolchain"), "current_toolchain")
    for name in ("reference_runtime", "vm", "native_aot", "native_c_core", "hardware_adapter", "embedded_workbench"):
        entry = _object(toolchain.get(name), f"current_toolchain.{name}")
        if entry.get("status") not in {"implemented", "partial", "experimental", "planned"}:
            raise TargetProfileError(f"invalid status for current_toolchain.{name}")
        if not isinstance(entry.get("scope"), str) or not entry["scope"]:
            raise TargetProfileError(f"scope is required for current_toolchain.{name}")

    native = toolchain["native_aot"]
    if native.get("freestanding") is not False and native.get("status") == "experimental":
        raise TargetProfileError("the current experimental AOT slice must not be reported as freestanding")
    if native.get("supports_duckos_source") is True and native.get("target_profile") == "hosted-scalar":
        raise TargetProfileError("the hosted scalar backend cannot claim DuckOS source coverage")

    caps = profile.get("required_compiler_capabilities")
    if not isinstance(caps, list) or not caps:
        raise TargetProfileError("required_compiler_capabilities must be a non-empty list")
    ids: set[str] = set()
    for cap in caps:
        item = _object(cap, "required_compiler_capabilities entry")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise TargetProfileError("compiler capability IDs must be unique non-empty strings")
        ids.add(identifier)
        if item.get("status") not in {"implemented", "partial", "planned"}:
            raise TargetProfileError(f"invalid maturity status for compiler capability {identifier}")
        if not isinstance(item.get("acceptance"), str) or len(item["acceptance"]) < 10:
            raise TargetProfileError(f"acceptance evidence is required for compiler capability {identifier}")

    decisions = profile.get("target_decisions")
    if not isinstance(decisions, list) or not decisions:
        raise TargetProfileError("target_decisions must be a non-empty list")
    for decision in decisions:
        item = _object(decision, "target_decisions entry")
        if item.get("status") not in {"open", "proposed", "approved"}:
            raise TargetProfileError("invalid target decision status")

    safety = _object(profile.get("safety_policy"), "safety_policy")
    required_safety = {
        "physical_memory_access_requires_platform_adapter",
        "privileged_operations_require_explicit_capability",
        "mmio_volatile_is_not_atomic",
        "no_implicit_host_runtime_in_kernel",
        "unsupported_constructs_must_fail_before_codegen",
        "target_profile_does_not_claim_bootability",
    }
    if not required_safety.issubset(safety) or any(type(safety[key]) is not bool for key in required_safety):
        raise TargetProfileError("required system safety invariants must be explicit booleans")
    if safety["target_profile_does_not_claim_bootability"] is not True:
        raise TargetProfileError("target profile must not claim bootability")

    rules = profile.get("promotion_rules")
    if not isinstance(rules, list) or not rules or any(not isinstance(rule, str) or len(rule) < 20 for rule in rules):
        raise TargetProfileError("promotion_rules must contain explicit evidence requirements")

    if schema is not None:
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise TargetProfileError("unexpected JSON Schema dialect")
        if schema.get("$id") is None or not isinstance(schema["$id"], str):
            raise TargetProfileError("JSON Schema must declare an ID")

    return {
        "schema": "reaper.system-target-validation.v1",
        "ok": True,
        "target_id": profile["target_id"],
        "maturity": profile["maturity"],
        "required_compiler_capabilities": len(caps),
        "open_architecture_decisions": sum(item["status"] == "open" for item in decisions),
        "native_aot_freestanding": native.get("freestanding"),
        "native_aot_supports_duckos_source": native.get("supports_duckos_source"),
    }


def validate_files(profile_path: str | Path = DEFAULT_PROFILE, schema_path: str | Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    try:
        profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    except OSError as error:
        raise TargetProfileError(f"cannot read target contract: {error}") from error
    except json.JSONDecodeError as error:
        raise TargetProfileError(f"invalid target contract JSON: {error}") from error
    profile_object = _object(profile, "profile")
    schema_object = _object(schema, "schema")
    try:
        import jsonschema
    except ImportError:
        # Core target safety invariants are still checked by validate_profile.
        pass
    else:
        try:
            jsonschema.validate(instance=profile_object, schema=schema_object)
        except jsonschema.ValidationError as error:
            raise TargetProfileError(f"target profile does not satisfy its JSON Schema: {error.message}") from error
        except jsonschema.SchemaError as error:
            raise TargetProfileError(f"target profile JSON Schema is invalid: {error.message}") from error
    return validate_profile(profile_object, schema_object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Reaper's machine-readable system target profiles.")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        result = validate_files(args.profile, args.schema)
    except (TargetProfileError, OSError, ValueError) as error:
        print(f"Reaper system target validation: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
