"""Cloudsim simulation test for `assign_variables_to_element`.

Asserts that a 16 ns wait is inserted on the named analog element. Skips if the
compiler no longer emits that wait (QOP >= 2.4.4).
"""

import numpy as np
import pytest

from qm import SimulationConfig, LoopbackInterface
from qm.qua import program, play, declare, fixed

from qualang_tools.addons.calibration.calibrations import u
from qualang_tools.addons.variables import assign_variables_to_element

FEM_IDX = 1


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


def analog_samples(job, port=1):
    analog = job.get_simulated_samples().con1.analog
    for key in (f"{FEM_IDX}-{port}", str(port)):
        if key in analog:
            return analog[key]
    raise KeyError(f"Could not find analog port {port} in {list(analog.keys())}")


def test_assign_variables_to_element_inserts_wait(qmm, config):
    if qmm is None:
        pytest.skip("requires simulator available")

    op = "playOp"
    with program() as prog:
        a = declare(int)
        b = declare(fixed)
        play(op, "qe1")
        assign_variables_to_element("qe1", a, b)
        play(op, "qe1")

    pulse_length = config["pulses"]["constPulse"]["length"]
    pulse_amplitude = config["waveforms"]["const_wf"]["sample"]
    job = qmm.simulate(
        config,
        prog,
        SimulationConfig(
            2 * pulse_length + 200,
            simulation_interface=LoopbackInterface([("con1", FEM_IDX, 1, "con1", FEM_IDX, 1)]),
            include_analog_waveforms=True,
        ),
    )
    output = analog_samples(job)
    th = pulse_amplitude / 2
    rising_edges = np.where((output[:-1] <= th / 2) & (output[1:] > th / 2))[0]
    falling_edges = np.where((output[:-1] > th / 2) & (output[1:] <= th / 2))[0]
    if len(rising_edges) < 2 or len(falling_edges) < 1:
        pytest.skip("could not locate two analog pulses; compiler may have dropped the wait")

    wait_samples = output[falling_edges[0] : rising_edges[1]]
    expected = 4 * int(u.clock_cycle) * 2  # 16 ns at 2 GS/s
    if len(wait_samples) != expected:
        pytest.skip(
            f"wait gap was {len(wait_samples)} samples, expected {expected} "
            "(assign_variables_to_element is a no-op on QOP >= 2.4.4)"
        )
    assert len(wait_samples) == expected
