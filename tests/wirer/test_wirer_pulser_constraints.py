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


def test_6q_allocation(instruments_2mw):
    qubits = [1, 2, 3, 4, 5, 6]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_2mw)

    if visualize_flag:  # Disabled for testing
        visualize(connectivity.elements, instruments_2mw.available_channels, use_matplotlib=True)

    # Check RESONATOR channels: all on fem1 channel1
    for qubit in qubits:
        resonator_channels = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]
        assert len(resonator_channels) == 2
        output_channel = resonator_channels[1]
        assert isinstance(output_channel, InstrumentChannelMwFemOutput)
        pytest.channels_are_equal(
            output_channel,
            InstrumentChannelMwFemOutput(con=1, port=1, slot=1)  # All resonators on fem1 channel 1
        )

    # Check DRIVE channels: fem1 lines 2 & 3 for qubits 1 & 2, fem2 lines 1-4 for qubits 3-6
    expected_drive_channels = [
        InstrumentChannelMwFemOutput(con=1, port=2, slot=1),  # qubit 1
        InstrumentChannelMwFemOutput(con=1, port=3, slot=1),  # qubit 2
        InstrumentChannelMwFemOutput(con=1, port=1, slot=2),  # qubit 3
        InstrumentChannelMwFemOutput(con=1, port=2, slot=2),  # qubit 4
        InstrumentChannelMwFemOutput(con=1, port=3, slot=2),  # qubit 5
        InstrumentChannelMwFemOutput(con=1, port=4, slot=2),  # qubit 6
    ]
    for qubit, expected_channel in zip(qubits, expected_drive_channels):
        drive_channel = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]
        assert len(drive_channel) == 1
        pytest.channels_are_equal(drive_channel, expected_channel)


def test_opx_limit(instruments_1opx_1octave):
    all_qubits = [1, 2, 3, 4]
    active_qubits = [1, 2]
    other_qubits = list(set(all_qubits) - set(active_qubits))

    q2_ch = opx_iq_octave_spec(out_port_i=5, out_port_q=6, rf_out=4)

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=active_qubits)
    connectivity.add_qubit_drive_lines(qubits=[1])
    connectivity.add_qubit_drive_lines(qubits=[2], constraints=q2_ch)
    connectivity.add_qubit_flux_lines(qubits=active_qubits)

    allocate_wiring(connectivity, instruments_1opx_1octave, block_used_channels=False, observe_pulser_allocation=True)
    visualize(connectivity.elements, use_matplotlib=True)

    connectivity.add_resonator_line(qubits=other_qubits)
    connectivity.add_qubit_drive_lines(qubits=other_qubits)
    connectivity.add_qubit_flux_lines(qubits=other_qubits)

    try:
        allocate_wiring(connectivity, instruments_1opx_1octave, observe_pulser_allocation=True)
    except NotEnoughChannelsException:
        assert True
    else:
        assert False, "Expected NotEnoughChannelsException but none was raised."

    if visualize_flag:
        visualize(connectivity.elements, instruments_1opx_1octave.available_channels)


def test_6q_allocation_with_pulser_constraints(instruments_2mw):
    """
    Test that when observe_pulser_allocation=True, the pulsers of the second MW-FEM are used for qubits 3-6.
    """
    qubits = [1, 2, 3, 4, 5, 6]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)

    # Allocate with observing pulser resources
    allocate_wiring(connectivity, instruments_2mw, observe_pulser_allocation=True)

    if visualize_flag:  # Disabled for testing
        visualize(connectivity.elements, instruments_2mw.available_channels, use_matplotlib=True)

    # Check RESONATOR channels: all on fem1 channel1
    for qubit in qubits:
        resonator_channels = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]
        assert len(resonator_channels) == 2
        output_channel = resonator_channels[1]
        assert isinstance(output_channel, InstrumentChannelMwFemOutput)
        pytest.channels_are_equal(
            output_channel,
            InstrumentChannelMwFemOutput(con=1, port=1, slot=1)  # All resonators on fem1 channel 1
        )

    # Check DRIVE channels: When ignoring pulser constraints, all should be on fem1, with constraints we need to start
    # using fem2 for qubits 3-6
    expected_drive_channels = [
        InstrumentChannelMwFemOutput(con=1, port=2, slot=1),  # qubit 1
        InstrumentChannelMwFemOutput(con=1, port=3, slot=1),  # qubit 2
        InstrumentChannelMwFemOutput(con=1, port=1, slot=2),  # qubit 3
        InstrumentChannelMwFemOutput(con=1, port=2, slot=2),  # qubit 4
        InstrumentChannelMwFemOutput(con=1, port=3, slot=2),  # qubit 5
        InstrumentChannelMwFemOutput(con=1, port=4, slot=2),  # qubit 6
    ]
    for qubit, expected_channel in zip(qubits, expected_drive_channels):
        drive_channel = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE]
        assert len(drive_channel) == 1
        assert pytest.channels_are_equal(drive_channel[0], expected_channel)


def test_6q_and_pairs_allocation(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5, 6]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw, observe_pulser_allocation=True)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels, use_matplotlib=True)

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
        drive_channel_distribution = {1: [3, 2], 2: [3, 3], 3: [7, 1], 4: [7, 2], 5: [7, 3], 6: [7, 4]}
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



def test_16q_drive_allocation(instruments_2mw):
    """
    Test normal allocation behavior - both with and without observe_pulser_allocation,
    the result should be the same for drive lines since each uses its own physical channel.
    Physical channels are the limiting factor (8 drives per FEM).
    """
    qubits = list(range(1, 17))  # 16 qubits (exactly 8 per FEM)

    connectivity = Connectivity()
    connectivity.add_qubit_drive_lines(qubits=qubits)

    # This should work fine - exactly fits the physical channel limits
    allocate_wiring(connectivity, instruments_2mw, observe_pulser_allocation=True)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2mw.available_channels, use_matplotlib=True)

    # Count how many drive channels are on each FEM
    fem1_count = 0
    fem2_count = 0

    for qubit in qubits:
        drive_channel = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.DRIVE][0]
        if drive_channel.slot == 1:
            fem1_count += 1
        elif drive_channel.slot == 2:
            fem2_count += 1

    # Should be 8 drives per FEM (using all physical channels)
    assert fem1_count == 8, f"FEM1 has {fem1_count} drives, should be 8"
    assert fem2_count == 8, f"FEM2 has {fem2_count} drives, should be 8"


def test_16q_resonator_allocation(instruments_2mw):
    """
    Test where pulser constraints matter: many resonator lines sharing the same physical channel.
    With observe_pulser_allocation=True, should respect the 16 pulser limit per FEM.
    Each MW-FEM output uses 2 pulsers, so max 8 resonator lines per output channel per FEM.
    """
    qubits = list(range(1, 17))  # 16 qubits, all resonators on same channel

    connectivity = Connectivity()
    # All resonators will try to go to port 1 of MW-FEM, each using 2 pulsers
    connectivity.add_resonator_line(qubits=qubits)

    with pytest.raises(NotEnoughPulsersException):
        # Since the user added more than 8 resonators to the same channel, this should fail with an indicative error
        allocate_wiring(connectivity, instruments_2mw, observe_pulser_allocation=True)


def test_resonator_pulser_constraints_ignore_observation(instruments_2mw):
    """
    Test where pulser constraints are ignored: many resonator lines sharing the same physical channel.
    With observe_pulser_allocation=False (now the default), should ignore the 16 pulser limit per FEM.
    All 20 resonators should go to the first FEM even though it exceeds pulser limits.
    """
    qubits = list(range(1, 21))  # 20 qubits, all resonators on same channel

    connectivity = Connectivity()
    # All resonators will try to go to port 1 of MW-FEM
    connectivity.add_resonator_line(qubits=qubits)

    # Use default behavior (observe_pulser_allocation=False) - this should work by ignoring pulser constraints
    allocate_wiring(connectivity, instruments_2mw)

    if visualize_flag:  # Disabled for testing
        visualize(connectivity.elements, instruments_2mw.available_channels, use_matplotlib=True)

    # Count resonators on each FEM
    fem1_count = 0
    fem2_count = 0

    for qubit in qubits:
        resonator_channels = connectivity.elements[QubitReference(qubit)].channels[WiringLineType.RESONATOR]
        output_channel = resonator_channels[1]  # The output channel
        if output_channel.slot == 1:
            fem1_count += 1
        elif output_channel.slot == 2:
            fem2_count += 1

    # When ignoring pulser constraints, all should go to first FEM
    assert fem1_count == 20, f"FEM1 should have all 20 resonators, but has {fem1_count}"
    assert fem2_count == 0, f"FEM2 should have 0 resonators, but has {fem2_count}"


def test_180q_transmon_qubit_allocation(instruments_stacked_9opx1000):
    """
    Test a large-scale allocation with 100 transmon qubits across 9 OPX1000 chassis.
    We want to have 5 resonator lines per MW-FEM (which means we will need to define 20 resonator channels on 20 MW-FEMs)
    each qubit then should also have its own drive line and flux line.
    """
    qubits = list(range(1, 181))  # 100 qubits

    connectivity = Connectivity()
    # 5 qubits per resonator line
    for i in range(0, 180, 4):
        connectivity.add_resonator_line(qubits=qubits[i:i + 4])
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)

    allocate_wiring(connectivity, instruments_stacked_9opx1000, observe_pulser_allocation=True)

    if visualize_flag:  # Disabled for testing
        visualize(connectivity.elements, instruments_stacked_9opx1000.available_channels, use_matplotlib=True)

    # Just check that all qubits have been allocated channels
    for qubit in qubits:
        assert WiringLineType.RESONATOR in connectivity.elements[QubitReference(qubit)].channels
        assert WiringLineType.DRIVE in connectivity.elements[QubitReference(qubit)].channels
        assert WiringLineType.FLUX in connectivity.elements[QubitReference(qubit)].channels


def test_remove_nonexistent_pulser_raises():
    from qualang_tools.wirer.instruments.instrument_pulsers import InstrumentPulsers, Pulser
    ip = InstrumentPulsers()
    pulser = Pulser(controller=1, slot=1)
    # Do not add pulser, try to remove
    with pytest.raises(NotEnoughPulsersException):
        ip.remove(pulser)


def test_replenish_invalid_args_raises():
    from qualang_tools.wirer.instruments.instrument_pulsers import InstrumentPulsers
    ip = InstrumentPulsers()
    # Invalid: controller=None, slot=5
    with pytest.raises(NotEnoughPulsersException):
        ip.replenish_pulsers(None, 5)
