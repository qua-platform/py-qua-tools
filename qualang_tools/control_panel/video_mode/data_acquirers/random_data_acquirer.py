import numpy as np
from time import sleep
from typing import Any, Dict, List

from dash import html

from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
from qualang_tools.control_panel.video_mode.data_acquirers.base_data_aqcuirer import BaseDataAcquirer
from qualang_tools.control_panel.video_mode.dash_tools import create_input_field, ModifiedFlags


__all__ = ["RandomDataAcquirer"]


class RandomDataAcquirer(BaseDataAcquirer):
    """Data acquirer that acquires random data."""

    def __init__(
        self,
        *,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages: int = 1,
        acquire_time: float = 1,
        **kwargs,
    ):
        self.acquire_time = acquire_time
        super().__init__(x_axis=x_axis, y_axis=y_axis, num_averages=num_averages, **kwargs)

    def acquire_data(self) -> np.ndarray:
        """Acquire random data.

        This method acquires random data from the simulated device.
        """
        sleep(self.acquire_time)
        results = np.random.rand(self.y_axis.points, self.x_axis.points)
        return results

    def get_dash_components(self, include_subcomponents: bool = True) -> List[html.Div]:
        dash_components = super().get_dash_components(include_subcomponents=include_subcomponents)
        dash_components.extend(
            [
                html.Div(
                    create_input_field(
                        id={"type": self.component_id, "index": "acquire-time"},
                        label="Acquire time",
                        value=self.acquire_time,
                        min=0.1,
                        max=10,
                        step=0.1,
                        units="s",
                    )
                )
            ]
        )
        return dash_components

    def update_parameters(self, parameters: Dict[str, Dict[str, Any]]) -> ModifiedFlags:
        flags = super().update_parameters(parameters)

        params = parameters[self.component_id]
        if self.acquire_time != params["acquire-time"]:
            self.acquire_time = params["acquire-time"]
            flags |= ModifiedFlags.PARAMETERS_MODIFIED

        return flags
