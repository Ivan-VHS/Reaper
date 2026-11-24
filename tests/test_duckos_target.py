from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.validate_system_target import (
    DEFAULT_PROFILE,
    DEFAULT_SCHEMA,
    TargetProfileError,
    validate_files,
    validate_profile,
)


class DuckOSSystemTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = json.loads(DEFAULT_PROFILE.read_text(encoding="utf-8"))
        self.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_checked_in_profile_is_valid_and_explicitly_planned(self) -> None:
        result = validate_files()
        self.assertTrue(result["ok"])
        self.assertEqual(result["target_id"], "duckos-kernel")
        self.assertEqual(result["maturity"], "planned")
        self.assertFalse(result["native_aot_freestanding"])
        self.assertFalse(result["native_aot_supports_duckos_source"])

    def test_unapproved_target_must_not_freeze_architecture_or_abi(self) -> None:
        self.profile["target"]["architecture"] = "x86_64"
        with self.assertRaisesRegex(TargetProfileError, "must remain unset"):
            validate_profile(self.profile, self.schema)

    def test_hosted_scalar_aot_cannot_claim_freestanding_support(self) -> None:
        self.profile["current_toolchain"]["native_aot"]["freestanding"] = True
        with self.assertRaisesRegex(TargetProfileError, "must not be reported as freestanding"):
            validate_profile(self.profile, self.schema)

    def test_compiler_capability_ids_must_be_unique(self) -> None:
        self.profile["required_compiler_capabilities"].append(
            dict(self.profile["required_compiler_capabilities"][0])
        )
        with self.assertRaisesRegex(TargetProfileError, "must be unique"):
            validate_profile(self.profile, self.schema)

    def test_bootability_claim_requires_an_explicit_safety_boundary(self) -> None:
        self.profile["safety_policy"]["target_profile_does_not_claim_bootability"] = False
        with self.assertRaisesRegex(TargetProfileError, "must not claim bootability"):
            validate_profile(self.profile, self.schema)


if __name__ == "__main__":
    unittest.main()
