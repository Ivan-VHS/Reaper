from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter, ModuleCycleError, MemoryManager, RegionError, RuntimeDebugger
from reaper.errors import ReaperRuntimeError
from reaper.modules import ModuleLoader


class ModuleRuntimeTests(unittest.TestCase):
    def test_import_alias_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "math.rpr").write_text(
                "export craft add(a, b) {\n    yield a + b\n}\n",
                encoding="utf-8",
            )
            main = root / "main.rpr"
            source = 'import "math.rpr" as math\nemit math["add"](20, 22)\n'
            main.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(main))
            self.assertEqual(output, ["42"])

    def test_import_without_alias_exports_names_into_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "values.rpr").write_text(
                "export make answer := 42\n",
                encoding="utf-8",
            )
            main = root / "main.rpr"
            source = 'import "values.rpr"\nemit answer\n'
            main.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(main))
            self.assertEqual(output, ["42"])

    def test_cyclic_import_is_reported_with_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = root / "a.rpr"
            b = root / "b.rpr"
            a.write_text('import "b.rpr" as b\n', encoding="utf-8")
            b.write_text('import "a.rpr" as a\n', encoding="utf-8")
            with self.assertRaisesRegex(ModuleCycleError, "cyclic .rpr import"):
                Interpreter(output=lambda _line: None).run(a.read_text(encoding="utf-8"), str(a))

    def test_dependency_graph_scans_transitive_imports_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "c.rpr").write_text('export make value := 1\n', encoding="utf-8")
            (root / "b.rpr").write_text('import "c.rpr"\n', encoding="utf-8")
            (root / "a.rpr").write_text('import "b.rpr"\n', encoding="utf-8")
            graph = ModuleLoader(Interpreter()).scan(str(root / "a.rpr"))
            a = str((root / "a.rpr").resolve())
            b = str((root / "b.rpr").resolve())
            c = str((root / "c.rpr").resolve())
            self.assertEqual(graph[a], [b])
            self.assertEqual(graph[b], [c])
            self.assertEqual(graph[c], [])


class ManagedRuntimeTests(unittest.TestCase):
    def test_heap_tracks_reachable_and_collects_unreachable_allocations(self) -> None:
        heap = MemoryManager()
        live = heap.track([1, 2, 3])
        heap.track({"nested": [4, 5]})
        self.assertEqual(heap.stats()["objects"], 3)
        self.assertEqual(heap.collect([live]), 2)
        self.assertEqual(heap.stats()["objects"], 1)

    def test_region_closes_only_when_its_allocations_are_unreachable(self) -> None:
        heap = MemoryManager()
        region = heap.begin_region()
        value = heap.track([1])
        with self.assertRaisesRegex(RegionError, "still reachable"):
            heap.end_region(region, [value])
        self.assertEqual(heap.end_region(region, []), 1)
        self.assertEqual(heap.stats()["regions"], 0)

    def test_files_are_closed_deterministically_after_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "resource.txt"
            output: list[str] = []
            interpreter = Interpreter(output=output.append)
            source = (
                'make handle := file_open("resource.txt", "w")\n'
                'file_write(handle, "reaper")\n'
                'file_close(handle)\n'
                'emit resource_stats()["open_files"]\n'
            )
            interpreter.run(source, str(Path(directory) / "main.rpr"))
            self.assertEqual(target.read_text(encoding="utf-8"), "reaper")
            self.assertEqual(output, ["0"])
            failing = Interpreter(output=lambda _line: None)
            with self.assertRaisesRegex(ReaperRuntimeError, "division by zero"):
                failing.run(
                    'make handle := file_open("failed.txt", "w")\nemit 1 / 0\n',
                    str(Path(directory) / "main.rpr"),
                )
            self.assertEqual(failing.resources.stats()["open_files"], 0)

    def test_with_file_closes_resource_even_when_callback_returns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "with.txt"
            source = (
                'craft write(handle) {\n'
                '    file_write(handle, "scoped")\n'
                '}\n'
                'with_file("with.txt", "w", write)\n'
                'emit resource_stats()["open_files"]\n'
            )
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(Path(directory) / "main.rpr"))
            self.assertEqual(target.read_text(encoding="utf-8"), "scoped")
            self.assertEqual(output, ["0"])

    def test_native_ffi_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "native FFI is disabled"):
            Interpreter(output=lambda _line: None).run('ffi_open("missing.so")')


class VirtualMachineTests(unittest.TestCase):
    SOURCE = """
craft double(value) { yield value * 2 }
craft even(value) { yield value % 2 == 0 }
vary total := 0
each value in [1, 2, 3, 4] {
    change total := total + value
}
loop while total < 12 {
    change total := total + 1
}
when total == 12 {
    emit [1, 2, 3, 4] :: map(double) :: filter(even)
} otherwise {
    emit "wrong"
}
emit total
"""

    def test_vm_matches_treewalk_for_functions_pipelines_and_control_flow(self) -> None:
        outputs = {}
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(self.SOURCE, engine=engine)
            outputs[engine] = output
        self.assertEqual(outputs["vm"], outputs["treewalk"])
        self.assertEqual(outputs["vm"], ["[2, 4, 6, 8]", "12"])

    def test_vm_rejects_top_level_yield(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "inside a craft"):
            Interpreter(output=lambda _line: None).run("yield 1", engine="vm")


class DebuggerTests(unittest.TestCase):
    def test_breakpoint_snapshot_contains_variables_and_call_stack(self) -> None:
        snapshots = []
        debugger = RuntimeDebugger({2}, snapshots.append)
        source = (
            "craft double(value) {\n"
            "    yield value * 2\n"
            "}\n"
            "make start := 10\n"
            "emit double(start)\n"
        )
        Interpreter(output=lambda _line: None, debugger=debugger).run(source)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].line, 2)
        self.assertEqual(snapshots[0].variables["start"], 10)
        self.assertEqual(snapshots[0].call_stack, ["double"])


if __name__ == "__main__":
    unittest.main()
