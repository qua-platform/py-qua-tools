"""Cloudsim simulation tests for `qualang_tools.macros.long_wait`.

Ported from `tests_against_server/test_long_wait.py` (simulation only; the 30s live
execute test is not included). Uses an OPX1000 LF analog config because cloudsim
does not accept OPX1 controllers.
"""

import numpy as np
import pytest

from qm import SimulationConfig, LoopbackInterface
from qm.qua import program, play

from qualang_tools.addons.calibration.calibrations import u
from qualang_tools.macros.long_wait import long_wait

FEM_IDX = 1
dummy_max_wait_time = 200  # clock cycles


@pytest.fixture
def config():
    return {
        "controllers": {
            "con1": {
                "type": "opx1000",
                "fems": {
                    FEM_IDX: {
                        "type": "LF",
                        "analog_outputs": {
                            1: {
                                "offset": 0.0,
                                "output_mode": "direct",
                                "sampling_rate": 1e9,
                                "upsampling_mode": "pulse",
                            },
                            2: {
                                "offset": 0.0,
                                "output_mode": "direct",
                                "sampling_rate": 1e9,
                                "upsampling_mode": "pulse",
                            },
                        },
                        "analog_inputs": {
                            1: {"offset": 0.0, "gain_db": 0, "sampling_rate": 1e9},
                        },
                    },
                },
            }
        },
        "elements": {
            "qe1": {
                "singleInput": {"port": ("con1", FEM_IDX, 1)},
                "intermediate_frequency": 0,
                "operations": {"playOp": "constPulse"},
            },
            "qe2": {
                "singleInput": {"port": ("con1", FEM_IDX, 2)},
                "intermediate_frequency": 0,
                "operations": {"playOp": "constPulse"},
            },
        },
        "pulses": {
            "constPulse": {
                "operation": "control",
                "length": 1000,
                "waveforms": {"single": "const_wf"},
            },
        },
        "waveforms": {
            "const_wf": {"type": "constant", "sample": 0.2},
        },
    }


def analog_samples(job, port):
    analog = job.get_simulated_samples().con1.analog
    for key in (f"{FEM_IDX}-{port}", str(port)):
        if key in analog:
            return analog[key]
    raise KeyError(f"Could not find analog port {port} in {list(analog.keys())}")


def execute_program(qmm, config, prog, simulation_duration=10_000):
    return qmm.simulate(
        config,
        prog,
        SimulationConfig(
            simulation_duration,
            simulation_interface=LoopbackInterface([("con1", FEM_IDX, 1, "con1", FEM_IDX, 1)]),
            include_analog_waveforms=True,
        ),
    )


def wait_sample_count(output, pulse_amplitude):
    th = pulse_amplitude / 2
    rising_edges = np.where((output[:-1] <= th / 2) & (output[1:] > th / 2))[0]
    falling_edges = np.where((output[:-1] > th / 2) & (output[1:] <= th / 2))[0]
    wait_samples = output[falling_edges[0] : rising_edges[1]]
    return len(wait_samples)


# Cloudsim LF analog is 2 GS/s (2 samples/ns); OPX1 server tests used 1 GS/s.
SAMPLES_PER_CLOCK_CYCLE = int(u.clock_cycle) * 2


@pytest.mark.parametrize(
    "wait_time",
    [4, 16, 100, dummy_max_wait_time - 1, dummy_max_wait_time, dummy_max_wait_time + 1, 100 * dummy_max_wait_time],
)
def test_long_wait_time_simulation(qmm, config, wait_time):
    if qmm is None:
        pytest.skip("requires simulator available")

    op = "playOp"
    with program() as prog:
        play(op, "qe1")
        long_wait(wait_time, threshold_for_looping=dummy_max_wait_time)
        play(op, "qe1")

    element = config["elements"]["qe1"]
    pulse = config["pulses"][element["operations"][op]]
    pulse_length = pulse["length"]
    pulse_amplitude = config["waveforms"][pulse["waveforms"]["single"]]["sample"]

    job = execute_program(qmm, config, prog, simulation_duration=wait_time + 2 * pulse_length + 100)
    output = analog_samples(job, 1)
    assert wait_sample_count(output, pulse_amplitude) == wait_time * SAMPLES_PER_CLOCK_CYCLE


@pytest.mark.parametrize(
    "wait_time",
    [4, 16, 100, dummy_max_wait_time - 1, dummy_max_wait_time, dummy_max_wait_time + 1, 100 * dummy_max_wait_time],
)
def test_long_wait_time_simulation_multi_element(qmm, config, wait_time):
    if qmm is None:
        pytest.skip("requires simulator available")

    op = "playOp"
    with program() as prog:
        play(op, "qe1")
        play(op, "qe2")
        long_wait(wait_time, "qe1", "qe2", threshold_for_looping=dummy_max_wait_time)
        play(op, "qe1")
        play(op, "qe2")

    element = config["elements"]["qe1"]
    pulse = config["pulses"][element["operations"][op]]
    pulse_length = pulse["length"]
    pulse_amplitude = config["waveforms"][pulse["waveforms"]["single"]]["sample"]

    job = execute_program(qmm, config, prog, simulation_duration=wait_time + 2 * pulse_length + 100)
    for port in (1, 2):
        output = analog_samples(job, port)
        assert wait_sample_count(output, pulse_amplitude) == wait_time * SAMPLES_PER_CLOCK_CYCLE
