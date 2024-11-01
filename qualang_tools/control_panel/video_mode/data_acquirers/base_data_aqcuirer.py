from abc import ABC, abstractmethod
from typing import List
import xarray as xr
import logging
import numpy as np
from dash import html
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
import dash_bootstrap_components as dbc
from qualang_tools.control_panel.video_mode.dash_tools import create_axis_layout


__all__ = ["BaseDataAcquirer"]


class BaseDataAcquirer(ABC):
    """Base class for data acquirers.

    This class defines the interface for data acquirers, which are responsible for acquiring data from a device.
    Subclasses must implement the `acquire_data` method to provide the actual data acquisition logic.

    Args:
        x_axis: The x-axis of the data acquirer.
        y_axis: The y-axis of the data acquirer.
        num_averages: The number of averages to take as a rolling average.
    """

    def __init__(
        self,
        *,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages=1,
        component_id: str = "data-acquirer",
        **kwargs,
    ):
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.num_averages = num_averages
        self.component_id = component_id
        self.data_history = []
        logging.debug("Initializing DataGenerator")

        self.num_acquisitions = 0

        self.data_array = xr.DataArray(
            np.zeros((self.x_axis.points, self.y_axis.points)),
            coords=[
                (self.x_axis.name, self.x_axis.sweep_values_with_offset),
                (self.y_axis.name, self.y_axis.sweep_values_with_offset),
            ],
            attrs={"units": "V", "long_name": "Signal"},
        )
        for axis in [self.x_axis, self.y_axis]:
            attrs = {"label": axis.label or axis.name}
            if axis.units is not None:
                attrs["units"] = axis.units
            self.data_array.coords[axis.name].attrs.update(attrs)
        logging.debug("DataGenerator initialized with initial data")

    @abstractmethod
    def acquire_data(self) -> np.ndarray:
        """Acquire data from the device.

        This method must be implemented by subclasses to provide the actual data acquisition logic.
        """
        pass

    def update_data(self):
        """Update the data array with the new data.

        This method acquires new data from the device and updates the data array.
        It also performs a rolling average of the data to reduce noise.
        """
        new_data = self.acquire_data()
        self.num_acquisitions += 1

        if new_data.shape != self.data_array.values.shape:
            self.data_history.clear()

        self.data_history.append(new_data)

        if len(self.data_history) > self.num_averages:
            self.data_history.pop(0)

        averaged_data = np.mean(self.data_history, axis=0)

        self.data_array = xr.DataArray(
            averaged_data,
            coords=[
                (self.x_axis.name, self.x_axis.sweep_values_with_offset),
                (self.y_axis.name, self.y_axis.sweep_values_with_offset),
            ],
            attrs=self.data_array.attrs,  # Preserve original attributes like units
        )
        for axis in [self.x_axis, self.y_axis]:
            attrs = {"label": axis.label or axis.name}
            if axis.units is not None:
                attrs["units"] = axis.units
            self.data_array.coords[axis.name].attrs.update(attrs)

        mean_abs_data = np.mean(np.abs(averaged_data))
        logging.debug(f"Data acquired with shape: {self.data_array.shape}, mean(abs(data)) = {mean_abs_data}")
        return self.data_array

    @abstractmethod
    def get_dash_components(self):
        """Return the x and y axis components in a single row."""
        return [
            html.Div(
                [
                    dbc.Row(
                        [
                            create_axis_layout(
                                axis="x",
                                component_id=self.component_id,
                                span=self.x_axis.span,
                                points=self.x_axis.points,
                                min_span=0.01,
                                max_span=None,
                                units=self.x_axis.units,
                            ),
                            create_axis_layout(
                                axis="y",
                                component_id=self.component_id,
                                span=self.y_axis.span,
                                points=self.y_axis.points,
                                min_span=0.01,
                                max_span=None,
                                units=self.y_axis.units,
                            ),
                        ],
                        className="g-0",
                    ),  # g-0 removes gutters between columns
                ]
            )
        ]

    def get_all_dash_components(self):
        """Return all Dash components, including axis components."""
        return self.get_dash_components()

    def update_parameter(self, parameters):
        """Update the data acquirer's attributes based on the input values."""
        params = parameters[self.component_id]
        params_modified = False
        if self.x_axis.span != params["x-span"]:
            self.x_axis.span = params["x-span"]
            params_modified = True
        if self.x_axis.points != params["x-points"]:
            self.x_axis.points = params["x-points"]
            params_modified = True
        if self.y_axis.span != params["y-span"]:
            self.y_axis.span = params["y-span"]
            params_modified = True
        if self.y_axis.points != params["y-points"]:
            self.y_axis.points = params["y-points"]
            params_modified = True

        return {"parameters_modified": params_modified}

    def get_component_ids(self) -> List[str]:
        """Return a list of component IDs for this data acquirer."""
        return [self.component_id]
