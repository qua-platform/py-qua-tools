from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelOpxPlusDigitalOutput,
    InstrumentChannelOctaveInput,
    InstrumentChannelOctaveDigitalInput,
    InstrumentChannelOctaveOutput,
)

visualize_flag = pytest.visualize_flag


def test_opx_plus_resonator_constraining():
    # Define the available instrument setup
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    q1_res_ch = opx_iq_octave_spec(out_port_i=9, out_port_q=10, rf_out=1)

    qubits = [1]
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, triggered=True, constraints=q1_res_ch)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits[0], triggered=True)

    allocate_wiring(connectivity, instruments)

    if visualize_flag:
        visualize(connectivity.elements, instruments.available_channels)

    # resonator lines should be hard-coded to I=9, Q=10, rf_out=1
    for i, channel in enumerate(connectivity.elements[QubitReference(index=1)].channels[WiringLineType.RESONATOR]):
        assert pytest.channels_are_equal(
            channel,
            [
                InstrumentChannelOpxPlusInput(con=1, port=1, slot=None),
                InstrumentChannelOpxPlusInput(con=1, port=2, slot=None),
                InstrumentChannelOpxPlusOutput(con=1, port=9, slot=None),
                InstrumentChannelOpxPlusOutput(con=1, port=10, slot=None),
                InstrumentChannelOpxPlusDigitalOutput(con=1, port=1, slot=None),
                InstrumentChannelOctaveInput(con=1, port=1, slot=None),
                InstrumentChannelOctaveOutput(con=1, port=1, slot=None),
                InstrumentChannelOctaveDigitalInput(con=1, port=1, slot=None),
            ][i],
        )


def test_fix_attribute_equality():
    """
    Make sure that channels aren't considered equal just because their attributes
    are equal.
    """
    spec = opx_iq_octave_spec()

    assert all(spec.channel_templates.count(element) == 1 for element in spec.channel_templates)
