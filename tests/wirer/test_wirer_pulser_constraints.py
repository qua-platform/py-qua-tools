import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference, QubitPairReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelLfFemOutput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelMwFemInput,
)

visualize_flag = pytest.visualize_flag


def test_6q_allocation(instruments_2mw):
    qubits = [1, 2, 3, 4, 5, 6]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_2mw)

    if True:
        visualize(connectivity.elements, instruments_2mw.available_channels, use_matplotlib=True)

    # Check RESONATOR channels: all on fem1 channel1
    for qubit in qubits:
        resonator_channels = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]
        assert len(resonator_channels) == 2
        output_channel = resonator_channels[1]
        assert isinstance(output_channel, InstrumentChannelMwFemOutput)
        pytest.channels_are_equal(
            output_channel,
            InstrumentChannelMwFemOutput(con=1, port=1, slot=1)  # All resonators on fem1 channel 1
        )

    # Check DRIVE channels: fem1 lines 2 & 3 for qubits 1 & 2, fem2 lines 1-4 for qubits 3-6
    expected_drive_channels = [
        InstrumentChannelMwFemOutput(con=1, port=2, slot=1),  # qubit 1
        InstrumentChannelMwFemOutput(con=1, port=3, slot=1),  # qubit 2
        InstrumentChannelMwFemOutput(con=1, port=1, slot=2),  # qubit 3
        InstrumentChannelMwFemOutput(con=1, port=2, slot=2),  # qubit 4
        InstrumentChannelMwFemOutput(con=1, port=3, slot=2),  # qubit 5
        InstrumentChannelMwFemOutput(con=1, port=4, slot=2),  # qubit 6
    ]
    for qubit, expected_channel in zip(qubits, expected_drive_channels):
        drive_channel = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]
        assert len(drive_channel) == 1
        pytest.channels_are_equal(drive_channel, expected_channel)