import pytest
from qualang_tools.wirer import ConnectivitySuperconductingQubits, allocate_wiring, visualize
from qualang_tools.wirer.connectivity.element import Element, Reference
from qualang_tools.wirer.connectivity.wiring_spec import *
from qualang_tools.wirer.wirer.channel_specs import *


def test_add_dummy_line(instruments_2lf_2mw):
    qubits = [1, 2, 3, 4, 5]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5)]

    connectivity = ConnectivitySuperconductingQubits()
    connectivity.add_resonator_line(qubits=qubits, constraints=mw_fem_spec(slot=7))
    connectivity.add_qubit_drive_lines(qubits=qubits, constraints=mw_fem_spec(slot=7))
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    dummy_element = Element(id="test")
    connectivity.add_wiring_spec(
        frequency=DC,
        io_type=INPUT_AND_OUTPUT,
        line_type="ch",
        triggered=False,
        constraints=None,
        elements=[dummy_element],
    )

    allocate_wiring(connectivity, instruments_2lf_2mw)

    if pytest.visualize_flag:
        visualize(connectivity.elements, instruments_2lf_2mw.available_channels)

    # regression test
    test_element = connectivity.elements[Reference("test")]
    for i, channel in enumerate(test_element.channels["ch"]):
        assert pytest.channels_are_equal(
            channel,
            [InstrumentChannelLfFemInput(con=1, port=1, slot=1), InstrumentChannelLfFemOutput(con=1, port=6, slot=1)][
                i
            ],
        )
