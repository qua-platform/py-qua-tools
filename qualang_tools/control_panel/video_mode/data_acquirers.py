from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Literal, Optional
import xarray as xr
import logging
from time import sleep, perf_counter
import numpy as np
from qm import Program, QuantumMachine
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import *
from qualang_tools.control_panel.video_mode.scan_modes import ScanMode
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis


__all__ = ["BaseDataAcquirer", "RandomDataAcquirer", "OPXDataAcquirer"]


class BaseDataAcquirer(ABC):
    def __init__(
        self,
        *,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages=1,
        **kwargs,
    ):
        assert not kwargs

        self.x_axis = x_axis
        self.y_axis = y_axis
        self.num_averages = num_averages
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
            label = axis.label or axis.name
            self.data_array.coords[axis.name].attrs.update({"units": "V", "long_name": label})
        logging.debug("DataGenerator initialized with initial data")

    def update_voltage_ranges(self):
        self.data_array = self.data_array.assign_coords(
            {axis.name: axis.sweep_values for axis in [self.x_axis, self.y_axis]}
        )

        x_vals = self.x_axis.sweep_values
        y_vals = self.y_axis.sweep_values
        logging.debug(
            f"Updated voltage ranges: "
            f"x_vals=[{x_vals[0]}, {x_vals[1]}, ..., {x_vals[-1]}], "
            f"y_vals=[{y_vals[0]}, {y_vals[1]}, ..., {y_vals[-1]}]"
        )

    def update_attrs(self, attrs):
        for attr in attrs:
            setattr(attr["obj"], attr["key"], attr["new"])
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

        if len(self.data_history) > self.num_averages:
            self.data_history.pop(0)

        averaged_data = np.mean(self.data_history, axis=0)

        self.data_array = xr.DataArray(
            averaged_data,
            coords=[("x", self.x_axis.sweep_values_with_offset), ("y", self.y_axis.sweep_values_with_offset)],
            attrs=self.data_array.attrs,  # Preserve original attributes like units
        )

        self.data_array.coords[self.x_axis.name].attrs.update(
            {"units": "V", "long_name": self.x_axis.label or self.x_axis.name}
        )
        self.data_array.coords[self.y_axis.name].attrs.update(
            {"units": "V", "long_name": self.y_axis.label or self.y_axis.name}
        )
        mean_abs_data = np.mean(np.abs(averaged_data))
        logging.debug(f"Data acquired with shape: {self.data_array.shape}, mean(abs(data)) = {mean_abs_data}")
        return self.data_array


class RandomDataAcquirer(BaseDataAcquirer):

    def acquire_data(self):
        sleep(1)
        results = np.random.rand(self.x_axis.points, self.y_axis.points)
        return results


class OPXDataAcquirer(BaseDataAcquirer):
    stream_vars = ["I", "Q"]
    result_types = ["I", "Q", "amplitude", "phase"]

    def __init__(
        self,
        *,
        qm: QuantumMachine,
        qua_inner_loop_action: Callable,
        scan_mode: ScanMode,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages=1,
        result_type: Literal["I", "Q", "abs", "phase"] = "I",
        initial_delay: Optional[float] = None,
        **kwargs,
    ):
        self.qm = qm
        self.scan_mode = scan_mode
        self.qua_inner_loop_action = qua_inner_loop_action
        self.initial_delay = initial_delay
        self.program: Optional[Program] = None
        self.job: Optional[RunningQmJob] = None
        self.result_type = result_type
        self.results: Dict[str, Any] = {}

        super().__init__(
            x_axis=x_axis,
            y_axis=y_axis,
            num_averages=num_averages,
            **kwargs,
        )

    def update_attrs(self, attrs):
        super().update_attrs(attrs)
        logging.info(f"Updated attrs: {attrs}")

        requires_regeneration = ["span", "points"]
        if any(attr["key"] in requires_regeneration for attr in attrs):
            logging.info("Regenerating QUA program due to new parameters")
            self.program = None
            self.run_program()

    def generate_program(self) -> Program:
        x_vals = self.x_axis.sweep_values_unattenuated
        y_vals = self.y_axis.sweep_values_unattenuated

        with program() as prog:
            IQ_streams = {"I": declare_stream(), "Q": declare_stream()}

            with infinite_loop_():
                self.qua_inner_loop_action.initial_action()
                if self.initial_delay is not None:
                    wait(int(self.initial_delay * 1e9) // 4)

                for voltages in self.scan_mode.scan(x_vals=x_vals, y_vals=y_vals):
                    I, Q = self.qua_inner_loop_action(voltages)
                    save(I, IQ_streams["I"])
                    save(Q, IQ_streams["Q"])

            with stream_processing():
                streams = {
                    "I": IQ_streams["I"].buffer(self.x_axis.points * self.y_axis.points),
                    "Q": IQ_streams["Q"].buffer(self.x_axis.points * self.y_axis.points),
                }
                combined_stream = None
                for var in self.stream_vars:
                    if combined_stream is None:
                        combined_stream = streams[var]
                    else:
                        combined_stream = combined_stream.zip(streams[var])
                combined_stream.save("combined")  # type: ignore
        return prog

    def process_results(self, results: Dict[str, Any]) -> np.ndarray:
        if self.result_type in ["I", "Q"]:
            result = results[self.result_type]
        elif self.result_type == "abs":
            result = np.abs(results["I"] + 1j * results["Q"])
        elif self.result_type == "phase":
            result = np.angle(results["I"] + 1j * results["Q"])
        else:
            raise ValueError(f"Invalid result type: {self.result_type}")

        x_idxs, y_idxs = self.scan_mode.get_idxs(x_points=self.x_axis.points, y_points=self.y_axis.points)
        results_2D = np.zeros((self.y_axis.points, self.x_axis.points), dtype=float)
        results_2D[y_idxs, x_idxs] = result

        return results_2D

    def acquire_data(self) -> np.ndarray:
        if self.program is None:
            self.run_program()

        t0 = perf_counter()
        results_tuple = self.job.result_handles.get("combined").fetch_all()  # type: ignore
        self.results = dict(zip(self.stream_vars, results_tuple))  # type: ignore
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
        self.job.result_handles.get("combined").wait_for_values(1)  # type: ignore
