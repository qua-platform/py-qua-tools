import warnings
from contextlib import contextmanager

import pytest

from qm.api.models.capabilities import ServerCapabilities
from qm.api.models.info import QuaMachineInfo, ImplementationInfo
from qm.containers.capabilities_container import create_capabilities_container


@contextmanager
def ignore_deprecation_warnings():
    warnings.simplefilter("ignore")
    yield
    warnings.simplefilter("default")


@pytest.fixture(autouse=True)
def capability_container():
    container = create_capabilities_container(
        QuaMachineInfo([], ImplementationInfo("", "", ""))
    )
    container.capabilities.override(
        ServerCapabilities(
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        )
    )
    return container
