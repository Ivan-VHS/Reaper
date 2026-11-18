from __future__ import annotations

import unittest

from reaper.security import (
    CapabilityAuthority, CapabilityError, capability_scope, require_capability,
)


class CapabilityTests(unittest.TestCase):
    def test_capability_is_explicit_and_scoped(self) -> None:
        authority = CapabilityAuthority(b"0123456789abcdef0123456789abcdef")
        token = authority.issue("filesystem.read", "/tmp")
        with self.assertRaises(CapabilityError):
            require_capability("filesystem.read", "/tmp")
        with capability_scope(authority, token):
            self.assertIs(require_capability("filesystem.read", "/tmp"), token)
        with self.assertRaises(CapabilityError):
            require_capability("filesystem.read", "/tmp")

    def test_capability_is_bound_to_permission_and_subject(self) -> None:
        authority = CapabilityAuthority(b"0123456789abcdef0123456789abcdef")
        token = authority.issue("native.load", "/trusted/libsample.so")
        self.assertTrue(authority.verify(token, "native.load", "/trusted/libsample.so"))
        self.assertFalse(authority.verify(token, "native.load", "/other/lib.so"))
        self.assertFalse(authority.verify(token, "filesystem.read", "/trusted/libsample.so"))

    def test_revocation_invalidates_existing_token(self) -> None:
        authority = CapabilityAuthority(b"0123456789abcdef0123456789abcdef")
        token = authority.issue("clock.read")
        authority.revoke(token)
        self.assertFalse(authority.verify(token, "clock.read"))


if __name__ == "__main__":
    unittest.main()
