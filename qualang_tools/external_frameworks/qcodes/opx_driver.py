import time
from typing import Dict, Optional

from qcodes import (
    Instrument,
    Parameter,
    MultiParameter,
)
from qcodes.utils.validators import Numbers, Arrays
from qm import SimulationConfig
from qm.qua import program
from qm.QuantumMachinesManager import QuantumMachinesManager
import matplotlib.pyplot as plt
import numpy as np


# noinspection PyAbstractClass
class OPX(Instrument):
    def __init__(
        self,
        config: Dict,
        name: str = "OPX",
        host=None,
        port=None,
        close_other_machines=True,
    ) -> None:
        """
        QCoDeS driver for the OPX.

        :param config: python dict containing the configuration expected by the OPX.
        :param name: The name of the instrument used internally by QCoDeS. Must be unique.
        :param host: IP address of the router to which the OPX is connected.
        :param port: Port of the OPX or main OPX if working with a cluster.
        :param close_other_machines: Flag to control if opening a quantum machine will close the existing ones. Default is True. Set to False if multiple a QOP is to be used by multiple users or to run several experiments in parallel.
        """
        super().__init__(name)

        self.qm = None
        self.qmm = None
        self.config = None
        self.result_handles = None
        self.job = None
        self.counter = 0
        self.results = {"names": [], "types": [], "buffers": [], "units": []}
        self.prog_id = None
        self.simulated_wf = {}
        # self.add_parameter("results", label="results", get_cmd=self.get_res)
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
            "axis1_axis",
            unit="",
            label="Axis 1",
            parameter_class=GeneratedSetPoints,
            startparam=self.axis1_start,
            stopparam=self.axis1_stop,
            numpointsparam=self.axis1_npoints,
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
            "axis2_axis",
            unit="",
            label="Axis 2",
            parameter_class=GeneratedSetPoints,
            startparam=self.axis2_start,
            stopparam=self.axis2_stop,
            numpointsparam=self.axis2_npoints,
            vals=Arrays(shape=(self.axis2_npoints.get_latest,)),
        )
        # Open QMM
        self.connect_to_qmm(host=host, port=port)
        # Set config
        self.set_config(config=config)
        # Open QM
        self.open_qm(close_other_machines)

    def connect_to_qmm(self, host=None, port=None):
        """
        Enable the connection with the OPX by creating the QuantumMachineManager.
        Displays the connection message with idn when the connection is established.

        :param host: IP address of the router to which the OPX is connected.
        :param port: Port of the OPX or main OPX if working with a cluster.
        """
        self.qmm = QuantumMachinesManager(host=host, port=port)
        self.connect_message()

    def connect_message(
        self, idn_param: str = "IDN", begin_time: Optional[float] = None
    ) -> None:
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

    def open_qm(self, close_other_machines):
        """
        Open a quantum machine with a given configuration ready to execute a program.
        Beware that each call will close the existing quantum machines and interrupt the running jobs.
        """
        self.qm = self.qmm.open_qm(
            self.config, close_other_machines=close_other_machines
        )

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
                self.result_handles.get(self.results["names"][i]).wait_for_values(
                    self.counter
                )
                if self.results["types"][i] == "IQ":
                    out = (
                        -(
                            self.result_handles.get(self.results["names"][i]).fetch(
                                self.counter - 1
                            )["value"]
                        )
                        * 4096
                        / self.readout_pulse_length()
                    )
                # raw adc traces
                elif self.results["types"][i] == "adc":
                    out = (
                        -(
                            self.result_handles.get(self.results["names"][i]).fetch(
                                self.counter - 1
                            )["value"]
                        )
                        / 4096
                    )
                # Reshape data
                if len(self.results["buffers"][i]) == 2:
                    output[self.results["names"][i]] = out.reshape(
                        self.results["buffers"][i][0], self.results["buffers"][i][1]
                    )
                elif len(self.results["buffers"][i]) == 1:
                    output[self.results["names"][i]] = out.reshape(
                        self.results["buffers"][i][0]
                    )
                else:
                    output[self.results["names"][i]] = out

            # Add amplitude and phase if I and Q are in the SP
            if "I" in output.keys() and "Q" in output.keys():
                output["R"] = np.sqrt(output["I"] ** 2 + output["Q"] ** 2)
                output["Phi"] = (
                    np.unwrap(np.angle(output["I"] + 1j * output["Q"])) * 180 / np.pi
                )
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
                # Check if next buffer is for averaging
                if len(gene.values[2].list_value.values[1].list_value.values) > 0:
                    if (
                        gene.values[2]
                        .list_value.values[1]
                        .list_value.values[0]
                        .string_value
                        == "average"
                    ):
                        averaging_buffer = True
            elif gene.values[0].string_value == "buffer":
                if not averaging_buffer:
                    self.results["buffers"][count].append(
                        int(gene.values[1].string_value)
                    )
                    # Check if next buffer is for averaging
                    if len(gene.values[2].list_value.values[1].list_value.values) > 0:
                        if (
                            gene.values[2]
                            .list_value.values[1]
                            .list_value.values[0]
                            .string_value
                            == "average"
                        ):
                            averaging_buffer = True
                else:
                    averaging_buffer = False
            elif gene.values[0].string_value == "@macro_adc_trace":
                self.results["buffers"][count].append(int(self.readout_pulse_length()))
                self.results["types"][count] = "adc"
            else:
                pass
            if len(gene.values) > 2:
                self._extend_result(gene.values[2].list_value, count, averaging_buffer)

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
            self.axis1_start(setpoints[0])
            self.axis1_stop(setpoints[-1])
            self.axis1_step(setpoints[1] - setpoints[0])
            self.axis1_npoints(len(setpoints))
            self.axis1_axis.unit = unit
            self.axis1_axis.label = label
        elif scanned_axis == "axis2":
            self.axis2_start(setpoints[0])
            self.axis2_stop(setpoints[-1])
            self.axis2_step(setpoints[1] - setpoints[0])
            self.axis2_npoints(len(setpoints))
            self.axis2_axis.unit = unit
            self.axis2_axis.label = label

    def get_measurement_parameter(self):
        """
        Find the correct Parameter shape based on the stream-processing and return the measurement Parameter.

        :return: Qcodes measurement parameters.
        """

        # Reset the results in case the stream processing was changed between two iterations
        self.results = {"names": [], "types": [], "buffers": [], "units": []}
        # Add amplitude and phase if I and Q are in the SP
        if len(self.results["names"]) == 0:
            self._get_stream_processing(self.get_prog())

            if "I" in self.results["names"] and "Q" in self.results["names"]:
                self.results["names"].append("R")
                self.results["names"].append("Phi")
                self.results["units"].append("V")
                self.results["units"].append("rad")
            if "adc" in self.results["types"]:
                self.axis1_start(0)
                self.axis1_stop(int(self.readout_pulse_length()))
                self.axis1_step(1)
                self.axis1_npoints(int(self.readout_pulse_length()))
                self.axis1_axis.unit = "ns"
                self.axis1_axis.label = "Readout time"

        if len(self.results["buffers"]) > 0 and len(self.results["buffers"][0]) > 0:
            if len(self.results["buffers"][0]) == 2:
                return ResultParameters(
                    self,
                    self.results["names"],
                    "OPX_results",
                    names=self.results["names"],
                    units=self.results["units"],
                    shapes=(
                        (self.results["buffers"][0][0], self.results["buffers"][0][1]),
                    )
                    * len(self.results["names"]),
                    setpoints=((self.axis2_axis(), self.axis1_axis()),)
                    * len(self.results["names"]),
                    setpoint_units=((self.axis2_axis.unit, self.axis1_axis.unit),)
                    * len(self.results["names"]),
                    setpoint_labels=((self.axis2_axis.label, self.axis1_axis.label),)
                    * len(self.results["names"]),
                )
            elif len(self.results["buffers"][0]) == 1:
                return ResultParameters(
                    self,
                    self.results["names"],
                    "OPX_results",
                    names=self.results["names"],
                    units=self.results["units"],
                    shapes=((self.results["buffers"][0][0],),)
                    * len(self.results["names"]),
                    setpoints=((self.axis1_axis(),),) * len(self.results["names"]),
                    setpoint_units=((self.axis1_axis.unit,),)
                    * len(self.results["names"]),
                    setpoint_labels=((self.axis1_axis.label,),)
                    * len(self.results["names"]),
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

    def run_exp(self):
        """
        Execute a given QUA program, initialize the counter to 0 and creates a result handle to fetch the results.
        """
        prog = self.get_prog()
        self.job = self.qm.execute(prog)
        self.counter = 0
        self.result_handles = self.job.result_handles

    def resume(self):
        """
        Resume the job and increment the counter to keep track of the fetched results.
        """
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
        self.job = self.qmm.simulate(
            self.config, prog, SimulationConfig(self.sim_time() // 4)
        )
        self.simulated_wf["analog"] = self.job.get_simulated_samples().con1.analog
        self.simulated_wf["digital"] = self.job.get_simulated_samples().con1.digital
        self.result_handles = self.job.result_handles

    def plot_simulated_wf(self):
        """
        Plot the simulated waveforms in a new figure using matplotlib.
        """
        plt.figure()
        for t in self.simulated_wf.keys():
            for port in self.simulated_wf[t].keys():
                plt.plot(self.simulated_wf[t][port], label=f"{t} {port}")
        plt.xlabel("Time [ns]")
        plt.ylabel("Voltage level [V]")
        plt.title("Simulated waveforms")
        plt.grid("on")
        plt.legend()

    def close(self) -> None:
        """
        Close the quantum machine and tear down the OPX instrument.
        """
        if self.qm is not None:
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
        return np.linspace(
            self._startparam(), self._stopparam(), self._numpointsparam()
        )


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
