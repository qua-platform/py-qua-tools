from .connectivity_transmon_interface import Connectivity as ConnectivitySuperconductingQubits
from .connectivity_nv_center_interface import Connectivity as ConnectivityNVCenters
from typing import Union

AnyConnectivity = Union[ConnectivitySuperconductingQubits, ConnectivityNVCenters]
__all__ = ["AnyConnectivity", "ConnectivitySuperconductingQubits", "ConnectivityNVCenters"]
