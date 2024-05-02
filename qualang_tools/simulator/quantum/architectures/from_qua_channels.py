import numpy as np

from dataclasses import dataclass
from enum import Enum

from qiskit import pulse


@dataclass
class BackendChannel:
    qubit_index: int


class ChannelType(Enum):
    DRIVE = 'd'
    CONTROL = 'u'
    READOUT = 'r'


@dataclass
class TransmonPairBackendChannel(BackendChannel):
    qubit_index: int

    def __post_init__(self):
        self._channel_index = None
        if self.qubit_index not in [0, 1]:
            raise ValueError(f"Qubit index must be 0 or 1, got {self.qubit_index}")

    def assign_channel_index(self, index: int):
        self._channel_index = index

    def get_channel_index(self):
        if self._channel_index is None:
            raise ValueError("Drive channel not yet assigned.")
        return self._channel_index


@dataclass
class TransmonPairBackendChannelReadout(TransmonPairBackendChannel):
    pass


@dataclass
class TransmonPairBackendChannelIQ(TransmonPairBackendChannel):
    carrier_frequency: float
    operator: np.ndarray
    type: ChannelType

    def get_qiskit_pulse_channel(self):
        if self.type == ChannelType.DRIVE:
            return pulse.DriveChannel(self.get_channel_index())
        elif self.type == ChannelType.CONTROL:
            return pulse.ControlChannel(self.get_channel_index())
        elif self.type == ChannelType.READOUT:
            return pulse.AcquireChannel(self.get_channel_index())
        else:
            raise NotImplementedError(f"Unrecognized channel type {self.type}")
