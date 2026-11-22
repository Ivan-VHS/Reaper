from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class PathBuiltinTests(unittest.TestCase):
    def capture(self, source: str, filename: str, engine: str = "treewalk") -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, filename, engine=engine)
        return output

    def test_path_helpers_are_script_relative_in_both_engines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "sample.json").write_text("{}", encoding="utf-8")
            script = root / "automation" / "audit.rpr"
            script.parent.mkdir()
            script.write_text("", encoding="utf-8")
            source = """
            let path = path_join("..", "data", "sample.json")
            emit path_name(path)
            emit path_stem(path)
            emit path_suffix(path)
            emit path_exists(path)
            emit path_is_file(path)
            emit path_is_dir("..")
            emit absolute_path(path)
            """
            expected = [
                "sample.json", "sample", ".json", "true", "true", "true",
                str((root / "data" / "sample.json").resolve()),
            ]
            for engine in ("treewalk", "vm"):
                with self.subTest(engine=engine):
                    self.assertEqual(self.capture(source, str(script), engine), expected)

    def test_path_helpers_reject_non_text_and_nul(self) -> None:
        for source in (
            'emit absolute_path("")',
            'emit absolute_path("bad\\0path")',
            "emit path_join()",
        ):
            with self.subTest(source=source):
                with self.assertRaises(Exception):
                    Interpreter(output=lambda _line: None).run(source)

    def test_path_helpers_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "keep.txt"
            original.write_text("stable", encoding="utf-8")
            source = f'emit path_is_file("{original.as_posix()}")'
            output: list[str] = []
            Interpreter(output=output.append).run(source)
            self.assertEqual(output, ["true"])
            self.assertEqual(original.read_text(encoding="utf-8"), "stable")


if __name__ == "__main__":
    unittest.main()
