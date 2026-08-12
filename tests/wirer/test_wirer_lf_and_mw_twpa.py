import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference, QubitPairReference, ElementReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelLfFemOutput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelMwFemInput,
)

visualize_flag = pytest.visualize_flag


def test_6q_allocation(instruments_2lf_2mw):
    twpas = ["A", "B"]
    qubits = [1, 2, 3, 4, 5, 6]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))
    connectivity.add_twpa_lines(twpas=twpas[0], pump_constraints=mw_fem_spec(slot=7, out_port=3))
    connectivity.add_twpa_lines(twpas=twpas[1], pump_constraints=mw_fem_spec(slot=7, out_port=4), isolation_constraints=mw_fem_spec(slot=7, out_port=5))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels, use_matplotlib=True)


    for twpa in twpas:
        twpa_pump_channel_distribution = {"A": [3], "B": [4]}
        twpa_isolation_channel_distribution = {"A": [], "B": [5]}
        # twpa pump channels should have some port as qubit index since they're allocated sequentially
        for i, channel in enumerate(connectivity.elements[ElementReference("twpa", twpa)].channels[WiringLineType.TWPA_PUMP]):
            assert pytest.channels_are_equal(channel, [InstrumentChannelMwFemOutput(con=1, port=twpa_pump_channel_distribution[twpa][i], slot=7)][i])
        if twpa == "B":
            for i, channel in enumerate(connectivity.elements[ElementReference("twpa", twpa)].channels[WiringLineType.TWPA_ISOLATION]):
                assert pytest.channels_are_equal(channel, [InstrumentChannelMwFemOutput(con=1, port=twpa_isolation_channel_distribution[twpa][i], slot=7)][i])

    for qubit in qubits:
        # flux channels should have some port as qubit index since they're allocated sequentially
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.FLUX]):
            assert pytest.channels_are_equal(channel, [InstrumentChannelLfFemOutput(con=1, port=qubit, slot=1)][i])

        # resonators all on same feedline, so should be first available input + outputs channels on MW-FEM
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelMwFemInput(con=1, port=1, slot=3),
                    InstrumentChannelMwFemOutput(con=1, port=1, slot=3),
                ][i],
            )

        # drive channels are on MW-FEM, these will be allocated until pulsers are exhausted on FEM 3 and will then
        # be continued to be allocated on FEM 7
        drive_channel_distribution = {1: [3, 2], 2: [3, 3], 3: [3, 4], 4: [3, 5], 5: [3, 6], 6: [3, 7]}
        for channel in connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]:
            expected_channel = InstrumentChannelMwFemOutput(
                con=1,
                slot=drive_channel_distribution[qubit][0],
                port=drive_channel_distribution[qubit][1]
            )
            assert pytest.channels_are_equal(channel, expected_channel)

    for i, pair in enumerate(qubit_pairs):
        # coupler channels should have some port as pair index since they're allocated sequentially, but on slot 2
        for j, channel in enumerate(connectivity.elements[QubitPairReference(*pair)].channels[WiringLineType.COUPLER]):
            assert pytest.channels_are_equal(channel, [InstrumentChannelLfFemOutput(con=1, port=i + 1, slot=2)][j])
