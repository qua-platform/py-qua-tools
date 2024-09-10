import pytest

from qualang_tools.wirer import *

visualize_flag = pytest.visualize_flag

def test_5q_allocation_flux_charge(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, constraints=mw_fem_spec(slot=7))
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_charge_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    print(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)
