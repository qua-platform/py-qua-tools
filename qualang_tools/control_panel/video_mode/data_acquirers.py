from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional, Sequence
import numpy as np
from qm import Program, QuantumMachine
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import *
import xarray as xr
import logging
from qualang_tools.loops import from_array


__all__ = ["BaseDataAcquirer", "RandomDataAcquirer", "OPXDataAcquirer"]

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
        pre_measurement_delay: float = 0,
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
        self.pre_measurement_delay = pre_measurement_delay
        logging.debug("Initializing DataGenerator")

        self.data_array = xr.DataArray(
            self.acquire_data(),
            coords=[("y", self.y_vals), ("x", self.x_vals)],
            attrs={"units": "V", "long_name": "Signal"},
        )
        self.data_array.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.data_array.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
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
        self.data_array = self.data_array.assign_coords(x=self.x_vals, y=self.y_vals)

        x_vals = self.x_vals
        y_vals = self.y_vals
        logging.debug(
            f"Updated voltage ranges: "
            f"x_vals=[{x_vals[0]}, {x_vals[1]}, ..., {x_vals[-1]}], "
            f"y_vals=[{y_vals[0]}, {y_vals[1]}, ..., {y_vals[-1]}]"
        )

    @property
    def total_measurement_time(self):
        return (self.integration_time + self.pre_measurement_delay) * self.x_points * self.y_points * 1000

    @abstractmethod
    def update_attrs(self, attrs):
        pass

    @abstractmethod
    def acquire_data(self) -> np.ndarray:
        pass

    def update_data(self):
        new_data = self.acquire_data()

        if new_data.shape != self.data_array.values.shape:
            self.data_history.clear()

        self.data_history.append(new_data)
        logging.debug(f"New data generated with shape: {new_data.shape}")

        if len(self.data_history) > self.num_averages:
            self.data_history.pop(0)

        averaged_data = np.mean(self.data_history, axis=0)

        self.data_array = xr.DataArray(
            averaged_data,
            coords=[("y", self.y_vals), ("x", self.x_vals)],
            attrs=self.data_array.attrs,  # Preserve original attributes like units
        )

        self.data_array.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.data_array.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
        logging.debug(f"Averaged data calculated with shape: {self.data_array.shape}")
        return self.data_array


class RandomDataAcquirer(BaseDataAcquirer):
    def update_attrs(self, attrs):
        for attr in attrs:
            if attr["attr"] in ["x_offset", "y_offset"]:
                attr["obj"].set(attr["new"])
        else:
            setattr(attr["obj"], attr["attr"], attr["new"])

    def acquire_data(self):
        return np.random.rand(len(self.y_vals), len(self.x_vals))


class OPXDataAcquirer(BaseDataAcquirer):
    def __init__(
        self,
        *,
        qm: QuantumMachine,
        qua_inner_loop_action: Callable,
        scan_function: Callable,
        num_averages=1,
        **kwargs,
    ):
        self.qm = qm
        self.scan_function = scan_function
        self.qua_inner_loop_action = qua_inner_loop_action
        self.program: Optional[Program] = None
        self.job: Optional[RunningQmJob] = None

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

    def update_attrs(self, attrs):
        if any(name in attrs for name in ["x_span", "y_span", "x_points", "y_points", "integration_time"]):
            self.generate_program()
            self.run_program()

    def acquire_data(self) -> np.ndarray:
        if self.program is None:
            self.program = self.generate_program()
            self.run_program()
        results = {key: self.job.result_handles.get(key).fetch_all() for key in ["I", "Q", "n", "idxs_x", "idxs_y"]}
        # TODO: Process results
        return results

    def generate_program(self) -> Program:
        x_vals = self.x_vals - self.x_offset_parameter.get()
        y_vals = self.y_vals - self.y_offset_parameter.get()

        assert self.integration_cycles >= 16

        with program() as prog:
            n = declare(int, 0)
            n_stream = declare_stream()
            idxs_streams = {"x": declare_stream(), "y": declare_stream()}
            voltages_streams = {"x": declare_stream(), "y": declare_stream()}
            IQ_streams = {"I": declare_stream(), "Q": declare_stream()}

            with infinite_loop_():
                assign(n, n + 1)
                self.scan_function(
                    x_vals=x_vals,
                    y_vals=y_vals,
                    qua_inner_loop_action=self.qua_inner_loop_action,
                    integration_time=self.integration_time,
                    pre_measurement_delay=self.pre_measurement_delay,
                    idxs_streams=idxs_streams,
                    voltages_streams=voltages_streams,
                    IQ_streams=IQ_streams,
                )

            with stream_processing():
                # TODO Or save_all?
                idxs_streams["x"].buffer(self.x_points * self.y_points).save("idxs_x")
                idxs_streams["y"].buffer(self.x_points * self.y_points).save("idxs_y")
                IQ_streams["I"].buffer(self.x_points * self.y_points).save("I")
                IQ_streams["Q"].buffer(self.x_points * self.y_points).save("Q")
                n_stream.save("n")

        return prog

    def run_program(self):
        if self.program is None:
            self.program = self.generate_program()

        self.job = self.qm.execute(self.program)

        # Wait until one buffer is filled{
        for key in ["I", "Q", "n", "idxs_x", "idxs_y"]:
            self.job.result_handles.get(key).wait_for_values(1)


class InnerLoopAction:
    def __init__(self):
        pass

    def __call__(self, idxs, voltages, integration_time, pre_measurement_delay):
        I = declare(fixed)
        Q = declare(fixed)

        set_dc_offset("elem_x", "single", voltages["x"])
        set_dc_offset("elem_y", "single", voltages["y"])
        align()
        wait(pre_measurement_delay)
        measure(
            "readout",
            "readout_element",
            None,
            demod.full("cos", I),
            demod.full("sin", Q),
            # duration=integration_time // 4,
        )

        return I, Q
