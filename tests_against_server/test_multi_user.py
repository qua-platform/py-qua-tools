import pytest
import numpy as np
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.QmJob import QmJob
from qm.qua import *
from qualang_tools.multi_user import qm_session


@pytest.fixture
def config1():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                    3: {"offset": 0.0},
                },
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            }
        },
        "elements": {
            "qubit": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 10e9,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 50e6,
                "operations": {
                    "cw": "const_pulse",
                },
            },
            "resonator": {
                "singleInput": {
                    "port": ("con1", 3),
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
            "const_pulse": {
                "operation": "control",
                "length": 1e3,
                "waveforms": {
                    "I": "const_wf",
                    "Q": "zero_wf",
                },
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "cosine_weights": {
                "cosine": [(1.0, 80)],
                "sine": [(0.0, 80)],
            },
            "sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(1.0, 80)],
            },
            "minus_sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(-1.0, 80)],
            },
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 50e6,
                    "lo_frequency": 10e9,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
        },
    }


@pytest.fixture
def config2():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                    3: {"offset": 0.0},
                },
                "digital_outputs": {},
                "analog_inputs": {},
            }
        },
        "elements": {
            "qubit": {
                "mixInputs": {
                    "I": ("con1", 1),
                    "Q": ("con1", 2),
                    "lo_frequency": 10e9,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 50e6,
                "operations": {
                    "cw": "const_pulse",
                },
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
            "const_pulse": {
                "operation": "control",
                "length": 1e3,
                "waveforms": {
                    "I": "const_wf",
                    "Q": "zero_wf",
                },
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "cosine_weights": {
                "cosine": [(1.0, 80)],
                "sine": [(0.0, 80)],
            },
            "sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(1.0, 80)],
            },
            "minus_sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(-1.0, 80)],
            },
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 50e6,
                    "lo_frequency": 10e9,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
        },
    }


def test_multi_user_timeout(config1, config2):
    # Open QMM
    qmm = QuantumMachinesManager()
    qmm.close_all_quantum_machines()
    # A dummy QUA program
    with program() as prog_1:
        pause()
        play("readout", "resonator")
    with program() as prog_2:
        play("cw", "qubit")
    # Try to open two qms successively
    try:
        qm = qmm.open_qm(config1)
        qm.execute(prog_1)
        with qm_session(qmm, config2, timeout=3) as qm:
            job: QmJob = qm.execute(prog_2)
        raise Exception("Didn't reach timeout!")
    except Exception as e:
        if e.__class__.__name__ == "TimeoutError":
            pass
        else:
            raise Exception from e


def test_multi_user_wait(config1, config2):
    # Open QMM
    qmm = QuantumMachinesManager()
    qmm.close_all_quantum_machines()
    # A dummy QUA program
    with program() as prog_1:
        n = declare(int)
        with for_(n, 0, n < 200_000, n + 1):
            # Waits 2s
            wait(10_000, "resonator")
        play("readout", "resonator")
    with program() as prog_2:
        play("cw", "qubit")
    # Try to open two qms successively
    try:
        qm = qmm.open_qm(config1)
        qm.execute(prog_1)
        with qm_session(qmm, config2, timeout=10) as qm:
            job: QmJob = qm.execute(prog_2)
        return True
    except Exception as e:
        raise Exception from e


def test_multi_user_no_open_qm(config1, config2):
    # Open QMM
    qmm = QuantumMachinesManager()
    qmm.close_all_quantum_machines()
    # A dummy QUA program
    with program() as prog_2:
        play("cw", "qubit")
    # Try to open two qms successively
    try:
        with qm_session(qmm, config2, timeout=10) as qm:
            job: QmJob = qm.execute(prog_2)
        return True
    except Exception as e:
        raise Exception from e
