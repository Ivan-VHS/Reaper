"""VentuSample pack v1/v2 validation and read-only comparison for Reaper.

The adapter consumes metadata only. WAV assets remain in the pack folder and
are never opened, executed, modified or uploaded by this module.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from . import metric_space
from .native import pytyliki_distance

VENTUSAMPLE_PACK_SCHEMA = "ventusample.pack.v1"
VENTUSAMPLE_PACK_V2_SCHEMA = "ventusample.pack.v2"
REAPER_VENTUSAMPLE_COMPARISON_SCHEMA = "reaper.ventusample-comparison.v1"
MAX_PACK_FILES = 256

_TOP_LEVEL_FIELDS = {"schema", "generator", "audio_format", "parameters", "source_sample", "files"}
_PARAMETER_FIELDS = {
    "style", "target", "bpm", "key", "scale", "bars", "variations",
    "swing_percent", "density_percent", "grit_percent", "saturation_percent",
    "stereo_percent", "high_pass_hz", "low_pass_hz", "snare_offset_ms",
    "bus_compression_ratio", "triplet_rolls", "micro_humanize", "vinyl_dust",
    "seed", "sample_rate", "sampler", "timbre", "source_mix_percent",
    "source_pitch_semitones",
}
_FILE_FIELDS = {"file", "peak", "rms", "crest_db", "variation"}
_V2_PARAMETER_FIELDS = {"musical_key", "mode_family"}
_V2_OPTIONAL_PARAMETER_FIELDS = {
    "stochastic_enabled", "stochastic_seed", "stochastic_intensity_percent",
    "stochastic_trigger_mode", "stochastic_plugin_mask", "stochastic_topology",
}
_V2_FILE_FIELDS = {"musical_key", "scale", "mode_family"}
_V2_OPTIONAL_FILE_FIELDS = {"stochastic_routes"}
_STYLES = {
    "Boom Bap", "East Coast", "Harlem Dip-Trap", "G-Unit", "Modern Trap",
    "Atlanta Trap", "UK Drill", "UK Grime", "Memphis", "Jazz Rap",
    "G-Funk", "Boom Trap", "Cripple Trill", "Billionaire Golden Era",
}
_STYLES_V2 = _STYLES | {"Billionaire Golden Era"}
_MODE_FAMILIES = {"major", "minor", "modal"}
_FILE_MODE_FAMILIES = _MODE_FAMILIES | {"pitched_note"}
_TARGETS = {"Full Loop", "Melody", "Drums", "Bass", "One-Shot Kit"}
_KEYS = {"C", "Csharp", "D", "Dsharp", "E", "F", "Fsharp", "G", "Gsharp", "A", "Asharp", "B"}
_SCALES = {"Natural Minor", "Harmonic Minor", "Dorian", "Phrygian", "Major", "Minor Pentatonic"}
_SAMPLERS = {"Clean", "MPC 2500", "MPC 3000XL", "MPC 5000"}
_TIMBRES = {"Keys", "Bell", "Pluck", "Organ", "Brass", "Strings"}
_SAMPLE_RATES = {22050, 44100, 48000, 96000}


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a whole number")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _real(value: Any, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError(f"{name} must be finite and between {minimum} and {maximum}")
    return result


def _choice(value: Any, name: str, options: set[str]) -> str:
    if not isinstance(value, str) or value not in options:
        raise ValueError(f"{name} must be one of the supported VentuSample values")
    return value


def _safe_filename(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 255:
        raise ValueError(f"{name} must be non-empty filename text of at most 255 characters")
    if value in {".", ".."} or "/" in value or "\\" in value or PurePosixPath(value).name != value:
        raise ValueError(f"{name} must be a simple relative filename, not a path")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{name} cannot contain control characters")
    return value


def _validate_pack(pack: Any) -> tuple[dict[str, float], dict[str, Any]]:
    label = "VentuSample pack"
    if not isinstance(pack, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    keys = set(pack)
    missing = _TOP_LEVEL_FIELDS - keys
    extra = keys - _TOP_LEVEL_FIELDS
    if missing or extra:
        raise ValueError(f"{label} fields are invalid; missing={sorted(missing)}, extra={sorted(extra)}")
    schema_id = pack.get("schema")
    if schema_id not in {VENTUSAMPLE_PACK_SCHEMA, VENTUSAMPLE_PACK_V2_SCHEMA}:
        raise ValueError(
            f"{label}.schema must be {VENTUSAMPLE_PACK_SCHEMA} or {VENTUSAMPLE_PACK_V2_SCHEMA}"
        )
    is_v2 = schema_id == VENTUSAMPLE_PACK_V2_SCHEMA
    generator = pack.get("generator")
    if not isinstance(generator, str) or not generator.strip() or len(generator) > 128:
        raise ValueError(f"{label}.generator must be non-empty text of at most 128 characters")
    if pack.get("audio_format") != "wav_pcm16_stereo":
        raise ValueError(f"{label}.audio_format must be wav_pcm16_stereo")
    source_sample = pack.get("source_sample")
    if not isinstance(source_sample, str) or len(source_sample) > 255:
        raise ValueError(f"{label}.source_sample must be text of at most 255 characters")
    if source_sample and ("/" in source_sample or "\\" in source_sample or source_sample in {".", ".."}):
        raise ValueError(f"{label}.source_sample must contain a filename, not a local path")

    parameters = pack.get("parameters")
    if not isinstance(parameters, Mapping):
        raise TypeError(f"{label}.parameters must be an object")
    parameter_keys = set(parameters)
    required_parameter_fields = _PARAMETER_FIELDS | (_V2_PARAMETER_FIELDS if is_v2 else set())
    allowed_parameter_fields = required_parameter_fields | (_V2_OPTIONAL_PARAMETER_FIELDS if is_v2 else set())
    missing_parameters = required_parameter_fields - parameter_keys
    extra_parameters = parameter_keys - allowed_parameter_fields
    if missing_parameters or extra_parameters:
        raise ValueError(
            f"{label}.parameters fields are invalid; missing={sorted(missing_parameters)}, "
            f"extra={sorted(extra_parameters)}"
        )

    style = _choice(parameters["style"], "parameters.style", _STYLES_V2 if is_v2 else _STYLES)
    target = _choice(parameters["target"], "parameters.target", _TARGETS)
    key = _choice(parameters["key"], "parameters.key", _KEYS)
    scale = _choice(parameters["scale"], "parameters.scale", _SCALES)
    sampler = _choice(parameters["sampler"], "parameters.sampler", _SAMPLERS)
    timbre = _choice(parameters["timbre"], "parameters.timbre", _TIMBRES)

    bpm = _integer(parameters["bpm"], "parameters.bpm", 60, 190)
    bars = _integer(parameters["bars"], "parameters.bars", 1, 16)
    variations = _integer(parameters["variations"], "parameters.variations", 1, 32)
    swing = _integer(parameters["swing_percent"], "parameters.swing_percent", 50, 68)
    density = _integer(parameters["density_percent"], "parameters.density_percent", 0, 100)
    grit = _integer(parameters["grit_percent"], "parameters.grit_percent", 0, 100)
    saturation = _integer(parameters["saturation_percent"], "parameters.saturation_percent", 0, 100)
    stereo = _integer(parameters["stereo_percent"], "parameters.stereo_percent", 0, 100)
    high_pass = _integer(parameters["high_pass_hz"], "parameters.high_pass_hz", 20, 300)
    low_pass = _integer(parameters["low_pass_hz"], "parameters.low_pass_hz", 2000, 20000)
    snare_offset = _integer(parameters["snare_offset_ms"], "parameters.snare_offset_ms", -30, 30)
    compression = _real(parameters["bus_compression_ratio"], "parameters.bus_compression_ratio", 1.0, 12.0)
    seed = _integer(parameters["seed"], "parameters.seed", 0, 2147483647)
    sample_rate = _integer(parameters["sample_rate"], "parameters.sample_rate", 22050, 96000)
    if sample_rate not in _SAMPLE_RATES:
        raise ValueError("parameters.sample_rate must be one of 22050, 44100, 48000 or 96000")
    if high_pass >= low_pass or low_pass >= 0.49 * sample_rate:
        raise ValueError("filter bounds must satisfy high_pass_hz < low_pass_hz < 0.49 * sample_rate")
    source_mix = _integer(parameters["source_mix_percent"], "parameters.source_mix_percent", 0, 100)
    source_pitch = _integer(parameters["source_pitch_semitones"], "parameters.source_pitch_semitones", -12, 12)
    for name in ("triplet_rolls", "micro_humanize", "vinyl_dust"):
        if not isinstance(parameters[name], bool):
            raise TypeError(f"parameters.{name} must be boolean")

    musical_key = None
    mode_family = None
    stochastic_parameters: dict[str, Any] = {}
    if is_v2:
        musical_key = parameters["musical_key"]
        if not isinstance(musical_key, str) or not musical_key.strip() or len(musical_key) > 64:
            raise ValueError("parameters.musical_key must be non-empty text of at most 64 characters")
        mode_family = _choice(parameters["mode_family"], "parameters.mode_family", _MODE_FAMILIES)
        if "stochastic_enabled" in parameters:
            if not isinstance(parameters["stochastic_enabled"], bool):
                raise TypeError("parameters.stochastic_enabled must be boolean")
            stochastic_parameters["stochastic_enabled"] = parameters["stochastic_enabled"]
        if "stochastic_seed" in parameters:
            stochastic_parameters["stochastic_seed"] = _integer(
                parameters["stochastic_seed"], "parameters.stochastic_seed", 0, 2147483647
            )
        if "stochastic_intensity_percent" in parameters:
            stochastic_parameters["stochastic_intensity_percent"] = _integer(
                parameters["stochastic_intensity_percent"],
                "parameters.stochastic_intensity_percent", 0, 100
            )
        if "stochastic_trigger_mode" in parameters:
            stochastic_parameters["stochastic_trigger_mode"] = _choice(
                parameters["stochastic_trigger_mode"], "parameters.stochastic_trigger_mode",
                {"file", "bar", "onset"}
            )
        if "stochastic_plugin_mask" in parameters:
            stochastic_parameters["stochastic_plugin_mask"] = _integer(
                parameters["stochastic_plugin_mask"], "parameters.stochastic_plugin_mask", 0, 255
            )
        if "stochastic_topology" in parameters:
            stochastic_parameters["stochastic_topology"] = _choice(
                parameters["stochastic_topology"], "parameters.stochastic_topology",
                {"hybrid", "serial", "parallel"}
            )

    files = pack.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_PACK_FILES:
        raise ValueError(f"{label}.files must contain 1..{MAX_PACK_FILES} audio records")
    filenames: set[str] = set()
    peaks: list[float] = []
    rms_values: list[float] = []
    crest_values: list[float] = []
    seen_variations: set[int] = set()
    variation_counts = {number: 0 for number in range(1, variations + 1)}
    files_per_variation = 8 if target == "One-Shot Kit" else 1
    expected_count = variations * files_per_variation
    if len(files) != expected_count:
        raise ValueError(
            f"{label}.files must contain exactly {expected_count} records for "
            f"{variations} variation(s) of {target}"
        )
    for index, item in enumerate(files):
        if not isinstance(item, Mapping):
            raise TypeError(f"{label}.files[{index}] must be an object")
        required_file_fields = _FILE_FIELDS | (_V2_FILE_FIELDS if is_v2 else set())
        allowed_file_fields = required_file_fields | (_V2_OPTIONAL_FILE_FIELDS if is_v2 else set())
        if not required_file_fields.issubset(item) or set(item) - allowed_file_fields:
            raise ValueError(
                f"{label}.files[{index}] fields are invalid; "
                f"missing={sorted(required_file_fields - set(item))}, "
                f"extra={sorted(set(item) - allowed_file_fields)}"
            )
        filename = _safe_filename(item["file"], f"{label}.files[{index}].file")
        if not filename.lower().endswith(".wav"):
            raise ValueError(f"{label}.files[{index}].file must use the .wav extension")
        marker = filename.casefold()
        if marker in filenames:
            raise ValueError(f"{label}.files contains duplicate filename: {filename}")
        filenames.add(marker)
        peaks.append(_real(item["peak"], f"{label}.files[{index}].peak", 0.0, 1.0))
        rms_values.append(_real(item["rms"], f"{label}.files[{index}].rms", 0.0, 1.0))
        crest_values.append(_real(item["crest_db"], f"{label}.files[{index}].crest_db", 0.0, 100.0))
        variation = _integer(item["variation"], f"{label}.files[{index}].variation", 1, variations)
        if is_v2:
            file_key = item["musical_key"]
            if file_key is not None and (
                not isinstance(file_key, str) or len(file_key) > 64
            ):
                raise ValueError(f"{label}.files[{index}].musical_key must be null or text of at most 64 characters")
            file_scale = item["scale"]
            if file_scale is not None and file_scale not in _SCALES:
                raise ValueError(f"{label}.files[{index}].scale is not a supported scale")
            if item["mode_family"] is not None:
                _choice(item["mode_family"], f"{label}.files[{index}].mode_family", _FILE_MODE_FAMILIES)
            if "stochastic_routes" in item:
                routes = item["stochastic_routes"]
                if not isinstance(routes, list) or len(routes) > 8:
                    raise ValueError(f"{label}.files[{index}].stochastic_routes must contain at most 8 routes")
                if any(not isinstance(route, str) or not route.strip() or len(route) > 512 for route in routes):
                    raise ValueError(f"{label}.files[{index}].stochastic_routes contains an invalid route")
        seen_variations.add(variation)
        variation_counts[variation] += 1
    if seen_variations != set(range(1, variations + 1)):
        raise ValueError(f"{label}.files must contain every declared variation")
    if any(count != files_per_variation for count in variation_counts.values()):
        raise ValueError(
            f"{label}.files must contain exactly {files_per_variation} file(s) per variation"
        )

    mean = lambda values: math.fsum(values) / len(values)
    metrics = {
        "bpm_normalized": bpm / 190.0,
        "bars_normalized": bars / 16.0,
        "variations_normalized": variations / 32.0,
        "swing_normalized": (swing - 50.0) / 18.0,
        "density_normalized": density / 100.0,
        "grit_normalized": grit / 100.0,
        "saturation_normalized": saturation / 100.0,
        "stereo_normalized": stereo / 100.0,
        "high_pass_normalized": (high_pass - 20.0) / 280.0,
        "low_pass_normalized": (low_pass - 2000.0) / 18000.0,
        "snare_offset_normalized": (snare_offset + 30.0) / 60.0,
        "compression_normalized": (compression - 1.0) / 11.0,
        "triplet_rolls_enabled": float(parameters["triplet_rolls"]),
        "micro_humanize_enabled": float(parameters["micro_humanize"]),
        "vinyl_dust_enabled": float(parameters["vinyl_dust"]),
        "sample_rate_normalized": sample_rate / 96000.0,
        "source_mix_normalized": source_mix / 100.0,
        "source_pitch_normalized": (source_pitch + 12.0) / 24.0,
        "mean_peak": mean(peaks),
        "max_peak": max(peaks),
        "mean_rms": mean(rms_values),
        "mean_crest_normalized": mean(crest_values) / 100.0,
    }
    metadata = {
        "schema": schema_id,
        "generator": generator,
        "style": style,
        "target": target,
        "bpm": bpm,
        "key": key,
        "scale": scale,
        "bars": bars,
        "variations": variations,
        "seed": seed,
        "sample_rate": sample_rate,
        "sampler": sampler,
        "timbre": timbre,
        "source_sample": source_sample,
        "file_count": len(files),
        "source_sample_present": bool(source_sample),
    }
    if is_v2:
        metadata["musical_key"] = musical_key
        metadata["mode_family"] = mode_family
        metadata.update(stochastic_parameters)
    return metrics, metadata


def ventusample_metrics(pack: Any) -> dict[str, float]:
    """Validate a complete VentuSample v1/v2 pack manifest and return normalized metrics."""
    metrics, _ = _validate_pack(pack)
    return dict(sorted(metrics.items()))


def compare_ventusample_packs(
    reference: Any, candidate: Any, native_library: str | None = None
) -> dict[str, Any]:
    """Compare two validated pack manifests; no WAV asset is opened or altered."""
    left, left_meta = _validate_pack(reference)
    right, right_meta = _validate_pack(candidate)
    if left.keys() != right.keys():
        raise ValueError("VentuSample metric dimensions differ; refusing implicit alignment")

    dimensions = list(sorted(left))
    reference_values = [left[name] for name in dimensions]
    candidate_values = [right[name] for name in dimensions]
    python_distance = metric_space.euclidean_distance(reference_values, candidate_values)
    distance = python_distance
    distance_backend = "reaper-python"
    native_details: dict[str, Any] | None = None
    if native_library is not None:
        if not isinstance(native_library, str) or not native_library:
            raise TypeError("native_library must be an explicit absolute path string")
        distance = pytyliki_distance(reference_values, candidate_values, native_library)
        distance_backend = "pytyliki-c-abi-v1"
        native_details = {
            "library": str(Path(native_library).expanduser().resolve()),
            "abi_version": 1,
        }

    components = {
        name: {
            "reference": left[name],
            "candidate": right[name],
            "difference": right[name] - left[name],
        }
        for name in dimensions
    }
    result: dict[str, Any] = {
        "schema": REAPER_VENTUSAMPLE_COMPARISON_SCHEMA,
        "mode": "read_only",
        "reference": left_meta,
        "candidate": right_meta,
        "same_style": left_meta["style"] == right_meta["style"],
        "same_target": left_meta["target"] == right_meta["target"],
        "same_key_and_scale": (
            left_meta["key"] == right_meta["key"] and left_meta["scale"] == right_meta["scale"]
        ),
        "same_sampler": left_meta["sampler"] == right_meta["sampler"],
        "same_timbre": left_meta["timbre"] == right_meta["timbre"],
        "same_seed": left_meta["seed"] == right_meta["seed"],
        "same_schema": left_meta["schema"] == right_meta["schema"],
        "same_musical_key": left_meta.get("musical_key", left_meta["key"]) == right_meta.get("musical_key", right_meta["key"]),
        "same_mode_family": left_meta.get("mode_family") == right_meta.get("mode_family"),
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "euclidean_distance": distance,
        "python_euclidean_distance": python_distance,
        "distance_backend": distance_backend,
        "components": components,
    }
    if native_details is not None:
        result["native_backend"] = native_details
    canonical = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    result["report_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result
