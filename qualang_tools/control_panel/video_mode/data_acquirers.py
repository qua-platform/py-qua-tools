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


__all__ = ["BaseDataAcquirer", "RandomDataAcquirer", "OPXDataAcquirer"]


class BaseDataAcquirer(ABC):
    def __init__(
        self,
        *,
        x_offset_parameter,
        y_offset_parameter,
        x_span,
        y_span,
        x_attenuation: float = 0.0,
        y_attenuation: float = 0.0,
        x_points=101,
        y_points=101,
        num_averages=1,
        **kwargs,
    ):
        assert not kwargs

        self.x_offset_parameter = x_offset_parameter
        self.y_offset_parameter = y_offset_parameter
        self.x_span = x_span
        self.y_span = y_span
        self.num_averages = num_averages
        self.x_points = x_points
        self.y_points = y_points
        self.x_attenuation = x_attenuation
        self.y_attenuation = y_attenuation
        self.data_history = []
        logging.debug("Initializing DataGenerator")

        self.num_acquisitions = 0

        self.data_array = xr.DataArray(
            np.zeros((self.x_points, self.y_points)),
            coords=[("x", self.x_vals), ("y", self.y_vals)],
            attrs={"units": "V", "long_name": "Signal"},
        )
        for axis, param in {"x": self.x_offset_parameter, "y": self.y_offset_parameter}.items():
            if getattr(param, "label", None):
                param_name = param.label
            elif getattr(param, "name", None):
                param_name = param.name
            else:
                param_name = "X_axis"
            self.data_array.coords[axis].attrs.update({"units": "V", "long_name": param_name})
        logging.debug("DataGenerator initialized with initial data")

    @property
    def x_vals(self):
        x_offset = self.x_offset_parameter.get_latest()
        x_min = x_offset - self.x_span / 2
        x_max = x_offset + self.x_span / 2
        return np.linspace(x_min, x_max, self.x_points)

    @property
    def y_vals(self):
        y_offset = self.y_offset_parameter.get_latest()
        y_min = y_offset - self.y_span / 2
        y_max = y_offset + self.y_span / 2
        return np.linspace(y_min, y_max, self.y_points)

    @property
    def x_vals_unattenuated(self):
        x_attenuation_factor = 10 ** (self.x_attenuation / 20)  # Convert dB to voltage scale
        return self.x_vals * x_attenuation_factor

    @property
    def y_vals_unattenuated(self):
        y_attenuation_factor = 10 ** (self.y_attenuation / 20)  # Convert dB to voltage scale
        return self.y_vals * y_attenuation_factor

    def update_voltage_ranges(self):
        self.data_array = self.data_array.assign_coords(x=self.x_vals, y=self.y_vals)

        x_vals = self.x_vals
        y_vals = self.y_vals
        logging.debug(
            f"Updated voltage ranges: "
            f"x_vals=[{x_vals[0]}, {x_vals[1]}, ..., {x_vals[-1]}], "
            f"y_vals=[{y_vals[0]}, {y_vals[1]}, ..., {y_vals[-1]}]"
        )

    def update_attrs(self, attrs):
        for attr_name, attr in attrs.items():
            if attr_name in ["x_offset", "y_offset"]:
                attr["obj"].set(attr["new"])
        else:
            setattr(attr["obj"], attr_name, attr["new"])
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
            coords=[("x", self.x_vals), ("y", self.y_vals)],
            attrs=self.data_array.attrs,  # Preserve original attributes like units
        )

        self.data_array.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.data_array.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
        mean_abs_data = np.mean(np.abs(averaged_data))
        logging.debug(f"Data acquired with shape: {self.data_array.shape}, mean(abs(data)) = {mean_abs_data}")
        return self.data_array


class RandomDataAcquirer(BaseDataAcquirer):

    def acquire_data(self):
        sleep(1)
        results = np.random.rand(len(self.y_vals), len(self.x_vals))

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
        x_offset_parameter,
        y_offset_parameter,
        x_span,
        y_span,
        x_attenuation: float = 0.0,
        y_attenuation: float = 0.0,
        x_points=101,
        y_points=101,
        num_averages=1,
        result_type: Literal["I", "Q", "abs", "phase"] = "I",
        final_delay: Optional[float] = None,
        **kwargs,
    ):
        self.qm = qm
        self.scan_mode = scan_mode
        self.qua_inner_loop_action = qua_inner_loop_action
        self.initial_delay = final_delay
        self.program: Optional[Program] = None
        self.job: Optional[RunningQmJob] = None
        self.result_type = result_type
        self.results: Dict[str, Any] = {}

        super().__init__(
            x_offset_parameter=x_offset_parameter,
            y_offset_parameter=y_offset_parameter,
            x_span=x_span,
            y_span=y_span,
            x_attenuation=x_attenuation,
            y_attenuation=y_attenuation,
            num_averages=num_averages,
            x_points=x_points,
            y_points=y_points,
            **kwargs,
        )

    def update_attrs(self, attrs):
        super().update_attrs(attrs)
        logging.info(f"Updated attrs: {attrs}")

        requires_regeneration = ["x_span", "y_span", "x_points", "y_points"]
        if any(attr in requires_regeneration for attr in attrs):
            logging.info("Regenerating QUA program due to new parameters")
            self.program = None
            self.run_program()

    def generate_program(self) -> Program:
        x_vals = self.x_vals_unattenuated
        x_vals -= self.x_offset_parameter.get()
        y_vals = self.y_vals_unattenuated
        y_vals -= self.y_offset_parameter.get()

        with program() as prog:
            n = declare(int, 0)
            n_stream = declare_stream()
            IQ_streams = {"I": declare_stream(), "Q": declare_stream()}

            with infinite_loop_():
                save(n, n_stream)

                self.qua_inner_loop_action.initial_action()
                if self.initial_delay is not None:
                    wait(int(self.initial_delay * 1e9) // 4)

                for voltages in self.scan_mode.scan(x_vals=x_vals, y_vals=y_vals):
                    I, Q = self.qua_inner_loop_action(voltages)
                    save(I, IQ_streams["I"])
                    save(Q, IQ_streams["Q"])
                assign(n, n + 1)  # type: ignore

            with stream_processing():
                streams = {
                    "I": IQ_streams["I"].buffer(self.x_points * self.y_points),
                    "Q": IQ_streams["Q"].buffer(self.x_points * self.y_points),
                    "n": n_stream,
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

        x_idxs, y_idxs = self.scan_mode.get_idxs(x_points=self.x_points, y_points=self.y_points)
        results_2D = np.zeros((self.y_points, self.x_points), dtype=float)
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
