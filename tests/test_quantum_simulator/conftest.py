import pytest

from qualang_tools.simulator.quantum.architectures import TransmonSettings
from qualang_tools.simulator.quantum.architectures.transmon import Transmon
from qualang_tools.simulator.quantum.architectures.transmon_pair import TransmonPair
from qualang_tools.simulator.quantum.architectures.transmon_pair_backend_from_qua import TransmonPairBackendFromQUA, \
    ConfigToTransmonPairBackendMap
from qualang_tools.simulator.quantum.architectures.from_qua_channels import TransmonPairBackendChannelReadout, \
    TransmonPairBackendChannelIQ, ChannelType
from qualang_tools.simulator.quantum.architectures.transmon_pair_settings import TransmonPairSettings
from qualang_tools.units import unit


@pytest.fixture
def transmon() -> Transmon:
    settings = TransmonSettings(
        resonant_frequency=4860000000.0,
        anharmonicity=-320000000.0,
        rabi_frequency=3e7
    )

    return Transmon(settings)


@pytest.fixture
def transmon_pair() -> TransmonPair:
    settings = TransmonPairSettings(
        TransmonSettings(
            resonant_frequency=4860000000.0,
            anharmonicity=-320000000.0,
            rabi_frequency=3e7
        ),
        TransmonSettings(
            resonant_frequency=4970000000.0,
            anharmonicity=-320000000.0,
            rabi_frequency=1.3e7
        ),
        coupling_strength=2000000.0
    )

    return TransmonPair(settings)


@pytest.fixture
def transmon_pair_qua_config(transmon_pair) -> dict:
    u = unit(coerce_to_integer=True)

    x90_amp = 0.2
    x90_len = 220

    qubit_1_IF = 50 * u.MHz
    qubit_1_LO = int(transmon_pair.transmon_1.resonant_frequency) - qubit_1_IF

    qubit_2_IF = 60 * u.MHz
    qubit_2_LO = int(transmon_pair.transmon_2.resonant_frequency) - qubit_2_IF

    resonator_1_LO = 5.5 * u.GHz
    resonator_1_IF = 60 * u.MHz

    resonator_2_LO = 5.5 * u.GHz
    resonator_2_IF = 60 * u.MHz

    readout_len = 5000
    readout_amp = 0.2

    time_of_flight = 24

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},  # I resonator 1
                    2: {"offset": 0.0},  # Q resonator 1
                    3: {"offset": 0.0},  # I resonator 2
                    4: {"offset": 0.0},  # Q resonator 2
                    5: {"offset": 0.0},  # I qubit 1
                    6: {"offset": 0.0},  # Q qubit 1
                    7: {"offset": 0.0},  # I qubit 2
                    8: {"offset": 0.0},  # Q qubit 2
                },
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            },
        },
        "elements": {
            "qubit_1": {
                "RF_inputs": {"port": ("octave1", 3)},
                "intermediate_frequency": qubit_1_IF,
                "operations": {
                    "x90": "x90_pulse",
                },
            },
            "qubit_1t2": {
                "RF_inputs": {"port": ("octave1", 3)},
                "intermediate_frequency": qubit_1_IF,
                "operations": {
                    "x90": "x90_pulse",
                },
            },
            "qubit_2": {
                "RF_inputs": {"port": ("octave1", 4)},
                "intermediate_frequency": qubit_2_IF,
                "operations": {
                    "x90": "x90_pulse",
                },
            },
            "resonator_1": {
                "RF_inputs": {"port": ("octave1", 1)},
                "RF_outputs": {"port": ("octave1", 1)},
                "intermediate_frequency": resonator_1_IF,
                "operations": {
                    "readout": "readout_pulse",
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
            "resonator_2": {
                "RF_inputs": {"port": ("octave1", 2)},
                "RF_outputs": {"port": ("octave1", 1)},
                "intermediate_frequency": resonator_2_IF,
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
                        "LO_frequency": resonator_1_LO,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                    2: {
                        "LO_frequency": resonator_2_LO,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                    3: {
                        "LO_frequency": qubit_1_LO,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                    4: {
                        "LO_frequency": qubit_2_LO,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                },
                "RF_inputs": {
                    1: {
                        "LO_frequency": resonator_1_LO,
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
    }


def _freq_from_qua_config(element: str, config: dict) -> int:
    element_config = config['elements'][element]
    IF = element_config['intermediate_frequency']
    channel_port = element_config['RF_inputs']['port']
    LO = config['octaves'][channel_port[0]]['RF_outputs'][channel_port[1]]['LO_frequency']

    return LO + IF


@pytest.fixture
def config_to_transmon_pair_backend_map(transmon_pair_qua_config, transmon_pair) -> ConfigToTransmonPairBackendMap:
    qubit_1_freq = _freq_from_qua_config("qubit_1", transmon_pair_qua_config)
    qubit_2_freq = _freq_from_qua_config("qubit_2", transmon_pair_qua_config)
    return {
        "qubit_1": TransmonPairBackendChannelIQ(
            qubit_index=0,
            carrier_frequency=qubit_1_freq,
            operator=transmon_pair.transmon_1_drive_operator(),
            type=ChannelType.DRIVE
        ),
        "qubit_1t2": TransmonPairBackendChannelIQ(
            qubit_index=0,
            carrier_frequency=qubit_2_freq,
            operator=transmon_pair.transmon_1_drive_operator(),
            type=ChannelType.CONTROL
        ),
        "qubit_2": TransmonPairBackendChannelIQ(
            qubit_index=1,
            carrier_frequency=qubit_2_freq,
            operator=transmon_pair.transmon_2_drive_operator(),
            type=ChannelType.DRIVE
        ),
        "resonator_1": TransmonPairBackendChannelReadout(0),
        "resonator_2": TransmonPairBackendChannelReadout(1),
    }


@pytest.fixture
def transmon_pair_backend(transmon_pair, config_to_transmon_pair_backend_map):
    return TransmonPairBackendFromQUA(transmon_pair, config_to_transmon_pair_backend_map)