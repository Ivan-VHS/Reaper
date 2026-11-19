from __future__ import annotations

import unittest

from reaper.citadel import (
    CitadelRouter,
    RelayError,
    RelayNotFoundError,
    RelayPayloadError,
)


class CitadelRouterTests(unittest.TestCase):
    def test_dispatch_passes_the_original_object_reference(self) -> None:
        router = CitadelRouter()
        payload = {"items": [1, 2]}
        router.register("worker", lambda value: value, payload_type=dict)
        self.assertIs(router.dispatch("worker", payload), payload)

    def test_type_mismatch_is_rejected_and_counted(self) -> None:
        router = CitadelRouter()
        router.register("numbers", lambda value: value + 1, payload_type=int)
        self.assertEqual(router.dispatch("numbers", 4), 5)
        with self.assertRaises(RelayPayloadError):
            router.dispatch("numbers", "4")
        self.assertEqual(router.stats()[0].dispatches, 1)
        self.assertEqual(router.stats()[0].rejected, 1)

    def test_duplicate_unknown_and_capacity_paths(self) -> None:
        router = CitadelRouter(max_routes=1)
        router.register("one", lambda value: value)
        with self.assertRaises(RelayError):
            router.register("one", lambda value: value)
        with self.assertRaises(RelayError):
            router.register("two", lambda value: value)
        with self.assertRaises(RelayNotFoundError):
            router.dispatch("missing", None)
        self.assertEqual(router.destinations(), ("one",))
        self.assertTrue(router.unregister("one"))
        self.assertFalse(router.unregister("one"))

    def test_handler_failure_is_reported_in_stats_and_propagated(self) -> None:
        router = CitadelRouter()
        def fail(_value):
            raise RuntimeError("handler failed")
        router.register("fail", fail)
        with self.assertRaisesRegex(RuntimeError, "handler failed"):
            router.dispatch("fail", None)
        self.assertEqual(router.stats()[0].failures, 1)

    def test_configuration_is_validated(self) -> None:
        with self.assertRaises(ValueError):
            CitadelRouter(max_routes=0)
        with self.assertRaises(TypeError):
            CitadelRouter().register("bad", lambda value: value, payload_type=())


if __name__ == "__main__":
    unittest.main()
