from typing import Literal

import numpy as np

from dataclasses import dataclass
from enum import Enum

from qiskit import pulse


class ChannelType(Enum):
    DRIVE = 'd'
    CONTROL = 'u'
    READOUT = 'r'


@dataclass
class BackendChannel:
    qubit_index: int
    type: ChannelType


@dataclass
class TransmonPairBackendChannel(BackendChannel):
    def __post_init__(self):
        self._channel_index = None
        if self.qubit_index not in [0, 1]:
            raise ValueError(f"Qubit index must be 0 or 1, got {self.qubit_index}")


@dataclass
class TransmonPairBackendChannelSingle(TransmonPairBackendChannel):
    def assign_channel_index(self, index: int):
        self._channel_index = index

    def get_channel_index(self):
        if self._channel_index is None:
            raise ValueError("Drive channel not yet assigned.")
        return self._channel_index

    def get_qiskit_pulse_channel(self):
        if self.type == ChannelType.DRIVE:
            return pulse.DriveChannel(self.get_channel_index())
        elif self.type == ChannelType.CONTROL:
            return pulse.ControlChannel(self.get_channel_index())
        elif self.type == ChannelType.READOUT:
            return pulse.AcquireChannel(self.get_channel_index())
        else:
            raise NotImplementedError(f"Unrecognized channel type {self.type}")


@dataclass
class TransmonPairBackendChannelReadout(TransmonPairBackendChannelSingle):
    type: ChannelType = ChannelType.READOUT


@dataclass
class TransmonPairBackendChannelIQ(TransmonPairBackendChannel):
    carrier_frequency: float
    operator_i: np.ndarray
    operator_q: np.ndarray

    def assign_channel_index(self, index: int, quadrature: Literal['I', 'Q']):
        quadrature = quadrature.lower()
        if quadrature not in ['i', 'q']:
            raise ValueError(f"Expected quadrature to be 'I' or 'Q', got {quadrature}")
        if quadrature == 'i':
            self._i_channel_index = index
        else:
            self._q_channel_index = index

    def get_i_channel_index(self):
        if self._i_channel_index is None:
            raise ValueError("Drive channel not yet assigned.")
        return self._i_channel_index

    def get_q_channel_index(self):
        if self._q_channel_index is None:
            raise ValueError("Drive channel not yet assigned.")
        return self._q_channel_index

    def get_qiskit_pulse_channel(self, quadrature: Literal['I', 'Q']):
        quadrature = quadrature.lower()
        if quadrature not in ['i', 'q']:
            raise ValueError(f"Expected quadrature to be 'I' or 'Q', got {quadrature}")

        if quadrature == 'i':
            def get_channel_index():
                return self.get_i_channel_index()
        else:
            def get_channel_index():
                return self.get_q_channel_index()

        if self.type == ChannelType.DRIVE:
            return pulse.DriveChannel(get_channel_index())
        elif self.type == ChannelType.CONTROL:
            return pulse.ControlChannel(get_channel_index())
        elif self.type == ChannelType.READOUT:
            return pulse.AcquireChannel(get_channel_index())
        else:
            raise NotImplementedError(f"Unrecognized channel type {self.type}")
