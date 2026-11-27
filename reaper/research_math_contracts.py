"""Reaper-side contracts for Pytyliki's bounded mathematical research kernels.

This module validates plans and the versioned catalog. It does not execute native
kernels, prove conjectures, or infer results from numerical observations.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from copy import deepcopy
from functools import lru_cache
import json
import math
from pathlib import Path
import sys
from typing import Any


CATALOG_SCHEMA = "reaper.mathematical-research-contracts.v1"
CATALOG_VERSION = "1.0.0"
MANIFEST_SCHEMA = "pytyliki.mathematical-research-kernels.v1"
MANIFEST_VERSION = "1.0.0"
PYTYLIKI_ABI = "pytyliki-research-math-c11-v1"
MAX_AREAS = 17
FUNCTIONS_PER_AREA = 3
EXPECTED_FUNCTIONS = MAX_AREAS * FUNCTIONS_PER_AREA
_ALLOWED_EFFECTS = frozenset({"pure_exact", "pure_numeric", "finite_numeric", "bounded_search"})
_ALLOWED_ARRAY_TYPES = {
    "i32_array": "i32",
    "usize_array": "usize",
    "u8_array": "u8",
    "u32_array": "u32",
    "u64_array": "u64",
    "i64_array": "i64",
    "f64_array": "finite_f64",
    "f64_grid": "finite_f64",
    "matrix_f64": "finite_f64",
}
_SUPPORTED_TYPES = frozenset({
    "usize", "u64", "u32", "u8", "i32", "i64", "finite_f64",
    "positive_f64", "nonnegative_f64", "prime32",
    "point2", "point2_array", "point2_tuple4", "edge_array",
    "vm_instruction_array", "vm_state", "vm_state_array",
    "f64_tuple4", "i8_tuple4", *_ALLOWED_ARRAY_TYPES.keys(),
})


class ResearchContractError(ValueError):
    """A catalog, invocation or cross-repository manifest violates its contract."""


@dataclass(frozen=True, slots=True)
class KernelCallPlan:
    function_id: str
    api: str
    backend: str
    arguments: tuple[tuple[str, Any], ...]
    returns: str
    effect: str
    evidence: str
    execution_performed: bool = False
    claim_status: str = "EXPERIMENTAL_EVIDENCE_ONLY"

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": "reaper.mathematical-research-call-plan.v1",
            "function_id": self.function_id,
            "api": self.api,
            "backend": self.backend,
            "arguments": {name: _thaw(value) for name, value in self.arguments},
            "returns": self.returns,
            "effect": self.effect,
            "evidence": self.evidence,
            "execution_performed": self.execution_performed,
            "claim_status": self.claim_status,
        }


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, tuple):
        if value and all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)
                         for item in value):
            return {key: _thaw(item) for key, item in value}
        return [_thaw(item) for item in value]
    return value


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def _is_prime32(value: int) -> bool:
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    divisor = 3
    while divisor <= value // divisor:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def _check_scalar(value: Any, kind: str, label: str) -> None:
    integer_bounds = {
        "usize": (0, sys.maxsize),
        "u64": (0, (1 << 64) - 1),
        "u32": (0, (1 << 32) - 1),
        "u8": (0, 255),
        "i32": (-(1 << 31), (1 << 31) - 1),
        "i64": (-(1 << 63), (1 << 63) - 1),
    }
    if kind in integer_bounds:
        low, high = integer_bounds[kind]
        if not _is_integer(value) or not low <= value <= high:
            raise ResearchContractError(f"{label} must be {kind} in [{low}, {high}]")
        return
    if kind == "prime32":
        if not _is_integer(value) or value > (1 << 31) - 1 or not _is_prime32(value):
            raise ResearchContractError(f"{label} must be a prime in [2, 2147483647]")
        return
    if kind in {"finite_f64", "positive_f64", "nonnegative_f64"}:
        if not _is_finite_number(value):
            raise ResearchContractError(f"{label} must be a finite number")
        numeric = float(value)
        if kind == "positive_f64" and numeric <= 0.0:
            raise ResearchContractError(f"{label} must be positive")
        if kind == "nonnegative_f64" and numeric < 0.0:
            raise ResearchContractError(f"{label} must be non-negative")
        return
    raise ResearchContractError(f"unsupported contract type: {kind}")


def _check_value(value: Any, kind: str, label: str, spec: Mapping[str, Any]) -> None:
    if kind in _ALLOWED_ARRAY_TYPES:
        if not isinstance(value, (list, tuple)):
            raise ResearchContractError(f"{label} must be an array")
        if len(value) > int(spec.get("max_items", 1_000_000)):
            raise ResearchContractError(f"{label} exceeds max_items")
        if len(value) < int(spec.get("min_items", 0)):
            raise ResearchContractError(f"{label} has fewer than min_items")
        item_type = _ALLOWED_ARRAY_TYPES[kind]
        for index, item in enumerate(value):
            _check_scalar(item, item_type, f"{label}[{index}]")
        return

    if kind in {"point2", "point2_array", "point2_tuple4"}:
        def check_point(point: Any, point_label: str) -> None:
            if isinstance(point, Mapping):
                if set(point) != {"x", "y"}:
                    raise ResearchContractError(f"{point_label} must contain exactly x and y")
                coords = (point["x"], point["y"])
            elif isinstance(point, (list, tuple)) and len(point) == 2:
                coords = point
            else:
                raise ResearchContractError(f"{point_label} must be a pair of coordinates")
            for axis, coordinate in zip(("x", "y"), coords):
                _check_scalar(coordinate, "finite_f64", f"{point_label}.{axis}")

        if kind == "point2":
            check_point(value, label)
            return
        if kind == "point2_tuple4":
            if not isinstance(value, (list, tuple)) or len(value) != 4:
                raise ResearchContractError(f"{label} must contain exactly four points")
            for index, point in enumerate(value):
                check_point(point, f"{label}[{index}]")
            return
        if not isinstance(value, (list, tuple)):
            raise ResearchContractError(f"{label} must be an array of points")
        if len(value) > int(spec.get("max_items", 128)) or len(value) < int(spec.get("min_items", 0)):
            raise ResearchContractError(f"{label} is outside its point-count bounds")
        for index, point in enumerate(value):
            check_point(point, f"{label}[{index}]")
        return

    if kind == "edge_array":
        if not isinstance(value, (list, tuple)) or len(value) > int(spec.get("max_items", 8128)):
            raise ResearchContractError(f"{label} must be a bounded edge array")
        for index, edge in enumerate(value):
            if isinstance(edge, Mapping):
                if set(edge) != {"left", "right"}:
                    raise ResearchContractError(f"{label}[{index}] must contain left and right")
                pair = (edge["left"], edge["right"])
            elif isinstance(edge, (list, tuple)) and len(edge) == 2:
                pair = edge
            else:
                raise ResearchContractError(f"{label}[{index}] must be an edge pair")
            _check_scalar(pair[0], "usize", f"{label}[{index}].left")
            _check_scalar(pair[1], "usize", f"{label}[{index}].right")
        return

    if kind == "f64_tuple4":
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise ResearchContractError(f"{label} must contain four finite values")
        for index, item in enumerate(value):
            _check_scalar(item, "finite_f64", f"{label}[{index}]")
        return

    if kind == "i8_tuple4":
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise ResearchContractError(f"{label} must contain four orientations")
        for index, item in enumerate(value):
            if not _is_integer(item) or item not in (-1, 1):
                raise ResearchContractError(f"{label}[{index}] must be -1 or 1")
        return

    if kind == "vm_instruction_array":
        if not isinstance(value, (list, tuple)) or len(value) > int(spec.get("max_items", 100_000)):
            raise ResearchContractError(f"{label} must be a bounded instruction array")
        for index, instruction in enumerate(value):
            if not isinstance(instruction, Mapping) or set(instruction) != {"opcode", "reg", "target"}:
                raise ResearchContractError(f"{label}[{index}] must have opcode, reg and target")
            _check_scalar(instruction["opcode"], "u8", f"{label}[{index}].opcode")
            _check_scalar(instruction["reg"], "u8", f"{label}[{index}].reg")
            _check_scalar(instruction["target"], "u32", f"{label}[{index}].target")
        return

    if kind == "vm_state":
        if not isinstance(value, Mapping) or set(value) != {"pc", "registers", "steps", "halted"}:
            raise ResearchContractError(f"{label} must be a complete VM state")
        _check_scalar(value["pc"], "u32", f"{label}.pc")
        _check_scalar(value["steps"], "u64", f"{label}.steps")
        if not isinstance(value["registers"], (list, tuple)) or len(value["registers"]) != 2:
            raise ResearchContractError(f"{label}.registers must contain two uint64 counters")
        for index, item in enumerate(value["registers"]):
            _check_scalar(item, "u64", f"{label}.registers[{index}]")
        if not isinstance(value["halted"], bool):
            raise ResearchContractError(f"{label}.halted must be Boolean")
        return

    if kind == "vm_state_array":
        if not isinstance(value, (list, tuple)) or len(value) > int(spec.get("max_items", 100_000)):
            raise ResearchContractError(f"{label} must be a bounded VM-state array")
        for index, state in enumerate(value):
            _check_value(state, "vm_state", f"{label}[{index}]", {})
        return

    _check_scalar(value, kind, label)


def validate_catalog_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise ResearchContractError("catalog must be an object")
    required_top = {
        "schema", "version", "canonical_owner", "kernel_owner", "kernel_abi",
        "problem_policy", "areas",
    }
    if set(document) != required_top:
        raise ResearchContractError("catalog has missing or unexpected top-level fields")
    if document["schema"] != CATALOG_SCHEMA or document["version"] != CATALOG_VERSION:
        raise ResearchContractError("unsupported mathematical research catalog schema/version")
    if document["canonical_owner"] != "Reaper" or document["kernel_owner"] != "Pytyliki":
        raise ResearchContractError("catalog ownership boundary is invalid")
    if document["kernel_abi"] != PYTYLIKI_ABI:
        raise ResearchContractError("unsupported Pytyliki research-kernel ABI")

    policy = document["problem_policy"]
    if not isinstance(policy, Mapping) or set(policy) != {
        "open_problem_results", "forbid_claims", "require_bounded_work", "require_source_provenance"
    }:
        raise ResearchContractError("problem policy has missing or unexpected fields")
    if policy["open_problem_results"] != "EXPERIMENTAL_EVIDENCE_ONLY":
        raise ResearchContractError("open mathematical problems must remain evidence-only")
    forbidden_claims = policy["forbid_claims"]
    if not isinstance(forbidden_claims, list) or set(forbidden_claims) != {"PROVED", "DISPROVED", "SOLVED"}:
        raise ResearchContractError("the catalog must forbid unsupported proof/solution claims")
    if policy["require_bounded_work"] is not True or policy["require_source_provenance"] is not True:
        raise ResearchContractError("bounded work and source provenance are mandatory")

    areas = document["areas"]
    if not isinstance(areas, list) or len(areas) != MAX_AREAS:
        raise ResearchContractError(f"catalog must contain exactly {MAX_AREAS} areas")
    area_ids: set[str] = set()
    function_ids: set[str] = set()
    api_names: set[str] = set()
    for area in areas:
        if not isinstance(area, Mapping) or set(area) != {"id", "name", "problem_status", "claim_boundary", "functions"}:
            raise ResearchContractError("each area must have id, name, status, claim boundary and functions")
        if not isinstance(area["id"], str) or not area["id"] or area["id"] in area_ids:
            raise ResearchContractError("area identifiers must be unique non-empty strings")
        area_ids.add(area["id"])
        if area["problem_status"] not in {
            "OPEN_CONJECTURE", "OPEN_PROBLEM",
            "GENERAL_UNDECIDABILITY_PROVEN_RESTRICTED_CASES_OPEN",
        }:
            raise ResearchContractError(f"invalid problem status for {area['id']}")
        if not isinstance(area["claim_boundary"], str) or len(area["claim_boundary"]) < 20:
            raise ResearchContractError(f"{area['id']} needs an explicit claim boundary")
        functions = area["functions"]
        if not isinstance(functions, list) or len(functions) != FUNCTIONS_PER_AREA:
            raise ResearchContractError(f"{area['id']} must define exactly three functions")
        for function in functions:
            if not isinstance(function, Mapping) or set(function) != {
                "id", "api", "args", "returns", "effect", "evidence", "backend", "limits"
            }:
                raise ResearchContractError(f"{area['id']} has an invalid function record")
            function_id, api = function["id"], function["api"]
            if not isinstance(function_id, str) or function_id in function_ids:
                raise ResearchContractError("function identifiers must be unique")
            if not function_id.startswith(area["id"] + "."):
                raise ResearchContractError(f"{function_id} is outside its area namespace")
            if not isinstance(api, str) or not api.startswith("pl_math_") or api in api_names:
                raise ResearchContractError("C API names must be unique pl_math_* identifiers")
            function_ids.add(function_id)
            api_names.add(api)
            if function["backend"] != "pytyliki.c11" or function["effect"] not in _ALLOWED_EFFECTS:
                raise ResearchContractError(f"{function_id} has an unsupported backend or effect")
            if not isinstance(function["returns"], str) or not function["returns"]:
                raise ResearchContractError(f"{function_id} must declare a result type")
            if not isinstance(function["evidence"], str) or not function["evidence"]:
                raise ResearchContractError(f"{function_id} must declare an evidence class")
            if not isinstance(function["limits"], Mapping):
                raise ResearchContractError(f"{function_id} limits must be an object")
            args = function["args"]
            if not isinstance(args, list):
                raise ResearchContractError(f"{function_id} args must be an array")
            arg_names: set[str] = set()
            for arg in args:
                if not isinstance(arg, Mapping) or not {"name", "type"} <= set(arg):
                    raise ResearchContractError(f"{function_id} contains an invalid argument descriptor")
                if set(arg) - {"name", "type", "min", "max", "min_exclusive", "max_exclusive", "min_items", "max_items"}:
                    raise ResearchContractError(f"{function_id} argument contains unknown constraints")
                if not isinstance(arg["name"], str) or arg["name"] in arg_names:
                    raise ResearchContractError(f"{function_id} argument names must be unique")
                if arg["type"] not in _SUPPORTED_TYPES:
                    raise ResearchContractError(f"{function_id} uses unsupported type {arg['type']}")
                arg_names.add(arg["name"])
    if len(function_ids) != EXPECTED_FUNCTIONS or len(api_names) != EXPECTED_FUNCTIONS:
        raise ResearchContractError(f"catalog must contain exactly {EXPECTED_FUNCTIONS} unique functions")
    return dict(document)


@lru_cache(maxsize=4)
def _load_catalog_cached(path_string: str) -> dict[str, Any]:
    try:
        document = json.loads(Path(path_string).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ResearchContractError(f"cannot load research catalog: {error}") from error
    return validate_catalog_document(document)


def load_research_math_catalog(path: str | Path | None = None) -> dict[str, Any]:
    catalog_path = Path(path) if path is not None else (
        Path(__file__).with_name("mathematical_research.v1.json")
    )
    return deepcopy(_load_catalog_cached(str(catalog_path.resolve())))


def find_math_kernel(function_id: str, catalog: Mapping[str, Any] | None = None) -> dict[str, Any]:
    selected = catalog or load_research_math_catalog()
    for area in selected["areas"]:
        for function in area["functions"]:
            if function["id"] == function_id:
                return dict(function)
    raise ResearchContractError(f"unknown mathematical research function: {function_id}")


def _validate_cross_constraints(function_id: str, arguments: Mapping[str, Any]) -> None:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ResearchContractError(f"{function_id}: {message}")

    if function_id.startswith("complexity."):
        variables = arguments["variables"]
        literals = arguments["literals"]
        offsets = arguments["clause_offsets"]
        clause_count = arguments["clause_count"]
        require(arguments["literal_count"] == len(literals), "literal_count must match literals length")
        require(len(offsets) == clause_count + 1, "clause_offsets length must equal clause_count + 1")
        require(bool(offsets) and offsets[0] == 0 and offsets[-1] == len(literals),
                "clause_offsets must span the complete literal array")
        require(all(left <= right for left, right in zip(offsets, offsets[1:])),
                "clause_offsets must be nondecreasing")
        for literal in literals:
            require(literal != 0 and abs(literal) <= variables, "CNF literal is outside the variable range")
        if function_id == "complexity.sat_verify":
            assignment = arguments["assignment"]
            require(len(assignment) == variables, "assignment length must equal variables")
            require(all(value in (0, 1) for value in assignment), "assignment values must be Boolean bytes")

    if function_id in {"navier_stokes.grid_divergence", "navier_stokes.grid_vorticity"}:
        nx, ny, nz = arguments["nx"], arguments["ny"], arguments["nz"]
        cells = nx * ny * nz
        require(cells <= 1_000_000, "grid exceeds the one-million-cell contract limit")
        for field in ("u", "v", "w"):
            require(len(arguments[field]) == cells, f"{field} length must equal nx * ny * nz")

    if function_id.startswith("hodge.") and function_id != "hodge.type_check":
        count, dimension = arguments["cycle_count"], arguments["dimension"]
        require(len(arguments["cycles"]) == count * dimension,
                "cycle matrix shape does not match count and dimension")
        if function_id == "hodge.class_in_cycle_span_mod_prime":
            require(len(arguments["candidate"]) == dimension, "candidate vector length must equal dimension")

    if function_id.startswith("tate."):
        dimension = arguments["dimension"]
        if function_id == "tate.fixed_vector_verify":
            require(len(arguments["frobenius"]) == dimension * dimension, "Frobenius matrix must be square")
            require(len(arguments["vector"]) == dimension, "fixed vector length must equal dimension")
        elif function_id == "tate.invariant_dimension_mod_prime":
            require(len(arguments["frobenius"]) == dimension * dimension, "Frobenius matrix must be square")
        else:
            require(len(arguments["cycle_vectors"]) == arguments["cycle_count"] * dimension,
                    "cycle-vector matrix shape does not match count and dimension")

    if function_id in {"goldbach.verify", "goldbach.find_pair_bounded"}:
        number = arguments["even_value"]
        require(number > 2 and number % 2 == 0, "even_value must be an even integer greater than two")
        if function_id == "goldbach.verify":
            require(arguments["prime_a"] <= number, "prime_a must not exceed even_value")

    if function_id == "hadwiger_nelson.unit_graph_build":
        require(len(arguments["xy"]) == 2 * arguments["vertex_count"],
                "xy must contain one integer coordinate pair per vertex")
        require(all(-33_000_000 <= value <= 33_000_000 for value in arguments["xy"]),
                "coordinates must fit the native scaled-coordinate range")
    elif function_id in {"hadwiger_nelson.coloring_verify", "hadwiger_nelson.coloring_search_bounded"}:
        vertices = arguments["vertex_count"]
        if function_id == "hadwiger_nelson.coloring_verify":
            require(len(arguments["colors"]) == vertices, "colors length must equal vertex_count")
        for edge in arguments["edges"]:
            require(edge[0] < vertices and edge[1] < vertices, "edge endpoint is outside vertex_count")

    if function_id.startswith("inscribed_square."):
        curve = arguments["curve"]
        if function_id == "inscribed_square.verify":
            require(len(arguments["square"]) == 4, "square must contain exactly four points")
        if function_id == "inscribed_square.search_sampled":
            sample_count = (len(curve) - 1) * arguments["subdivisions"] + 1
            require(sample_count <= 128, "sampled curve exceeds the fixed 128-point search buffer")

    if function_id.startswith("halting."):
        program = arguments["program"]
        require(len(program) > 0, "program cannot be empty")
        for index, instruction in enumerate(program):
            opcode, register, target = instruction["opcode"], instruction["reg"], instruction["target"]
            require(opcode in (0, 1, 2, 3), f"program[{index}] has an unknown opcode")
            if opcode in (1, 2):
                require(register in (0, 1), f"program[{index}] register must be 0 or 1")
            if opcode in (2, 3):
                require(target < len(program), f"program[{index}] jump target is outside the program")
        if function_id == "halting.vm_step":
            state = arguments["before"]
            require(state["halted"] or state["pc"] < len(program), "input PC is outside the program")
        elif function_id == "halting.vm_run_bounded":
            state = arguments["initial_state"]
            require(state["halted"] or state["pc"] < len(program), "initial PC is outside the program")
        if function_id == "halting.vm_trace_verify":
            trace = arguments["trace"]
            require(len(trace) > 0, "trace cannot be empty")
            require(all(state["halted"] or state["pc"] < len(program) for state in trace),
                    "trace contains a non-halted state with an out-of-range PC")

    if function_id.startswith("matrix."):
        if function_id == "matrix.scaling_exponent":
            require(arguments["n2"] > arguments["n1"], "n2 must be larger than n1")
        else:
            dimension = arguments["dimension"]
            for name in ("left", "right"):
                require(len(arguments[name]) == dimension * dimension,
                        f"{name} matrix length must equal dimension squared")
            if function_id == "matrix.product_verify_f64":
                require(len(arguments["candidate"]) == dimension * dimension,
                        "candidate matrix length must equal dimension squared")


def prepare_math_kernel_call(
    function_id: str,
    arguments: Mapping[str, Any],
    catalog: Mapping[str, Any] | None = None,
) -> KernelCallPlan:
    if not isinstance(arguments, Mapping):
        raise ResearchContractError("kernel arguments must be supplied as a mapping")
    selected = catalog or load_research_math_catalog()
    function = find_math_kernel(function_id, selected)
    specs = function["args"]
    expected = {arg["name"] for arg in specs}
    supplied = set(arguments)
    if supplied != expected:
        missing = sorted(expected - supplied)
        unexpected = sorted(supplied - expected)
        raise ResearchContractError(f"argument mismatch; missing={missing}, unexpected={unexpected}")

    validated: list[tuple[str, Any]] = []
    for spec in specs:
        name, kind = spec["name"], spec["type"]
        value = arguments[name]
        _check_value(value, kind, name, spec)
        if _is_finite_number(value):
            numeric = float(value)
            if "min" in spec and numeric < spec["min"]:
                raise ResearchContractError(f"{name} is below its minimum")
            if "max" in spec and numeric > spec["max"]:
                raise ResearchContractError(f"{name} exceeds its maximum")
            if "min_exclusive" in spec and numeric <= spec["min_exclusive"]:
                raise ResearchContractError(f"{name} must be greater than {spec['min_exclusive']}")
            if "max_exclusive" in spec and numeric >= spec["max_exclusive"]:
                raise ResearchContractError(f"{name} must be less than {spec['max_exclusive']}")
        validated.append((name, _freeze(value)))

    _validate_cross_constraints(function_id, arguments)

    return KernelCallPlan(
        function_id=function["id"],
        api=function["api"],
        backend=function["backend"],
        arguments=tuple(validated),
        returns=function["returns"],
        effect=function["effect"],
        evidence=function["evidence"],
    )


def validate_pytyliki_kernel_manifest(
    manifest: Any,
    catalog: Mapping[str, Any] | None = None,
) -> None:
    selected = catalog or load_research_math_catalog()
    if not isinstance(manifest, Mapping) or set(manifest) != {
        "schema", "version", "owner", "contract_schema", "execution_performed", "functions"
    }:
        raise ResearchContractError("Pytyliki kernel manifest has an invalid envelope")
    if manifest["schema"] != MANIFEST_SCHEMA or manifest["version"] != MANIFEST_VERSION:
        raise ResearchContractError("unsupported Pytyliki mathematical-kernel manifest")
    if manifest["owner"] != "Pytyliki" or manifest["contract_schema"] != CATALOG_SCHEMA:
        raise ResearchContractError("Pytyliki manifest ownership or contract version mismatch")
    if manifest["execution_performed"] is not False:
        raise ResearchContractError("a kernel catalog manifest must not claim execution")
    rows = manifest["functions"]
    if not isinstance(rows, list):
        raise ResearchContractError("manifest functions must be an array")
    expected = [
        {"id": function["id"], "api": function["api"]}
        for area in selected["areas"]
        for function in area["functions"]
    ]
    actual = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"id", "api"}:
            raise ResearchContractError("manifest function rows must contain exactly id and api")
        actual.append({"id": row["id"], "api": row["api"]})
    if actual != expected:
        raise ResearchContractError("Pytyliki manifest does not match the Reaper canonical function catalog")


__all__ = [
    "CATALOG_SCHEMA",
    "EXPECTED_FUNCTIONS",
    "KernelCallPlan",
    "ResearchContractError",
    "find_math_kernel",
    "load_research_math_catalog",
    "prepare_math_kernel_call",
    "validate_catalog_document",
    "validate_pytyliki_kernel_manifest",
]
