from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter, OverrideAuthority, SystemFunctionError


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_MODULE = ROOT / "stdlib" / "system.rpr"


class ReaperSystemFunctionTests(unittest.TestCase):
    def _run_library(self, engine: str = "treewalk") -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            payload = {
                "contracts": [
                    {"id": "base", "fields": {"id": "u64", "mode": "text"}},
                    {
                        "id": "device",
                        "depends_on": ["base"],
                        "fields": {"mode": "text", "latency": "u32"},
                    },
                ],
                "before": [
                    {"id": "a", "value": 1},
                    {"id": "b", "value": 2},
                ],
                "after": [
                    {"id": "a", "value": 3},
                    {"id": "c", "value": 4},
                ],
                "fixtures": [
                    {"before": {"schema": 1, "rows": [1, 2]}},
                ],
            }
            (work / "input.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            source = f'''
import "{SYSTEM_MODULE.as_posix()}" as system
make input := read_json("input.json")

craft accept(before, after) {{
    yield size(after) == 2
}}
craft arena_work() {{
    make scratch := [1, 2, 3, 4]
    yield 7
}}
craft double(value) {{
    yield value * 2
}}
craft migrate(state) {{
    yield [state, "migrated"]
}}
craft rollback(state) {{
    yield state[0]
}}

make contracts := system["contract_graph_check"](input["contracts"])
make arena := system["arena_slot"](65536, arena_work)
make budget := system["worker_budget"](1000, 65536, double, [21], input["before"])
make plan := system["diff_reconcile"](input["before"], input["after"], "id")
make applied := system["reconcile_apply"](input["before"], plan, accept)
make matched := system["ephemeral_match"]("temporary-secret", "temporary-secret")
make lease := system["lease_window"](0, 2, 86400000)
make mutation := system["guarded_mutation"](input["before"], input["after"], "override", nothing, manual_token)
make measured := system["latency_measure"]("double", double, [21])
make profile := system["latency_report"]()
make local_ok := system["local_only_check"](true, ["file.read"], ["reaper.core"])
make local_bad := system["local_only_check"](true, ["network.http"], ["reaper.core"])
make rollback_result := system["rollback_plan_check"](migrate, rollback, input["fixtures"])

emit contracts["ok"]
emit contracts["phase"]
emit arena["value"]
emit budget["status"]
emit budget["value"]
emit applied["committed"]
emit matched
emit lease["active"]
emit mutation["mode"]
emit size(system["revision_log"]())
emit measured
emit profile["schema"]
emit local_ok["ok"]
emit local_bad["ok"]
emit rollback_result["ok"]
'''
            path = work / "main.rpr"
            path.write_text(source, encoding="utf-8")
            output: list[str] = []
            authority = OverrideAuthority()
            interpreter = Interpreter(output=output.append, override_authority=authority)
            interpreter.globals.define(
                "manual_token", authority.issue("mutation:override", 30_000)
            )
            interpreter.run(source, str(path), engine=engine)
            return output

    def test_public_reaper_functions_work_in_treewalk_and_vm(self) -> None:
        expected = [
            "true",
            "runtime_preflight",
            "7",
            "completed",
            "42",
            "true",
            "true",
            "true",
            "override",
            "1",
            "42",
            "reaper.latency-profile.v1",
            "true",
            "false",
            "true",
        ]
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self._run_library(engine), expected)

    def test_contract_graph_reports_cycles_and_inherited_field_conflicts(self) -> None:
        interpreter = Interpreter(output=lambda _line: None)
        cyclic = interpreter.system_functions.contract_graph_check([
            {"id": "alpha", "depends_on": ["beta"], "fields": {"state": "u32"}},
            {"id": "beta", "depends_on": ["alpha"], "fields": {"state": "text"}},
        ])
        self.assertFalse(cyclic["ok"])
        self.assertTrue(any("cycle" in item for item in cyclic["errors"]))

        conflicting_parents = interpreter.system_functions.contract_graph_check([
            {"id": "base_a", "fields": {"state": "u32"}},
            {"id": "base_b", "fields": {"state": "text"}},
            {"id": "child", "depends_on": ["base_a", "base_b"], "fields": {}},
        ])
        self.assertFalse(conflicting_parents["ok"])
        self.assertTrue(any("inherited field 'state' conflicts" in item
                            for item in conflicting_parents["errors"]))

    def test_script_cannot_issue_its_own_override_token(self) -> None:
        with self.assertRaisesRegex(Exception, "unknown name '_override_issue'"):
            Interpreter(output=lambda _line: None, override_authority=OverrideAuthority()).run(
                '_override_issue("mutation:override", 30000)'
            )

    def test_lease_remaining_includes_future_start_delay(self) -> None:
        lease = Interpreter(output=lambda _line: None).system_functions.lease_window(
            86_400_000, 2, 0
        )
        self.assertFalse(lease["active"])
        self.assertEqual(lease["remaining_ms"], 3 * 86_400_000)

    def test_local_only_detects_url_schemes_and_net_imports(self) -> None:
        functions = Interpreter(output=lambda _line: None).system_functions
        self.assertFalse(functions.local_only_check(True, ["https://example.test"], [])["ok"])
        self.assertFalse(functions.local_only_check(True, [], ["net.socket"])["ok"])

    def test_worker_memory_budget_halts_without_claiming_process_isolation(self) -> None:
        source = '''
craft allocate() {
    yield [1, 2, 3, 4, 5, 6]
}
make result := _worker_budget(1000, 1, allocate, [], nothing)
emit result["status"]
emit result["isolation"]
'''
        output: list[str] = []
        Interpreter(output=output.append).run(source)
        self.assertEqual(output[0], "halted")
        self.assertEqual(output[1], "cooperative_reference_runtime")

    def test_override_tokens_are_scoped_single_use_and_host_owned(self) -> None:
        authority = OverrideAuthority()
        interpreter = Interpreter(output=lambda _line: None, override_authority=authority)
        token = authority.issue("mutation:override", 10_000)
        result = interpreter.system_functions.guarded_mutation(
            {"value": 1}, {"value": 2}, "override", None, token
        )
        self.assertEqual(result["revision"], 1)
        with self.assertRaisesRegex(SystemFunctionError, "single-use"):
            interpreter.system_functions.guarded_mutation(
                {"value": 2}, {"value": 3}, "override", None, token
            )

    def test_automatic_mutation_requires_validator(self) -> None:
        source = '''
craft reject(before, after) { yield false }
make result := _guarded_mutation([1], [2], "auto", reject, nothing)
'''
        with self.assertRaisesRegex(Exception, "strict validator"):
            Interpreter(output=lambda _line: None).run(source)

    def test_region_budget_is_enforced_and_released(self) -> None:
        source = '''
craft work() {
    make scratch := [1, 2, 3]
    yield 9
}
make result := _arena_slot(work, 1)
'''
        interpreter = Interpreter(output=lambda _line: None)
        with self.assertRaisesRegex(Exception, "memory limit"):
            interpreter.run(source)
        self.assertEqual(interpreter.memory.stats()["regions"], 0)

    def test_ephemeral_comparison_and_local_only_reject_network_effects(self) -> None:
        functions = Interpreter(output=lambda _line: None).system_functions
        self.assertTrue(functions.ephemeral_match("same", b"same"))
        self.assertFalse(functions.ephemeral_match("left", "right"))
        self.assertTrue(functions.local_only_check(True, ["file.read"], ["reaper.core"])["ok"])
        self.assertFalse(functions.local_only_check(True, ["network.http"], [])["ok"])

    def test_rollback_plan_requires_a_real_inverse(self) -> None:
        source = '''
craft migrate(state) { yield [state, "next"] }
craft wrong_rollback(state) { yield nothing }
make result := _rollback_plan_check(migrate, wrong_rollback, [{"before": [1, 2]}])
emit result["ok"]
'''
        output: list[str] = []
        Interpreter(output=output.append).run(source)
        self.assertEqual(output, ["false"])


if __name__ == "__main__":
    unittest.main()
