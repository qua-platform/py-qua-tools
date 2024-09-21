from abc import ABC, abstractmethod
import numpy as np
from qm.qua import *
import xarray as xr
import logging


__all__ = ["BaseDataAcquirer", "RandomDataAcquirer"]

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class BaseDataAcquirer(ABC):
    def __init__(
        self,
        *,
        x_offset_parameter,
        y_offset_parameter,
        x_span,
        y_span,
        x_points=101,
        y_points=101,
        num_averages=1,
        integration_time: float = 10e-6,
        **kwargs,
    ):
        assert not kwargs

        self.x_offset_parameter = x_offset_parameter
        self.y_offset_parameter = y_offset_parameter
        self.x_span = x_span
        self.y_span = y_span
        self.num_averages = num_averages
        self.integration_time = integration_time
        self.x_points = x_points
        self.y_points = y_points
        self.data_history = []

        logging.debug("Initializing DataGenerator")

        self.xarr = xr.DataArray(
            self.acquire_data(),
            coords=[("y", self.y_vals), ("x", self.x_vals)],
            attrs={"units": "V", "long_name": "Signal"},
        )
        self.xarr.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.xarr.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
        logging.debug("DataGenerator initialized with initial data")

    @property
    def x_vals(self):
        x_offset = self.x_offset_parameter.latest_value
        x_min = x_offset - self.x_span / 2
        x_max = x_offset + self.x_span / 2
        return np.linspace(x_min, x_max, self.x_points)

    @property
    def y_vals(self):
        y_offset = self.y_offset_parameter.latest_value
        y_min = y_offset - self.y_span / 2
        y_max = y_offset + self.y_span / 2
        return np.linspace(y_min, y_max, self.y_points)

    @property
    def integration_cycles(self):
        integration_cycles = int(self.integration_time * 1e9)
        integration_cycles -= integration_cycles % 4
        return integration_cycles

    def update_voltage_ranges(self):
        self.xarr = self.xarr.assign_coords(x=self.x_vals, y=self.y_vals)

        x_vals = self.x_vals
        y_vals = self.y_vals
        logging.debug(
            f"Updated voltage ranges: "
            f"x_vals=[{x_vals[0]}, {x_vals[1]}, ..., {x_vals[-1]}], "
            f"y_vals=[{y_vals[0]}, {y_vals[1]}, ..., {y_vals[-1]}]"
        )

    @abstractmethod
    def acquire_data(self) -> np.ndarray:
        pass

    def update_data(self):
        new_data = self.acquire_data()

        if new_data.shape != self.xarr.values.shape:
            self.data_history.clear()

        self.data_history.append(new_data)
        logging.debug(f"New data generated with shape: {new_data.shape}")

        if len(self.data_history) > self.num_averages:
            self.data_history.pop(0)

        averaged_data = np.mean(self.data_history, axis=0)

        self.xarr = xr.DataArray(
            averaged_data,
            coords=[("y", self.y_vals), ("x", self.x_vals)],
            attrs=self.xarr.attrs,  # Preserve original attributes like units
        )

        self.xarr.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.xarr.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
        logging.debug(f"Averaged data calculated with shape: {self.xarr.shape}")
        return self.xarr


class RandomDataAcquirer(BaseDataAcquirer):
    def acquire_data(self):
        return np.random.rand(len(self.y_vals), len(self.x_vals))


class OPXDataAcquirer(BaseDataAcquirer):
    def __init__(
        self,
        *,
        x_element,
        y_element,
        x_offset_parameter,
        y_offset_parameter,
        x_span,
        y_span,
        num_averages=1,
        x_points=101,
        y_points=101,
        **kwargs,
    ):
        self.x_element = x_element
        self.y_element = y_element

        super().__init__(
            x_offset_parameter=x_offset_parameter,
            y_offset_parameter=y_offset_parameter,
            x_span=x_span,
            y_span=y_span,
            num_averages=num_averages,
            x_points=x_points,
            y_points=y_points,
            **kwargs,
        )

    def generate_program(self):
        from qualang_tools.loops import from_array

        x_vals = self.x_vals - self.x_offset_parameter.get()
        y_vals = self.y_vals - self.y_offset_parameter.get()

        assert self.integration_cycles >= 16

        with program() as prog:
            x_val = declare(fixed)
            y_val = declare(fixed)
            output_stream = declare_stream()

            with infinite_loop_():
                with for_(*from_array(x_val, x_vals)):
                    set_dc_offset(self.x_element, "single", x_val)

                    with for_(*from_array(y_val, y_vals)):
                        set_dc_offset(self.y_element, "single", y_val)
                        wait(self.integration_cycles)
                        align()

                        measured_val = self.measure()
                        save(measured_val, output_stream)
                        align()

            with stream_processing():
                # TODO Or save_all?
                output_stream.buffer(self.x_points, self.y_points).save("output_data")

        return prog

    def measure(self):
        measured_val = declare(fixed)

        measure(
            "readout",
            self.readout_element,
        )

        return measured_val
