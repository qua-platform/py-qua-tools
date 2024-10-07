import pytest

from qualang_tools.wirer import *

visualize_flag = pytest.visualize_flag

def test_opx_plus_resonator_constraining():
    # Define the available instrument setup
    instruments = Instruments()
    instruments.add_opx_plus(controllers = [1])
    instruments.add_octave(indices = 1)

    q1_res_ch = opx_iq_octave_spec(out_port_i=9, out_port_q=10, rf_out=1)

    qubits = [1]
    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, triggered=True, constraints=q1_res_ch)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits[0], triggered=True)

    allocate_wiring(connectivity, instruments)

    if visualize_flag:
        visualize(connectivity.elements, instruments.available_channels)

def test_fix_attribute_equality():
    """
    Make sure that channels aren't considered equal just because their attributes
    are equal.
    """
    spec = opx_iq_octave_spec()

    assert all(spec.channel_templates.count(element) == 1 for element in spec.channel_templates)
