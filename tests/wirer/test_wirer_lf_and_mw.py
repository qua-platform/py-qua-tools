import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference, QubitPairReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelLfFemOutput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelMwFemInput,
)

visualize_flag = pytest.visualize_flag


def test_6q_allocation(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5, 6]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels, use_matplotlib=True)

    for qubit in qubits:
        # flux channels should have some port as qubit index since they're allocated sequentially
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.FLUX]):
            assert pytest.channels_are_equal(channel, [InstrumentChannelLfFemOutput(con=1, port=qubit, slot=1)][i])

        # resonators all on same feedline, so should be first preferred MW-FEM readout pairing (out1+in2)
        for i, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelMwFemInput(con=1, port=2, slot=3),
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


def test_4rr_allocation(instruments_2lf_2mw):
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=1)
    connectivity.add_qubit_drive_lines(qubits=list(range(7)))
    connectivity.add_resonator_line(qubits=2)
    connectivity.add_resonator_line(qubits=3)
    connectivity.add_resonator_line(qubits=4)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    # resonators all on different feedlines, preferred MW-FEM readout pairings:
    # 1st & 2nd: out1+in2, 3rd & 4th: out8+in1 (across slots 3 and 7)
    for i, qubit in enumerate([1, 2, 3, 4]):
        for j, channel in enumerate(connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]):
            assert pytest.channels_are_equal(
                channel,
                [
                    InstrumentChannelMwFemInput(con=1, port=[2, 2, 1, 1][i], slot=[3, 7, 3, 7][i]),
                    InstrumentChannelMwFemOutput(con=1, port=[1, 1, 8, 8][i], slot=[3, 7, 3, 7][i]),
                ][j],
            )


def test_mw_fem_readout_default_pairing(instruments_2lf_2mw):
    """Verify that MW-FEM readout lines get the preferred port pairings:
    1st allocation: output 1 + input 2
    2nd allocation: output 8 + input 1
    Then falls back to generic first-available for subsequent allocations.
    """
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=1)
    connectivity.add_resonator_line(qubits=2)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    # 1st readout: preferred pairing out=1, in=2 on first available MW-FEM (slot 3)
    channels_q1 = connectivity.elements[QubitReference(1)].channels[WiringLineType.RESONATOR]
    assert pytest.channels_are_equal(channels_q1[0], InstrumentChannelMwFemInput(con=1, port=2, slot=3))
    assert pytest.channels_are_equal(channels_q1[1], InstrumentChannelMwFemOutput(con=1, port=1, slot=3))

    # 2nd readout: preferred pairing out=1, in=2 on next available MW-FEM (slot 7)
    channels_q2 = connectivity.elements[QubitReference(2)].channels[WiringLineType.RESONATOR]
    assert pytest.channels_are_equal(channels_q2[0], InstrumentChannelMwFemInput(con=1, port=2, slot=7))
    assert pytest.channels_are_equal(channels_q2[1], InstrumentChannelMwFemOutput(con=1, port=1, slot=7))


def test_mw_fem_readout_fallback_after_preferred(instruments_2lf_2mw):
    """Verify that after preferred pairings (out1+in2) are exhausted on both slots,
    the allocator uses the second preferred pairing (out8+in1).
    """
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=1)
    connectivity.add_resonator_line(qubits=2)
    connectivity.add_resonator_line(qubits=3)
    connectivity.add_resonator_line(qubits=4)

    allocate_wiring(connectivity, instruments_2lf_2mw)

    # 1st: out=1, in=2 on slot 3
    channels_q1 = connectivity.elements[QubitReference(1)].channels[WiringLineType.RESONATOR]
    assert pytest.channels_are_equal(channels_q1[0], InstrumentChannelMwFemInput(con=1, port=2, slot=3))
    assert pytest.channels_are_equal(channels_q1[1], InstrumentChannelMwFemOutput(con=1, port=1, slot=3))

    # 2nd: out=1, in=2 on slot 7
    channels_q2 = connectivity.elements[QubitReference(2)].channels[WiringLineType.RESONATOR]
    assert pytest.channels_are_equal(channels_q2[0], InstrumentChannelMwFemInput(con=1, port=2, slot=7))
    assert pytest.channels_are_equal(channels_q2[1], InstrumentChannelMwFemOutput(con=1, port=1, slot=7))

    # 3rd: out=8, in=1 on slot 3 (second preferred pairing)
    channels_q3 = connectivity.elements[QubitReference(3)].channels[WiringLineType.RESONATOR]
    assert pytest.channels_are_equal(channels_q3[0], InstrumentChannelMwFemInput(con=1, port=1, slot=3))
    assert pytest.channels_are_equal(channels_q3[1], InstrumentChannelMwFemOutput(con=1, port=8, slot=3))

    # 4th: out=8, in=1 on slot 7 (second preferred pairing)
    channels_q4 = connectivity.elements[QubitReference(4)].channels[WiringLineType.RESONATOR]
    assert pytest.channels_are_equal(channels_q4[0], InstrumentChannelMwFemInput(con=1, port=1, slot=7))
    assert pytest.channels_are_equal(channels_q4[1], InstrumentChannelMwFemOutput(con=1, port=8, slot=7))


def test_mw_fem_drive_lines_unaffected(instruments_2lf_2mw):
    """Verify that output-only allocations (drive lines) are NOT affected by the
    preferred readout pairing — they still use first-available ports.
    """
    connectivity = Connectivity()
    connectivity.add_qubit_drive_lines(qubits=[1, 2, 3])

    allocate_wiring(connectivity, instruments_2lf_2mw)

    # Drives are output-only, so they should get ports 1, 2, 3 sequentially
    for qubit, expected_port in [(1, 1), (2, 2), (3, 3)]:
        channels = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]
        assert pytest.channels_are_equal(
            channels[0], InstrumentChannelMwFemOutput(con=1, port=expected_port, slot=3)
        )
