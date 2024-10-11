from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelLfFemOutput, \
    InstrumentChannelMwFemInput, InstrumentChannelMwFemOutput

visualize_flag = pytest.visualize_flag

def test_alternating_blocking_of_used_channels(instruments_2lf_2mw):
    connectivity = Connectivity()

    connectivity.add_qubit_drive_lines(qubits=1)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_drive_lines(qubits=2)
    allocate_wiring(connectivity, instruments_2lf_2mw)

    connectivity.add_qubit_drive_lines(qubits=3)
    allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    connectivity.add_qubit_drive_lines(qubits=4)
    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    expected_ports = [
        1,  # q1 allocated to 1, but channel isn't blocked
        1,  # q2 allocated to 1, since it wasn't blocked
        2,  # q3 allocated to 2, since it's the next available channel, but not blocked
        2   # q4 allocated to 2, since it wasn't blocked
    ]
    for qubit_index in [1, 2, 3, 4]:
        drive_channels = connectivity.elements[QubitReference(qubit_index)].channels[WiringLineType.DRIVE]
        for i, channel in enumerate(drive_channels):
            assert asdict(channel) == asdict([
                InstrumentChannelMwFemOutput(con=1, slot=3, port=expected_ports[qubit_index-1])
            ][i])