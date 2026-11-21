import math
import unittest

from reaper.atomic_quantum import (
    AtomicQuantumError, KernelUnavailableError, amplitude_damp, bell_pair,
    cnot, dephase, fidelity, function_catalog, get_function, ghz_state,
    hadamard, measure_z, normalize, phase_rotate, probabilities, telemetry,
    zero_state,
)

class AtomicQuantumTests(unittest.TestCase):
    def test_catalogue_is_complete_and_unique(self):
        rows = function_catalog()
        self.assertEqual(len(rows), 133)
        self.assertEqual(len({row["id"] for row in rows}), 133)
        self.assertEqual(rows[0]["id"], "atom_superpose_basis_01")
        self.assertEqual(rows[-1]["id"], "telem_system_health_133")
        self.assertEqual(get_function("entangle_bell_pair_23")["status"], "simulated")

    def test_hadamard_and_phase_preserve_norm(self):
        state = zero_state(1)
        hadamard(state, 0)
        self.assertEqual(probabilities(state), [0.4999999999999999, 0.4999999999999999])
        phase_rotate(state, 0, math.pi / 2)
        self.assertAlmostEqual(sum(probabilities(state)), 1.0, places=12)

    def test_bell_and_ghz_states(self):
        bell = bell_pair()
        self.assertEqual(bell.qubits, 2)
        self.assertAlmostEqual(probabilities(bell)[0], 0.5)
        self.assertAlmostEqual(probabilities(bell)[3], 0.5)
        ghz = ghz_state(3)
        self.assertAlmostEqual(probabilities(ghz)[0], 0.5)
        self.assertAlmostEqual(probabilities(ghz)[7], 0.5)
        self.assertAlmostEqual(fidelity(bell, bell.copy()), 1.0)

    def test_seeded_measurement_is_repeatable_and_collapses(self):
        first, second = bell_pair(), bell_pair()
        result_a = measure_z(first, 0, seed=7)
        result_b = measure_z(second, 0, seed=7)
        self.assertEqual(result_a, result_b)
        self.assertAlmostEqual(sum(probabilities(first)), 1.0)
        self.assertEqual(sum(1 for value in probabilities(first) if value > 0), 1)

    def test_noise_channels_remain_normalized(self):
        state = bell_pair()
        dephase(state, 0, 1.0, seed=3)
        amplitude_damp(state, 1, 0.25, seed=5)
        self.assertAlmostEqual(sum(probabilities(state)), 1.0, places=12)

    def test_bounds_and_catalogue_only_are_explicit(self):
        with self.assertRaises(AtomicQuantumError):
            zero_state(11)
        with self.assertRaises(AtomicQuantumError):
            hadamard(zero_state(1), 2)
        with self.assertRaises(KernelUnavailableError):
            from reaper.atomic_quantum import require_kernel
            require_kernel("algo_hhl_invert_117")

    def test_telemetry_is_simulation_labelled(self):
        report = telemetry(bell_pair())
        self.assertEqual(report["quality"], "simulated")
        self.assertEqual(report["execution_model"], "bounded_classical_simulation")
        self.assertAlmostEqual(report["norm"], 1.0)

if __name__ == "__main__":
    unittest.main()
