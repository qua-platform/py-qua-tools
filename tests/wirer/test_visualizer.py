import pytest

from qualang_tools.wirer import Connectivity, lf_fem_spec, allocate_wiring, Instruments
from qualang_tools.wirer.visualizer.web_visualizer import visualize

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


@pytest.mark.skip(reason="plotting")
def test_empty_opx1000_visualization():
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=1)
    instruments.add_mw_fem(controller=1, slots=2)
    connectivity = Connectivity()
    allocate_wiring(connectivity, instruments)
    visualize(connectivity.elements, instruments.available_channels)


@pytest.mark.skip(reason="plotting")
def test_empty_opx_octave_visualization(instruments_1opx_1octave):
    connectivity = Connectivity()
    allocate_wiring(connectivity, instruments_1opx_1octave)
    visualize(connectivity.elements, instruments_1opx_1octave.available_channels)


@pytest.mark.skip(reason="plotting")
def test_basic_superconducting_qubit_example_multi_chassis(instruments_5opx1000):
    connectivity = Connectivity()
    # Define arbitrary set of qubits and qubit pairs for convenience
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)
    allocate_wiring(connectivity, instruments_5opx1000)
    visualize(connectivity.elements, instruments_5opx1000.available_channels)


@pytest.mark.skip(reason="plotting")
def test_basic_superconducting_qubit_example(instruments_1opx_1octave):
    connectivity = Connectivity()
    # Define arbitrary set of qubits and qubit pairs for convenience
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)
    allocate_wiring(connectivity, instruments_1opx_1octave)
    visualize(connectivity.elements, instruments_1opx_1octave.available_channels)
