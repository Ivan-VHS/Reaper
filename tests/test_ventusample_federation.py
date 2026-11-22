from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter
import reaper.ventusample as ventusample_adapter
from reaper.ventusample import (
    REAPER_VENTUSAMPLE_COMPARISON_SCHEMA,
    compare_ventusample_packs,
    ventusample_metrics,
)


def make_pack() -> dict[str, object]:
    return {
        "schema": "ventusample.pack.v1",
        "generator": "VentuSample native DSP 0.1.0",
        "audio_format": "wav_pcm16_stereo",
        "parameters": {
            "style": "East Coast",
            "target": "Full Loop",
            "bpm": 93,
            "key": "C",
            "scale": "Natural Minor",
            "bars": 4,
            "variations": 1,
            "swing_percent": 58,
            "density_percent": 64,
            "grit_percent": 22,
            "saturation_percent": 24,
            "stereo_percent": 72,
            "high_pass_hz": 32,
            "low_pass_hz": 18000,
            "snare_offset_ms": 15,
            "bus_compression_ratio": 4.0,
            "triplet_rolls": True,
            "micro_humanize": True,
            "vinyl_dust": False,
            "seed": 2500,
            "sample_rate": 44100,
            "sampler": "MPC 3000XL",
            "timbre": "Keys",
            "source_mix_percent": 65,
            "source_pitch_semitones": 0,
        },
        "source_sample": "",
        "files": [
            {
                "file": "VentuSample_East_Coast_93BPM_C_full_loop_v1.wav",
                "peak": 0.65,
                "rms": 0.19,
                "crest_db": 10.68,
                "variation": 1,
            }
        ],
    }


def make_pack_v2() -> dict[str, object]:
    pack = make_pack()
    pack["schema"] = "ventusample.pack.v2"
    parameters = pack["parameters"]
    parameters["musical_key"] = "C Natural Minor"
    parameters["mode_family"] = "minor"
    parameters.update({
        "stochastic_enabled": True,
        "stochastic_seed": 42,
        "stochastic_intensity_percent": 35,
        "stochastic_trigger_mode": "bar",
        "stochastic_plugin_mask": 5,
        "stochastic_topology": "parallel",
    })
    item = pack["files"][0]
    item.update({
        "musical_key": "C Natural Minor",
        "scale": "Natural Minor",
        "mode_family": "minor",
        "stochastic_routes": ["offline.eq", "offline.saturation"],
    })
    return pack


class VentuSampleFederationTests(unittest.TestCase):
    def test_billionaire_golden_era_profile_and_schema_stay_in_sync(self) -> None:
        pack = make_pack()
        pack["parameters"]["style"] = "Billionaire Golden Era"
        metrics = ventusample_metrics(pack)
        self.assertEqual(metrics["bpm_normalized"], 93 / 190)

        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "ventusample.pack.v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_styles = set(schema["properties"]["parameters"]["properties"]["style"]["enum"])
        self.assertEqual(schema_styles, ventusample_adapter._STYLES)

    def test_metrics_validate_pack_and_normalize_audio_metadata(self) -> None:
        metrics = ventusample_metrics(make_pack())
        self.assertAlmostEqual(metrics["bpm_normalized"], 93 / 190)
        self.assertAlmostEqual(metrics["mean_peak"], 0.65)
        self.assertAlmostEqual(metrics["mean_rms"], 0.19)
        self.assertEqual(len(metrics), 22)

    def test_identical_packs_have_zero_distance_and_deterministic_hash(self) -> None:
        pack = make_pack()
        first = compare_ventusample_packs(pack, pack)
        second = compare_ventusample_packs(pack, pack)
        self.assertEqual(first["schema"], REAPER_VENTUSAMPLE_COMPARISON_SCHEMA)
        self.assertEqual(first["euclidean_distance"], 0.0)
        self.assertEqual(first["distance_backend"], "reaper-python")
        self.assertEqual(first["report_sha256"], second["report_sha256"])
        self.assertTrue(first["same_style"])
        self.assertTrue(first["same_seed"])

    def test_changed_parameters_and_measurements_are_reported(self) -> None:
        reference = make_pack()
        candidate = make_pack()
        candidate["parameters"]["bpm"] = 150
        candidate["files"][0]["rms"] = 0.25
        report = compare_ventusample_packs(reference, candidate)
        self.assertGreater(report["euclidean_distance"], 0.0)
        self.assertNotEqual(
            report["components"]["bpm_normalized"]["reference"],
            report["components"]["bpm_normalized"]["candidate"],
        )

    def test_rejects_path_traversal_and_bad_metric_values(self) -> None:
        unsafe = make_pack()
        unsafe["files"][0]["file"] = "../outside.wav"
        with self.assertRaisesRegex(ValueError, "simple relative filename"):
            ventusample_metrics(unsafe)

        invalid = make_pack()
        invalid["files"][0]["peak"] = float("nan")
        with self.assertRaisesRegex(ValueError, "must be finite"):
            ventusample_metrics(invalid)

    def test_rejects_incomplete_variation_set(self) -> None:
        pack = make_pack()
        pack["parameters"]["variations"] = 2
        with self.assertRaisesRegex(ValueError, "exactly 2 records"):
            ventusample_metrics(pack)

    def test_one_shot_kit_requires_eight_files_for_each_variation(self) -> None:
        pack = make_pack()
        pack["parameters"]["target"] = "One-Shot Kit"
        pack["parameters"]["variations"] = 2
        pack["files"] = [
            {
                "file": f"kit_{index}.wav",
                "peak": 0.6,
                "rms": 0.2,
                "crest_db": 9.5,
                "variation": 1 if index < 9 else 2,
            }
            for index in range(16)
        ]
        with self.assertRaisesRegex(ValueError, "exactly 8 file"):
            ventusample_metrics(pack)

    def test_v2_metrics_validate_tonal_and_stochastic_metadata(self) -> None:
        pack = make_pack_v2()
        metrics = ventusample_metrics(pack)
        self.assertEqual(len(metrics), 22)
        self.assertAlmostEqual(metrics["bpm_normalized"], 93 / 190)
        report = compare_ventusample_packs(pack, pack)
        self.assertTrue(report["same_schema"])
        self.assertTrue(report["same_musical_key"])
        self.assertTrue(report["same_mode_family"])
        self.assertEqual(report["reference"]["stochastic_topology"], "parallel")

    def test_v2_rejects_bad_mode_and_stochastic_route_metadata(self) -> None:
        invalid_mode = make_pack_v2()
        invalid_mode["parameters"]["mode_family"] = "unknown"
        with self.assertRaisesRegex(ValueError, "mode_family"):
            ventusample_metrics(invalid_mode)
        invalid_route = make_pack_v2()
        invalid_route["files"][0]["stochastic_routes"] = ["../outside"]
        with self.assertRaisesRegex(ValueError, "invalid route"):
            ventusample_metrics(invalid_route)

    def test_v1_and_v2_manifests_are_comparable_without_losing_schema_identity(self) -> None:
        report = compare_ventusample_packs(make_pack(), make_pack_v2())
        self.assertFalse(report["same_schema"])
        self.assertTrue(report["same_style"])
        self.assertEqual(report["schema"], REAPER_VENTUSAMPLE_COMPARISON_SCHEMA)

    def test_reaper_language_builtins_can_audit_a_manifest_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pack.json").write_text(json.dumps(make_pack()), encoding="utf-8")
            script = root / "audit.rpr"
            source = (
                f"make pack := read_json({json.dumps(str(root / 'pack.json'))})\n"
                "make metrics := ventusample_metrics(pack)\n"
                "make report := ventusample_compare(pack, pack)\n"
                'emit report["schema"]\n'
                'emit text(metrics["bpm_normalized"])\n'
            )
            output: list[str] = []
            Interpreter(output=output.append).run(source, filename=str(script))
            self.assertEqual(output[0], REAPER_VENTUSAMPLE_COMPARISON_SCHEMA)
            self.assertAlmostEqual(float(output[1]), 93 / 190)


if __name__ == "__main__":
    unittest.main()
