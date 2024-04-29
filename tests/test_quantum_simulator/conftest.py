import pytest

from qualang_tools.simulator.quantum.architectures import TransmonSettings
from qualang_tools.units import unit
from quantum_environment.transmon_backend import TransmonBackend


@pytest.fixture
def transmon_settings() -> TransmonSettings:
    return TransmonSettings(
        **{
            "resonant_frequency": 4860000000.0,
            "anharmonicity": -320000000.0,
            "rabi_frequency": 1e7
        }
    )


@pytest.fixture
def transmon_backend(transmon_settings) -> TransmonBackend:
    return TransmonBackend(transmon_settings)


@pytest.fixture
def config():
    """
    Octave configuration working for QOP222 and qm-qua==1.1.5 and newer.
    """
    u = unit(coerce_to_integer=True)

    x90_amp = 0.1
    x90_len = 220

    qubit_LO = 3.5 * u.GHz
    qubit_IF = 50 * u.MHz

    resonator_LO = 5.5 * u.GHz
    resonator_IF = 60 * u.MHz

    readout_len = 5000
    readout_amp = 0.2

    time_of_flight = 24

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
                "intermediate_frequency": qubit_IF,
                "operations": {
                    "x90": "x90_pulse",
                },
            },
            "resonator": {
                "RF_inputs": {"port": ("octave1", 1)},
                "RF_outputs": {"port": ("octave1", 1)},
                "intermediate_frequency": resonator_IF,
                "operations": {
                    "readout": "readout_pulse",
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
        },
        "octaves": {
            "octave1": {
                "RF_outputs": {
                    1: {
                        "LO_frequency": resonator_LO,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                    2: {
                        "LO_frequency": qubit_LO,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                },
                "RF_inputs": {
                    1: {
                        "LO_frequency": resonator_LO,
                        "LO_source": "internal",
                    },
                },
                "connectivity": "con1",
            }
        },
        "pulses": {
            "x90_pulse": {
                "operation": "control",
                "length": x90_len,
                "waveforms": {
                    "I": "x90_I_wf",
                    "Q": "x90_Q_wf",
                },
            },
            "readout_pulse": {
                "operation": "measurement",
                "length": readout_len,
                "waveforms": {
                    "I": "readout_wf",
                    "Q": "zero_wf",
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
            "x90_I_wf": {"type": "constant", "sample": x90_amp},
            "x90_Q_wf": {"type": "constant", "sample": 0.},
            "readout_wf": {"type": "constant", "sample": readout_amp},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "cosine_weights": {
                "cosine": [(1.0, readout_len)],
                "sine": [(0.0, readout_len)],
            },
            "sine_weights": {
                "cosine": [(0.0, readout_len)],
                "sine": [(1.0, readout_len)],
            },
            "minus_sine_weights": {
                "cosine": [(0.0, readout_len)],
                "sine": [(-1.0, readout_len)],
            },
        },
    }
