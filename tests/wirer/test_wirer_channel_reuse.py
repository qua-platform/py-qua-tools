from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelMwFemInput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelLfFemOutput,
)

visualize_flag = pytest.visualize_flag


def test_5q_allocation_with_channel_reuse(instruments_2lf_2mw):
    connectivity = Connectivity()
    for i in [0, 2]:
        qubits = [1 + i, 2 + i]
        qubit_pairs = [(1 + i, 2 + i)]

        connectivity.add_resonator_line(qubits=qubits)
        connectivity.add_qubit_drive_lines(qubits=qubits)
        connectivity.add_qubit_flux_lines(qubits=qubits)
        connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

        allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit in [1, 3]:
        # resonator lines re-used for qubits 1 & 3
        for i, channel in enumerate(
            connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.RESONATOR]
        ):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelMwFemInput(con=1, port=1, slot=3),
                    InstrumentChannelMwFemOutput(con=1, port=1, slot=3),
                ][i],
            )

        # drive lines re-used for qubits 1 & 3
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.DRIVE]):
            assert pytest.channels_are_equal(channel, [InstrumentChannelMwFemOutput(con=1, port=2, slot=3)][i])

        # flux lines re-used for qubits 1 & 3
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.FLUX]):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelLfFemOutput(con=1, port=1, slot=1),
                ][i],
            )


def test_alternating_blocking_of_used_channels(instruments_1opx_1octave):
    connectivity = Connectivity()

    connectivity.add_qubit_drive_lines(qubits=1)
    allocate_wiring(connectivity, instruments_1opx_1octave, block_used_channels=False)

    connectivity.add_qubit_drive_lines(qubits=2)
    allocate_wiring(connectivity, instruments_1opx_1octave)

    connectivity.add_qubit_drive_lines(qubits=3)
    allocate_wiring(connectivity, instruments_1opx_1octave, block_used_channels=False)

    connectivity.add_qubit_drive_lines(qubits=4)
    allocate_wiring(connectivity, instruments_1opx_1octave)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1opx_1octave.available_channels)

    expected_ports = [
        1,  # q1 allocated to 1, but channel isn't blocked
        1,  # q2 allocated to 1, since it wasn't blocked
        2,  # q3 allocated to 2, since it's the next available channel, but not blocked
        2,  # q4 allocated to 2, since it wasn't blocked
    ]
    for qubit_index in [1, 2, 3, 4]:
        drive_channels = connectivity.elements[QubitReference(qubit_index)].channels[WiringLineType.DRIVE]
        for i, channel in enumerate(drive_channels):
            assert pytest.channels_are_equal(
                channel, [InstrumentChannelMwFemOutput(con=1, slot=3, port=expected_ports[qubit_index - 1])][i]
            )
