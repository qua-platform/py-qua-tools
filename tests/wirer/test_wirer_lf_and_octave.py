from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from pprint import pprint

from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelOpxPlusInput, \
    InstrumentChannelOpxPlusOutput, InstrumentChannelOpxPlusDigitalOutput, InstrumentChannelOctaveInput, \
    InstrumentChannelOctaveDigitalInput, InstrumentChannelOctaveOutput

visualize_flag = pytest.visualize_flag

def test_rf_io_allocation(instruments_1OPX1Octave):
    qubits = [1, 2, 3, 4]


    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave)

    if visualize_flag:
        visualize(connectivity.elements, available_channels=instruments_1OPX1Octave.available_channels)

    for qubit in qubits:
        # resonator lines should be the same because only 1 feedline
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelOpxPlusInput(con=1, port=1, slot=None),
                InstrumentChannelOpxPlusInput(con=1, port=2, slot=None),
                InstrumentChannelOpxPlusOutput(con=1, port=1, slot=None),
                InstrumentChannelOpxPlusOutput(con=1, port=2, slot=None),
                # InstrumentChannelOpxPlusDigitalOutput(con=1, port=1, slot=None),
                InstrumentChannelOctaveInput(con=1, port=1, slot=None),
                InstrumentChannelOctaveOutput(con=1, port=1, slot=None),
                # InstrumentChannelOctaveDigitalInput(con=1, port=1, slot=None)
            ][i])

        # drive lines should be allocated sequentially
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.DRIVE]):
            assert pytest.channels_are_equal(channel, [
                InstrumentChannelOpxPlusOutput(con=1, port=1+2*qubit, slot=None),
                InstrumentChannelOpxPlusOutput(con=1, port=2+2*qubit, slot=None),
                InstrumentChannelOctaveOutput(con=1, port=1+qubit, slot=None),
            ][i])



def test_qw_soprano_allocation(instruments_qw_soprano):
    qubits = [1, 2, 3, 4, 5]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_qw_soprano)

    if visualize_flag:
        visualize(connectivity.elements, available_channels=instruments_qw_soprano.available_channels)

    # should run without error

def test_qw_soprano_2qb_allocation(instruments_1OPX1Octave):
    active_qubits = [1, 2]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=active_qubits, constraints=octave_spec(rf_out=1))
    connectivity.add_qubit_drive_lines(qubits=[1], constraints=opx_iq_octave_spec(rf_out=2))
    connectivity.add_qubit_drive_lines(qubits=[2], constraints=opx_iq_octave_spec(rf_out=4))
    connectivity.add_qubit_flux_lines(qubits=active_qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave)

    if visualize_flag:
        visualize(connectivity.elements, available_channels=instruments_1OPX1Octave.available_channels)

    # should run without error

def test_qw_soprano_2qb_among_5_allocation(instruments_1OPX1Octave):
    all_qubits = [1, 2, 3, 4]
    active_qubits = [1, 2]
    other_qubits = list(set(all_qubits) - set(active_qubits))

    q2_ch = opx_iq_octave_spec(out_port_i=5, out_port_q=6, rf_out=4)

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=active_qubits)
    connectivity.add_qubit_drive_lines(qubits=[1])
    connectivity.add_qubit_drive_lines(qubits=[2], constraints=q2_ch)
    connectivity.add_qubit_flux_lines(qubits=active_qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave, block_used_channels=False)

    connectivity.add_resonator_line(qubits=other_qubits)
    connectivity.add_qubit_drive_lines(qubits=other_qubits)
    connectivity.add_qubit_flux_lines(qubits=other_qubits)

    allocate_wiring(connectivity, instruments_1OPX1Octave)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1OPX1Octave.available_channels)

    # should run without error