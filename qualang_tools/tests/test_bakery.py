import pytest
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig

from qualang_tools.bakery.bakery import baking


def get_config():
    config = {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": +0.0},
                },
            }
        },
        "elements": {
            "qe1": {
                "singleInput": {"port": ("con1", 1)},
                "intermediate_frequency": 5e6,
                "operations": {
                    "playOp": "constPulse",
                },
            },
        },
        "pulses": {
            "constPulse": {
                "operation": "control",
                "length": 1000,  # in ns
                "waveforms": {"single": "const_wf"},
            },
        },
        "waveforms": {
            "const_wf": {"type": "constant", "sample": 0.2},
        },
    }
    return config



def simulate_program_and_return(config,prog,duration=20000):
    qmm = QuantumMachinesManager()
    qmm.close_all_quantum_machines()
    job = qmm.simulate(config, prog, SimulationConfig(duration))
    samples = job.get_simulated_samples()
    return samples


def test_simple_bake():
    config = get_config()
    with baking(config=config) as b:
        for x in range(10):
            b.add_Op(f'new_op_{x}',"qe1",samples=[1,0,1,0])
            b.play(f'new_op_{x}',"qe1")

    with program() as prog:
        b.run()

    samples = simulate_program_and_return(config,prog)
    assert len(samples.con1.analog['1'])==80000

