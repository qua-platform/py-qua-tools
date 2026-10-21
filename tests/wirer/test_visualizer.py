from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from qualang_tools.wirer import Connectivity, lf_fem_spec, allocate_wiring, Instruments, qdac2_spec
from qualang_tools.wirer.visualizer.web_visualizer import visualize_web


def _assert_web_visualization(elements, channels, tmp_path, *expected_ids):
    html_path = visualize_web(
        elements,
        channels,
        output_path=str(tmp_path / "wiring.html"),
        show_matplotlib=False,
    )
    html = Path(html_path).read_text(encoding="utf-8")
    assert html
    assert "data:image/png;base64," in html
    for instrument_id in expected_ids:
        assert instrument_id in html


def test_6q_allocation_visualization(instruments_2lf_2mw, tmp_path):
    qubits = [1, 2, 3, 4, 5, 6]
    qubit_pairs = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, triggered=True)
    connectivity.add_qubit_drive_lines(qubits=qubits, triggered=True)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs, constraints=lf_fem_spec(out_slot=2))

    allocate_wiring(connectivity, instruments_2lf_2mw)

    _assert_web_visualization(
        connectivity.elements,
        instruments_2lf_2mw.available_channels,
        tmp_path,
        "OPX1000",
    )


def test_4q_allocation_visualization(instruments_1opx_1octave, tmp_path):
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]

    connectivity = Connectivity()
    connectivity.add_resonator_line(qubits=qubits, triggered=True)
    connectivity.add_qubit_drive_lines(qubits=qubits, triggered=True)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)

    allocate_wiring(connectivity, instruments_1opx_1octave)

    _assert_web_visualization(
        connectivity.elements,
        instruments_1opx_1octave.available_channels,
        tmp_path,
        "OPX+",
        "Octave",
    )


def test_empty_opx1000_visualization(tmp_path):
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=1)
    instruments.add_mw_fem(controller=1, slots=2)
    connectivity = Connectivity()
    allocate_wiring(connectivity, instruments)
    _assert_web_visualization(connectivity.elements, instruments.available_channels, tmp_path, "OPX1000")


def test_empty_opx_octave_visualization(instruments_1opx_1octave, tmp_path):
    connectivity = Connectivity()
    allocate_wiring(connectivity, instruments_1opx_1octave)
    _assert_web_visualization(
        connectivity.elements,
        instruments_1opx_1octave.available_channels,
        tmp_path,
        "OPX+",
        "Octave",
    )


def test_basic_superconducting_qubit_example_multi_chassis(instruments_5opx1000, tmp_path):
    connectivity = Connectivity()
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)
    allocate_wiring(connectivity, instruments_5opx1000)
    _assert_web_visualization(
        connectivity.elements,
        instruments_5opx1000.available_channels,
        tmp_path,
        "OPX1000",
        "Octave",
    )


def test_basic_superconducting_qubit_example(instruments_1opx_1octave, tmp_path):
    connectivity = Connectivity()
    qubits = [1, 2]
    qubit_pairs = [(1, 2)]
    connectivity.add_resonator_line(qubits=qubits)
    connectivity.add_qubit_drive_lines(qubits=qubits)
    connectivity.add_qubit_flux_lines(qubits=qubits)
    connectivity.add_qubit_pair_flux_lines(qubit_pairs=qubit_pairs)
    allocate_wiring(connectivity, instruments_1opx_1octave)
    _assert_web_visualization(
        connectivity.elements,
        instruments_1opx_1octave.available_channels,
        tmp_path,
        "OPX+",
        "Octave",
    )


def test_five_voltage_gates_qdac2_visualization(tmp_path):
    instruments = Instruments()
    instruments.add_qdac2(indices=1)
    connectivity = Connectivity()
    connectivity.add_voltage_gate_lines([1, 2, 3, 4, 5], triggered=False)
    allocate_wiring(connectivity, instruments)
    _assert_web_visualization(connectivity.elements, instruments.available_channels, tmp_path, "QDAC2")


def test_five_voltage_gates_qdac2_opx_visualization(tmp_path):
    instruments = Instruments()
    instruments.add_qdac2(indices=1)
    instruments.add_lf_fem(controller=1, slots=[1])
    connectivity = Connectivity()
    connectivity.add_voltage_gate_lines([1, 2, 3, 4, 5], triggered=False, constraints=lf_fem_spec(1) & qdac2_spec(1))
    connectivity.add_voltage_gate_lines(
        [6], triggered=True, constraints=lf_fem_spec(1) & qdac2_spec(index=1, trigger_in_port=2)
    )
    allocate_wiring(connectivity, instruments, block_used_channels=False)
    connectivity.add_voltage_gate_lines(
        [7],
        triggered=True,
        constraints=lf_fem_spec(1, out_port=7) & qdac2_spec(index=1, out_port=11, trigger_in_port=2),
    )
    allocate_wiring(connectivity, instruments)

    _assert_web_visualization(
        connectivity.elements,
        instruments.available_channels,
        tmp_path,
        "QDAC2",
        "OPX1000",
    )
