from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Literal, Optional
import xarray as xr
import logging
from time import sleep, perf_counter
import numpy as np
from qm import Program, QuantumMachinesManager
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import *
from qualang_tools.control_panel.video_mode.scan_modes import ScanMode
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
from dash import html
import dash_bootstrap_components as dbc


__all__ = ["BaseDataAcquirer", "RandomDataAcquirer", "OPXDataAcquirer"]


def dicts_equal(d1: Dict[Any, Any], d2: Dict[Any, Any]) -> bool:
    """Check if two dictionaries are equal.

    This method checks if two dictionaries are equal by comparing their keys and values recursively.
    """
    if d1.keys() != d2.keys():
        return False
    for key, value in d1.items():
        if isinstance(value, dict):
            if not dicts_equal(value, d2[key]):
                return False
        elif isinstance(value, list):
            if not isinstance(d2[key], list) or len(value) != len(d2[key]):
                return False
            for v1, v2 in zip(value, d2[key]):
                if isinstance(v1, dict):
                    if not dicts_equal(v1, v2):
                        return False
                elif v1 != v2:
                    return False
        elif value != d2[key]:
            return False
    return True


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
        **kwargs,
    ):
        if kwargs:
            raise ValueError(f"Unexpected kwargs for DataAcquirer: {kwargs}")

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
            self.data_array.coords[axis.name].attrs.update({"units": axis.units, "long_name": label})
        logging.debug("DataGenerator initialized with initial data")

    def update_attrs(self, attrs: List[Dict[str, Any]]):
        """Update the attributes of the data array.

        This method updates the attributes of the data array with the provided attributes.
        This method is invoked from the Dash app when the user updates the parameters in the control panel.

        Args:
            attrs: The attributes to update.
        """
        for attr in attrs:
            setattr(attr["obj"], attr["key"], attr["new"])
        pass

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
            label = axis.label or axis.name
            self.data_array.coords[axis.name].attrs.update({"units": axis.units, "long_name": label})
        mean_abs_data = np.mean(np.abs(averaged_data))
        logging.debug(f"Data acquired with shape: {self.data_array.shape}, mean(abs(data)) = {mean_abs_data}")
        return self.data_array

    @abstractmethod
    def get_dash_components(self):
        """Return a list of Dash components specific to this data acquirer."""
        pass

    def get_all_dash_components(self):
        """Return all Dash components, including those from contained objects."""
        return self.get_dash_components()


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
        return [
            html.Div(
                [
                    dbc.Label("Acquire time"),
                    dbc.Input(
                        id="acquire-time",
                        type="number",
                        value=self.acquire_time,
                        min=0.1,
                        max=10,
                        step=0.1,
                    ),
                ]
            )
        ]

    def get_all_dash_components(self):
        return self.get_dash_components()


class OPXDataAcquirer(BaseDataAcquirer):
    """Data acquirer for OPX devices.

    This class is responsible for acquiring data from OPX devices.

    Args:
        qm: The QuantumMachine instance.
        qua_inner_loop_action: The inner loop action to execute.
        scan_mode: The scan mode to use.
        x_axis: The x-axis of the data acquirer.
        y_axis: The y-axis of the data acquirer.
        num_averages: The number of averages to take as a rolling average.
        result_type: The type of result to acquire.
        initial_delay: The initial delay before starting each scan.
    """

    stream_vars = ["I", "Q"]
    result_types = ["I", "Q", "amplitude", "phase"]

    def __init__(
        self,
        *,
        qmm: QuantumMachinesManager,
        qua_config: Dict[str, Any],
        qua_inner_loop_action: Callable,
        scan_mode: ScanMode,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages=1,
        result_type: Literal["I", "Q", "abs", "phase"] = "I",
        initial_delay: Optional[float] = None,
        **kwargs,
    ):
        self.qmm = qmm
        self.qua_config = qua_config
        self.qm = self.qmm.open_qm(self.qua_config)

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

    def update_attrs(self, attrs: List[Dict[str, Any]]):
        """Update the attributes of the data array.

        This method updates the attributes of the data array with the provided attributes.
        This method is invoked from the Dash app when the user updates the parameters in the control panel.

        Args:
            attrs: The attributes to update.
        """
        super().update_attrs(attrs)
        logging.info(f"Updated attrs: {attrs}")

        requires_regeneration = ["span", "points"]
        if any(attr["key"] in requires_regeneration for attr in attrs):
            logging.info("Regenerating QUA program due to new parameters")
            self.program = None
            self.run_program()

    def generate_program(self) -> Program:
        """Generate a QUA program to acquire data from the device."""
        x_vals = self.x_axis.sweep_values_unattenuated
        y_vals = self.y_axis.sweep_values_unattenuated

        with program() as prog:
            IQ_streams = {"I": declare_stream(), "Q": declare_stream()}

            with infinite_loop_():
                self.qua_inner_loop_action.initial_action()
                if self.initial_delay is not None:
                    wait(int(self.initial_delay * 1e9) // 4)

                for x, y in self.scan_mode.scan(x_vals=x_vals, y_vals=y_vals):
                    I, Q = self.qua_inner_loop_action(x, y)
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
        """Process the results from the device.

        This method processes the results from the device and returns a 2D array.
        The class variable `result_type` determines the type of result to acquire.
        The `scan_mode` determines the order in which the data is acquired and sorted
        """
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
        """Acquire data from the device.

        This method acquires data from the device and returns a 2D array.
        """
        if self.program is None:
            self.run_program()

        t0 = perf_counter()
        results_tuple = self.job.result_handles.get("combined").fetch_all()  # type: ignore
        self.results = dict(zip(self.stream_vars, results_tuple))  # type: ignore
        result_array = self.process_results(self.results)
        logging.info(f"Time to acquire data: {(perf_counter() - t0) * 1e3:.2f} ms")

        return result_array

    def run_program(self, verify: bool = True):
        """Run the QUA program.

        This method runs the QUA program and returns the results.

        Args:
            verify: Whether to verify that data can be acquired once started.
        """
        if self.program is None:
            self.program = self.generate_program()

        self.job = self.qm.execute(self.program)

        if not verify:
            return

        # Wait until one buffer is filled{
        self.job.result_handles.get("combined").wait_for_values(1)  # type: ignore

    def get_dash_components(self):
        return [
            html.Div(
                [
                    dbc.Label("Result Type"),
                    dbc.Select(
                        id="result-type",
                        options=[{"label": rt, "value": rt} for rt in self.result_types],
                        value=self.result_type,
                    ),
                ]
            )
        ]

    def get_all_dash_components(self):
        components = self.get_dash_components()
        components.extend(self.scan_mode.get_dash_components())
        components.extend(self.qua_inner_loop_action.get_dash_components())
        return components

    def get_object_and_attribute(self, id):
        if id.startswith('scan-mode-'):
            return self.scan_mode, id.replace('scan-mode-', '')
        elif id.startswith('inner-loop-'):
            return self.qua_inner_loop_action, id.replace('inner-loop-', '')
        else:
            return self, id


class OPXQuamDataAcquirer(OPXDataAcquirer):
    """Data acquirer for OPX devices using QUAM.

    This class is responsible for acquiring data from OPX devices using QUAM.

    Args:
        qmm: The QuantumMachinesManager instance.
        machine: The QUAM machine instance to use.
        qua_inner_loop_action: The inner loop action to execute.
        scan_mode: The scan mode to use.
        x_axis: The x-axis of the data acquirer.
        y_axis: The y-axis of the data acquirer.
        num_averages: The number of averages to take as a rolling average.
        result_type: The type of result to acquire.
        initial_delay: The initial delay before starting each scan.
    """

    def __init__(
        self,
        *,
        qmm: QuantumMachinesManager,
        machine: Any,
        qua_inner_loop_action: Callable,
        scan_mode: ScanMode,
        x_axis: SweepAxis,
        y_axis: SweepAxis,
        num_averages=1,
        result_type: Literal["I", "Q", "abs", "phase"] = "I",
        initial_delay: Optional[float] = None,
        **kwargs,
    ):
        self.machine = machine
        qua_config = machine.generate_config()

        super().__init__(
            qmm=qmm,
            qua_config=qua_config,
            qua_inner_loop_action=qua_inner_loop_action,
            scan_mode=scan_mode,
            x_axis=x_axis,
            y_axis=y_axis,
            num_averages=num_averages,
            result_type=result_type,
            initial_delay=initial_delay,
            **kwargs,
        )

    def get_dash_components(self):
        components = super().get_dash_components()
        # Add any QUAM-specific components here
        return components

    def get_all_dash_components(self):
        components = super().get_all_dash_components()
        # Add any QUAM-specific components here
        return components
