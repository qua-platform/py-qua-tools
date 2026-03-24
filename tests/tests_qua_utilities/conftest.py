import pytest
from typing import Generator, Optional

from qm_saas import QmSaas

from qm.quantum_machines_manager import QuantumMachinesManager
from qm import FullQuaConfig

CLOUD_SIM_HOST = "qm-saas.quantum-machines.co"
HOST_IP = "localhost"
READOUT_LEN = 100
FEM_IDX = 6
config: FullQuaConfig = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1000",
            "fems": {
                1: {
                    "type": "LF",
                    "analog_outputs": {
                        1: {"offset": 0.0, "sampling_rate": 2e9},
                        2: {"offset": 0.0, "sampling_rate": 2e9},
                        3: {"offset": 0.0, "sampling_rate": 2e9},
                        4: {"offset": 0.0, "output_mode": "amplified", "upsampling_mode": "pulse"},
                        5: {"offset": 0.0, "sampling_rate": 2e9},
                        6: {"offset": 0.0},
                        7: {"offset": 0.0},
                        8: {"offset": 0.0},
                    },
                    "digital_outputs": {
                        1: {},
                        2: {},
                        3: {},
                    },
                    "analog_inputs": {
                        1: {"offset": +0.0},
                        2: {"offset": +0.0},
                    },
                },
                FEM_IDX: {
                    "type": "MW",
                    "analog_outputs": {
                        1: {"sampling_rate": 1e9, "band": 2, "upconverters": {1: {"frequency": 5e9}}},
                        2: {
                            "sampling_rate": 1e9,
                            "full_scale_power_dbm": 7,
                            "band": 1,
                            "upconverters": {2: {"frequency": 1e9}},
                        },
                        3: {
                            "sampling_rate": 1e9,
                            "full_scale_power_dbm": 1,
                            "band": 1,
                            "upconverters": {1: {"frequency": 2e9}, 2: {"frequency": 1e9}},
                        },
                        4: {"sampling_rate": 1e9, "band": 1, "upconverter_frequency": 1.234e9},
                        7: {"sampling_rate": 1e9, "band": 2, "upconverter_frequency": 5e9},
                        8: {"sampling_rate": 1e9, "band": 2, "upconverter_frequency": 5e9},
                    },
                    "digital_outputs": {
                        1: {"level": "LVTTL", "shareable": False, "inverted": False},
                        2: {},
                        3: {},
                    },
                    "analog_inputs": {
                        1: {"sampling_rate": 1e9, "band": 2, "downconverter_frequency": 5e9},
                        2: {"sampling_rate": 1e9, "band": 2, "downconverter_frequency": 5e9},
                    },
                },
            },
        },
    },
    "elements": {
        "q1": {
            "MWInput": {
                "port": ("con1", FEM_IDX, 3),
                "upconverter": 1,
            },
            "intermediate_frequency": 100e6,
            "operations": {"pi": "const_pulse"},
        },
        "q2": {
            "MWInput": {
                "port": ("con1", FEM_IDX, 3),
                "upconverter": 1,
            },
            "intermediate_frequency": 100e6,
            "operations": {"pi": "const_pulse"},
        },
        "q3": {
            "MWInput": {
                "port": ("con1", FEM_IDX, 3),
                "upconverter": 1,
            },
            "intermediate_frequency": 100e6,
            "operations": {"pi": "const_pulse"},
        },
        "resonator": {
            "MWInput": {
                "port": ("con1", FEM_IDX, 8),
            },
            "intermediate_frequency": 200e6,
            "MWOutput": {
                "port": ("con1", FEM_IDX, 1),
            },
            "time_of_flight": 484,
            "smearing": 0,
            "operations": {"readout": "readout_pulse"},
        },
    },
    "pulses": {
        "readout_pulse": {
            "operation": "measurement",
            "length": READOUT_LEN,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {"cos": "cos", "sin": "sin"},
            "digital_marker": "ON",
        },
        "const_pulse": {
            "operation": "control",
            "length": READOUT_LEN,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": 0.5},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "integration_weights": {
        "cos": {
            "cosine": [(1.0, READOUT_LEN)],
            "sine": [(0.0, READOUT_LEN)],
        },
        "sin": {
            "cosine": [(0.0, READOUT_LEN)],
            "sine": [(1.0, READOUT_LEN)],
        },
    },
    "mixers": {
        "octave_oct1_1": [
            {
                "intermediate_frequency": 50e6,
                "lo_frequency": 1e9,
                "correction": (1, 0, 0, 1),
            },
        ],
    },
}

def pytest_addoption(parser):
    """Add custom command-line options"""
    parser.addoption(
        "--qop-version",
        action="store",
        default="v3_6_0",
        help="Cloud simulator QOP version to use for the tests - e.g., v3_5_0, v3_6_0, default: local for local simulator"
    )
    parser.addoption(
        "--cloudsim-pwd",
        action="store",
        default="jG4yUA9YTqcYHBVsVenf",
        help="Cloud simulator password"
    )
    parser.addoption(
        "--cloudsim-email",
        action="store",
        default="qm_devops@quantum-machines.co",
        help="Cloud simulator user email"
    )

@pytest.fixture(scope="session")
def qop_cloud_sim_version(request: pytest.FixtureRequest) -> Optional[str]:
    """Fixture that returns the version passed with --qop-version (string or None)."""
    return request.config.getoption("--qop-version")

@pytest.fixture(scope="session")
def cloud_sim_pwd(request: pytest.FixtureRequest) -> Optional[str] :
    """Fixture that returns the version passed with --qop-version (string or None)."""
    return request.config.getoption("--cloudsim-pwd")

@pytest.fixture(scope="session")
def cloud_sim_email(request: pytest.FixtureRequest) -> Optional[str] :
    """Fixture that returns the version passed with --qop-version (string or None)."""
    return request.config.getoption("--cloudsim-email")

def get_local_qmm() -> QuantumMachinesManager:
    return QuantumMachinesManager(host=HOST_IP, port=9510)

@pytest.fixture(scope="session")
def qmm(
    qop_cloud_sim_version: str, cloud_sim_pwd: str, cloud_sim_email: str
) -> Generator[QuantumMachinesManager, None, None]:
    if qop_cloud_sim_version != "local":
        client = QmSaas(email=cloud_sim_email, password=cloud_sim_pwd, host=CLOUD_SIM_HOST)
        with client.simulator(qop_cloud_sim_version) as sim_instance:
            qmm = QuantumMachinesManager(
                host=sim_instance.host,
                port=sim_instance.port,
                connection_headers=sim_instance.default_connection_headers,
            )
            yield qmm
    else:
        yield get_local_qmm()
