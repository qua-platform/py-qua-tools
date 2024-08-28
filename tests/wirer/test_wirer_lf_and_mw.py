from qualang_tools.wirer import *

visualize_flag = True

def test_5q_allocation(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, constraints=mw_fem_spec(slot=7))
    connectivity.add_qubit_drive_lines(qubits=qubits, constraints=mw_fem_spec(slot=7))
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    print(connectivity.elements)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)


def test_4rr_allocation(instruments_2lf_2mw):
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=1)
    connectivity.add_qubit_drive_lines(qubits=list(range(7)))
    connectivity.add_resonator_line(qubits=2)
    connectivity.add_resonator_line(qubits=3)
    connectivity.add_resonator_line(qubits=4)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements)


def test_6rr_6xy_6flux_allocation():
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=1)
    instruments.add_mw_fem(controller=1, slots=2)

    qubits = [1, 2, 3, 4, 5, 6]
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments)

    if visualize_flag:
        visualize(connectivity.elements, instruments.available_channels)