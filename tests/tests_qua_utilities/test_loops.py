"""Cloudsim-backed tests for `qualang_tools.loops`.

Ported as a small subset from `tests_against_server/test_loops.py`, using the session
`qmm` fixture and `qmm.simulate(...)`. Tests skip when no simulator is available.

The local config is OPX1000 MW (same topology as the folder fetch_xarray tests) because
the cloud simulator does not accept OPX1 analog configs. Error paths already live in
`tests/test_loops.py`.
"""

from copy import deepcopy

import numpy as np
import pytest

from qm import SimulationConfig
from qm.qua import (
    program,
    declare,
    declare_stream,
    fixed,
    for_,
    save,
    stream_processing,
    update_frequency,
    play,
    amp,
)

from qualang_tools.loops import from_array, qua_arange, qua_linspace, qua_logspace, get_equivalent_log_array

READOUT_LEN = 100
FEM_IDX = 6
ANALOG_OUTPUT_PORT = 8
ANALOG_INPUT_PORT = 1


@pytest.fixture
def config():
    return {
        "controllers": {
            "con1": {
                "type": "opx1000",
                "fems": {
                    FEM_IDX: {
                        "type": "MW",
                        "analog_outputs": {
                            ANALOG_OUTPUT_PORT: {
                                "sampling_rate": 1e9,
                                "band": 2,
                                "upconverter_frequency": 5e9,
                            },
                        },
                        "analog_inputs": {
                            ANALOG_INPUT_PORT: {
                                "sampling_rate": 1e9,
                                "band": 2,
                                "downconverter_frequency": 5e9,
                            },
                        },
                    },
                },
            },
        },
        "elements": {
            "resonator": {
                "MWInput": {"port": ("con1", FEM_IDX, ANALOG_OUTPUT_PORT)},
                "intermediate_frequency": 200e6,
                "MWOutput": {"port": ("con1", FEM_IDX, ANALOG_INPUT_PORT)},
                "time_of_flight": 484,
                "smearing": 0,
                "operations": {"readout": "readout_pulse"},
            },
        },
        "pulses": {
            "readout_pulse": {
                "operation": "measurement",
                "length": READOUT_LEN,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
                "integration_weights": {"cos": "cos", "sin": "sin"},
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "const_wf": {"type": "constant", "sample": 0.5},
            "zero_wf": {"type": "constant", "sample": 0.0},
        },
        "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
        "integration_weights": {
            "cos": {"cosine": [(1.0, READOUT_LEN)], "sine": [(0.0, READOUT_LEN)]},
            "sin": {"cosine": [(0.0, READOUT_LEN)], "sine": [(1.0, READOUT_LEN)]},
        },
    }


def _simulate_and_fetch(qmm, config, prog, duration=50_000, handle="a"):
    job = qmm.simulate(deepcopy(config), prog, SimulationConfig(duration))
    job.result_handles.wait_for_all_values()
    return job.result_handles.get(handle).fetch_all()["value"]


@pytest.mark.parametrize(
    ["start", "stop", "step"],
    [
        [10, 20, 1],
        [11, 0, -1],
        [0, 1, 0.2],
    ],
)
def test_qua_arange(qmm, config, start, stop, step):
    if qmm is None:
        pytest.skip("requires simulator available")

    if float(step).is_integer():
        with program() as prog:
            a = declare(int)
            a_st = declare_stream()
            with for_(*qua_arange(a, start, stop, step)):
                update_frequency("resonator", a)
                play("readout", "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")
    else:
        with program() as prog:
            a = declare(fixed)
            a_st = declare_stream()
            with for_(*qua_arange(a, start, stop, step)):
                play("readout" * amp(a), "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")

    a_qua = _simulate_and_fetch(qmm, config, prog)
    a_list = np.arange(start, stop, step)

    assert len(a_list) == len(a_qua)
    assert np.allclose(a_list, a_qua, atol=1e-4)


@pytest.mark.parametrize(
    ["vector", "qua_type"],
    [
        [np.arange(10, 20, 1), "int"],
        [np.linspace(0.1, 1, 6), "fixed"],
    ],
)
def test_from_array(qmm, config, vector, qua_type):
    if qmm is None:
        pytest.skip("requires simulator available")

    if qua_type == "int":
        with program() as prog:
            a = declare(int)
            a_st = declare_stream()
            with for_(*from_array(a, vector)):
                update_frequency("resonator", a)
                play("readout", "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")
    else:
        with program() as prog:
            a = declare(fixed)
            a_st = declare_stream()
            with for_(*from_array(a, vector)):
                play("readout" * amp(a), "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")

    a_qua = _simulate_and_fetch(qmm, config, prog)
    a_list = vector
    if (qua_type == "int") and (np.isclose(a_list[1] / a_list[0], a_list[-1] / a_list[-2])):
        a_list = get_equivalent_log_array(a_list)

    assert len(a_list) == len(a_qua)
    assert np.allclose(a_list, a_qua, atol=1e-4)


@pytest.mark.parametrize(["start", "stop", "N"], [[0.1, 1, 5]])
def test_qua_linspace(qmm, config, start, stop, N):
    if qmm is None:
        pytest.skip("requires simulator available")

    with program() as prog:
        a = declare(fixed)
        a_st = declare_stream()
        with for_(*qua_linspace(a, start, stop, N)):
            play("readout" * amp(a), "resonator")
            save(a, a_st)
        with stream_processing():
            a_st.save_all("a")

    a_qua = _simulate_and_fetch(qmm, config, prog)
    a_list = np.linspace(start, stop, N)

    assert len(a_list) == len(a_qua)
    assert np.allclose(a_list, a_qua, atol=1e-4)


@pytest.mark.parametrize(["start", "stop", "N"], [[-3.8, 0.2, 7]])
def test_qua_logspace_fixed(qmm, config, start, stop, N):
    if qmm is None:
        pytest.skip("requires simulator available")

    with program() as prog:
        a = declare(fixed)
        a_st = declare_stream()
        with for_(*qua_logspace(a, start, stop, N)):
            play("readout" * amp(a), "resonator")
            save(a, a_st)
        with stream_processing():
            a_st.save_all("a")

    a_qua = _simulate_and_fetch(qmm, config, prog)
    a_list = np.logspace(start, stop, N)

    assert len(a_list) == len(a_qua)
    assert np.allclose(a_list, a_qua, atol=1e-4)


@pytest.mark.parametrize(["start", "stop", "N"], [[np.log10(500), np.log10(12500), 11]])
def test_qua_logspace_int(qmm, config, start, stop, N):
    if qmm is None:
        pytest.skip("requires simulator available")

    with program() as prog:
        t = declare(int)
        t_st = declare_stream()
        with for_(*qua_logspace(t, start, stop, N)):
            play("readout", "resonator", duration=t)
            save(t, t_st)
        with stream_processing():
            t_st.save_all("a")

    a_qua = _simulate_and_fetch(qmm, config, prog, duration=70_000)
    a_list = get_equivalent_log_array(np.round(np.logspace(start, stop, N)))

    assert len(a_list) == len(a_qua)
    assert np.allclose(a_list, a_qua, atol=1e-4)
