import matplotlib.pyplot as plt
import pytest
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
import numpy as np
from qualang_tools.bakery.bakery import baking
from copy import deepcopy


def gauss(amplitude, mu, sigma, length):
    t = np.linspace(-length / 2, length / 2, length)
    gauss_wave = amplitude * np.exp(-((t - mu) ** 2) / (2 * sigma ** 2))
    return [float(x) for x in gauss_wave]


@pytest.fixture
def config():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g ** 2) * (2 * c ** 2 - 1))
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": +0.0},
                    2: {"offset": +0.0},
                    3: {"offset": +0.0},
                },
                "digital_outputs": {1: {}, 2: {}},
            }
        },
        "elements": {
            "qe1": {
                "singleInput": {"port": ("con1", 1)},
                "intermediate_frequency": 0,
                "operations": {
                    "playOp": "constPulse",
                    "a_pulse": "arb_pulse1",
                    "playOp2": "constPulse2",
                },
                "digitalInputs": {
                    "digital_input1": {
                        "port": ("con1", 1),
                        "delay": 0,
                        "buffer": 0,
                    }
                },
            },
            "qe2": {
                "mixInputs": {
                    "I": ("con1", 2),
                    "Q": ("con1", 3),
                    "lo_frequency": 0,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 0,
                "operations": {"constOp": "constPulse_mix", "gaussOp": "gauss_pulse"},
            },
        },
        "pulses": {
            "constPulse": {
                "operation": "control",
                "length": 1000,  # in ns
                "waveforms": {"single": "const_wf"},
            },
            "constPulse2": {
                "operation": "control",
                "length": 1000,  # in ns
                "waveforms": {"single": "const_wf"},
                "digital_marker": "ON",
            },
            "arb_pulse1": {
                "operation": "control",
                "length": 100,  # in ns
                "waveforms": {"single": "arb_wf"},
            },
            "constPulse_mix": {
                "operation": "control",
                "length": 80,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
            },
            "gauss_pulse": {
                "operation": "control",
                "length": 80,
                "waveforms": {"I": "gauss_wf", "Q": "zero_wf"},
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
            "arb_wf": {"type": "arbitrary", "samples": [i / 200 for i in range(100)]},
            "gauss_wf": {"type": "arbitrary", "samples": gauss(0.2, 0, 15, 80)},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 0,
                    "lo_frequency": 0,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
        },
    }


def simulate_program_and_return(config, prog, duration=20000):
    qmm = QuantumMachinesManager()
    qmm.close_all_quantum_machines()
    job = qmm.simulate(
        config, prog, SimulationConfig(duration, include_analog_waveforms=True)
    )
    return job


def test_simple_bake(config):
    cfg = deepcopy(config)
    with baking(config=cfg) as b:
        for x in range(10):
            b.add_op(f"new_op_{x}", "qe1", samples=[1, 0, 1, 0])
            b.play(f"new_op_{x}", "qe1")

    with program() as prog:
        b.run()

    job = simulate_program_and_return(cfg, prog)
    samples = job.get_simulated_samples()
    assert len(samples.con1.analog["1"]) == 80000


def test_bake_with_macro(config):
    cfg = deepcopy(config)

    def play_twice(b):
        b.play("a_pulse", "qe1")
        b.play("a_pulse", "qe1")

    with baking(config=cfg) as b:
        play_twice(b)

    with program() as prog:
        b.run()

    job = simulate_program_and_return(cfg, prog, 200)
    samples = job.get_simulated_samples()
    tstamp = int(
        job.simulated_analog_waveforms()["controllers"]["con1"]["ports"]["1"][0][
            "timestamp"
        ]
    )
    assert all(
        samples.con1.analog["1"][tstamp: tstamp + 200]
        == [i / 200 for i in range(100)] + [i / 200 for i in range(100)]
    )


def test_amp_modulation_run(config):
    cfg = deepcopy(config)
    with baking(config=cfg, padding_method="right", override=False) as b:
        b.play("playOp", "qe1")
    with baking(config=cfg, padding_method="right", override=False) as b2:
        b2.play("playOp", "qe1")
    amp_Python = 2
    with program() as prog:
        b.run(amp_array=[("qe1", amp_Python)])

    with program() as prog2:
        amp_QUA = declare(fixed, value=amp_Python)
        b2.run(amp_array=[("qe1", amp_QUA)])

    with program() as prog3:
        play("playOp" * amp(amp_Python), "qe1")

    job1 = simulate_program_and_return(cfg, prog, 500)
    samples1 = job1.get_simulated_samples()
    samples1_data = samples1.con1.analog["1"]

    job2 = simulate_program_and_return(cfg, prog2, 500)
    samples2 = job2.get_simulated_samples()
    samples2_data = samples2.con1.analog["1"]
    job3 = simulate_program_and_return(cfg, prog3, 500)
    samples3 = job3.get_simulated_samples()
    samples3_data = samples3.con1.analog["1"]

    assert len(samples1_data) == len(samples2_data)
    assert all(
        [samples1_data[i] == samples3_data[i] for i in range(len(samples1_data))]
    )
    assert all(
        [samples2_data[i] == samples3_data[i] for i in range(len(samples2_data))]
    )


def test_play_baked_with_existing_digital_wf(config):
    cfg = deepcopy(config)
    with baking(cfg) as b:
        b.play("playOp2", "qe1")

    with program() as prog:
        b.run()
    job = simulate_program_and_return(cfg, prog)
    samples = job.get_simulated_samples()
    assert len(samples.con1.digital["1"] > 0)
