import time
from typing import Dict, Optional

from qcodes import (
    Instrument,
    Parameter,
    MultiParameter,
)
from qcodes.utils.validators import Numbers, Arrays
from qm import SimulationConfig, generate_qua_script
from qm.qua import program
from qm import QuantumMachinesManager
from qualang_tools.results import wait_until_job_is_paused
from qualang_tools.results import fetching_tool
from qualang_tools.plot import interrupt_on_close
import matplotlib.pyplot as plt
import numpy as np
import warnings

warnings.filterwarnings("ignore")


# noinspection PyAbstractClass
class OPX(Instrument):
    def __init__(
        self,
        config: Dict,
        name: str = "OPX",
        host: str = None,
        port: int = None,
        cluster_name: str = None,
        octave=None,
        close_other_machines: bool = True,
        unwrap_phase: bool = True,
    ) -> None:
        """
        QCoDeS driver for the OPX.

        :param config: python dict containing the configuration expected by the OPX.
        :param name: The name of the instrument used internally by QCoDeS. Must be unique.
        :param host: IP address of the router to which the OPX is connected.
        :param cluster_name: Name of the cluster as defined in the OPX admin panel (from version QOP220)
        :param port: Port of the OPX or main OPX if working with a cluster.
        :param octave: Octave configuration if an Octave is to be used in this experiment.
        :param close_other_machines: Flag to control if opening a quantum machine will close the existing ones. Default is True. Set to False if multiple a QOP is to be used by multiple users or to run several experiments in parallel.
        """
        super().__init__(name)

        self.qm = None
        self.qm_id = None
        self.qmm = None
        self.close_other_machines = close_other_machines
        self.config = None
        self.result_handles = None
        self.job = None
        self.counter = 0
        self.demod_factor = 1
        self.results = {"names": [], "types": [], "buffers": [], "units": []}
        self.prog_id = None
        self.simulated_wf = {}
        self.unwrap_phase = unwrap_phase
        # Parameter for simulation duration
        self.add_parameter(
            "sim_time",
            unit="ns",
            label="sim_time",
            initial_value=100000,
            vals=Numbers(
                4,
            ),
            get_cmd=None,
            set_cmd=None,
        )
        self.measurement_variables = None
        self.add_parameter(
            "readout_pulse_length",
            unit="ns",
            vals=Numbers(16, 1e7),
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis1_stop",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis1_start",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis1_step",
            unit="",
            initial_value=0.1,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis1_npoints",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis1_full_list",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis1_axis",
            unit="",
            label="Axis 1",
            parameter_class=GeneratedSetPointsArbitrary,
            full_list=self.axis1_full_list,
            vals=Arrays(shape=(self.axis1_npoints.get_latest,)),
        )
        self.add_parameter(
            "axis2_stop",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis2_start",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis2_step",
            unit="",
            initial_value=0.1,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis2_npoints",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis2_full_list",
            unit="",
            initial_value=0,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "axis2_axis",
            unit="",
            label="Axis 2",
            parameter_class=GeneratedSetPointsArbitrary,
            full_list=self.axis2_full_list,
            vals=Arrays(shape=(self.axis1_npoints.get_latest,)),
        )
        # Open QMM
        self.connect_to_qmm(host=host, port=port, cluster_name=cluster_name, octave=octave)
        # Set config
        self.set_config(config=config)
        # Open QM
        self.open_qm(close_other_machines)

    def connect_to_qmm(self, host: str = None, port: int = None, cluster_name: str = None, octave=None):
        """
        Enable the connection with the OPX by creating the QuantumMachineManager.
        Displays the connection message with idn when the connection is established.

        :param host: IP address of the router to which the OPX is connected.
        :param port: Port of the OPX or main OPX if working with a cluster.
        :param cluster_name: Name of the cluster as defined in the OPX admin panel (from version QOP220)
        :param octave: Octave configuration if an Octave is to be used in this experiment.
        """
        self.qmm = QuantumMachinesManager(host=host, port=port, cluster_name=cluster_name, octave=octave)
        self.connect_message()

    def connect_message(self, idn_param: str = "IDN", begin_time: Optional[float] = None) -> None:
        """
        Print a standard message on initial connection to an instrument.

        Args:
            idn_param: Name of parameter that returns ID dict.
                Default ``IDN``.
            begin_time: ``time.time()`` when init started.
                Default is ``self._t0``, set at start of ``Instrument.__init__``.
        """
        idn = {"vendor": "Quantum Machines"}
        idn.update(self.get(idn_param))
        if idn["server"][0] == "1":
            idn["model"] = "OPX"
        elif idn["server"][0] == "2":
            idn["model"] = "OPX+"
        else:
            idn["model"] = ""
        t = time.time() - (begin_time or self._t0)

        con_msg = (
            "Connected to: {vendor} {model} in {t:.2f}s. "
            "QOP Version = {server}, SDK Version = {client}.".format(t=t, **idn)
        )
        print(con_msg)
        self.log.info(f"Connected to instrument: {idn}")

    def get_idn(self) -> Dict[str, Optional[str]]:
        """
        Parse a standard VISA *IDN? response into an ID dict.

        :return: A dict containing the SDK version (client) and QOP version (server).
        """
        return self.qmm.version()

    def set_config(self, config):
        """
        Update the configuration used by the OPX.

        :param config: the new configuration.
        """
        self.config = config

    def open_qm(self, close_other_machines: bool):
        """
        Open a quantum machine with a given configuration ready to execute a program.
        Beware that each call will close the existing quantum machines and interrupt the running jobs.
        """
        self.qm = self.qmm.open_qm(self.config, close_other_machines=close_other_machines)
        self.qm_id = self.qm.id

    def update_qm(self):
        """
        Close and re-open a new quantum machine so that it reloads the configuration in case it has been updated.
        """
        if self.qm_id in self.qmm.list_open_quantum_machines():
            self.qm.close()
        self.open_qm(self.close_other_machines)

    # Empty method that can be replaced by your pulse sequence in the main script
    # This can also be modified so that you can put the sequences here directly...
    def qua_program(self):
        """
        Custom QUA program

        :return: QUA program
        """
        with program() as prog:
            pass
        return prog

    # @abstractmethod
    def get_prog(self):
        """Get the QUA program from the user"""
        prog = self.qua_program
        return prog

    # @abstractmethod
    def get_res(self):
        """
        Fetch the results from the OPX, convert it into Volts and cast it into a dict.

        :return: dict containing the fetched results.
        """

        if self.result_handles is None:
            return None
        else:
            output = {}
            for i in range(len(self.results["types"])):
                # Get data and convert to Volt
                out = None
                # demodulated or integrated data
                self.result_handles.get(self.results["names"][i]).wait_for_values(self.counter)
                if self.results["types"][i] == "IQ":
                    out = (
                        -(self.result_handles.get(self.results["names"][i]).fetch(self.counter - 1)["value"])
                        * 4096
                        / self.readout_pulse_length()
                        * self.demod_factor
                        * self.results["scale_factor"][i]
                    )
                # raw adc traces
                elif self.results["types"][i] == "adc":
                    out = (
                        -(self.result_handles.get(self.results["names"][i]).fetch(self.counter - 1)["value"])
                        / 4096
                        * self.results["scale_factor"][i]
                    )
                # Reshape data
                if len(self.results["buffers"][i]) == 2:
                    output[self.results["names"][i]] = out.reshape(
                        self.results["buffers"][i][0], self.results["buffers"][i][1]
                    )
                elif len(self.results["buffers"][i]) == 1:
                    output[self.results["names"][i]] = out.reshape(self.results["buffers"][i][0])
                else:
                    output[self.results["names"][i]] = out

            # Add amplitude and phase if I and Q are in the SP
            if "I" in output.keys() and "Q" in output.keys():
                output["R"] = np.sqrt(output["I"] ** 2 + output["Q"] ** 2)
                if self.unwrap_phase is True:
                    output["Phi"] = np.unwrap(np.angle(output["I"] + 1j * output["Q"])) * 180 / np.pi
                else:
                    output["Phi"] = np.angle(output["I"] + 1j * output["Q"]) * 180 / np.pi
            return output

    def _extend_result(self, gene, count, averaging_buffer):
        """
        Recursive function to get relevant information from the stream processing to construct the result Parameter.

        :param gene: stream processing generator (item of prog.result_analysis._result_analysis.model).
        :param count: counter to keep track of the buffers for a given stream.
        :param averaging_buffer: flag identifying if a buffer is used for averaging.
        """

        if len(gene.values) > 0:
            if gene.values[0].string_value == "saveAll":
                self.results["names"].append(gene.values[1].string_value)
                self.results["types"].append("IQ")
                self.results["units"].append("V")
                self.results["buffers"].append([])
                self.results["scale_factor"].append(1)
                # Check if next buffer is for averaging
                if len(gene.values[2].list_value.values[1].list_value.values) > 0:
                    if gene.values[2].list_value.values[1].list_value.values[0].string_value == "average":
                        averaging_buffer = True
            elif gene.values[0].string_value == "buffer":
                if not averaging_buffer:
                    self.results["buffers"][count].append(int(gene.values[1].string_value))
                    # Check if next buffer is for averaging
                    if len(gene.values[2].list_value.values[1].list_value.values) > 0:
                        if gene.values[2].list_value.values[1].list_value.values[0].string_value == "average":
                            averaging_buffer = True
                else:
                    averaging_buffer = False
            elif gene.values[0].string_value == "@macro_adc_trace":
                self.results["buffers"][count].append(int(self.readout_pulse_length()))
                self.results["types"][count] = "adc"
                self.results["scale_factor"].append(1)
            else:
                pass
            if len(gene.values) > 2:
                self._extend_result(gene.values[2].list_value, count, averaging_buffer)
            elif gene.values[0].string_value == "average":
                self._extend_result(gene.values[1].list_value, count, averaging_buffer)

    def _get_stream_processing(self, prog):
        """
        Get relevant information from the stream processing to construct the result Parameter.

        :param prog: QUA program.
        """
        count = 0
        for i in prog.result_analysis._result_analysis.model:
            self._extend_result(i, count, False)
            count += 1

    def set_sweep_parameters(self, scanned_axis, setpoints, unit=None, label=None):
        """
        Set the setpoint parameters.

        :param scanned_axis: Can be axis1 for the most inner loop and axis2 for the outer one. 3 dimensional scans or higher are not implemented.
        :param setpoints: Values of the sweep parameter as a python list.
        :param unit: Unit of the setpoint ("V" for instance).
        :param label: Label of the setpoint ("Bias voltage" for instance).
        """
        if scanned_axis == "axis1":
            self.axis1_full_list(setpoints)
            self.axis1_start(setpoints[0])
            self.axis1_stop(setpoints[-1])
            if len(setpoints) > 1:
                self.axis1_step(setpoints[1] - setpoints[0])
            else:
                self.axis1_step(0)
            self.axis1_npoints(len(setpoints))
            self.axis1_axis.unit = unit
            self.axis1_axis.label = label
        elif scanned_axis == "axis2":
            self.axis2_full_list(setpoints)
            self.axis2_start(setpoints[0])
            self.axis2_stop(setpoints[-1])
            if len(setpoints) > 1:
                self.axis2_step(setpoints[1] - setpoints[0])
            else:
                self.axis2_step(0)
            self.axis2_npoints(len(setpoints))
            self.axis2_axis.unit = unit
            self.axis2_axis.label = label

    def get_measurement_parameter(self, scale_factor=((),)):
        """
        Find the correct Parameter shape based on the stream-processing and return the measurement Parameter.

        :param scale_factor: list of tuples containing the parameter to rescale, the scale factor with respect to Volts and the new unit as in scale_factor=[(I, 0.152, "pA"), (Q, 0.152, "pA")].
        :return: Qcodes measurement parameters.
        """

        # Reset the results in case the stream processing was changed between two iterations
        self.results = {
            "names": [],
            "types": [],
            "buffers": [],
            "units": [],
            "scale_factor": [],
        }
        # Add amplitude and phase if I and Q are in the SP
        if len(self.results["names"]) == 0:
            self._get_stream_processing(self.get_prog())

            if "I" in self.results["names"] and "Q" in self.results["names"]:
                self.results["names"].append("R")
                self.results["names"].append("Phi")
                self.results["units"].append("V")
                self.results["units"].append("deg")
            if "adc" in self.results["types"]:
                self.axis1_start(0)
                self.axis1_stop(int(self.readout_pulse_length()))
                self.axis1_step(1)
                self.axis1_npoints(int(self.readout_pulse_length()))
                self.axis1_full_list(np.arange(self.axis1_start(), self.axis1_stop(), self.axis1_step()))
                self.axis1_axis.unit = "ns"
                self.axis1_axis.label = "Readout time"
        # Rescale the results if a scale factor is provided
        if len(scale_factor) > 0:
            if len(scale_factor[0]) > 0:
                if len(scale_factor[0]) == 3:
                    for param in scale_factor:
                        if param[0] in self.results["names"]:
                            self.results["units"][self.results["names"].index(param[0])] = param[2]
                            self.results["scale_factor"][self.results["names"].index(param[0])] = param[1]
                else:
                    raise ValueError(
                        "scale_factor must be a list of tuples with 3 elements (the result name, the scale factor and the new unit), as in [('I', 0.152, 'pA'), ]."
                    )
        if len(self.results["buffers"]) > 0 and len(self.results["buffers"][0]) > 0:
            if len(self.results["buffers"][0]) == 2:
                return ResultParameters(
                    self,
                    self.results["names"],
                    "OPX_results",
                    names=self.results["names"],
                    units=self.results["units"],
                    shapes=((self.results["buffers"][0][0], self.results["buffers"][0][1]),)
                    * len(self.results["names"]),
                    setpoints=((self.axis2_axis(), self.axis1_axis()),) * len(self.results["names"]),
                    setpoint_units=((self.axis2_axis.unit, self.axis1_axis.unit),) * len(self.results["names"]),
                    setpoint_labels=((self.axis2_axis.label, self.axis1_axis.label),) * len(self.results["names"]),
                    setpoint_names=(
                        (
                            self.axis2_axis.label.replace(" ", "").lower(),
                            self.axis1_axis.label.replace(" ", "").lower(),
                        ),
                    )
                    * len(self.results["names"]),
                )
            elif len(self.results["buffers"][0]) == 1:
                return ResultParameters(
                    self,
                    self.results["names"],
                    "OPX_results",
                    names=self.results["names"],
                    units=self.results["units"],
                    shapes=((self.results["buffers"][0][0],),) * len(self.results["names"]),
                    setpoints=((self.axis1_axis(),),) * len(self.results["names"]),
                    setpoint_units=((self.axis1_axis.unit,),) * len(self.results["names"]),
                    setpoint_labels=((self.axis1_axis.label,),) * len(self.results["names"]),
                    setpoint_names=((self.axis1_axis.label.replace(" ", "").lower(),),) * len(self.results["names"]),
                )
        else:
            return ResultParameters(
                self,
                self.results["names"],
                "OPX_results",
                names=self.results["names"],
                units=self.results["units"],
                shapes=((),) * len(self.results["names"]),
                setpoints=((),) * len(self.results["names"]),
                setpoint_units=((),) * len(self.results["names"]),
                setpoint_labels=((),) * len(self.results["names"]),
            )

    def update_readout_length(self, readout_element: str, readout_operation: str, new_length: int):
        """
        Update the readout length of a given readout operation and readout element.
        This only works if the corresponding integration weights are constant.

        **Warning**: this function only updates the config in the current environment.
        The configuration.py file needs to be modified manually if one wishes to permanently update the readout length.

        :param readout_element: the readout element to update.
        :param readout_operation: the operation to update.
        :param new_length: the new readout length in ns - Must be a multiple of 4ns and larger than 16ns.
        """
        assert new_length % 4 == 0, "The readout length must be a multiple of 4ns."
        assert new_length > 15, "The minimum readout length is 16ns."

        config = self.config
        pulse = config["elements"][readout_element]["operations"][readout_operation]

        # Update length
        config["pulses"][pulse]["length"] = new_length
        # Update integration weights
        for weight in config["pulses"][pulse]["integration_weights"].values():
            iw = config["integration_weights"][weight]
            if len(iw["cosine"]) == 1 and len(iw["sine"]) == 1:
                value_cos = iw["cosine"][0][0]
                value_sin = iw["sine"][0][0]
                iw["cosine"] = [(value_cos, new_length)]
                iw["sine"] = [(value_sin, new_length)]
            else:
                raise RuntimeError(
                    "This method the update the readout length only works if the corresponding integration weights are constant."
                )
        # Update the quantum machine
        self.update_qm()
        print(
            f"The duration of the operation '{readout_operation}' from element '{readout_element}' is now {new_length} ns"
        )

    def live_plotting(self, results_to_plot: list = (), number_of_runs: int = 0):
        """
        Fetch and plot the specified OPX results while the program is running.

        **Warning:** This method will only work if used when no external parameters are being swept (no dond),
        because it requires the averaging to be done on the most outer loop and with the *.average()* method in the
        stream_processing as opposed to *.buffer(n_avg).map(FUNCTIONS.average())*.

        :param results_to_plot: list of the streamed data to be plotted in real-time.
        :param number_of_runs: Total number of averaging loops.
        """
        # Get the plotting grid
        if len(results_to_plot) == 0:
            raise ValueError("At least 1 result to plot must be provided")
        elif len(results_to_plot) == 2:
            grid = 1
        elif len(results_to_plot) == 3:
            grid = 121
        elif len(results_to_plot) == 4 or len(results_to_plot) == 5:
            grid = 221
        else:
            raise ValueError("Live plotting is limited to 4 parameters.")
        # Get results from QUA program
        results = fetching_tool(self.job, results_to_plot, "live")
        progress = 0
        # Live plotting
        fig = plt.figure()
        interrupt_on_close(fig, self.job)  # Interrupts the job when closing the figure
        while results.is_processing():
            # Fetch results
            data_list = results.fetch_all()
            # Subplot counter
            i = 0
            for data in data_list:
                if results_to_plot[i] == "iteration":
                    progress = data + 1
                    if data + 1 == number_of_runs:
                        self.job.halt()

                else:
                    # Convert the results into Volts
                    data = -data[-1] * 4096 / int(self.readout_pulse_length()) * self.demod_factor
                    # Plot results
                    if len(data.shape) == 1:
                        if len(results_to_plot) > 1:
                            plt.subplot(grid + i)
                        plt.cla()
                        plt.plot(self.axis1_axis(), data)
                        plt.xlabel(self.axis1_axis.label + f" [{self.axis1_axis.unit}]")
                        plt.ylabel(results_to_plot[i] + " [V]")
                    elif len(data.shape) == 2:
                        if len(results_to_plot) > 1:
                            plt.subplot(grid + i)
                        plt.cla()
                        plt.pcolor(self.axis1_axis(), self.axis2_axis(), data)
                        plt.xlabel(self.axis1_axis.label + f" [{self.axis1_axis.unit}]")
                        plt.ylabel(self.axis2_axis.label + f" [{self.axis2_axis.unit}]")
                        plt.title(results_to_plot[i] + " [V]")
                i += 1

            plt.suptitle(f"Iteration: {progress}/{number_of_runs} = {progress / number_of_runs * 100:.1f} %")
            plt.pause(1)
            plt.tight_layout()

    def run_exp(self):
        """
        Execute a given QUA program, initialize the counter to 0 and creates a result handle to fetch the results.
        """
        prog = self.get_prog()
        if " demod" in generate_qua_script(prog, self.config):
            self.demod_factor = 2
        else:
            self.demod_factor = 1
        self.job = self.qm.execute(prog)
        self.counter = 0
        self.result_handles = self.job.result_handles

    def resume(self, timeout: int = 30):
        """
        Resume the job and increment the counter to keep track of the fetched results.

        :param timeout: duration in seconds after which the console will be freed even if the pause statement has not been reached to prevent from being stuck here forever.
        """
        wait_until_job_is_paused(self.job, timeout)
        if not self.job.is_paused():
            raise RuntimeError(f"The program has not reached the pause statement before {timeout} s.")
        else:
            self.job.resume()
            self.counter += 1

    def compile_prog(self, prog):
        """
        Compile a given QUA program and stores it under the prog_id attribute.

        :param prog: A QUA program to be compiled.
        """
        self.prog_id = self.qm.compile(prog)

    def execute_compiled_prog(self):
        """
        Add a compiled program to the current queue and create a result handle to fetch the results.
        """
        if self.prog_id is not None:
            pending_job = self.qm.queue.add_compiled(self.prog_id)
            self.job = pending_job.wait_for_execution()
            self.result_handles = self.job.result_handles

    def simulate(self):
        """
        Simulate a given QUA program and store the simulated waveform into the simulated_wf attribute.
        """
        prog = self.get_prog()
        self.job = self.qmm.simulate(self.config, prog, SimulationConfig(self.sim_time() // 4))
        simulated_samples = self.job.get_simulated_samples()
        for con in [f"con{i}" for i in range(1, 10)]:
            if hasattr(simulated_samples, con):
                self.simulated_wf[con] = {}
                self.simulated_wf[con]["analog"] = self.job.get_simulated_samples().__dict__[con].analog
                self.simulated_wf[con]["digital"] = self.job.get_simulated_samples().__dict__[con].digital
        self.result_handles = self.job.result_handles

    def plot_simulated_wf(self):
        """
        Plot the simulated waveforms in a new figure using matplotlib.
        """
        plt.figure()
        for con in self.simulated_wf.keys():
            for t in self.simulated_wf[con].keys():
                for port in self.simulated_wf[con][t].keys():
                    if not np.all(self.simulated_wf[con][t][port] == 0):
                        if len(self.simulated_wf.keys()) == 1:
                            plt.plot(self.simulated_wf[con][t][port], label=f"{t} {port}")
                        else:
                            plt.plot(
                                self.simulated_wf[con][t][port],
                                label=f"{con} {t} {port}",
                            )
        plt.xlabel("Time [ns]")
        plt.ylabel("Voltage level [V]")
        plt.title("Simulated waveforms")
        plt.grid("on")
        plt.legend()

    def close(self) -> None:
        """
        Close the quantum machine and tear down the OPX instrument.
        """
        if self.qm_id in self.qmm.list_open_quantum_machines():
            self.qm.close()
        super().close()

    def halt(self) -> None:
        """
        Interrupt the current job and halt the running program.
        """
        if self.job is not None:
            self.job.halt()


# noinspection PyAbstractClass
class ResultParameters(MultiParameter):
    """
    Subclass of MultiParameter suited for the results acquired with the OPX.
    """

    def __init__(
        self,
        instr,
        params,
        name,
        names,
        units,
        shapes=None,
        setpoints=None,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            names=names,
            units=units,
            shapes=shapes,
            setpoints=setpoints,
            *args,
            **kwargs,
        )

        self._instr = instr
        self._params = params

    def get_raw(self):
        vals = []
        result = self._instr.get_res()
        for param in self._params:
            if param in self._instr.results["names"]:
                vals.append(result[param])
        return tuple(vals)


# noinspection PyAbstractClass
class GeneratedSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """

    def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._startparam = startparam
        self._stopparam = stopparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(self._startparam(), self._stopparam(), self._numpointsparam())


# noinspection PyAbstractClass
class GeneratedSetPointsSpan(Parameter):
    """
    A parameter that generates a setpoint array from center, span and num points
    parameters.
    """

    def __init__(self, spanparam, centerparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._spanparam = spanparam
        self._centerparam = centerparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(
            self._centerparam() - self._spanparam() / 2,
            self._centerparam() + self._spanparam() / 2,
            self._numpointsparam(),
        )


# noinspection PyAbstractClass
class GeneratedSetPointsArbitrary(Parameter):
    """
    A parameter that generates a setpoint array from an arbitrary list of points.
    """

    def __init__(self, full_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_list = full_list

    def get_raw(self):
        return self.full_list()
