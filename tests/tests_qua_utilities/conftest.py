import pytest
from typing import Generator, Optional

from qm_saas import QmSaas

from qm.quantum_machines_manager import QuantumMachinesManager
from qm import FullQuaConfig

HOST_IP = "localhost"
READOUT_LEN = 100
FEM_IDX = 6
ANALOG_OUTPUT_PORT = 8
ANALOG_INPUT_PORT = 1
config: FullQuaConfig = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1000",
            "fems": {
                FEM_IDX: {
                    "type": "MW",
                    "analog_outputs": {
                        ANALOG_OUTPUT_PORT: {"sampling_rate": 1e9, "band": 2, "upconverter_frequency": 5e9},
                    },
                    "analog_inputs": {
                        ANALOG_INPUT_PORT: {"sampling_rate": 1e9, "band": 2, "downconverter_frequency": 5e9},
                    },
                },
            },
        },
    },
    "elements": {
        "resonator": {
            "MWInput": {
                "port": ("con1", FEM_IDX, ANALOG_OUTPUT_PORT),
            },
            "intermediate_frequency": 200e6,
            "MWOutput": {
                "port": ("con1", FEM_IDX, ANALOG_INPUT_PORT),
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
    }
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
        "--cloudsim-host",
        action="store",
        default=None,
        help="Cloud simulator host"
    )
    parser.addoption(
        "--cloudsim-pwd",
        action="store",
        default=None,
        help="Cloud simulator password"
    )
    parser.addoption(
        "--cloudsim-email",
        action="store",
        default=None,
        help="Cloud simulator user email"
    )

@pytest.fixture(scope="session")
def qop_cloud_sim_version(request: pytest.FixtureRequest) -> Optional[str]:
    """Fixture that returns the version passed with --qop-version (string or None)."""
    return request.config.getoption("--qop-version")

@pytest.fixture(scope="session")
def cloud_sim_host(request: pytest.FixtureRequest) -> str:
    host = request.config.getoption("--cloudsim-host")
    if host is None:
        raise ValueError("--cloudsim-host is required. Pass it directly or via the CI_CLOUD_SIMULATOR_HOST secret.")
    return host

@pytest.fixture(scope="session")
def cloud_sim_pwd(request: pytest.FixtureRequest) -> str:
    pwd = request.config.getoption("--cloudsim-pwd")
    if pwd is None:
        raise ValueError("--cloudsim-pwd is required. Pass it directly or via the CI_CLOUD_SIMULATOR_PASSWORD secret.")
    return pwd

@pytest.fixture(scope="session")
def cloud_sim_email(request: pytest.FixtureRequest) -> str:
    email = request.config.getoption("--cloudsim-email")
    if email is None:
        raise ValueError("--cloudsim-email is required. Pass it directly or via the CI_CLOUD_SIMULATOR_USER_EMAIL secret.")
    return email

def get_local_qmm() -> QuantumMachinesManager:
    return QuantumMachinesManager(host=HOST_IP, port=9510)

@pytest.fixture(scope="session")
def qmm(
    qop_cloud_sim_version: str, cloud_sim_pwd: str, cloud_sim_email: str, cloud_sim_host: str
) -> Generator[QuantumMachinesManager, None, None]:
    if qop_cloud_sim_version != "local":
        client = QmSaas(email=cloud_sim_email, password=cloud_sim_pwd, host=cloud_sim_host)
        with client.simulator(qop_cloud_sim_version) as sim_instance:
            qmm = QuantumMachinesManager(
                host=sim_instance.host,
                port=sim_instance.port,
                connection_headers=sim_instance.default_connection_headers,
            )
            yield qmm
    else:
        yield get_local_qmm()
