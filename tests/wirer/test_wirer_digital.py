import pytest

from qualang_tools.wirer import *

visualize_flag = pytest.visualize_flag

def test_triggered_wiring_spec_generates_digital_channels(instruments_2lf_2mw):
    connectivity = Connectivity()
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]

    connectivity.add_resonator_line(qubits=qubits, triggered=True)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    print(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)
