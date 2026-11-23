from __future__ import annotations

import unittest

from reaper import Interpreter
from reaper.ir import lower, verify
from reaper.parser import parse


class NativeCompilerSevenStageFrontendTests(unittest.TestCase):
    def test_dictionary_literal_works_in_reference_runtime(self) -> None:
        output: list[str] = []
        source = '''
make inventory := {"apples": 4, "pears": 2}
emit inventory["apples"]
emit inventory["pears"]
'''
        Interpreter(output=output.append).run(source, "collections.rpr")
        self.assertEqual(output, ["4", "2"])

    def test_dictionary_literal_flows_through_canonical_ir_and_vm(self) -> None:
        source = 'make values := {"first": 13}\\nemit values["first"]\\n'
        tree = parse(source, "map-ir.rpr")
        module = lower(tree, "map-ir.rpr")
        verify(module)
        output: list[str] = []
        Interpreter(output=output.append).run(source, "map-ir.rpr", engine="vm")
        self.assertEqual(output, ["13"])

    def test_dictionary_keys_must_be_hashable(self) -> None:
        output: list[str] = []
        with self.assertRaisesRegex(Exception, "not hashable"):
            Interpreter(output=output.append).run('make data := {[1, 2]: 3}\\n', "bad-map.rpr")

    def test_dictionary_literal_rejects_missing_separator(self) -> None:
        with self.assertRaisesRegex(Exception, "expected ':'"):
            parse('emit {"name" 4}\\n', "bad-map.rpr")


if __name__ == "__main__":
    unittest.main()
