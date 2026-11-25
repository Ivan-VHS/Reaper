from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter, ReaperRuntimeError
from reaper.ventusample import (
    VENTUSAMPLE_COMPARISON_SCHEMA,
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
        "files": [{
            "file": "VentuSample_East_Coast_93BPM_C_full_loop_v1.wav",
            "peak": 0.65,
            "rms": 0.19,
            "crest_db": 10.68,
            "variation": 1,
        }],
    }


class VentuSamplePackRuntimeTests(unittest.TestCase):
    def test_metrics_validate_and_normalize_all_22_descriptors(self) -> None:
        metrics = ventusample_metrics(make_pack())
        self.assertEqual(len(metrics), 22)
        self.assertAlmostEqual(metrics["bpm_normalized"], 93 / 190)
        self.assertAlmostEqual(metrics["mean_peak"], 0.65)
        self.assertAlmostEqual(metrics["mean_rms"], 0.19)
        self.assertEqual(list(metrics), sorted(metrics))

    def test_schema_style_enum_matches_runtime_profile(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "reaper" / "ventusample_pack.v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        styles = set(schema["properties"]["parameters"]["properties"]["style"]["enum"])
        from reaper.ventusample import _STYLES
        self.assertEqual(styles, _STYLES)

    def test_identical_comparison_has_zero_distance_and_stable_digest(self) -> None:
        pack = make_pack()
        first = compare_ventusample_packs(pack, pack)
        second = compare_ventusample_packs(pack, pack)
        self.assertEqual(first["schema"], VENTUSAMPLE_COMPARISON_SCHEMA)
        self.assertEqual(first["euclidean_distance"], 0.0)
        self.assertEqual(first["report_sha256"], second["report_sha256"])
        self.assertEqual(first["distance_backend"], "python-standard-library")

    def test_changed_descriptors_are_reported(self) -> None:
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

    def test_path_traversal_and_non_finite_measurements_are_rejected(self) -> None:
        unsafe = make_pack()
        unsafe["files"][0]["file"] = "../outside.wav"
        with self.assertRaisesRegex(ValueError, "simple relative filename"):
            ventusample_metrics(unsafe)
        invalid = make_pack()
        invalid["files"][0]["peak"] = float("nan")
        with self.assertRaisesRegex(ValueError, "must be finite"):
            ventusample_metrics(invalid)

    def test_variation_cardinality_and_one_shot_layout_are_enforced(self) -> None:
        incomplete = make_pack()
        incomplete["parameters"]["variations"] = 2
        with self.assertRaisesRegex(ValueError, "exactly 2 records"):
            ventusample_metrics(incomplete)
        one_shot = make_pack()
        one_shot["parameters"]["target"] = "One-Shot Kit"
        one_shot["parameters"]["variations"] = 2
        one_shot["files"] = [
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
            ventusample_metrics(one_shot)

    def test_rpr_runtime_can_load_and_compare_pack_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pack.json").write_text(json.dumps(make_pack()), encoding="utf-8")
            source = '''
            make pack := read_json("pack.json")
            make metrics := ventusample_metrics(pack)
            make report := ventusample_compare(pack, pack)
            emit report["schema"]
            emit text(metrics["bpm_normalized"])
            emit report["distance_backend"]
            '''
            import os
            original = Path.cwd()
            try:
                os.chdir(root)
                output: list[str] = []
                Interpreter(output=output.append).run(source, "ventusample.rpr", engine="vm")
            finally:
                os.chdir(original)
        self.assertEqual(output, [
            VENTUSAMPLE_COMPARISON_SCHEMA,
            str(93 / 190),
            "python-standard-library",
        ])

    def test_rpr_runtime_rejects_unsupported_pack_without_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = make_pack()
            bad["schema"] = "ventusample.pack.v2"
            (root / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
            import os
            original = Path.cwd()
            try:
                os.chdir(root)
                with self.assertRaisesRegex(ReaperRuntimeError, "ventusample_metrics.*schema"):
                    Interpreter(output=lambda _line: None).run(
                        'make pack := read_json("bad.json")\nemit ventusample_metrics(pack)'
                    )
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
