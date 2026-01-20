from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference, QubitPairReference, ElementReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelOpxPlusDigitalOutput,
    InstrumentChannelOctaveInput,
    InstrumentChannelOctaveDigitalInput,
    InstrumentChannelOctaveOutput,
    InstrumentChannelLfFemInput,
    InstrumentChannelLfFemOutput,
)

visualize_flag = pytest.visualize_flag


def channels_are_equal(left, right) -> bool:
    return type(left) is type(right) and asdict(left) == asdict(right)


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
        assert channels_are_equal(
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

def test_constrained_resonator_prioritized_over_unconstrained_barriers():
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=[2, 3])

    s1_res_constraints = lf_fem_spec(con=1, in_slot=2, out_slot=2, in_port=1, out_port=1)
    s2to3_res_constraints = lf_fem_spec(con=1, in_slot=3, out_slot=3, in_port=2, out_port=8)
    gate_constraints = lf_fem_spec(con=1, out_slot=3)

    sensor_dots = [1, 2, 3]
    quantum_dots = [1, 2, 3]
    quantum_dot_pairs = list(zip(quantum_dots, quantum_dots[1:]))

    connectivity = Connectivity()
    connectivity.add_sensor_dot_resonator_line(sensor_dots[0], shared_line=False, constraints=s1_res_constraints)
    connectivity.add_sensor_dot_resonator_line(
        sensor_dots[1:], shared_line=True, constraints=s2to3_res_constraints
    )
    connectivity.add_sensor_dot_voltage_gate_lines(sensor_dots, constraints=gate_constraints)
    connectivity.add_quantum_dot_voltage_gate_lines(quantum_dots, constraints=gate_constraints)
    connectivity.add_quantum_dot_pairs(quantum_dot_pairs)

    allocate_wiring(connectivity, instruments)

    sensor1 = connectivity.elements[ElementReference(name="s", index=1)]
    resonator_channels = sensor1.channels[WiringLineType.RF_RESONATOR]
    expected_input = InstrumentChannelLfFemInput(con=1, port=1, slot=2)
    expected_output = InstrumentChannelLfFemOutput(con=1, port=1, slot=2)

    assert any(channels_are_equal(channel, expected_input) for channel in resonator_channels)
    assert any(channels_are_equal(channel, expected_output) for channel in resonator_channels)

    for control, target in quantum_dot_pairs:
        pair_element = connectivity.elements[QubitPairReference(control, target)]
        barrier_channels = pair_element.channels[WiringLineType.BARRIER_GATE]
        assert any(isinstance(channel, InstrumentChannelLfFemOutput) for channel in barrier_channels)


def test_fix_attribute_equality():
    """
    Make sure that channels aren't considered equal just because their attributes
    are equal.
    """
    spec = opx_iq_octave_spec()

    assert all(spec.channel_templates.count(element) == 1 for element in spec.channel_templates)
