from __future__ import annotations

import dataclasses
import pickle
import unittest

from reaper.capabilities import (
    CapabilityAuthority,
    CapabilityDenied,
    CapabilityError,
    CapabilityRequest,
    RefinedValue,
    TaintedValue,
    refine_tainted,
)


def request(*, principal="reaper-plugin:dropaul", resource="plugins/dropaul", actions=("invoke", "plan-workflow"), ttl=30):
    return CapabilityRequest.parse({
        "principal": principal,
        "resource": resource,
        "actions": list(actions),
        "ttl_seconds": ttl,
    })


class CapabilityAuthorityTests(unittest.TestCase):
    def test_grant_authorizes_only_its_principal_resource_and_action(self):
        authority = CapabilityAuthority(secret=b"k" * 32)
        token = authority.issue(request())
        decision = authority.verify(
            token,
            principal="REAPER-PLUGIN:Dropaul",
            resource="plugins/dropaul",
            action="plan_workflow",
        )
        self.assertEqual(decision.principal, "reaper-plugin:dropaul")
        self.assertEqual(decision.action, "plan-workflow")
        with self.assertRaises(CapabilityDenied):
            authority.verify(token, principal="reaper-plugin:other", resource="plugins/dropaul", action="invoke")
        with self.assertRaises(CapabilityDenied):
            authority.verify(token, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="network")
        authority.close()

    def test_resource_prefix_is_segment_bounded(self):
        authority = CapabilityAuthority()
        token = authority.issue(request(resource="project/app"))
        authority.verify(token, principal="reaper-plugin:dropaul", resource="project/app/config", action="invoke")
        with self.assertRaises(CapabilityDenied):
            authority.verify(token, principal="reaper-plugin:dropaul", resource="project/application", action="invoke")
        authority.close()

    def test_revocation_and_principal_revocation(self):
        authority = CapabilityAuthority()
        first = authority.issue(request())
        second = authority.issue(request(principal="reaper-plugin:other", resource="plugins/other"))
        self.assertTrue(authority.revoke(first))
        self.assertFalse(authority.revoke(first))
        with self.assertRaises(CapabilityDenied):
            authority.verify(first, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        self.assertEqual(authority.revoke_principal("reaper-plugin:other"), 1)
        with self.assertRaises(CapabilityDenied):
            authority.verify(second, principal="reaper-plugin:other", resource="plugins/other", action="invoke")
        self.assertEqual(authority.active_count, 0)
        authority.close()

    def test_expiry_uses_injected_clock(self):
        now = [1_000_000_000]
        authority = CapabilityAuthority(secret=b"x" * 32, max_ttl_seconds=10, clock_ns=lambda: now[0])
        token = authority.issue(request(ttl=2))
        authority.verify(token, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        now[0] += 2_000_000_000
        with self.assertRaises(CapabilityDenied):
            authority.verify(token, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        self.assertEqual(authority.active_count, 0)
        authority.close()

    def test_token_from_another_authority_is_rejected(self):
        issuer = CapabilityAuthority()
        other = CapabilityAuthority()
        token = issuer.issue(request())
        with self.assertRaises(CapabilityDenied):
            other.verify(token, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        issuer.close()
        other.close()

    def test_signature_tampering_is_rejected(self):
        authority = CapabilityAuthority()
        token = authority.issue(request())
        tampered = dataclasses.replace(token, _signature=b"z" * 32)
        with self.assertRaises(CapabilityDenied):
            authority.verify(tampered, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        authority.close()

    def test_token_is_non_serializable_and_repr_redacts_signature(self):
        authority = CapabilityAuthority()
        token = authority.issue(request())
        self.assertNotIn(token._signature.hex(), repr(token))
        with self.assertRaises(TypeError):
            pickle.dumps(token)
        authority.close()

    def test_expired_or_invalid_requests_are_rejected(self):
        with self.assertRaises(CapabilityError):
            CapabilityRequest.parse({"principal":"x", "resource":"plugins/../outside", "actions":["invoke"]})
        with self.assertRaises(CapabilityError):
            CapabilityRequest.parse({"principal":"x", "resource":"plugins/x", "actions":["*"]})
        with self.assertRaises(CapabilityError):
            CapabilityRequest.parse({"principal":"x", "resource":"plugins/x", "actions":["invoke"], "ttl_seconds":0})
        with self.assertRaises(CapabilityError):
            CapabilityRequest.parse({"principal":"x", "resource":"plugins/x", "actions":["invoke"], "extra":"not-allowed"})


    def test_authorized_operation_serializes_revoke(self):
        import threading
        import time

        authority = CapabilityAuthority()
        token = authority.issue(request())
        entered = threading.Event()
        release = threading.Event()
        revoked = threading.Event()
        errors = []

        def protected_operation():
            try:
                with authority.authorized(
                    token,
                    principal="reaper-plugin:dropaul",
                    resource="plugins/dropaul",
                    action="invoke",
                ):
                    entered.set()
                    if not release.wait(2):
                        raise AssertionError("protected operation release timed out")
            except Exception as error:
                errors.append(error)

        def revoke():
            authority.revoke(token)
            revoked.set()

        worker = threading.Thread(target=protected_operation)
        worker.start()
        self.assertTrue(entered.wait(1))
        revoker = threading.Thread(target=revoke)
        revoker.start()
        time.sleep(0.03)
        self.assertFalse(revoked.is_set(), "revocation must wait for the active operation")
        release.set()
        worker.join(2)
        revoker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertFalse(revoker.is_alive())
        self.assertFalse(errors)
        self.assertTrue(revoked.is_set())
        with self.assertRaises(CapabilityDenied):
            authority.verify(token, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        authority.close()

    def test_malformed_signature_is_denied_not_raised(self):
        import dataclasses
        authority = CapabilityAuthority()
        token = authority.issue(request())
        malformed = dataclasses.replace(token, _signature="not-bytes")
        with self.assertRaises(CapabilityDenied):
            authority.verify(malformed, principal="reaper-plugin:dropaul", resource="plugins/dropaul", action="invoke")
        self.assertFalse(authority.revoke(malformed))
        authority.close()

    def test_tainted_values_require_an_explicit_refinement(self):
        raw = TaintedValue("  Example-Principal  ", "test input")
        refined = refine_tainted(raw, lambda value: value.strip().casefold(), refinement="principal")
        self.assertIsInstance(refined, RefinedValue)
        self.assertEqual(refined.value, "example-principal")
        with self.assertRaises(TypeError):
            RefinedValue("spoofed", "principal")


if __name__ == "__main__":
    unittest.main()
