import os
from pathlib import Path

import numpy as np
import pytest

from qualang_tools.octave_tools import get_calibration_parameters_from_db

@pytest.fixture
def config():
    return {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0},  # I resonator
                2: {"offset": 0.0},  # Q resonator
                3: {"offset": 0.0},  # I qubit
                4: {"offset": 0.0},  # Q qubit
            },
            "digital_outputs": {},
            "analog_inputs": {
                1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
            },
        },
    },
    "elements": {
        "qubit": {
            "RF_inputs": {"port": ("octave1", 2)},
            "intermediate_frequency": 50e6,
            "operations": {
                "cw": "const_pulse",
            },
        },
        "resonator": {
            "RF_inputs": {"port": ("octave1", 1)},
            "RF_outputs": {"port": ("octave1", 1)},
            "intermediate_frequency": -60e6,
            "operations": {
                "cw": "const_pulse",
            },
            "time_of_flight": 24,
            "smearing": 0,
        },
    },
    "octaves": {
        "octave1": {
            "RF_outputs": {
                1: {
                    "LO_frequency": 6e9,
                    "LO_source": "internal",
                    "output_mode": "always_on",
                    "gain": 0,
                },
                2: {
                    "LO_frequency": 5e9,
                    "LO_source": "internal",
                    "output_mode": "always_on",
                    "gain": 0,
                },
            },
            "RF_inputs": {
                1: {
                    "LO_frequency": 6e9,
                    "LO_source": "internal",
                },
            },
            "connectivity": "con1",
        }
    },
    "pulses": {
        "const_pulse": {
            "operation": "control",
            "length": 100,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": 0.125},
    },
}


def convert_to_correction(gain: float, phase: float):
    s = phase
    c = np.polyval([-3.125, 1.5, 1], s**2)
    g_plus = np.polyval([0.5, 1, 1], gain)
    g_minus = np.polyval([0.5, -1, 1], gain)

    c00 = g_plus * c
    c01 = g_plus * s
    c10 = g_minus * s
    c11 = g_minus * c

    return c00, c01, c10, c11

def abs_path_to(rel_path: str) -> str:
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    return os.path.join(source_dir, rel_path)

# res: 6e9, -60e6, gain=0 and 10
# qubit: 5e9, 50e6, gain=0 and -10
def test_validity_correction_parameters(config):
    param_qubit = get_calibration_parameters_from_db(abs_path_to(""), config, "qubit", 5e9, 50e6, 0)
    param_res = get_calibration_parameters_from_db(abs_path_to(""), config, "resonator", 6e9, -60e6, 0)
    assert param_qubit["correction_matrix"] == convert_to_correction(0.002667968769702953, 0.1732576938647769)
    assert param_res["correction_matrix"] == convert_to_correction(-0.001663141321574909, -0.02624172671912417)
    param_qubit = get_calibration_parameters_from_db(abs_path_to(""), config, "qubit", 5e9, 50e6, -10)
    param_res = get_calibration_parameters_from_db(abs_path_to(""), config, "resonator", 6e9, -60e6, 10)
    assert param_qubit["correction_matrix"] == convert_to_correction(0.000670812605205233, 0.16976806502793335)
    assert param_res["correction_matrix"] == convert_to_correction(-0.00357108327961989, -0.0270416534916431)

def test_verbose(config):
    param_qubit = get_calibration_parameters_from_db(abs_path_to(""), config, "qubit", 5e9, 50e6, 1, verbose_level=0)
    assert param_qubit["correction_matrix"] == ()
    param_qubit = get_calibration_parameters_from_db(abs_path_to(""), config, "qubit", 5e9, 50e6, 1, verbose_level=1)
    assert param_qubit["correction_matrix"] == ()
    with pytest.raises(Warning):
        get_calibration_parameters_from_db(abs_path_to(""), config, "qubit", 5e9, 50e6, 1, verbose_level=2)


