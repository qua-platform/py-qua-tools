import pytest
from typing import Generator, Optional

from qm_saas import QmSaas

from qm.quantum_machines_manager import QuantumMachinesManager
from qm import FullQuaConfig

from qualang_tools.results.qua_iterables_processing.qua_iterable_postprocess import qua_iterables_supported

# fetch_xarray_data and its tests rely on qm-qua APIs added in MIN_QM_QUA_VERSION.
# On older qm-qua these modules cannot even be imported, so skip collecting them.
collect_ignore = []
if not qua_iterables_supported():
    collect_ignore += [
        "test_fetch_xarray_basic.py",
        "test_fetch_xarray_averaging.py",
        "test_fetch_xarray_edge_cases.py",
        "test_fetch_xarray_zip.py",
    ]

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
        default="latest",
        help="Cloud simulator QOP version to use for the tests - e.g., v3_5_0, v3_6_0, latest, default: local for local simulator"
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
def cloud_sim_host(request: pytest.FixtureRequest) -> Optional[str]:
    return request.config.getoption("--cloudsim-host")

@pytest.fixture(scope="session")
def cloud_sim_pwd(request: pytest.FixtureRequest) -> Optional[str]:
    return request.config.getoption("--cloudsim-pwd")

@pytest.fixture(scope="session")
def cloud_sim_email(request: pytest.FixtureRequest) -> Optional[str]:
    return request.config.getoption("--cloudsim-email")

def get_local_qmm() -> QuantumMachinesManager:
    return QuantumMachinesManager(host=HOST_IP, port=9510)

@pytest.fixture(scope="session")
def qmm(
    qop_cloud_sim_version: str, cloud_sim_pwd: Optional[str], cloud_sim_email: Optional[str], cloud_sim_host: Optional[str]
) -> Generator[Optional[QuantumMachinesManager], None, None]:
    if qop_cloud_sim_version != "local":
        if not all([cloud_sim_host, cloud_sim_pwd, cloud_sim_email]):
            yield None
            return
        client = QmSaas(email=cloud_sim_email, password=cloud_sim_pwd, host=cloud_sim_host)
        version = None if qop_cloud_sim_version == "latest" else qop_cloud_sim_version
        with client.simulator(version) as sim_instance:
            qmm = QuantumMachinesManager(
                host=sim_instance.host,
                port=sim_instance.port,
                connection_headers=sim_instance.default_connection_headers,
            )
            yield qmm
    else:
        yield get_local_qmm()
