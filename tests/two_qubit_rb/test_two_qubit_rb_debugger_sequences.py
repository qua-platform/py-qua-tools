import itertools

import pytest
import cirq
import numpy as np

cirq = pytest.importorskip("cirq")

from qualang_tools.characterization.two_qubit_rb.TwoQubitRBDebugger import phased_xz_command_sequences


def test_search_for_new_sequence(sequence_tracker):
    """ Demonstrates the capability to search for a particular circuit using command-ids. """
    q0, q1 = cirq.LineQubit.range(2)
    c1 = cirq.Circuit(cirq.Y(q0) ** 0.5, cirq.Y(q1) ** -0.5, cirq.CZ(q0, q1), cirq.I(q0), cirq.Y(q1) ** 0.5)
    # c2 = cirq.Circuit(cirq.CNOT(q0, q1))
    found_sequence = []

    commands_per_circuit = [2] #, 2]

    for i, c in enumerate([c1]): # c2]):
        for command_ids in itertools.product(*[range(736)] * commands_per_circuit[i]):
            sequence = []
            for command_id in command_ids:
                sequence.extend(sequence_tracker.command_registry.get_command_by_id(command_id))

            U = sequence_tracker.calculate_sequence_unitary(sequence)

            if np.allclose(U, cirq.unitary(c)):
                found_sequence.extend(command_ids)
                break

    assert len(found_sequence) == sum(commands_per_circuit)
    assert found_sequence == [4, 248]


q0, q1 = cirq.LineQubit.range(2)
expected_circuits = {
    r"I \otimes I": cirq.Circuit(cirq.I(q0), cirq.I(q1)),
    r"I \otimes Z": cirq.Circuit(cirq.I(q0), cirq.Z(q1)),
    r"Z \otimes I": cirq.Circuit(cirq.Z(q0), cirq.I(q1)),
    r"I \otimes X": cirq.Circuit(cirq.I(q0), cirq.X(q1)),
    r"X \otimes I": cirq.Circuit(cirq.X(q0), cirq.I(q1)),
    r"X \otimes X": cirq.Circuit(cirq.X(q0), cirq.X(q1)),
    r"-\frac{X}{2} \otimes I": cirq.Circuit(cirq.X(q0)**-0.5, cirq.I(q1)),
    r"I \otimes -\frac{X}{2}": cirq.Circuit(cirq.I(q0), cirq.X(q1)**-0.5),
    r"-\frac{X}{2} \otimes -\frac{X}{2}": cirq.Circuit(cirq.X(q0)**-0.5, cirq.X(q1)**-0.5),
    r"\text{CZ}": cirq.Circuit(cirq.CZ(q0, q1)),
    r"\text{CNOT}": cirq.Circuit(cirq.CNOT(q0, q1)),
    r"(\frac{Y}{2} \otimes -\frac{Y}{2}), \text {CZ}, (I \otimes \frac{Y}{2}) \Rightarrow |\Phi^+\rangle_{Bell}": cirq.Circuit(
        cirq.Y(q0)**0.5, cirq.Y(q1)**-0.5, cirq.CZ(q0, q1), cirq.I(q0), cirq.Y(q1)**0.5
    ),
    r"(-\frac{X}{2} \otimes I), \text{CNOT}": cirq.Circuit(cirq.X(q0)**-0.5, cirq.CNOT(q0, q1)),
    r"(X \otimes I), \text{CNOT}": cirq.Circuit(cirq.X(q0), cirq.CNOT(q0, q1)),
    r"(I \otimes X), \text{SWAP}": cirq.Circuit(cirq.X(q1), cirq.SWAP(q0, q1)),
    r"(X \otimes X), \text{CZ}": cirq.Circuit(cirq.X(q0), cirq.X(q1), cirq.CZ(q0, q1)),
    r"((X \otimes X), \text{CZ}) x2": cirq.Circuit(cirq.X(q0), cirq.X(q1), cirq.CZ(q0, q1), cirq.X(q0), cirq.X(q1), cirq.CZ(q0, q1)),
    r"((X \otimes X), \text{CZ}) x3": cirq.Circuit(cirq.X(q0), cirq.X(q1), cirq.CZ(q0, q1), cirq.X(q0), cirq.X(q1), cirq.CZ(q0, q1), cirq.X(q0), cirq.X(q1), cirq.CZ(q0, q1)),
}

@pytest.mark.parametrize("label, command_ids", phased_xz_command_sequences.items())
def test_unitary_equivalence(sequence_tracker, label, command_ids):
    sequence = []
    for command_id in command_ids:
        sequence.extend(sequence_tracker.command_registry.get_command_by_id(command_id))

    U = sequence_tracker.calculate_sequence_unitary(sequence)

    expected_circuit = expected_circuits[label]
    if label ==  r"(\frac{Y}{2} \otimes -\frac{Y}{2}), \text {CZ}, (I \otimes \frac{Y}{2}) \Rightarrow |\Phi^+\rangle_{Bell}":
        print("hi")
    assert np.allclose(U, cirq.unitary(expected_circuit))
