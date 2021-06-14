import pytest
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig

from qualang_tools.bakery.bakery import baking


@pytest.fixture
def config():
    return {
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
                "intermediate_frequency": 0,
                "operations": {
                    "playOp": "constPulse",
                    "a_pulse": "arb_pulse1"
                },
            },
        },
        "pulses": {
            "constPulse": {
                "operation": "control",
                "length": 1000,  # in ns
                "waveforms": {"single": "const_wf"},
            },
            "arb_pulse1": {
                "operation": "control",
                "length": 100,  # in ns
                "waveforms": {"single": "arb_wf"},
            },
        },
        "waveforms": {
            "const_wf": {"type": "constant", "sample": 0.2},
            "arb_wf": {"type": "arbitrary", "samples": [i / 200 for i in range(100)]},
        },
    }


def simulate_program_and_return(config, prog, duration=20000):
    qmm = QuantumMachinesManager()
    qmm.close_all_quantum_machines()
    job = qmm.simulate(config, prog, SimulationConfig(duration, include_analog_waveforms=True))
    return job


def test_simple_bake(config):
    with baking(config=config) as b:
        for x in range(10):
            b.add_Op(f'new_op_{x}', "qe1", samples=[1, 0, 1, 0])
            b.play(f'new_op_{x}', "qe1")

    with program() as prog:
        b.run()

    job = simulate_program_and_return(config, prog)
    samples = job.get_simulated_samples()
    assert len(samples.con1.analog['1']) == 80000


def test_bake_with_macro(config):
    def play_twice(b):
        b.play('a_pulse', 'qe1')
        b.play('a_pulse', 'qe1')

    with baking(config=config) as b:
        play_twice(b)

    with program() as prog:
        b.run()

    job = simulate_program_and_return(config, prog, 200)
    samples = job.get_simulated_samples()
    tstamp = int(job.simulated_analog_waveforms()['controllers']['con1']['ports']['1'][0]['timestamp'])
    assert all(
        samples.con1.analog['1'][tstamp:tstamp + 200] == [i / 200 for i in range(100)] + [i / 200 for i in range(100)])
