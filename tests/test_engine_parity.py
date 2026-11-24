from __future__ import annotations

import unittest

from reaper import Interpreter


class RuntimeEngineParityTests(unittest.TestCase):
    def run_source(self, source: str, engine: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, engine=engine)
        return output

    def test_treewalk_and_vm_agree_on_control_flow_and_pipelines(self) -> None:
        source = """
        craft twice(value) { yield value * 2 }
        craft add(left, right) { yield left + right }

        vary total := 0
        each item in [1, 2, 3, 4] {
            change total := total + item :: twice()
        }

        when total == 20 and true {
            emit [1, 2, 3] :: map(twice) :: fold(0, add)
        } otherwise {
            emit "unexpected"
        }
        emit total
        """
        self.assertEqual(
            self.run_source(source, "treewalk"),
            self.run_source(source, "vm"),
        )

    def test_treewalk_and_vm_agree_on_scoped_shadowing(self) -> None:
        source = """
        make value := "outer"
        when true {
            make value := "inner"
            emit value
        }
        emit value
        """
        expected = ["inner", "outer"]
        self.assertEqual(self.run_source(source, "treewalk"), expected)
        self.assertEqual(self.run_source(source, "vm"), expected)

    def test_invalid_engine_is_rejected_before_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "engine must be"):
            Interpreter(output=lambda _line: None).run("emit 1", engine="native")


if __name__ == "__main__":
    unittest.main()
