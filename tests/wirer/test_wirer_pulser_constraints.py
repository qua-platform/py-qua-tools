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


def test_6q_allocation_with_pulser_constraints(instruments_2mw):
    """
    Test that when observe_pulser_allocation=False, all pulsers are allocated to the first FEM
    regardless of pulser limits (16 per FEM).
    """
    qubits = [1, 2, 3, 4, 5, 6]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)

    # Allocate with observe_pulser_allocation=False
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

    # Check DRIVE channels: When ignoring pulser constraints, all should be on fem1
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


def test_resonator_pulser_constraints_with_observation(instruments_2mw):
    """
    Test where pulser constraints matter: many resonator lines sharing the same physical channel.
    With observe_pulser_allocation=True, should respect the 16 pulser limit per FEM.
    Each MW-FEM output uses 2 pulsers, so max 8 resonator lines per output channel per FEM.
    """
    qubits = list(range(1, 17))  # 16 qubits, all resonators on same channel

    connectivity = Connectivity()
    # All resonators will try to go to port 1 of MW-FEM, each using 2 pulsers
    connectivity.add_resonator_line(qubits=qubits)

    # Explicitly enable pulser constraints - this should work with 8 resonators per FEM, using 16 pulsers per FEM
    allocate_wiring(connectivity, instruments_2mw, observe_pulser_allocation=True)

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

    # Should be distributed across FEMs respecting pulser limits
    assert fem1_count <= 8, f"FEM1 has {fem1_count} resonators, should be <= 8"
    assert fem2_count <= 8, f"FEM2 has {fem2_count} resonators, should be <= 8"
    assert fem1_count + fem2_count == 16, "Total resonators should be 16"


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


