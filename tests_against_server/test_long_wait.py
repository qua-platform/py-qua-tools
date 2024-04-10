import numpy as np
import pytest
from qualang_tools.macros.long_wait import long_wait, MAX_WAIT
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig, LoopbackInterface

import matplotlib.pyplot as plt

@pytest.fixture
def config():
    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0}},
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            }
        },
        "elements": {
            "resonator": {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "intermediate_frequency": 100e6,
                "operations": {
                    "readout": "readout_pulse",
                },
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": 24,
                "smearing": 0,
            },
        },
        "pulses": {
            "readout_pulse": {
                "operation": "measurement",
                "length": 80,
                "waveforms": {
                    "single": "const_wf",
                },
                "integration_weights": {
                    "cos": "cosine_weights",
                    "sin": "sine_weights",
                    "minus_sin": "minus_sine_weights",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
    }


def simulate_program_and_return(config, prog, duration=50000):
    qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
    qmm.close_all_quantum_machines()
    job = qmm.simulate(
        config,
        prog,
        SimulationConfig(
            duration,
            simulation_interface=LoopbackInterface([("con1", 1, "con1", 1)]),
            include_analog_waveforms=True,
        ),
    )

    # qm = qmm.open_qm(config)
    # job = qm.execute(prog)
    return job


# @pytest.mark.parametrize("wait_time", [4, 16, MAX_WAIT - 1, MAX_WAIT, MAX_WAIT + 1, 1000*MAX_WAIT])
@pytest.mark.parametrize("wait_time", [100])
def test_long_wait_time(config, wait_time):
    with program() as prog:
        play("pulse", "element")
        long_wait(wait_time)
        play("pulse", "element")

    job = simulate_program_and_return(config, prog)
    job.get_simulated_samples().con1.plot()
    plt.show()
