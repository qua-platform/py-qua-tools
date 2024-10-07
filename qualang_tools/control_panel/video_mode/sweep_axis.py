from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

from qualang_tools.control_panel.video_mode.voltage_parameters import VoltageParameter


__all__ = ["SweepAxis"]


@dataclass
class SweepAxis:
    name: str
    span: float
    points: int
    label: Optional[str] = None
    offset_parameter: Optional[VoltageParameter] = None
    attenuation: float = 0

    @property
    def sweep_values(self):
        return np.linspace(-self.span / 2, self.span / 2, self.points)

    @property
    def sweep_values_unattenuated(self):
        return self.sweep_values * 10 ** (self.attenuation / 20)

    @property
    def sweep_values_with_offset(self):
        if self.offset_parameter is None:
            return self.sweep_values_unattenuated
        return self.sweep_values_unattenuated + self.offset_parameter.get_latest()

    @property
    def amplitude_scale(self):
        return 10 ** (-self.attenuation / 20)
