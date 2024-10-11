from dataclasses import asdict

import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelMwFemInput, \
    InstrumentChannelMwFemOutput, InstrumentChannelLfFemOutput

visualize_flag = pytest.visualize_flag

def test_5q_allocation_with_channel_reuse(instruments_2lf_2mw):
    connectivity = Connectivity()
    for i in [0, 2]:
        qubits = [1+i, 2+i]
        qubit_pairs = [(1+i, 2+i)]

        connectivity.add_resonator_line(qubits=qubits)
        connectivity.add_qubit_drive_lines(qubits=qubits)
        connectivity.add_qubit_flux_lines(qubits=qubits)
        connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

        allocate_wiring(connectivity, instruments_2lf_2mw, block_used_channels=False)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    for qubit in [1, 3]:
        # resonator lines re-used for qubits 1 & 3
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.RESONATOR]):
            assert asdict(channel) == asdict([
                InstrumentChannelMwFemInput(con=1, port=1, slot=3),
                InstrumentChannelMwFemOutput(con=1, port=1, slot=3)
            ][i])

        # drive lines re-used for qubits 1 & 3
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.DRIVE]):
            assert asdict(channel) == asdict([
                InstrumentChannelMwFemOutput(con=1, port=2, slot=3)
            ][i])

        # flux lines re-used for qubits 1 & 3
        for i, channel in enumerate(connectivity.elements[QubitReference(index=qubit)].channels[WiringLineType.FLUX]):
            assert asdict(channel) == asdict([
                InstrumentChannelLfFemOutput(con=1, port=1, slot=1),
            ][i])
