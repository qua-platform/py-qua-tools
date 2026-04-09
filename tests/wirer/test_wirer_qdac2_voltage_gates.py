import pytest

from qualang_tools.wirer import (
    Connectivity,
    Instruments,
    allocate_wiring,
    lf_fem_spec,
    opx_spec,
    qdac2_spec,
)
from qualang_tools.wirer.connectivity.element import ElementReference
from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelLfFemOutput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelQdac2DigitalInput,
    InstrumentChannelQdac2Output,
)


def test_voltage_gate_lines_qdac2_untriggered():
    instruments = Instruments()
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    connectivity.add_voltage_gate_lines([1, 2, 3], triggered=False)

    allocate_wiring(connectivity, instruments)

    for i in (1, 2, 3):
        chans = connectivity.elements[ElementReference("vg", i)].channels[WiringLineType.GLOBAL_GATE]
        assert len(chans) == 1
        assert isinstance(chans[0], InstrumentChannelQdac2Output)


def test_voltage_gate_lines_qdac2_triggered():
    instruments = Instruments()
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    connectivity.add_voltage_gate_lines([1, 2], triggered=True)

    allocate_wiring(connectivity, instruments)

    for i in (1, 2):
        chans = connectivity.elements[ElementReference("vg", i)].channels[WiringLineType.GLOBAL_GATE]
        assert len(chans) == 2
        outs = [c for c in chans if isinstance(c, InstrumentChannelQdac2Output)]
        trigs = [c for c in chans if isinstance(c, InstrumentChannelQdac2DigitalInput)]
        assert len(outs) == 1 and len(trigs) == 1
        assert outs[0].con == trigs[0].con == 1


def test_voltage_gate_lines_qdac2_constrained():
    instruments = Instruments()
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    c = qdac2_spec(index=1, out_port=7, trigger_in_port=2)
    connectivity.add_voltage_gate_lines([1], triggered=True, constraints=c)

    allocate_wiring(connectivity, instruments)

    chans = connectivity.elements[ElementReference("vg", 1)].channels[WiringLineType.GLOBAL_GATE]
    assert any(
        pytest.channels_are_equal(c, InstrumentChannelQdac2Output(con=1, port=7)) for c in chans
    )
    assert any(
        pytest.channels_are_equal(c, InstrumentChannelQdac2DigitalInput(con=1, port=2)) for c in chans
    )


def test_voltage_gate_lf_fem_and_qdac_dual_channels():
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=1)
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    c = lf_fem_spec(con=1, out_slot=1) & qdac2_spec(index=1)
    connectivity.add_voltage_gate_lines([1], triggered=False, constraints=c)

    allocate_wiring(connectivity, instruments)

    chans = connectivity.elements[ElementReference("vg", 1)].channels[WiringLineType.GLOBAL_GATE]
    assert len(chans) == 2
    assert any(isinstance(c, InstrumentChannelLfFemOutput) for c in chans)
    assert any(isinstance(c, InstrumentChannelQdac2Output) for c in chans)


def test_voltage_gate_five_lf_fem_and_qdac_dual_channels():
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=1)
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    c = lf_fem_spec(con=1, out_slot=1) & qdac2_spec(index=1)
    connectivity.add_voltage_gate_lines([1, 2, 3, 4, 5], triggered=False, constraints=c)

    allocate_wiring(connectivity, instruments)

    for i in range(1, 6):
        chans = connectivity.elements[ElementReference("vg", i)].channels[WiringLineType.GLOBAL_GATE]
        assert len(chans) == 2
        assert any(isinstance(c, InstrumentChannelLfFemOutput) for c in chans)
        assert any(isinstance(c, InstrumentChannelQdac2Output) for c in chans)


def test_voltage_gate_opx_plus_and_qdac_dual_channels():
    instruments = Instruments()
    instruments.add_opx_plus(controllers=1)
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    c = opx_spec(con=1) & qdac2_spec(index=1)
    connectivity.add_voltage_gate_lines([1], triggered=False, constraints=c)

    allocate_wiring(connectivity, instruments)

    chans = connectivity.elements[ElementReference("vg", 1)].channels[WiringLineType.GLOBAL_GATE]
    assert len(chans) == 2
    assert any(isinstance(c, InstrumentChannelOpxPlusOutput) for c in chans)
    assert any(isinstance(c, InstrumentChannelQdac2Output) for c in chans)


def test_voltage_gate_lf_fem_and_qdac_triggered_dual():
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=1)
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    c = lf_fem_spec(con=1, out_slot=1) & qdac2_spec(index=1)
    connectivity.add_voltage_gate_lines([1], triggered=True, constraints=c)

    allocate_wiring(connectivity, instruments)

    chans = connectivity.elements[ElementReference("vg", 1)].channels[WiringLineType.GLOBAL_GATE]
    assert len(chans) == 4
    assert sum(isinstance(c, InstrumentChannelLfFemOutput) for c in chans) == 1
    assert sum(isinstance(c, InstrumentChannelQdac2Output) for c in chans) == 1
    assert sum(c.signal_type == "digital" for c in chans) == 2
