from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelMwFemDigitalOutput

visualize_flag = pytest.visualize_flag


def test_triggered_wiring_spec_generates_digital_channels(instruments_2lf_2mw):
    connectivity = Connectivity()
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]

    connectivity.add_resonator_line(qubits=qubits, triggered=True)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    # assert digital trigger channel is present
    for qubit in [1, 2]:
        resonator_channels = connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.RESONATOR]
        resonator_channels_as_dicts = [asdict(channel) for channel in resonator_channels]

        assert asdict(InstrumentChannelMwFemDigitalOutput(con=1, port=1, slot=3)) in resonator_channels_as_dicts
