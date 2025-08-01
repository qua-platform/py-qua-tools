import warnings
from contextlib import contextmanager

import pytest

from qm.api.models.capabilities import QopCaps, ServerCapabilities
from qm.api.models.info import QuaMachineInfo, ImplementationInfo
from qm.containers.capabilities_container import create_capabilities_container
from qm import QuantumMachinesManager

QuantumMachinesManager.set_capabilities_offline()
@contextmanager
def ignore_deprecation_warnings():
    warnings.simplefilter("ignore")
    yield
    warnings.simplefilter("default")


@pytest.fixture(autouse=True)
def capability_container():
    capabilities = QopCaps.get_all()
    capabilities_qop_names = [cap.qop_name for cap in capabilities]
    return create_capabilities_container(QuaMachineInfo(capabilities_qop_names, ImplementationInfo("", "", "")))
