from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import numpy as np
from qm import Program, QuantumMachine
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import *
import xarray as xr
import logging
from time import sleep, perf_counter


__all__ = ["BaseDataAcquirer", "RandomDataAcquirer", "OPXDataAcquirer"]


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

        self.num_acquisitions = 0

        self.data_array = xr.DataArray(
            np.zeros((self.y_points, self.x_points)),
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
        return (self.integration_time + self.pre_measurement_delay) * self.x_points * self.y_points

    @abstractmethod
    def update_attrs(self, attrs):
        pass

    @abstractmethod
    def acquire_data(self) -> np.ndarray:
        pass

    def update_data(self):
        new_data = self.acquire_data()
        self.num_acquisitions += 1

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
        sleep(1)
        results = np.random.rand(len(self.y_vals), len(self.x_vals))

        return results


class OPXDataAcquirer(BaseDataAcquirer):
    stream_vars = ["I", "Q", "n", "idxs_x", "idxs_y", "x_vals", "y_vals"]

    def __init__(
        self,
        *,
        qm: QuantumMachine,
        qua_inner_loop_action: Callable,
        scan_function: Callable,
        x_offset_parameter,
        y_offset_parameter,
        x_span,
        y_span,
        x_points=101,
        y_points=101,
        num_averages=1,
        integration_time: float = 10e-6,
        pre_measurement_delay: float = 0,
        measure_var: str = "I",
        **kwargs,
    ):
        self.qm = qm
        self.scan_function = scan_function
        self.qua_inner_loop_action = qua_inner_loop_action
        self.program: Optional[Program] = None
        self.job: Optional[RunningQmJob] = None
        self.measure_var = measure_var
        self.results: Dict[str, Any] = {}

        super().__init__(
            x_offset_parameter=x_offset_parameter,
            y_offset_parameter=y_offset_parameter,
            x_span=x_span,
            y_span=y_span,
            num_averages=num_averages,
            x_points=x_points,
            y_points=y_points,
            integration_time=integration_time,
            pre_measurement_delay=pre_measurement_delay,
            **kwargs,
        )

    def update_attrs(self, attrs):
        if any(name in attrs for name in ["x_span", "y_span", "x_points", "y_points", "integration_time"]):
            self.generate_program()
            self.run_program()

    def generate_program(self) -> Program:
        x_vals = self.x_vals - self.x_offset_parameter.get()
        y_vals = self.y_vals - self.y_offset_parameter.get()

        assert self.integration_cycles >= 16

        self.qua_inner_loop_action.integration_time = self.integration_time
        self.qua_inner_loop_action.pre_measurement_delay = self.pre_measurement_delay

        with program() as prog:
            n = declare(int, 0)
            n_stream = declare_stream()
            idxs_streams = {"x": declare_stream(), "y": declare_stream()}
            voltages_streams = {"x": declare_stream(), "y": declare_stream()}
            IQ_streams = {"I": declare_stream(), "Q": declare_stream()}

            with infinite_loop_():
                save(n, n_stream)
                self.scan_function(
                    x_vals=x_vals,
                    y_vals=y_vals,
                    qua_inner_loop_action=self.qua_inner_loop_action,
                    idxs_streams=idxs_streams,
                    voltages_streams=voltages_streams,
                    IQ_streams=IQ_streams,
                )
                assign(n, n + 1)
                wait(5000000)

            with stream_processing():
                for var in self.stream_vars:
                    if var == "n":
                        n_stream.save("n")
                    elif var == "idxs_x":
                        idxs_streams["x"].buffer(self.x_points, self.y_points).save("idxs_x")
                    elif var == "idxs_y":
                        idxs_streams["y"].buffer(self.x_points, self.y_points).save("idxs_y")
                    elif var == "x_vals":
                        voltages_streams["x"].buffer(self.x_points, self.y_points).save("x_vals")
                    elif var == "y_vals":
                        voltages_streams["y"].buffer(self.x_points, self.y_points).save("y_vals")
                    elif var == "I":
                        IQ_streams["I"].buffer(self.x_points, self.y_points).save("I")
                    elif var == "Q":
                        IQ_streams["Q"].buffer(self.x_points, self.y_points).save("Q")
                    else:
                        raise ValueError(f"Invalid stream variable: {var}")
        return prog

    def process_results(self, results: Dict[str, Any]) -> np.ndarray:
        return results[self.measure_var]

    def acquire_data(self) -> np.ndarray:
        if self.program is None:
            self.run_program()

        t0 = perf_counter()
        self.results = {key: self.job.result_handles.get(key).fetch_all() for key in self.stream_vars}
        result_array = self.process_results(self.results)
        logging.info(f"Time to acquire data: {(perf_counter() - t0) * 1e3:.2f} ms")

        return result_array

    def run_program(self, verify: bool = True):
        if self.program is None:
            self.program = self.generate_program()

        self.job = self.qm.execute(self.program)

        if not verify:
            return

        # Wait until one buffer is filled{
        for key in self.stream_vars:
            self.job.result_handles.get(key).wait_for_values(1)
