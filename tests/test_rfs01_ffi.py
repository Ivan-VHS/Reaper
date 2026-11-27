from __future__ import annotations

import ctypes
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper.ffi import FfiError
from reaper.rfs01_ffi import (
    PytylikiRFS01Bridge,
    _NodeV1,
)


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeRFS01Library:
    def __init__(self):
        self.pytyliki_rfs01_abi_version = FakeFunction(lambda: 1)
        self.pytyliki_rfs01_validate_node_v1 = FakeFunction(lambda node: 0)
        self.pytyliki_rfs01_validate_link_v1 = FakeFunction(lambda link: 0)
        self.pytyliki_rfs01_validate_signal_v1 = FakeFunction(lambda signal: 0)
        self.pytyliki_rfs01_signal_is_clean_v1 = FakeFunction(lambda signal: 1)
        self.pytyliki_rfs01_pressure_reserve_v1 = FakeFunction(self.reserve)
        self.pytyliki_rfs01_plan_pressure_forward_v1 = FakeFunction(self.pressure)
        self.pytyliki_rfs01_plan_signal_forward_v1 = FakeFunction(self.signal)
        self.pytyliki_rfs01_root_restore_v1 = FakeFunction(self.root)
        self.pytyliki_rfs01_core_restore_v1 = FakeFunction(self.core)

    @staticmethod
    def reserve(node, output):
        item = node._obj
        output._obj.value = item.integrity * (1.0 - min(item.pressure / item.load_limit, 1.0))
        return 0

    @staticmethod
    def _copy(source, output):
        ctypes.memmove(output, ctypes.byref(source), ctypes.sizeof(_NodeV1))

    @classmethod
    def pressure(cls, source, target, link, output):
        src, dst, edge = source._obj, target._obj, link._obj
        if edge.blocked or edge.origin.decode() != src.id.decode() or edge.target.decode() != dst.id.decode():
            return -4
        pressure = dst.pressure + src.pressure * edge.weight
        if pressure > dst.load_limit:
            return -3
        planned = _NodeV1()
        cls._copy(dst, ctypes.byref(planned))
        planned.pressure = pressure
        planned.active = 1
        cls._copy(planned, output)
        return 0

    @classmethod
    def signal(cls, source, target, link, signal, output):
        src, dst, edge, frame = source._obj, target._obj, link._obj, signal._obj
        if edge.blocked:
            return -4
        if frame.origin.decode() != src.id.decode() or not frame.trusted or frame.manufactured:
            return -5
        planned = _NodeV1()
        cls._copy(dst, ctypes.byref(planned))
        planned.noise_db = max(-160.0, dst.noise_db - 4.436974992327127)
        planned.active = 1
        cls._copy(planned, output)
        return 0

    @classmethod
    def root(cls, root, output):
        cls._copy(root._obj, output)
        return 0

    @classmethod
    def core(cls, current, root, output):
        planned = _NodeV1()
        cls._copy(current._obj, ctypes.byref(planned))
        planned.core_seed = root._obj.core_seed
        cls._copy(planned, output)
        return 0


class PytylikiRFS01BridgeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "libpytyliki_ffi.so"
        self.path.touch()

    def tearDown(self):
        self.directory.cleanup()

    def test_records_reserve_flow_and_recovery(self):
        library = FakeRFS01Library()
        with patch("reaper.rfs01_ffi._load_library", return_value=library):
            bridge = PytylikiRFS01Bridge(str(self.path))
            source = {
                "id": "basement", "layer": "Basement", "pressure": 20.0,
                "load_limit": 100.0, "integrity": 0.9, "noise_db": -18.0,
                "core_seed": "root-a", "active": False,
            }
            target = {
                "id": "corridor", "layer": "Corridor", "pressure": 2.0,
                "load_limit": 100.0, "integrity": 0.8, "noise_db": -10.0,
                "core_seed": "root-b", "active": False,
            }
            link = {
                "id": "bridge-1", "origin": "basement", "target": "corridor",
                "channel": "Bridge", "blocked": False, "weight": 0.1,
            }
            signal = {
                "sequence": 1, "origin": "basement", "payload": "pulse",
                "trusted": True, "manufactured": False,
            }

            bridge.validate_node(source)
            bridge.validate_link(link)
            bridge.validate_signal(signal)
            self.assertTrue(bridge.signal_is_clean(signal))
            self.assertAlmostEqual(bridge.reserve(source), 0.72)
            flowed = bridge.plan_pressure_forward(source, target, link)
            self.assertAlmostEqual(flowed["pressure"], 4.0)
            signalled = bridge.plan_signal_forward(source, target, link, signal)
            self.assertAlmostEqual(signalled["noise_db"], -14.436974992327127)
            restored = bridge.restore_core(signalled, target)
            self.assertEqual(restored["core_seed"], "root-b")
            self.assertEqual(restored["noise_db"], signalled["noise_db"])
            self.assertEqual(bridge.restore_root(target), target)
            bridge.close()
            with self.assertRaisesRegex(FfiError, "closed"):
                bridge.reserve(source)

    def test_explicit_absolute_library_path_is_required(self):
        with patch("reaper.rfs01_ffi._load_library", return_value=FakeRFS01Library()):
            with self.assertRaisesRegex(FfiError, "absolute"):
                PytylikiRFS01Bridge("libpytyliki_ffi.so")

    def test_invalid_python_record_is_rejected_before_native_call(self):
        with patch("reaper.rfs01_ffi._load_library", return_value=FakeRFS01Library()):
            bridge = PytylikiRFS01Bridge(str(self.path))
            with self.assertRaisesRegex(FfiError, "node.integrity"):
                bridge.validate_node({
                    "id": "bad", "layer": "Basement", "pressure": 0,
                    "load_limit": 10, "integrity": float("nan"), "noise_db": -10,
                    "core_seed": "root", "active": False,
                })


if __name__ == "__main__":
    unittest.main()
