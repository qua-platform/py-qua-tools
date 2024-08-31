import pytest

from qualang_tools.wirer import *

visualize_flag = pytest.visualize_flag

def test_5q_allocation_with_channel_reuse(instruments_2lf_2mw):
    connectivity = Connectivity()
    for i in [0, 2]:
        qubits = [1+i, 2+i]
        qubit_pairs = [(1+i, 2+i)]

        connectivity.add_resonator_line(qubits=qubits)
        connectivity.add_qubit_drive_lines(qubits=qubits)
        connectivity.add_qubit_flux_lines(qubits=qubits)
        connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

        allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    print(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)
