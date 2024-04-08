# Tests for the video mode functionality
import pytest
from qm.qua import *
from qm import QuantumMachinesManager, QuantumMachine
import numpy as np
from qualang_tools.video_mode import ParameterTable


def gauss(amplitude, mu, sigma, length):
    t = np.linspace(-length / 2, length / 2, length)
    gauss_wave = amplitude * np.exp(-((t - mu) ** 2) / (2 * sigma**2))
    return [float(x) for x in gauss_wave]


@pytest.fixture
def config():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]

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


@pytest.fixture
def param_dict():
    return {
        "amp": (0.1, fixed),
        "gauss_amp": 0.2,  # qua_type will be inferred
        "amp_array": (np.arange(0.1, 0.3, 0.1), "fixed"),
        "gauss_amp_array": [0.2, 0.3, 0.4],  # qua_type will be inferred
        "bool_param": (True, "bool"),
        "bool_param_array": [True, False],  # qua_type will be inferred
        "int_param": 1,  # qua_type will be inferred
        "int_param_array": ([1, 2, 3], "int"),
    }


def test_is_parameter_table_valid(param_dict):
    param_table = ParameterTable(param_dict)
    for i, (param_name, param) in enumerate(param_table.table.items()):
        assert param.index == i
        if isinstance(param_dict[param_name], tuple):
            if isinstance(param_dict[param_name][1], str):
                assert param.type is eval(param_dict[param_name][1])
            else:
                assert param.type is param_dict[param_name][1]
        else:
            assert param.type is type(param.value) if isinstance(param.value, (bool, int)) else fixed
        if isinstance(param.value, List):
            assert param.length == len(param.value)

        with pytest.raises(ValueError):
            var = param_table[param_name]
