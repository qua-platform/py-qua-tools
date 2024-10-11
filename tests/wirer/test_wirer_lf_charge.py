from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelLfFemOutput

visualize_flag = pytest.visualize_flag


def test_1q_allocation_flux_charge(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]

    connectivity = Connectivity()
    connectivity.add_qubit_charge_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit_index in qubits:
        charge_channels = connectivity.elements[QubitReference(qubit_index)].channels[WiringLineType.CHARGE]
        assert len(charge_channels) == 1

        for i, channel in enumerate(charge_channels):
            assert pytest.channels_are_equal(
                channel, [InstrumentChannelLfFemOutput(con=1, port=qubit_index, slot=1)][i]
            )
