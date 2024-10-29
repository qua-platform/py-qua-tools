import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitPairReference, QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelMwFemOutput

visualize_flag = False


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
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)


    for i, qubit_pair in enumerate(qubit_pairs):
        xy_channels = connectivity.elements[QubitReference(qubit_pair[0])].channels[WiringLineType.DRIVE]
        xd_channels = connectivity.elements[QubitPairReference(*qubit_pair)].channels[WiringLineType.CROSS_DRIVE]
        zz_channels = connectivity.elements[QubitPairReference(*qubit_pair)].channels[WiringLineType.ZZ_DRIVE]
        assert len(xy_channels) == 1
        assert len(xd_channels) == 1
        assert len(zz_channels) == 1

        # For each XY, XD and ZZ should be on the same channel for the same qubit pair + control index
        for channels in [xy_channels, xd_channels, zz_channels]:
            for j, channel in enumerate(channels):
                assert pytest.channels_are_equal(
                    channel, [
                        InstrumentChannelMwFemOutput(con=1, port=2, slot=3),
                        InstrumentChannelMwFemOutput(con=1, port=3, slot=3)
                    ][i]
                )
