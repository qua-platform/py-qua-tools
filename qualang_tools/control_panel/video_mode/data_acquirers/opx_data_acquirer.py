import numpy as np
import logging
from typing import Any, Dict, List, Literal, Optional, Callable
from time import perf_counter

from dash import html
import dash_bootstrap_components as dbc

from qm import QuantumMachinesManager, Program
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import program, declare_stream, infinite_loop_, save, stream_processing, wait

from qualang_tools.control_panel.video_mode.dash_tools import ModifiedFlags
from qualang_tools.control_panel.video_mode.data_acquirers.base_data_aqcuirer import BaseDataAcquirer
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
from qualang_tools.control_panel.video_mode.scan_modes import ScanMode


__all__ = ["OPXDataAcquirer"]


class OPXDataAcquirer(BaseDataAcquirer):
    """Data acquirer for OPX devices.

    This class is responsible for acquiring data from OPX devices.

    Args:
        qmm: The QuantumMachinesManager instance.
        qua_config: The QUAM configuration to use.
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
        result_type: Literal["I", "Q", "amplitude", "phase"] = "I",
        initial_delay: Optional[float] = None,
        **kwargs,
    ):
        self.qmm = qmm
        self.qua_config = qua_config
        self.qm = self.qmm.open_qm(self.qua_config)  # type: ignore

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

                self.qua_inner_loop_action.final_action()

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
        elif self.result_type == "amplitude":
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

    def run_program(self, verify: bool = True) -> None:
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

    def get_dash_components(self, include_subcomponents: bool = True) -> List[html.Div]:
        components = super().get_dash_components()

        components.append(
            html.Div(
                [
                    dbc.Label("Result Type"),
                    dbc.Select(
                        id={"type": self.component_id, "index": "result-type"},
                        options=[{"label": rt, "value": rt} for rt in self.result_types],
                        value=self.result_type,
                    ),
                ]
            )
        )

        if include_subcomponents:
            components.extend(self.scan_mode.get_dash_components())
            components.extend(self.qua_inner_loop_action.get_dash_components())

        return components

    def generate_config(self) -> None:
        raise NotImplementedError("OPXDataAcquirer does not implement generate_config")

    def update_parameters(self, parameters: Dict[str, Dict[str, Any]]) -> ModifiedFlags:
        flags = super().update_parameters(parameters)
        # Update program if any sweep axes have been modified
        if flags & ModifiedFlags.PARAMETERS_MODIFIED:
            flags |= ModifiedFlags.PROGRAM_MODIFIED

        params = parameters[self.component_id]
        if self.result_type != params["result-type"]:
            self.result_type = params["result-type"]
            flags |= ModifiedFlags.PARAMETERS_MODIFIED

        flags |= self.scan_mode.update_parameters(parameters)
        flags |= self.qua_inner_loop_action.update_parameters(parameters)

        if flags & ModifiedFlags.CONFIG_MODIFIED:
            self.generate_config()

        if flags & (ModifiedFlags.CONFIG_MODIFIED | ModifiedFlags.PROGRAM_MODIFIED):
            self.program = self.generate_program()
            self.run_program()

        return flags

    def get_component_ids(self) -> List[str]:
        component_ids = super().get_component_ids()
        component_ids.append(self.scan_mode.component_id)
        component_ids.append(self.qua_inner_loop_action.component_id)
        return component_ids
