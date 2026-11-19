from __future__ import annotations

import unittest

from reaper.resources import EpochManager, Region, RegionError


class RegionTests(unittest.TestCase):
    def test_bounded_allocation_and_handle_access(self) -> None:
        region = Region("short-lived", max_items=1)
        reference = region.allocate({"value": 7})
        self.assertEqual(reference.read()["value"], 7)
        with self.assertRaises(RegionError):
            region.allocate("overflow")
        reference.write("updated")
        self.assertEqual(reference.read(), "updated")

    def test_move_invalidates_previous_handle(self) -> None:
        region = Region()
        original = region.allocate(5)
        moved = original.move()
        with self.assertRaises(RegionError):
            original.read()
        self.assertEqual(moved.read(), 5)

    def test_borrow_blocks_reclamation_and_expires_after_scope(self) -> None:
        region = Region()
        reference = region.allocate("data")
        with region.borrow(reference) as borrowed:
            self.assertEqual(borrowed.read(), "data")
            with self.assertRaises(RegionError):
                region.close()
        with self.assertRaises(RegionError):
            borrowed.read()
        region.close()
        with self.assertRaises(RegionError):
            reference.read()

    def test_epoch_manager_reclaims_only_after_boundary(self) -> None:
        manager = EpochManager()
        region = manager.create_region("epoch-0")
        reference = region.allocate(42)
        manager.retire(region)
        self.assertEqual(manager.advance(), ("epoch-0",))
        self.assertTrue(region.is_closed)
        with self.assertRaises(RegionError):
            reference.read()

    def test_retired_region_rejects_new_allocations(self) -> None:
        manager = EpochManager()
        region = manager.create_region()
        manager.retire(region)
        with self.assertRaises(RegionError):
            region.allocate(1)


if __name__ == "__main__":
    unittest.main()
