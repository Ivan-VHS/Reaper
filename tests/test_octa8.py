from __future__ import annotations
import unittest
from reaper import Interpreter
from reaper.octa8 import Octa8Error, KINDS, octa8_assert_kind, octa8_digest, octa8_kind, octa8_map, octa8_pack, octa8_unpack, octa8_validate

class Octa8Tests(unittest.TestCase):
    def test_all_kinds_round_trip(self):
        values = [None, True, -7, 1.25, "Reaper", b"octa", [1, "x"], {"b": 2, "a": False}]
        self.assertEqual([octa8_kind(v) for v in values], list(KINDS))
        for value in values:
            self.assertEqual(octa8_unpack(octa8_pack(value)), value)

    def test_nested_values_and_canonical_digest(self):
        self.assertEqual(octa8_unpack(octa8_pack({"nested": [b"abc", {"flag": True}]})), {"nested": [b"abc", {"flag": True}]})
        self.assertEqual(octa8_digest(octa8_pack({"a": 1, "b": 2})), octa8_digest(octa8_pack({"b": 2, "a": 1})))

    def test_invalid_values_fail_closed(self):
        for value in (float("nan"), float("inf"), 2**63, object()):
            with self.assertRaises(Octa8Error):
                octa8_pack(value)
        self.assertFalse(octa8_validate({"schema": "wrong", "kind": "text", "value": "x"}))
        self.assertFalse(octa8_validate({"schema": "ivan-vhs.octa8.v1", "kind": "boolean", "value": 1}))

    def test_map_and_kind_assertion(self):
        envelope = octa8_pack(21)
        self.assertTrue(octa8_assert_kind(envelope, "integer"))
        self.assertEqual(octa8_unpack(octa8_map(envelope, lambda v: v * 2)), 42)
        with self.assertRaises(Octa8Error):
            octa8_assert_kind(envelope, "text")

    def test_language_builtins_treewalk_and_vm(self):
        source = 'make value := [1, 2, 3]\nmake packed := value :: octa8_pack()\nassert(octa8_validate(packed), "invalid OCTA envelope")\nemit text(packed :: octa8_unpack())'
        for engine in ("treewalk", "vm"):
            lines = []
            Interpreter(output=lines.append).run(source, engine=engine)
            self.assertEqual(lines, ["[1, 2, 3]"])

if __name__ == "__main__":
    unittest.main()
