import os
from pathlib import Path

import pytest

cirq = pytest.importorskip("cirq")

from qualang_tools.bakery.bakery import Baking
from qualang_tools.characterization.two_qubit_rb import TwoQubitRb


def test_all_verification(config):
    """
    Tests that a variety of random sequences are tracked, successfully verified
    by unitary-based simulation, and output to file. Tests that mapping from
    command-id to gate is also properly saved to file.
    """

    def bake_phased_xz(baker: Baking, q, x, z, a):
        pass

    def bake_cz(baker: Baking, q1, q2):
        pass

    def bake_cnot(baker: Baking, q1, q2):
        pass

    def prep():
        pass

    def meas():
        pass

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
