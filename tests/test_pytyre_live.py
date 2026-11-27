from __future__ import annotations

import os
import unittest
from pathlib import Path

from reaper import native


class LivePytylikiAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        library = os.environ.get("PYTYLIKI_LIBRARY")
        if not library:
            raise unittest.SkipTest("PYTYLIKI_LIBRARY is not set; live cross-repository ABI test only")
        path = Path(library)
        if not path.is_absolute() or not path.is_file():
            raise RuntimeError("PYTYLIKI_LIBRARY must be an existing absolute shared-library path")
        cls.library_path = str(path.resolve())
        native._load_library.cache_clear()

    @classmethod
    def tearDownClass(cls) -> None:
        native._load_library.cache_clear()

    def test_real_native_metrics_and_embedded_target_contract(self) -> None:
        self.assertEqual(native.pytyliki_norm([3, 4], self.library_path), 5.0)
        self.assertEqual(native.pytyliki_dot([3, 4], [1, 2], self.library_path), 11.0)
        self.assertEqual(native.pytyliki_distance([3, 4], [0, 0], self.library_path), 5.0)
        self.assertTrue(native.pytyliki_orthogonal([1, 0], [0, 1], 1e-12, self.library_path))

        profiles = native.pytyliki_embedded_profiles(self.library_path)
        self.assertEqual(len(profiles), 3)
        self.assertEqual(profiles[0]["id"], "cortex-m4-reference")

        budget = native.pytyliki_embedded_budget(
            "cortex-m4-reference",
            {
                "text_bytes": 1024,
                "rodata_bytes": 256,
                "data_bytes": 128,
                "bss_bytes": 512,
                "noinit_bytes": 64,
                "stack_reserve_bytes": 2048,
            },
            self.library_path,
        )
        self.assertEqual(budget["flash_used_bytes"], 1408)
        self.assertEqual(budget["sram_used_bytes"], 2752)
        self.assertTrue(budget["flash_fits"])
        self.assertTrue(budget["sram_fits"])


if __name__ == "__main__":
    unittest.main()
