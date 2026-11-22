from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from reaper.clife import AwakeningBranch, ClifeError, FaultEvent, FaultType, RuntimeState, Snapshot, branch_awakening, handle_fault, load_snapshot, restore_snapshot, save_snapshot, transition_steps

class ClifeTests(unittest.TestCase):
    def test_capture_save_load_restore_round_trip(self):
        snap = Snapshot.capture("reaper-demo", 4, b"project-state")
        with tempfile.TemporaryDirectory() as folder:
            loaded = load_snapshot(save_snapshot(snap, Path(folder) / "state.json"))
        self.assertEqual(restore_snapshot(loaded, "reaper-demo"), b"project-state")
    def test_payload_mutation_is_detected(self):
        snap = Snapshot.capture("reaper-demo", 1, b"source")
        altered = Snapshot(snap.project_id, snap.generation, b"tampered", snap.checksum_sha256)
        self.assertFalse(altered.verify())
        with self.assertRaises(ClifeError): restore_snapshot(altered, "reaper-demo")
    def test_project_binding_is_enforced(self):
        with self.assertRaises(ClifeError): restore_snapshot(Snapshot.capture("a", 1, b"x"), "b")
    def test_invalid_metadata_is_rejected(self):
        with self.assertRaises(ClifeError): Snapshot.capture(" ", 0, b"x")
        with self.assertRaises(ClifeError): Snapshot.capture("project", -1, b"x")
        with self.assertRaises(ClifeError): Snapshot.from_dict({"schema": "old"})
    def test_healthy_state_resumes(self):
        state = RuntimeState("reaper-demo")
        self.assertEqual(branch_awakening(state, None), AwakeningBranch.NORMAL_RESUME)
        self.assertFalse(state.recovery_locked)
    def test_verified_snapshot_after_recoverable_fault(self):
        state = RuntimeState("reaper-demo", generation=5, artifact_integrity=0.8)
        snap = Snapshot.capture("reaper-demo", 4, b"known-good")
        fault = FaultEvent(FaultType.ARTIFACT_INTEGRITY, 0.1)
        self.assertEqual(handle_fault(state, fault, snap), AwakeningBranch.VERIFIED_RESTORE)
        self.assertTrue(fault.mitigated)
    def test_foreign_snapshot_requires_hold(self):
        state = RuntimeState("reaper-demo", artifact_integrity=0.4)
        self.assertEqual(branch_awakening(state, Snapshot.capture("other", 0, b"x")), AwakeningBranch.PARTIAL_HOLD)
        self.assertTrue(state.recovery_locked)
    def test_high_threat_uses_safe_stop(self):
        state = RuntimeState("reaper-demo", artifact_integrity=0.2, resource_health=0.3, execution_health=0.2)
        self.assertEqual(branch_awakening(state, None, 0.95), AwakeningBranch.EMERGENCY_SAFE_STOP)
    def test_transition_is_finite_and_bounded(self):
        values = transition_steps(0, 1, 8)
        self.assertEqual(len(values), 8); self.assertAlmostEqual(values[-1], 1)
        with self.assertRaises(ClifeError): transition_steps(0, 1, 10000)

if __name__ == "__main__": unittest.main()
