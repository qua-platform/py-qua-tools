import os
from pathlib import Path

import numpy as np
import pytest
<<<<<<< Updated upstream
=======
import tqdm
from qm.qua import declare
>>>>>>> Stashed changes

cirq = pytest.importorskip("cirq")

from qualang_tools.characterization.two_qubit_rb import TwoQubitRb
from qualang_tools.characterization.two_qubit_rb.TwoQubitRBDebugger import phased_xz_command_sequences


def test_all_verification(config, bake_phased_xz, bake_cz, bake_cnot, prep, meas):
    """
    Tests that a variety of random sequences are tracked, successfully verified
    by unitary-based simulation, and output to file. Tests that mapping from
    command-id to gate is also properly saved to file.
    """

    cz_generator = {"CZ": bake_cz}
    cnot_generator = {"CNOT": bake_cnot}
    cz_cnot_generator = {"CZ": bake_cz, "CNOT": bake_cnot}

    bake_2q_gate_generators = [cz_cnot_generator, cz_generator, cnot_generator]

    for generator in bake_2q_gate_generators:
        rb = TwoQubitRb(
            config, bake_phased_xz, generator, prep, meas, verify_generation=False, interleaving_gate=None
        )
        repeats = 10
        depth = 10
        # can't run rb.run without an OPX connected, so manually create sequences.
        for _ in range(repeats):
            sequence = rb._gen_rb_sequence(depth)
            rb._sequence_tracker.make_sequence(sequence)

        rb._sequence_tracker.verify_sequences()

        parent_dir = Path(os.path.dirname(os.path.abspath(__file__)))

        rb.save_command_mapping_to_file(parent_dir / "commands.txt")
        rb.save_sequences_to_file(parent_dir / "sequences.txt")
        rb.print_command_mapping()
        rb.print_sequences()
        rb.verify_sequences()


<<<<<<< Updated upstream
def test_debugger_bell_state_circuit(config, bake_phased_xz, bake_cz, bake_cnot, prep, meas):
=======
def test_debugger_bell_state_circuit(config):
    def bake_phased_xz(baker: Baking, q, x, z, a):
        pass

    def bake_cz(baker: Baking, q1, q2):
        pass

    def bake_cnot(baker: Baking, q1, q2):
        pass

    def prep():
        pass

    def meas():
        return declare(bool), declare(bool)

>>>>>>> Stashed changes
    cz_generator = {"CZ": bake_cz}

    rb = TwoQubitRb(
        config, bake_phased_xz, cz_generator, prep, meas, verify_generation=False, interleaving_gate=None
    )

    parent_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    rb.save_command_mapping_to_file(parent_dir / "commands.txt")

    bell_state_circuit_string = r"(\frac{Y}{2} \otimes -\frac{Y}{2}), \text {CZ}, (I \otimes \frac{Y}{2}) \Rightarrow |\Phi^+\rangle_{Bell}"
    bell_state = (1 / np.sqrt(2)) * (
        np.kron(np.array([1, 0]), np.array([1, 0])) +
        np.kron(np.array([0, 1]), np.array([0, 1]))
    )
    bell_state_rho = np.outer(bell_state, bell_state.conj())

    # search for commands producing bell-state
    # for i in tqdm.tqdm(range(736)):
    #     sequence = []
    #     for command_id in [i]:
    #         sequence.extend(rb._sequence_tracker.command_registry.get_command_by_id(command_id))
    #     if np.allclose(rb._sequence_tracker.calculate_resultant_state(sequence), np.array(bell_state_rho)):
    #         print("Found!", i)

    sequence = []
    for command_id in phased_xz_command_sequences[bell_state_circuit_string]:
        sequence.extend(rb._sequence_tracker.command_registry.get_command_by_id(command_id))

    assert np.allclose(rb._sequence_tracker.calculate_resultant_state(sequence), np.array(bell_state_rho))

    # rb_debugger = TwoQubitRbDebugger(rb)
    # rb_debugger.run_phased_xz_commands(None, 100)
