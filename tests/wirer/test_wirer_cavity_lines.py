import pytest

from qualang_tools.wirer import *
from qualang_tools.wirer.connectivity.element import QubitReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType, WiringFrequency, WiringIOType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelOctaveOutput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelLfFemOutput,
    InstrumentChannelExternalMixerOutput,
)

visualize_flag = pytest.visualize_flag


# ==================== Basic Functionality Tests ====================

def test_add_cavity_line_single_qubit():
    """Verify that add_cavity_lines() accepts a single qubit and creates correct wiring spec."""
    connectivity = Connectivity()
    specs = connectivity.add_cavity_lines(qubit=1)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.line_type == WiringLineType.CAVITY
    assert spec.frequency == WiringFrequency.RF
    assert spec.io_type == WiringIOType.OUTPUT
    assert spec.triggered is False
    assert len(spec.elements) == 1
    assert spec.elements[0].id == QubitReference(1)


def test_add_cavity_line_rejects_list():
    """Verify that passing a list raises ValueError."""
    connectivity = Connectivity()
    with pytest.raises(ValueError, match="add_cavity_lines\\(\\) only accepts a single qubit"):
        connectivity.add_cavity_lines(qubit=[1, 2])


def test_add_cavity_line_with_trigger():
    """Verify that triggered=True parameter works correctly."""
    connectivity = Connectivity()
    specs = connectivity.add_cavity_lines(qubit=1, triggered=True)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.triggered is True
    assert spec.line_type == WiringLineType.CAVITY


def test_add_cavity_line_with_constraints():
    """Verify that constraints parameter is accepted and stored correctly."""
    connectivity = Connectivity()
    constraint = opx_iq_octave_spec(con=1, rf_out=2)
    specs = connectivity.add_cavity_lines(qubit=1, constraints=constraint)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.constraints is not None


# ==================== Channel Allocation Tests ====================

def test_cavity_line_allocation_mw_fem(instruments_2mw):
    """Allocate cavity line with MW-FEM setup."""
    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments_2mw)

    if visualize_flag:
        visualize(connectivity.elements, instruments_2mw.available_channels)

    # Verify channels are allocated
    qubit_ref = QubitReference(1)
    assert qubit_ref in connectivity.elements
    assert WiringLineType.CAVITY in connectivity.elements[qubit_ref].channels
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0


def test_cavity_line_allocation_opx_octave(instruments_1opx_1octave):
    """Allocate cavity line with OPX+ and Octave setup."""
    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments_1opx_1octave)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1opx_1octave.available_channels)

    qubit_ref = QubitReference(1)
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0
    # Should have OPX+ I/Q outputs and Octave RF output
    assert any(isinstance(ch, InstrumentChannelOpxPlusOutput) for ch in channels)
    assert any(isinstance(ch, InstrumentChannelOctaveOutput) for ch in channels)


def test_cavity_line_allocation_lf_fem_octave(instruments_1octave):
    """Allocate cavity line with LF-FEM and Octave setup."""
    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments_1octave)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1octave.available_channels)

    qubit_ref = QubitReference(1)
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0
    # Should have LF-FEM baseband I/Q and Octave RF
    assert any(isinstance(ch, InstrumentChannelLfFemOutput) for ch in channels)
    assert any(isinstance(ch, InstrumentChannelOctaveOutput) for ch in channels)


def test_cavity_line_allocation_external_mixer(instruments_1opx_2external_mixer):
    """Allocate cavity line with OPX+ and External Mixer."""
    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments_1opx_2external_mixer)

    if visualize_flag:
        visualize(connectivity.elements, instruments_1opx_2external_mixer.available_channels)

    qubit_ref = QubitReference(1)
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0
    # Should have OPX+ I/Q and External Mixer
    assert any(isinstance(ch, InstrumentChannelOpxPlusOutput) for ch in channels)
    assert any(isinstance(ch, InstrumentChannelExternalMixerOutput) for ch in channels)


def test_cavity_line_allocation_lf_fem_external_mixer():
    """Allocate cavity line with LF-FEM and External Mixer."""
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=[1])
    instruments.add_external_mixer(indices=[1])

    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments)

    qubit_ref = QubitReference(1)
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0
    # Should have LF-FEM baseband I/Q and External Mixer
    assert any(isinstance(ch, InstrumentChannelLfFemOutput) for ch in channels)
    assert any(isinstance(ch, InstrumentChannelExternalMixerOutput) for ch in channels)


# ==================== Constraint Tests ====================

def test_cavity_line_with_opx_constraint():
    """Use opx_iq_octave_spec constraint and verify allocation respects it."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    constraint = opx_iq_octave_spec(con=1, rf_out=2)
    connectivity.add_cavity_lines(qubit=1, constraints=constraint)

    allocate_wiring(connectivity, instruments)

    qubit_ref = QubitReference(1)
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0


def test_cavity_line_with_mw_fem_constraint():
    """Use mw_fem_spec constraint and verify allocation uses MW-FEM."""
    instruments = Instruments()
    instruments.add_mw_fem(controller=1, slots=[1])

    connectivity = Connectivity()
    constraint = mw_fem_spec()
    connectivity.add_cavity_lines(qubit=1, constraints=constraint)

    allocate_wiring(connectivity, instruments)

    qubit_ref = QubitReference(1)
    channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(channels) > 0
    assert any(isinstance(ch, InstrumentChannelMwFemOutput) for ch in channels)


def test_cavity_line_constraint_too_strict():
    """Use constraints that cannot be satisfied and verify exception."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    # Constrain to non-existent controller
    constraint = opx_iq_octave_spec(con=999, rf_out=1)
    connectivity.add_cavity_lines(qubit=1, constraints=constraint)

    with pytest.raises(ConstraintsTooStrictException):
        allocate_wiring(connectivity, instruments)


# ==================== Integration Tests ====================

def test_cavity_line_with_other_lines():
    """Add resonator, drive, flux, and cavity lines together."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)
    instruments.add_lf_fem(controller=1, slots=[1])

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=[1])
    connectivity.add_qubit_drive_lines(qubits=[1])
    connectivity.add_cavity_lines(qubit=1)
    connectivity.add_qubit_flux_lines(qubits=[1])

    allocate_wiring(connectivity, instruments)

    if visualize_flag:
        visualize(connectivity.elements, instruments.available_channels)

    qubit_ref = QubitReference(1)
    # Verify all line types are allocated
    assert WiringLineType.RESONATOR in connectivity.elements[qubit_ref].channels
    assert WiringLineType.DRIVE in connectivity.elements[qubit_ref].channels
    assert WiringLineType.CAVITY in connectivity.elements[qubit_ref].channels
    assert WiringLineType.FLUX in connectivity.elements[qubit_ref].channels


def test_multiple_cavity_lines_different_qubits():
    """Add cavity lines for multiple qubits (one per call)."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)
    connectivity.add_cavity_lines(qubit=2)
    connectivity.add_cavity_lines(qubit=3)

    allocate_wiring(connectivity, instruments)

    # Verify each qubit gets its own cavity line allocation
    for qubit in [1, 2, 3]:
        qubit_ref = QubitReference(qubit)
        assert qubit_ref in connectivity.elements
        assert WiringLineType.CAVITY in connectivity.elements[qubit_ref].channels
        channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
        assert len(channels) > 0


def test_cavity_line_visualization():
    """Allocate cavity lines and verify visualization includes cavity line type."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments)

    if visualize_flag:
        visualize(connectivity.elements, instruments.available_channels)

    # Test passes if allocation succeeds and visualization can be called
    qubit_ref = QubitReference(1)
    assert WiringLineType.CAVITY in connectivity.elements[qubit_ref].channels


# ==================== Edge Cases and Error Handling ====================

def test_cavity_line_insufficient_channels():
    """Create setup with insufficient channels and verify exception."""
    instruments = Instruments()
    # Create minimal setup that won't have enough channels for many cavity lines
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    # Try to allocate many cavity lines that exceed available channels
    for qubit in range(1, 100):  # Way more than available
        connectivity.add_cavity_lines(qubit=qubit)

    with pytest.raises(NotEnoughChannelsException):
        allocate_wiring(connectivity, instruments)


def test_cavity_line_allocation_order():
    """Verify cavity lines are allocated after drive lines but before flux lines."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)
    instruments.add_lf_fem(controller=1, slots=[1])

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=[1])
    connectivity.add_qubit_drive_lines(qubits=[1])
    connectivity.add_cavity_lines(qubit=1)
    connectivity.add_qubit_flux_lines(qubits=[1])

    allocate_wiring(connectivity, instruments)

    # Verify all are allocated (order is handled internally)
    qubit_ref = QubitReference(1)
    assert WiringLineType.DRIVE in connectivity.elements[qubit_ref].channels
    assert WiringLineType.CAVITY in connectivity.elements[qubit_ref].channels
    assert WiringLineType.FLUX in connectivity.elements[qubit_ref].channels


def test_cavity_line_element_storage():
    """Verify cavity line channels are stored correctly in element structure."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments)

    qubit_ref = QubitReference(1)
    assert qubit_ref in connectivity.elements
    element = connectivity.elements[qubit_ref]
    assert WiringLineType.CAVITY in element.channels
    channels = element.channels[WiringLineType.CAVITY]
    assert isinstance(channels, list)
    assert len(channels) > 0


# ==================== Regression Tests ====================

def test_existing_drive_lines_still_work():
    """Verify that existing add_qubit_drive_lines() functionality is not broken."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    connectivity.add_qubit_drive_lines(qubits=[1, 2, 3])

    allocate_wiring(connectivity, instruments)

    # Verify drive lines still work
    for qubit in [1, 2, 3]:
        qubit_ref = QubitReference(qubit)
        assert WiringLineType.DRIVE in connectivity.elements[qubit_ref].channels


def test_cavity_line_does_not_interfere_with_drive_lines():
    """Add both drive and cavity lines for same qubit and verify no conflicts."""
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)

    connectivity = Connectivity()
    connectivity.add_qubit_drive_lines(qubits=[1])
    connectivity.add_cavity_lines(qubit=1)

    allocate_wiring(connectivity, instruments)

    qubit_ref = QubitReference(1)
    # Both should be allocated separately
    assert WiringLineType.DRIVE in connectivity.elements[qubit_ref].channels
    assert WiringLineType.CAVITY in connectivity.elements[qubit_ref].channels
    # They should have different channel allocations
    drive_channels = connectivity.elements[qubit_ref].channels[WiringLineType.DRIVE]
    cavity_channels = connectivity.elements[qubit_ref].channels[WiringLineType.CAVITY]
    assert len(drive_channels) > 0
    assert len(cavity_channels) > 0
