import warnings
from contextlib import contextmanager

from qm.api.models.capabilities import ServerCapabilities
from qm import QuantumMachinesManager

QuantumMachinesManager.set_capabilities_offline()
@contextmanager
def ignore_deprecation_warnings():
    warnings.simplefilter("ignore")
    yield
    warnings.simplefilter("default")
