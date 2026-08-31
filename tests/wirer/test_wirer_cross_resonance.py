import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitPairReference, QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelMwFemOutput, InstrumentChannelOpxPlus, \
    InstrumentChannelOpxPlusOutput, InstrumentChannelOctaveOutput

visualize_flag = pytest.visualize_flag


def test_2q_allocation_cross_resonance(instruments_2lf_2mw):
    qubits = [1, 2]
    qubit_pairs = [(1, 2), (2, 1)]

    connectivity = Connectivity()

    connectivity.add_resonator_line(qubits=qubits)
    allocate_wiring(connectivity, instruments_2lf_2mw)

    connectivity.add_qubit_drive_lines(qubits=qubits)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_detuned_drive_lines(qubits=qubits)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_pair_zz_drive_lines(qubit_pairs)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_pair_cross_resonance_lines(qubit_pairs)
    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)


    for i, qubit_pair in enumerate(qubit_pairs):
        xy_channels = connectivity.elements[QubitReference(qubit_pair[0])].channels[WiringLineType.DRIVE]
        xy_detuned_channels = connectivity.elements[QubitReference(qubit_pair[0])].channels[WiringLineType.DETUNED_DRIVE]
        cr_channels = connectivity.elements[QubitPairReference(*qubit_pair)].channels[WiringLineType.CROSS_RESONANCE]
        zz_channels = connectivity.elements[QubitPairReference(*qubit_pair)].channels[WiringLineType.ZZ_DRIVE]
        assert len(xy_channels) == 1
        assert len(xy_detuned_channels) == 1
        assert len(cr_channels) == 1
        assert len(zz_channels) == 1

        # For each XY, XD and ZZ should be on the same channel for the same qubit pair + control index
        for channels in [xy_channels, xy_detuned_channels, cr_channels, zz_channels]:
            for j, channel in enumerate(channels):
                assert pytest.channels_are_equal(
                    channel, [
                        InstrumentChannelMwFemOutput(con=1, port=2, slot=3),
                        InstrumentChannelMwFemOutput(con=1, port=3, slot=3)
                    ][i]
                )


def test_2q_allocation_cross_resonance_opx_plus_octave(instruments_1opx_1octave):
    qubits = [1, 2]
    qubit_pairs = [(1, 2), (2, 1)]

    connectivity = Connectivity()

    connectivity.add_resonator_line(qubits=qubits)
    allocate_wiring(connectivity, instruments_1opx_1octave)

    connectivity.add_qubit_drive_lines(qubits=qubits)
    allocate_wiring(connectivity, instruments_1opx_1octave, block_used_channels=False)

    connectivity.add_qubit_detuned_drive_lines(qubits=qubits)
    allocate_wiring(connectivity, instruments_1opx_1octave, block_used_channels=False)

    connectivity.add_qubit_pair_zz_drive_lines(qubit_pairs)
    allocate_wiring(connectivity, instruments_1opx_1octave, block_used_channels=False)

    connectivity.add_qubit_pair_cross_resonance_lines(qubit_pairs)
    allocate_wiring(connectivity, instruments_1opx_1octave)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1opx_1octave.available_channels)


    for i, qubit_pair in enumerate(qubit_pairs):
        xy_channels = connectivity.elements[QubitReference(qubit_pair[0])].channels[WiringLineType.DRIVE]
        xy_detuned_channels = connectivity.elements[QubitReference(qubit_pair[0])].channels[WiringLineType.DETUNED_DRIVE]
        cr_channels = connectivity.elements[QubitPairReference(*qubit_pair)].channels[WiringLineType.CROSS_RESONANCE]
        zz_channels = connectivity.elements[QubitPairReference(*qubit_pair)].channels[WiringLineType.ZZ_DRIVE]
        assert len(xy_channels) == 3
        assert len(cr_channels) == 3
        assert len(zz_channels) == 3

        # For each XY, XD and ZZ should be on the same channel for the same qubit pair + control index
        for channels in [xy_channels, xy_detuned_channels, cr_channels, zz_channels]:
            for j, channel in enumerate(channels):
                assert pytest.channels_are_equal(
                    channel, [
                        [
                            InstrumentChannelOpxPlusOutput(con=1, port=3),
                            InstrumentChannelOpxPlusOutput(con=1, port=4),
                            InstrumentChannelOctaveOutput(con=1, port=2),
                        ],
                        [
                            InstrumentChannelOpxPlusOutput(con=1, port=5),
                            InstrumentChannelOpxPlusOutput(con=1, port=6),
                            InstrumentChannelOctaveOutput(con=1, port=3),
                        ],
                    ][i][j]
                )
