import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.wirer.channel_specs import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelLfFemOutput, InstrumentChannelLfFemDigitalOutput

visualize_flag = pytest.visualize_flag


def test_1q_allocation_laser(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]

    connectivity = ConnectivityNVCenters()
    connectivity.add_laser(qubits=qubits)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit_index in qubits:
        laser_channels = connectivity.elements[QubitReference(qubit_index)].channels[WiringLineType.LASER]
        # Default should be both analog and digital
        assert len(laser_channels) == 2
        assert pytest.channels_are_equal(
            laser_channels[0], InstrumentChannelLfFemOutput(con=1, port=qubit_index, slot=1)
        )
        assert pytest.channels_are_equal(
            laser_channels[1], InstrumentChannelLfFemDigitalOutput(con=1, port=qubit_index, slot=1)
        )

def test_1q_allocation_laser_do(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]

    connectivity = ConnectivityNVCenters()
    q1_laser_digital = lf_fem_dig_spec(con=1, slot=2, out_port=None)
    connectivity.add_laser(qubits=qubits, constraints=q1_laser_digital)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit_index in qubits:
        laser_channels = connectivity.elements[QubitReference(qubit_index)].channels[WiringLineType.LASER]
        # Digital channel only
        assert len(laser_channels) == 1
        assert pytest.channels_are_equal(
            laser_channels[0], InstrumentChannelLfFemDigitalOutput(con=1, port=qubit_index, slot=2)
        )

def test_1q_allocation_laser(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]

    connectivity = ConnectivityNVCenters()
    q1_laser_analog = lf_fem_spec(con=1, out_slot=2, out_port=None)
    connectivity.add_laser(qubits=qubits, constraints=q1_laser_analog)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit_index in qubits:
        laser_channels = connectivity.elements[QubitReference(qubit_index)].channels[WiringLineType.LASER]
        # Analog channel only
        assert len(laser_channels) == 2
        assert pytest.channels_are_equal(
            laser_channels[0], InstrumentChannelLfFemOutput(con=1, port=qubit_index, slot=2)
        )
