from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "examples" / "applications"

APPLICATIONS = (
    "telemetry_guard",
    "log_sieve",
    "game_tuner",
    "table_cleaner",
    "api_gateway",
    "secret_patrol",
    "latency_probe",
    "dag_runner",
    "span_indexer",
    "ledger_reconcile",
    "driver_manifest",
    "most_build",
    "text_shield",
    "physics_bench",
    "bf_vm",
)


def run_application(name: str) -> list[str]:
    path = APP_DIR / f"{name}.rpr"
    output: list[str] = []
    source = path.read_text(encoding="utf-8")
    Interpreter(output=output.append).run(source, str(path))
    return output


class ApplicationSmokeTests(unittest.TestCase):
    def test_all_fifteen_applications_execute(self) -> None:
        self.assertEqual(len(tuple(APP_DIR.glob("*.rpr"))) - 1, 15)
        for name in APPLICATIONS:
            with self.subTest(application=name):
                self.assertTrue(run_application(name), f"{name} produced no output")

    def test_telemetry_splits_valid_and_invalid_readings(self) -> None:
        output = run_application("telemetry_guard")
        self.assertEqual(output[:2], ["accepted = 2", "rejected = 2"])
        self.assertIn("sensor-01", output[2])
        self.assertIn("temp_out_of_range", output[3])

    def test_log_sieve_counts_server_errors(self) -> None:
        output = run_application("log_sieve")
        self.assertEqual(output[0], "[[auth, 2]]")
        self.assertEqual(output[1:], ["malformed = 1", "5xx = 2"])

    def test_game_tuner_selects_thermal_and_memory_profiles(self) -> None:
        output = run_application("game_tuner")
        self.assertIn("thermal_safe", output[0])
        self.assertIn("balanced_low_vram", output[1])
        self.assertIn("low_latency", output[2])

    def test_table_cleaner_normalizes_and_deduplicates_skus(self) -> None:
        output = run_application("table_cleaner")
        self.assertIn("A-1", output[0])
        self.assertIn("12.5", output[0])
        self.assertIn("C-3", output[0])
        self.assertNotIn("bad", output[0])

    def test_gateway_reuses_cached_response_for_duplicate_request_id(self) -> None:
        output = run_application("api_gateway")
        self.assertEqual(output[0], "[[ok, alive], [ok, hello], [ok, alive]]")
        self.assertEqual(output[1], "cached responses = 2")

    def test_secret_patrol_redacts_matching_lines(self) -> None:
        output = run_application("secret_patrol")
        self.assertIn("password_assignment", output[0])
        self.assertIn("private_key_block", output[0])
        self.assertNotIn("placeholder-value", output[0])

    def test_latency_probe_uses_nearest_rank_percentiles(self) -> None:
        output = run_application("latency_probe")
        self.assertEqual(output, ["[ok, 7, 27, 51, 51, 51]"])

    def test_dag_runner_returns_dependency_safe_order(self) -> None:
        output = run_application("dag_runner")
        self.assertEqual(output, ["[ok, [prepare, docs, compile, test, package, release]]"])

    def test_span_indexer_preserves_one_based_positions(self) -> None:
        output = run_application("span_indexer")
        self.assertEqual(output, ["[[alpha, 1, 7], [beta, 5, 11]]"])

    def test_ledger_uses_integer_cents(self) -> None:
        output = run_application("ledger_reconcile")
        self.assertEqual(
            output,
            ["[[TX-1, matched, 0], [TX-2, mismatch, -400], [TX-3, orphan_payment, 3000]]"],
        )

    def test_driver_manifest_filters_disabled_and_current_devices(self) -> None:
        output = run_application("driver_manifest")
        self.assertEqual(len(output), 1)
        self.assertIn("Storage controller", output[0])
        self.assertIn("Network adapter", output[0])
        self.assertNotIn("Disabled device", output[0])

    def test_most_uses_executable_russian_aliases(self) -> None:
        output = run_application("most_build")
        self.assertEqual(
            output,
            ["[true, reaper-cli, ready_for_release, sha256:example-digest]"],
        )

    def test_text_shield_returns_three_moderation_levels(self) -> None:
        output = run_application("text_shield")
        self.assertEqual(output, ["[allow, 0]", "[review, 65]", "[block, 80]"])

    def test_physics_bench_checks_energy_bounds(self) -> None:
        output = run_application("physics_bench")
        self.assertEqual(
            output,
            ["[ok, 80.0, [true, 80.0]]", "[ok, 2000.0, [false, invalid_output_energy]]"],
        )

    def test_brainfuck_vm_executes_nested_loop_semantics(self) -> None:
        output = run_application("bf_vm")
        self.assertEqual(output, ["[ok, [45]]"])


if __name__ == "__main__":
    unittest.main()
