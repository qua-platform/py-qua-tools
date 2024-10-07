from dataclasses import dataclass
from typing import Optional

import numpy as np

from qualang_tools.control_panel.video_mode.voltage_parameters import VoltageParameter


__all__ = ["SweepAxis"]


@dataclass
class SweepAxis:
    """Class representing a sweep axis.

    Attributes:
        name: Name of the axis.
        span: Span of the axis.
        points: Number of points in the sweep.
        label: Label of the axis.
        units: Units of the axis.
        offset_parameter: Offset parameter of the axis.
        attenuation: Attenuation of the axis (0 by default)
    """

    name: str
    span: float
    points: int
    label: Optional[str] = None
    units: Optional[str] = None
    offset_parameter: Optional[VoltageParameter] = None
    attenuation: float = 0

    @property
    def sweep_values(self):
        """Returns axis sweep values using span and points."""
        return np.linspace(-self.span / 2, self.span / 2, self.points)

    @property
    def sweep_values_unattenuated(self):
        """Returns axis sweep values without attenuation."""
        return self.sweep_values * 10 ** (self.attenuation / 20)

    @property
    def sweep_values_with_offset(self):
        """Returns axis sweep values with offset."""
        if self.offset_parameter is None:
            return self.sweep_values_unattenuated
        return self.sweep_values_unattenuated + self.offset_parameter.get_latest()

    @property
    def scale(self):
        """Returns axis scale factor, calculated from attenuation."""
        return 10 ** (-self.attenuation / 20)
