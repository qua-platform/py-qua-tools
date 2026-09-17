"""Cloudsim simulation tests for `VoltageGateSequence`.

Ports the first square block of `test_constant_square_python_1.py` and the first ramp
block of `test_ramps_python_1.py`. No plots. Uses OPX1000 LF analog sticky elements.
"""

from copy import deepcopy

import numpy as np
import pytest

from qm import SimulationConfig
from qm.qua import program, play

from qualang_tools.voltage_gates import VoltageGateSequence

FEM_IDX = 1
PORT_P1 = 1
PORT_P2 = 2
MAX_AMP = 0.4
SAMPLING_RATE = 1


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
                            PORT_P1: {
                                "offset": 0.0,
                                "output_mode": "direct",
                                "sampling_rate": 1e9,
                                "upsampling_mode": "pulse",
                            },
                            PORT_P2: {
                                "offset": 0.0,
                                "output_mode": "direct",
                                "sampling_rate": 1e9,
                                "upsampling_mode": "pulse",
                            },
                        },
                        "digital_outputs": {1: {}},
                    },
                },
            }
        },
        "elements": {
            "P1_sticky": {
                "singleInput": {"port": ("con1", FEM_IDX, PORT_P1)},
                "sticky": {"analog": True, "duration": 4},
                "operations": {},
            },
            "P2_sticky": {
                "singleInput": {"port": ("con1", FEM_IDX, PORT_P2)},
                "sticky": {"analog": True, "duration": 4},
                "operations": {},
            },
            "qdac_trigger1": {
                "digitalInputs": {
                    "trigger": {
                        "port": ("con1", FEM_IDX, 1),
                        "delay": 0,
                        "buffer": 0,
                    }
                },
                "operations": {"trigger": "trigger_pulse"},
            },
        },
        "pulses": {
            "trigger_pulse": {
                "operation": "control",
                "length": 1000,
                "digital_marker": "ON",
            },
        },
        "waveforms": {},
        "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
    }


def get_linear_ramp(start_value, end_value, duration, sampling_rate=1):
    num_points = duration
    if num_points <= 1:
        return [start_value] * num_points
    ramp = [start_value + (end_value - start_value) * (i + 1) / num_points for i in range(num_points)]
    return [point for point in ramp for _ in range(sampling_rate)]


def analog_channel(samples, port):
    analog = samples.con1.analog
    for key in (f"{FEM_IDX}-{port}", str(port)):
        if key in analog:
            return analog[key]
    raise KeyError(f"Could not find analog port {port} in {list(analog.keys())}")


def _to_1gs(wf, n_ns):
    """Downsample cloudsim 2 GS/s analog traces to 1 sample/ns when needed."""
    wf = np.asarray(wf)
    if len(wf) >= 2 * n_ns:
        return wf[::2]
    return wf


def validate_program(samples, requested_wf_p, requested_wf_m):
    requested_wf_p = np.asarray(requested_wf_p)
    requested_wf_m = np.asarray(requested_wf_m)
    wf_p = analog_channel(samples, PORT_P1)
    wf_m = analog_channel(samples, PORT_P2)
    t0_p = np.where(wf_p != 0)[0]
    t0_m = np.where(wf_m != 0)[0]
    t0 = min(t0_p[0], t0_m[0])
    wf_p = _to_1gs(wf_p[t0:], len(requested_wf_p))
    wf_m = _to_1gs(wf_m[t0:], len(requested_wf_m))
    zeros = np.where(wf_p == 0)[0]
    t1 = zeros[0] if len(zeros) else len(wf_p) - 1

    rel_p = np.mean((wf_p[: len(requested_wf_p)] - requested_wf_p) / requested_wf_p)
    rel_m = np.mean((wf_m[: len(requested_wf_m)] - requested_wf_m) / requested_wf_m)
    assert rel_p < 0.1 and rel_m < 0.1, "Simulated wf doesn't match requested wf."

    area_p = np.sum(wf_p[: t1 + 1]) / np.sum(wf_p[: len(requested_wf_p)]) * 100
    area_m = np.sum(wf_m[: t1 + 1]) / np.sum(wf_m[: len(requested_wf_m)]) * 100
    assert area_p < 1 and area_m < 1, "The compensation pulse leads to more than 1% error."

    assert (max(np.abs(np.diff(wf_p[: t1 + 1]))) < 0.5) and (
        max(np.abs(np.diff(wf_m[: t1 + 1]))) < 0.5
    ), "The maximum voltage gradient is above 0.5 V."


def test_constant_square_sequence(qmm, config):
    if qmm is None:
        pytest.skip("requires simulator available")

    cfg = deepcopy(config)
    level_init = [MAX_AMP, -0.1]
    duration_init = 1000
    level_manip = [0.49, -0.3]
    duration_manip = 100
    level_readout = [0.2, -0.2]
    duration_readout = 2000
    max_compensation_amplitude = 0.2

    seq = VoltageGateSequence(cfg, ["P1_sticky", "P2_sticky"])
    seq.add_points("initialization", level_init, duration_init)
    seq.add_points("idle", level_manip, duration_manip)
    seq.add_points("readout", level_readout, duration_readout)

    requested_wf_p, requested_wf_m = [
        (
            [level_init[i]] * duration_init * SAMPLING_RATE
            + [level_manip[i]] * duration_manip * SAMPLING_RATE
            + [level_readout[i]] * duration_readout * SAMPLING_RATE
        )
        for i in range(2)
    ]

    with program() as prog:
        play("trigger", "qdac_trigger1")
        seq.add_step(voltage_point_name="initialization")
        seq.add_step(voltage_point_name="idle")
        seq.add_step(voltage_point_name="readout")
        seq.add_compensation_pulse(max_amplitude=max_compensation_amplitude)
        seq.ramp_to_zero()

    job = qmm.simulate(cfg, prog, SimulationConfig(duration=20000 // 4))
    validate_program(job.get_simulated_samples(), requested_wf_p, requested_wf_m)


def test_ramp_sequence(qmm, config):
    if qmm is None:
        pytest.skip("requires simulator available")

    cfg = deepcopy(config)
    level_init = [0.1, -0.1]
    duration_init = 1000
    level_manip = [0.3, -0.3]
    ramp_to_manip = 100
    duration_manip = 100
    level_readout = [0.2, -0.2]
    ramp_to_readout = 400
    duration_readout = 2000
    max_compensation_amplitude = 0.2

    seq = VoltageGateSequence(cfg, ["P1_sticky", "P2_sticky"])
    seq.add_points("initialization", level_init, duration_init)
    seq.add_points("idle", level_manip, duration_manip)
    seq.add_points("readout", level_readout, duration_readout)

    requested_wf_p, requested_wf_m = [
        (
            [level_init[i]] * duration_init * SAMPLING_RATE
            + get_linear_ramp(level_init[i], level_manip[i], ramp_to_manip, SAMPLING_RATE)
            + [level_manip[i]] * duration_manip * SAMPLING_RATE
            + get_linear_ramp(level_manip[i], level_readout[i], ramp_to_readout, SAMPLING_RATE)
            + [level_readout[i]] * duration_readout * SAMPLING_RATE
        )
        for i in range(2)
    ]

    with program() as prog:
        play("trigger", "qdac_trigger1")
        seq.add_step(voltage_point_name="initialization")
        seq.add_step(voltage_point_name="idle", ramp_duration=100)
        seq.add_step(voltage_point_name="readout", ramp_duration=400)
        seq.add_compensation_pulse(max_amplitude=max_compensation_amplitude)
        seq.ramp_to_zero()

    job = qmm.simulate(cfg, prog, SimulationConfig(duration=20000 // 4))
    validate_program(job.get_simulated_samples(), requested_wf_p, requested_wf_m)
