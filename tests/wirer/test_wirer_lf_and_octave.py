import pytest

from qualang_tools.wirer import *
from pprint import pprint

visualize_flag = pytest.visualize_flag

def test_rf_io_allocation(instruments_1octave):
    qubits = [1,2,3,4]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_1octave)

    pprint(connectivity.elements)
    if visualize_flag:
        visualize(connectivity.elements, available_channels=instruments_1octave.available_channels)

def test_qw_soprano_allocation(instruments_qw_soprano):
    qubits = [1, 2, 3, 4, 5]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_qw_soprano)

    pprint(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, available_channels=instruments_qw_soprano.available_channels)

def test_qw_soprano_2qb_allocation(instruments_1OPX1Octave):
    active_qubits = [1, 2]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=active_qubits, constraints=octave_spec(rf_out=1))
    connectivity.add_qubit_drive_lines(qubits=[1], constraints=opx_iq_octave_spec(rf_out=2))
    connectivity.add_qubit_drive_lines(qubits=[2], constraints=opx_iq_octave_spec(rf_out=4))
    connectivity.add_qubit_flux_lines(qubits=active_qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave)

    pprint(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, available_channels=instruments_1OPX1Octave.available_channels)

def test_qw_soprano_2qb_among_5_allocation(instruments_1OPX1Octave):
    all_qubits = [1, 2, 3, 4]
    active_qubits = [1, 2]
    other_qubits = list(set(all_qubits) - set(active_qubits))

    q2_ch = opx_iq_octave_spec(out_port_i=5, out_port_q=6, rf_out=4)

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=active_qubits)
    connectivity.add_qubit_drive_lines(qubits=[1])
    connectivity.add_qubit_drive_lines(qubits=[2], constraints=q2_ch)
    connectivity.add_qubit_flux_lines(qubits=active_qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave, block_used_channels=False)

    connectivity.add_resonator_line(qubits=other_qubits)
    connectivity.add_qubit_drive_lines(qubits=other_qubits)
    connectivity.add_qubit_flux_lines(qubits=other_qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave)

    pprint(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1OPX1Octave.available_channels)
