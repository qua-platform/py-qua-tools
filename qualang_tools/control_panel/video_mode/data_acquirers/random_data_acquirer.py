from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
from qualang_tools.control_panel.video_mode.data_acquirers.base_data_aqcuirer import BaseDataAcquirer
from dash import html
from qualang_tools.control_panel.video_mode.dash_tools import create_input_field
import numpy as np
from time import sleep


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

    def acquire_data(self):
        """Acquire random data.

        This method acquires random data from the simulated device.
        """
        sleep(self.acquire_time)
        results = np.random.rand(self.x_axis.points, self.y_axis.points)
        return results

    def get_dash_components(self):
        dash_components = super().get_dash_components()
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

    def update_parameter(self, parameters):
        results = super().update_parameter(parameters)

        params = parameters[self.component_id]
        if self.acquire_time != params["acquire-time"]:
            results["parameters_modified"] = True
            self.acquire_time = params["acquire-time"]

        return results
