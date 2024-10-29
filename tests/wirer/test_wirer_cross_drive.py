from qualang_tools.wirer import *

visualize_flag = True


def test_2q_allocation_cross_drive(instruments_2lf_2mw):
    qubits = [1, 2]
    qubit_pairs = [(1, 2), (2, 1)]

    connectivity = Connectivity()

    connectivity.add_resonator_line(qubits=qubits)
    allocate_wiring(connectivity, instruments_2lf_2mw)

    connectivity.add_qubit_drive_lines(qubits=qubits)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_pair_zz_drive_lines(qubit_pairs)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_pair_cross_drive_lines(qubit_pairs)
    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements)  #, instruments_2lf_2mw.available_channels)
