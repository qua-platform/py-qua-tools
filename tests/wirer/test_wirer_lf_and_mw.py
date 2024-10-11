import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference, QubitPairReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelLfFemOutput, \
    InstrumentChannelMwFemOutput, InstrumentChannelMwFemInput

visualize_flag = pytest.visualize_flag

def test_6q_allocation(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5, 6]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit in qubits:
        # flux channels should have some port as qubit index since they're allocated sequentially
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.FLUX]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelLfFemOutput(con=1, port=qubit, slot=1)
            ][i])

        # resonators all on same feedline, so should be first available input + outputs channels on MW-FEM
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelMwFemInput(con=1, port=1, slot=3),
                InstrumentChannelMwFemOutput(con=1, port=1, slot=3)
            ][i])

        # drive channels are on MW-FEM
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelMwFemOutput(con=1, port=qubit+1, slot=3)
            ][i])

    for i, pair in enumerate(qubit_pairs):
        # coupler channels should have some port as pair index since they're allocated sequentially, but on slot 2
        for j, channel in enumerate(connectivity.elements[QubitPairReference(*pair)].channels[WiringLineType.COUPLER]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelLfFemOutput(con=1, port=i+1, slot=2)
            ][j])

def test_4rr_allocation(instruments_2lf_2mw):
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=1)
    connectivity.add_qubit_drive_lines(qubits=list(range(7)))
    connectivity.add_resonator_line(qubits=2)
    connectivity.add_resonator_line(qubits=3)
    connectivity.add_resonator_line(qubits=4)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    # resonators all on different feedlines, so should fill all 4 inputs of 2x MW-FEM
    for i, qubit in enumerate([1, 2, 3, 4]):
        for j, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelMwFemInput(con=1, port=[1, 2, 1, 2][i], slot=[3, 3, 7, 7][i]),
                InstrumentChannelMwFemOutput(con=1, port=[1, 2, 1, 2][i], slot=[3, 3, 7, 7][i])
            ][j])

