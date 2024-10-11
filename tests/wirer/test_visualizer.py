import pytest

from qualang_tools.wirer import visualize, Connectivity, lf_fem_spec, allocate_wiring


@pytest.mark.skip(reason="plotting")
def test_6q_allocation_visualization(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5, 6]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, triggered=True)
    connectivity.add_qubit_drive_lines(qubits=qubits, triggered=True)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    visualize(connectivity.elements, instruments_2lf_2mw.available_channels)


@pytest.mark.skip(reason="plotting")
def test_4q_allocation_visualization(instruments_1opx_1octave):
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, triggered=True)
    connectivity.add_qubit_drive_lines(qubits=qubits, triggered=True)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

    allocate_wiring(connectivity, instruments_1opx_1octave)

    visualize(connectivity.elements, instruments_1opx_1octave.available_channels)
