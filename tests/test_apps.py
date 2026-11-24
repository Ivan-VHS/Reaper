from __future__ import annotations

import json
import unittest
from pathlib import Path

from reaper.apps import ApplicationInputError, describe_app, list_apps, run_app


class ReaperApplicationSuiteTests(unittest.TestCase):
    def test_registry_has_all_fifteen_handlers(self):
        catalog = list_apps()
        self.assertEqual(catalog["schema"], "reaper.application-suite.v1")
        self.assertEqual(catalog["count"], 15)
        self.assertEqual(len({item["id"] for item in catalog["applications"]}), 15)

    def test_describe_rejects_unknown_application(self):
        with self.assertRaises(ApplicationInputError):
            describe_app("not-an-app")

    def test_telemetry_guard_partitions_valid_and_invalid_readings(self):
        result = run_app("telemetry_guard", {"readings": [
            {"id": "a", "temp_c": 25, "voltage_v": 12, "current_a": 2},
            {"id": "b", "temp_c": 151, "voltage_v": 12, "current_a": 1},
        ]})["result"]
        self.assertEqual(result["counts"], {"received": 2, "accepted": 1, "rejected": 1})
        self.assertEqual(result["accepted"][0]["power_w"], 24)
        self.assertEqual(result["rejected"][0]["reason"], "temp_out_of_range")

    def test_log_sieve_groups_5xx_by_service(self):
        result = run_app("log_sieve", {"lines": [
            "2026-01-01T00:00:00Z | api | 500 | failure",
            "2026-01-01T00:00:01Z | api | 503 | unavailable",
            "2026-01-01T00:00:02Z | auth | 200 | ok",
            "broken",
        ]})["result"]
        self.assertEqual(result["by_service"], [{"service": "api", "count": 2}])
        self.assertEqual(result["counts"]["malformed"], 1)

    def test_game_tuner_is_recommendation_only(self):
        result = run_app("game_tuner", {"hardware": {
            "gpu_temp_c": 90, "cpu_load_pct": 25, "vram_free_mb": 4096,
        }})["result"]
        self.assertEqual(result["profile"]["preset"], "thermal_safe")
        self.assertFalse(result["applied"])

    def test_table_cleaner_uses_decimal_strings_and_stable_sku_dedup(self):
        result = run_app("table_cleaner", {"rows": [
            {"sku": " ab-1 ", "price": "10,235", "qty": -2},
            {"sku": "AB-1", "price": "12.00", "qty": 4},
            {"sku": "xy-2", "price": "3.50", "qty": "5", "currency": "eur"},
        ]})["result"]
        self.assertEqual(result["counts"]["duplicates"], 1)
        self.assertEqual(result["rows"][0], {"sku": "AB-1", "price": "10.24", "qty": 0, "currency": "USD"})
        self.assertEqual(result["rows"][1]["currency"], "EUR")

    def test_api_gateway_replays_identical_idempotency_keys(self):
        payload = {
            "request": {"request_id": "req-1", "method": "POST", "path": "/orders", "body": {"n": 1}},
            "routes": [{"id": "orders.create", "method": "POST", "path": "/orders", "handler": "create_order"}],
        }
        first = run_app("api_gateway", payload)["result"]
        replay_payload = dict(payload)
        replay_payload["cache"] = {"req-1": {
            "fingerprint": first["fingerprint"], "response": first["response"],
        }}
        replay = run_app("api_gateway", replay_payload)["result"]
        self.assertEqual(first["decision"], "dispatch_plan")
        self.assertEqual(replay["decision"], "replay")
        self.assertTrue(replay["cache_hit"])
        self.assertFalse(first["dispatch_performed"])

    def test_api_gateway_rejects_idempotency_key_payload_conflict(self):
        payload = {
            "request": {"request_id": "req-1", "method": "POST", "path": "/orders", "body": {"n": 2}},
            "cache": {"req-1": {"fingerprint": "different", "response": {}}},
        }
        with self.assertRaisesRegex(ApplicationInputError, "idempotency_key_reused"):
            run_app("api_gateway", payload)

    def test_secret_patrol_redacts_discovered_values(self):
        secret = "password = super-secret-value"
        result = run_app("secret_patrol", {"files": [
            {"path": "config.env", "content": secret + "\nAKIA1234567890ABCDEF"},
        ]})["result"]
        self.assertEqual(result["finding_count"], 2)
        self.assertNotIn("super-secret-value", json.dumps(result))
        self.assertIn("[REDACTED]", json.dumps(result))

    def test_latency_probe_uses_nearest_rank_percentiles(self):
        result = run_app("latency_probe", {"samples_ms": [4, 1, 3, 2, 5]})["result"]
        self.assertEqual(result["p50_ms"], 3)
        self.assertEqual(result["p95_ms"], 5)
        self.assertEqual(result["p99_ms"], 5)

    def test_dag_runner_returns_stable_dependency_order(self):
        result = run_app("dag_runner", {"tasks": [
            {"id": "compile", "deps": ["fetch"]},
            {"id": "fetch", "deps": []},
            {"id": "package", "deps": ["compile"]},
            {"id": "lint", "deps": ["fetch"]},
        ]})["result"]
        self.assertEqual(result["parallel_levels"], [["fetch"], ["compile", "lint"], ["package"]])
        self.assertFalse(result["execution_performed"])

    def test_dag_runner_rejects_cycles(self):
        with self.assertRaisesRegex(ApplicationInputError, "dependency_cycle"):
            run_app("dag_runner", {"tasks": [
                {"id": "a", "deps": ["b"]}, {"id": "b", "deps": ["a"]},
            ]})

    def test_span_indexer_uses_reaper_craft_tokens(self):
        result = run_app("span_indexer", {
            "source": "craft first() { yield 1 }\ncraft second(x) { yield x }",
            "source_id": "sample.rpr",
        })["result"]
        self.assertEqual([item["name"] for item in result["symbols"]], ["first", "second"])
        self.assertEqual(result["symbols"][0]["span"]["source"], "sample.rpr")

    def test_ledger_reconcile_uses_integer_cents(self):
        result = run_app("ledger_reconcile", {
            "invoices": [{"id": "i-1", "total_cents": 1250}],
            "payments": [
                {"tx_id": "t-1", "invoice_id": "i-1", "amount_cents": 1250},
                {"tx_id": "t-2", "invoice_id": "missing", "amount_cents": 200},
            ],
        })["result"]
        self.assertEqual(result["counts"]["matched"], 1)
        self.assertEqual(result["counts"]["orphaned"], 1)
        self.assertEqual(result["reconciliation"][1]["diff_cents"], 200)

    def test_driver_manifest_is_a_read_only_semver_plan(self):
        result = run_app("driver_manifest", {"devices": [
            {"hw_id": "PCI\\VEN_1234", "name": "GPU", "enabled": True,
             "driver_version": "1.2.0", "latest_version": "1.3.0", "bus_priority": 1},
            {"hw_id": "USB\\VID_1234", "name": "Keyboard", "enabled": False,
             "driver_version": "", "latest_version": "2.0.0"},
        ]})["result"]
        self.assertEqual(len(result["plan"]), 1)
        self.assertFalse(result["installation_performed"])
        self.assertEqual(result["plan"][0]["target_version"], "1.3.0")

    def test_most_build_checks_sha256_format(self):
        result = run_app("most_build", {"artifact": {
            "name": "bundle.bin", "size_bytes": 128, "sha256": "A" * 64,
        }})["result"]
        self.assertEqual(result["status"], "ready_for_release_review")
        self.assertFalse(result["compiler_invoked"])
        with self.assertRaisesRegex(ApplicationInputError, "64 hexadecimal"):
            run_app("most_build", {"artifact": {
                "name": "bundle.bin", "size_bytes": 128, "sha256": "not-a-hash",
            }})

    def test_text_shield_scores_spam_signals(self):
        result = run_app("text_shield", {
            "text": "BUY NOW!!! https://a.test https://b.test https://c.test https://d.test",
            "banned_phrases": ["buy now"],
        })["result"]
        self.assertEqual(result["action"], "block")
        self.assertIn("banned_phrase_match", result["signals"])

    def test_physics_bench_validates_efficiency(self):
        result = run_app("physics_bench", {"run": {
            "mass_kg": 2, "speed_m_s": 3, "input_energy_j": 20,
            "force_n": 10, "distance_m": 2,
        }})["result"]
        self.assertEqual(result["kinetic_energy_j"], 9)
        self.assertEqual(result["work_j"], 20)
        self.assertEqual(result["efficiency_pct"], 45)
        with self.assertRaisesRegex(ApplicationInputError, "invalid_output_energy"):
            run_app("physics_bench", {"run": {
                "mass_kg": 2, "speed_m_s": 10, "input_energy_j": 10,
            }})

    def test_brainfuck_vm_runs_loops_and_enforces_tape_bounds(self):
        result = run_app("bf_vm", {"code": "+++++++[>++++++++<-]>+."})["result"]
        self.assertEqual(result["output"], "A")
        with self.assertRaisesRegex(ApplicationInputError, "tape_pointer_underflow"):
            run_app("bf_vm", {"code": "<"})
        with self.assertRaisesRegex(ApplicationInputError, "unmatched opening"):
            run_app("bf_vm", {"code": "["})

    def test_all_reaper_source_wrappers_parse_and_typecheck(self):
        from reaper.parser import parse
        from reaper.typecheck import TypeChecker

        root = Path(__file__).resolve().parents[1] / "examples" / "apps"
        wrappers = sorted(root.glob("*.rpr"))
        self.assertEqual(len(wrappers), 15)
        for wrapper in wrappers:
            tree = parse(wrapper.read_text(encoding="utf-8"), str(wrapper))
            checked = TypeChecker(str(wrapper)).check(tree)
            self.assertTrue(checked.ok, f"{wrapper.name}: {checked.as_dict()}")


if __name__ == "__main__":
    unittest.main()
