import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelExternalMixerInput,
    InstrumentChannelExternalMixerOutput,
)

visualize_flag = pytest.visualize_flag


def test_1q_allocation(instruments_1opx_2external_mixer):
    qubits = [1]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_1opx_2external_mixer)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1opx_2external_mixer.available_channels)

    for qubit in qubits:
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelOpxPlusInput(con=1, port=1),
                    InstrumentChannelOpxPlusInput(con=1, port=2),
                    InstrumentChannelOpxPlusOutput(con=1, port=1),
                    InstrumentChannelOpxPlusOutput(con=1, port=2),
                    InstrumentChannelExternalMixerInput(con=1, port=1),
                    InstrumentChannelExternalMixerOutput(con=1, port=1),
                ][i],
            )

        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelOpxPlusOutput(con=1, port=3),
                    InstrumentChannelOpxPlusOutput(con=1, port=4),
                    InstrumentChannelExternalMixerOutput(con=2, port=1),
                ][i],
            )

        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.FLUX]):
            assert pytest.channels_are_equal(channel, [InstrumentChannelOpxPlusOutput(con=1, port=5)][i])
