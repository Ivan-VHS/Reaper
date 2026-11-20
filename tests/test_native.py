from __future__ import annotations

import ctypes
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper import native


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeLibrary:
    def __init__(self, version=1):
        self.pytyliki_abi_version = FakeFunction(lambda: version)
        self.pytyliki_v1_norm_f64 = FakeFunction(self.norm)
        self.pytyliki_v1_dot_f64 = FakeFunction(self.dot)
        self.pytyliki_v1_distance_f64 = FakeFunction(self.distance)
        self.pytyliki_v1_orthogonal_f64 = FakeFunction(self.orthogonal)

    @staticmethod
    def norm(vector, count, output):
        values = [vector[index] for index in range(count)]
        output._obj.value = sum(value * value for value in values) ** 0.5
        return 0

    @staticmethod
    def dot(left, right, count, output):
        output._obj.value = sum(left[index] * right[index] for index in range(count))
        return 0

    @staticmethod
    def distance(left, right, count, output):
        output._obj.value = sum((left[index] - right[index]) ** 2 for index in range(count)) ** 0.5
        return 0

    @staticmethod
    def orthogonal(left, right, count, tolerance, output):
        a = [left[index] for index in range(count)]
        b = [right[index] for index in range(count)]
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        output._obj.value = int(na == 0 or nb == 0 or abs(dot / (na * nb)) <= tolerance)
        return 0


class NativeBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        native._load_library.cache_clear()

    def tearDown(self) -> None:
        native._load_library.cache_clear()

    def test_explicit_path_and_numeric_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary()) as loader:
                self.assertEqual(native.pytyliki_norm([3, 4], str(path)), 5.0)
                self.assertEqual(native.pytyliki_dot([3, 4], [0, 2], str(path)), 8.0)
                self.assertEqual(native.pytyliki_distance([3, 4], [0, 0], str(path)), 5.0)
                self.assertTrue(native.pytyliki_orthogonal([1, 0], [0, 1], 1e-12, str(path)))
                self.assertEqual(loader.call_count, 1)

    def test_rejects_relative_path_missing_file_and_wrong_abi(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute"):
            native._load_library("pytyliki_ffi.dll")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with self.assertRaisesRegex(ValueError, "unsupported Pytyliki ABI"):
                with patch("reaper.native.ctypes.CDLL", return_value=FakeLibrary(version=2)):
                    native._load_library(str(path))

    def test_vectors_are_bounded_and_finite(self) -> None:
        with self.assertRaises(TypeError):
            native._vector([True])
        with self.assertRaises(ValueError):
            native._vector([float("nan")])
        with self.assertRaises(ValueError):
            native._vector([1.0] * 4097)


if __name__ == "__main__":
    unittest.main()
