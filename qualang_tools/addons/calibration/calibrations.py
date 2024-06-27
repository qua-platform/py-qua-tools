"""
CALIBRATIONS
"""

from qm.qua import *
from qm import QuantumMachinesManager
from qm import QuantumMachine
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.units import unit
from qualang_tools.loops import from_array
from qm import SimulationConfig
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


available_variables = ["frequency", "amplitude", "duration"]
u = unit()


class QUA_calibrations:
    """
    Allows to easily perform various single qubit calibrations with the OPX.
    """

    def _check_element(self, element):
        if element in self.config["elements"]:
            return True
        else:
            raise Exception(f"The element '{element}' is not in the current config.")

    def _check_operation(self, operation, element):
        if operation in self.config["elements"][element]["operations"]:
            return True
        else:
            raise Exception(f"The operation '{operation}' is not in the current config for element '{element}'.")

    def _check_iw(self, int_weights):
        for iw in int_weights:
            if (
                iw
                not in self.config["pulses"][self.config["elements"][self.readout_elmt]["operations"][self.readout_op]][
                    "integration_weights"
                ]
            ):
                raise Exception(
                    f"The integration weight '{iw}' is not in the current config for operation '{self.readout_op}'."
                )
        return True

    def _check_outputs(self, outputs):
        for out in outputs:
            if out not in self.config["elements"][self.readout_elmt]["outputs"]:
                raise Exception(f"The output '{out}' is not in the current config for element '{self.readout_elmt}'.")
        return True

    def _check_plot_options(self, plot_options):
        if type(plot_options) is not dict:
            raise Exception("plot_options must be a python dictionary.")
        for key in plot_options:
            if key in self.plot_options.keys():
                self.plot_options[key] = plot_options[key]
            else:
                raise Exception(
                    f"Plot option {key} is not implemented, available options are {self.plot_options.keys()}"
                )

    def _user_variables_checks(self, calibration, scan_variables, iterations):
        # Check calibration
        if calibration in self.calibration_list:
            raise Exception("For the moment, it is not possible to run the same calibration twice in a row.")
        # Check variables
        for var in scan_variables:
            if var[0] not in available_variables:
                raise Exception(
                    f"The {var[0]} scan is not implemented. The available scan variables are {available_variables}."
                )
        # Check iterations
        if not (type(iterations) is int and iterations > 0):
            raise Exception("interations must be a python positive integer.")

    def _user_variables_init(self, calibration, scan_variables, iterations, cooldown_time):
        self.calibration_list.append(calibration)
        self.results[calibration] = {
            "scan_variables": [],
            "amplitude": [],
            "phase": [],
            "fit": {},
        }
        self.scan_var[calibration] = {}
        self.user_specifics[calibration] = {}
        # Add variables
        for var in scan_variables:
            self.scan_var[calibration][var[0]] = var[1]
            self.results[calibration]["scan_variables"].append(var)
        # Add iterations
        self.scan_var[calibration]["averaging"] = iterations
        # Check cooldown time
        if cooldown_time is None or (cooldown_time >= 4 and type(cooldown_time) is int):
            self.user_specifics[calibration]["cooldown_time"] = cooldown_time
        elif cooldown_time == 0:
            self.user_specifics[calibration]["cooldown_time"] = None
        else:
            raise Exception("cooldown_time must be a python positive integer larger than 4.")

    def _get_qua_variables(self, current_calib):
        n = declare(int)  # Averaging index
        var1 = None
        var1_scan = None
        var1_name = None
        var2 = None
        var2_scan = None
        var2_name = None
        for var_name in self.scan_var[current_calib].keys():
            if var_name == "frequency":
                if var1 is None:
                    var1 = declare(int)
                    var1_scan = self.scan_var[current_calib][var_name]
                    var1_name = var_name
                else:
                    var2 = declare(int)
                    var2_scan = self.scan_var[current_calib][var_name]
                    var2_name = var_name
            elif var_name == "amplitude":
                if current_calib == "Ramsey":
                    raise Exception("Amplitude scan is not available for Ramsey measurements.")
                elif (current_calib == "Resonator_spec") and self.flux_line_elmt is None:
                    raise Exception("Amplitude scan is not available for resonator spectroscopy without flux line.")
                if var1 is None:
                    var1 = declare(fixed)
                    var1_scan = self.scan_var[current_calib][var_name]
                    var1_name = var_name
                else:
                    var2 = declare(fixed)
                    var2_scan = self.scan_var[current_calib][var_name]
                    var2_name = var_name
            elif var_name == "duration":
                if (self.scan_var[current_calib][var_name] < 4).any():
                    raise Exception("No scanned duration can be lower than 4 clock cycles.")
                if current_calib in ["Rabi", "Ramsey"]:
                    pulse = self.config["elements"][self.qubit_elmt]["operations"][self.qubit_op]
                    for inpt in self.config["pulses"][pulse]["waveforms"]:
                        wf = self.config["pulses"][pulse]["waveforms"][inpt]
                        if self.config["waveforms"][wf]["type"] == "arbitrary":
                            if (
                                self.scan_var[current_calib][var_name] < self.config["pulses"][pulse]["length"] // 4
                            ).any():
                                raise Exception(
                                    "The scanned duration must be greater than the one defined in the configuration for arbitrary waveforms. Arbitrary waveforms can only be stretched and not compressed on the fly."
                                )
                if var1 is None:
                    var1 = declare(int)
                    var1_scan = self.scan_var[current_calib][var_name]
                    var1_name = var_name
                else:
                    var2 = declare(int)
                    var2_scan = self.scan_var[current_calib][var_name]
                    var2_name = var_name

            if len(self.scan_var[current_calib].keys()) == 2:
                return n, var1, var1_scan, var1_name
        return n, var1, var1_scan, var1_name, var2, var2_scan, var2_name

    def _align_measure_save(self, I, Q, I_st, Q_st, current_calib, align_flag=True):
        if align_flag:
            align(self.qubit_elmt, self.readout_elmt)
        # Measure the resonator
        if len(self.out) == 2:
            measure(
                self.readout_op,
                self.readout_elmt,
                None,
                dual_demod.full(self.iw[0], self.out[0], self.iw[1], self.out[1], I),
                dual_demod.full(self.iw[2], self.out[0], self.iw[3], self.out[1], Q),
            )
        elif len(self.out) == 1:
            measure(
                self.readout_op,
                self.readout_elmt,
                None,
                demod.full(self.iw[0], I, self.out[0]),
                demod.full(self.iw[1], Q, self.out[0]),
            )
        # Wait for the resonator to cooldown
        if self.user_specifics[current_calib]["cooldown_time"] is not None:
            wait(
                int(self.user_specifics[current_calib]["cooldown_time"]),
                self.readout_elmt,
            )
        # Save data to the stream processing
        save(I, I_st)
        save(Q, Q_st)

    def _plot_2d(self, x, y, amplitude, phase, x_label, y_label, title):
        plt.suptitle(title, fontsize=self.plot_options["fontsize"] + 2)
        plt.subplot(211)
        plt.cla()
        plt.title("Amplitude [V]")
        plt.pcolor(x, y, amplitude)
        plt.ylabel(y_label, fontsize=self.plot_options["fontsize"])
        plt.xticks(fontsize=self.plot_options["fontsize"])
        plt.yticks(fontsize=self.plot_options["fontsize"])
        plt.subplot(212)
        plt.cla()
        plt.title("Phase [rad]")
        plt.pcolor(x, y, phase)
        plt.xlabel(x_label, fontsize=self.plot_options["fontsize"])
        plt.ylabel(y_label, fontsize=self.plot_options["fontsize"])
        plt.xticks(fontsize=self.plot_options["fontsize"])
        plt.yticks(fontsize=self.plot_options["fontsize"])

    def _plot_1d(self, x, amplitude, phase, x_label, title):
        plt.suptitle(title, fontsize=self.plot_options["fontsize"] + 2)
        plt.subplot(211)
        plt.cla()
        plt.plot(
            x,
            amplitude,
            color=self.plot_options["color"],
            marker=self.plot_options["marker"],
            linewidth=self.plot_options["linewidth"],
        )
        plt.ylabel("Amplitude [V]", fontsize=self.plot_options["fontsize"])
        plt.xticks(fontsize=self.plot_options["fontsize"])
        plt.yticks(fontsize=self.plot_options["fontsize"])
        plt.subplot(212)
        plt.cla()
        plt.plot(
            x,
            phase,
            color=self.plot_options["color"],
            marker=self.plot_options["marker"],
            linewidth=self.plot_options["linewidth"],
        )
        plt.xlabel(x_label, fontsize=self.plot_options["fontsize"])
        plt.ylabel("Phase [rad]", fontsize=self.plot_options["fontsize"])
        plt.xticks(fontsize=self.plot_options["fontsize"])
        plt.yticks(fontsize=self.plot_options["fontsize"])

    def _get_IQ_data_and_plot(self, job, calib, plot, dim):
        pulse = self.config["elements"][self.readout_elmt]["operations"][self.readout_op]
        res_handles = job.result_handles
        if dim == 1:
            if plot == "live":
                results = fetching_tool(job, data_list=["I", "Q", "iteration"], mode="live")
                # Live plotting
                fig = plt.figure(figsize=self.plot_options["figsize"])
                interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
                while results.is_processing():
                    I, Q, iteration = results.fetch_all()
                    I = u.demod2volts(I, self.config["pulses"][pulse]["length"])
                    Q = u.demod2volts(Q, self.config["pulses"][pulse]["length"])

                    progress_counter(
                        iteration,
                        self.scan_var[calib]["averaging"],
                        start_time=results.get_start_time(),
                    )

                    self.results[calib]["amplitude"] = np.sqrt(I**2 + Q**2)
                    self.results[calib]["phase"] = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))

                    self._plot_1d(
                        x=self.scan_var[calib][list(self.scan_var[calib].keys())[0]],
                        amplitude=self.results[calib]["amplitude"],
                        phase=self.results[calib]["phase"],
                        x_label=list(self.scan_var[calib].keys())[0],
                        title=calib,
                    )
                    plt.pause(0.01)

            else:
                res_handles.wait_for_all_values()
                I = u.demod2volts(
                    res_handles.get("I").fetch_all(),
                    self.config["pulses"][pulse]["length"],
                )
                Q = u.demod2volts(
                    res_handles.get("Q").fetch_all(),
                    self.config["pulses"][pulse]["length"],
                )

                self.results[calib]["amplitude"] = np.sqrt(I**2 + Q**2)
                self.results[calib]["phase"] = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))

                if plot == "full":
                    plt.figure(figsize=self.plot_options["figsize"])
                    self._plot_1d(
                        x=self.scan_var[calib][list(self.scan_var[calib].keys())[0]],
                        amplitude=self.results[calib]["amplitude"],
                        phase=self.results[calib]["phase"],
                        x_label=list(self.scan_var[calib].keys())[0],
                        title=calib,
                    )
        elif dim == 2:
            res_handles = job.result_handles
            if plot == "live":
                results = fetching_tool(job, data_list=["I", "Q", "iteration"], mode="live")

                # Live plotting
                fig = plt.figure(figsize=self.plot_options["figsize"])
                interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
                while results.is_processing():
                    I, Q, iteration = results.fetch_all()
                    I = u.demod2volts(I, self.config["pulses"][pulse]["length"])
                    Q = u.demod2volts(Q, self.config["pulses"][pulse]["length"])

                    progress_counter(
                        iteration,
                        self.scan_var[calib]["averaging"],
                        start_time=results.get_start_time(),
                    )

                    self.results[calib]["amplitude"] = np.sqrt(I**2 + Q**2)
                    self.results[calib]["phase"] = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))

                    self._plot_2d(
                        x=self.scan_var[calib][list(self.scan_var[calib].keys())[0]],
                        y=self.scan_var[calib][list(self.scan_var[calib].keys())[1]],
                        amplitude=self.results[calib]["amplitude"],
                        phase=self.results[calib]["phase"],
                        x_label=list(self.scan_var[calib].keys())[0],
                        y_label=list(self.scan_var[calib].keys())[1],
                        title=calib,
                    )
                    plt.pause(0.01)
            else:
                res_handles.wait_for_all_values()
                I = u.demod2volts(
                    res_handles.get("I").fetch_all(),
                    self.config["pulses"][pulse]["length"],
                )
                Q = u.demod2volts(
                    res_handles.get("Q").fetch_all(),
                    self.config["pulses"][pulse]["length"],
                )

                self.results[calib]["amplitude"] = np.sqrt(I**2 + Q**2)
                self.results[calib]["phase"] = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))

                if plot == "full":
                    plt.figure(figsize=self.plot_options["figsize"])
                    self._plot_2d(
                        x=self.scan_var[calib][list(self.scan_var[calib].keys())[0]],
                        y=self.scan_var[calib][list(self.scan_var[calib].keys())[1]],
                        amplitude=self.results[calib]["amplitude"],
                        phase=self.results[calib]["phase"],
                        x_label=list(self.scan_var[calib].keys())[0],
                        y_label=list(self.scan_var[calib].keys())[1],
                        title=calib,
                    )

    def __init__(
        self,
        configuration,
        readout=("resonator", "readout"),
        qubit=("qubit", "pi"),
        integration_weights=("cos", "sin", "minus_sin", "cos"),
        outputs=("out1", "out2"),
        flux_line=None,
    ):
        """The QUA calibrations class. It has an API for performing various basic resonator and qubit calibrations.
        Currently the available calibrations are: 'resonator_spectroscopy', 'rabi' and 'ramsey'.
        All these calibrations are implemented with 1D or 2D scans among three variables ('frequency', 'amplitude', 'duration').
        The meaning of these variables is calibration specific.
        For instance 'duration' represent the qubit pulse length for Rabi and the idle time for Ramsey.
        Each calibration can be set using the `set_` (`set_rabi` for instance) method and executed using the
        `run_calibrations()` method or simulated using the `simulate_calibrations` method.
        The results are stored in a python dictionary called `results`.

        :param configuration: configuration file containing the qubit and readout elements and operations specified.
        :param readout: readout element and operation as defined in the configuration. Must be written as a tuple (element, operation).
        :param qubit: qubit element and operation as defined in the configuration. Must be written as a tuple (element, operation).
        :param integration_weights: integration weights as defined in the configuration. Must be written as a tuple of 4 items ('cos', 'sin', 'minus_sin', 'cos').
        :param outputs: readout element outputs as defined in the configuration. Must be a python tuple of two items ('out1', 'out2').
        :param flux_line: (optional) flux line element and operation as defined in the configuration. Must be written as a tuple (element, operation).
        """
        self.config = configuration
        # Check the validity of the user inputs for elements, operations, int weights and outputs
        if self._check_element(readout[0]):
            self.readout_elmt = readout[0]
        if self._check_element(qubit[0]):
            self.qubit_elmt = qubit[0]
        if flux_line is not None:
            if self._check_element(flux_line[0]):
                self.flux_line_elmt = flux_line[0]
            if self._check_operation(flux_line[1], flux_line[0]):
                self.flux_line_op = flux_line[1]
        else:
            self.flux_line_elmt = None
        if self._check_operation(readout[1], readout[0]):
            self.readout_op = readout[1]
        if self._check_operation(qubit[1], qubit[0]):
            self.qubit_op = qubit[1]
        if self._check_iw(integration_weights):
            self.iw = integration_weights
        if self._check_outputs(outputs):
            self.out = outputs

        self.calibration_list = []
        self.scan_var = {}
        self.results = {}
        self.cooldown_time = None
        self.user_specifics = {}
        self.simulation = False
        self.qm = None
        self.plot_options = {
            "fontsize": 14,
            "color": "b",
            "marker": None,
            "linewidth": 2,
            "figsize": (12, 15),
        }

    def set_resonator_spectroscopy(self, scan_variables, iterations=1, cooldown_time=None):
        """Sets the resonator spectroscopy calibration.
        This program will measure the resonator response for different readout pulse frequencies defined in scan_variables.

        :param scan_variables: variables to be scanned. Must be an array of tuples [('variable', [values])]. 1D and 2D scans are available.
        :param iterations: number of averaging iterations. Must be a positive Python integer.
        :param cooldown_time: resonator or qubit cooldown time in clock cycles (4ns). Must be an integer.
        :return: None
        """
        calibration = "Resonator_spec"
        self._user_variables_checks(calibration, scan_variables, iterations)
        self._user_variables_init(calibration, scan_variables, iterations, cooldown_time)

    def set_rabi(self, scan_variables, iterations=1, cooldown_time=None):
        """Performs a Rabi-like measurement by sending a pulse to the qubit and measuring the resonator response.
        The available scanning parameters are:
        'duration' (pulse length in clock cycles (4ns), must be an integer.),
        'frequency' (pulse frequency in Hz, must be an integer) and
        'amplitude' (pulse amplitude as a pre-factor to the amplitude set in the configuration, must be in [-2,2)).

        :param scan_variables: variables to be scanned. Must be an array of tuples [('variable', [values])]. 1D and 2D scans are available.
        :param iterations: number of averaging iterations. Must be a positive Python integer.
        :param cooldown_time: resonator or qubit cooldown time in clock cycles (4ns). Must be an integer.
        :return: None
        """
        calibration = "Rabi"
        self._user_variables_checks(calibration, scan_variables, iterations)
        self._user_variables_init(calibration, scan_variables, iterations, cooldown_time)

    def set_T1(self, scan_variables, iterations=1, cooldown_time=None):
        """Performs a T1 measurement by sending a pi-pulse to the qubit and measuring the resonator response after a varying time.
        The available scanning parameters are:
        'duration' (wait time in clock cycles (4ns), must be an integer).

        :param scan_variables: variables to be scanned. Must be an array of tuples [('variable', [values])].
        :param iterations: number of averaging iterations. Must be a positive Python integer.
        :param cooldown_time: resonator or qubit cooldown time in clock cycles (4ns). Must be an integer.
        :return: None
        """
        calibration = "T1"
        self._user_variables_checks(calibration, scan_variables, iterations)
        self._user_variables_init(calibration, scan_variables, iterations, cooldown_time)
        if (len(scan_variables) > 1) or (scan_variables[0][0] != "duration"):
            raise Exception("Only 'duration' scans are available for T1 calibration.")

    def set_ramsey(self, scan_variables, iterations=1, cooldown_time=None, idle_time=None):
        """Performs a Ramsey-like measurement (pi/2 - idle time - pi/2).
        The available scanning parameters are:
        'duration' (idle time in clock cycles unit (4 ns)),
        'frequency' (pulse frequency in Hz, must be an integer).

        :param scan_variables: variables to be scanned. Must be an array of tuples [('variable', [values])]. 1D and 2D scans are available.
        :param iterations: number of averaging iterations. Must be a positive Python integer.
        :param cooldown_time: resonator or qubit cooldown time in clock cycles (4ns). Must be an integer.
        :param idle_time: Ramsey sequence idle time in clock cycles unit (4 ns). Must be an integer larger than 4.
        :return: None
        """
        calibration = "Ramsey"
        self._user_variables_checks(calibration, scan_variables, iterations)
        self._user_variables_init(calibration, scan_variables, iterations, cooldown_time)
        # Check idle time
        if idle_time is None or (idle_time >= 4 and type(idle_time) is int):
            self.user_specifics[calibration]["idle_time"] = idle_time
        elif cooldown_time == 0:
            self.user_specifics[calibration]["cooldown_time"] = None
        else:
            raise Exception("idle_time must be 0 or a python positive integer larger than 4.")

    def set_raw_traces(self, scan_variables=(), iterations=1, cooldown_time=None):
        """Acquires the raw and averaged traces from the two inputs of the OPX.

        :param scan_variables: None
        :param iterations: number of averaging iterations. Must be a positive Python integer.
        :param cooldown_time: resonator or qubit cooldown time in clock cycles (4ns). Must be an integer.
        :return: None
        """
        calibration = "raw_traces"
        self._user_variables_checks(calibration, scan_variables, iterations)
        self._user_variables_init(calibration, scan_variables, iterations, cooldown_time)

    def set_time_of_flight(self, scan_variables=(), iterations=1, cooldown_time=None, threshold=10 / 4096):
        """Measures the time of flight and offsets of the two inputs of the OPX.

        :param scan_variables: None
        :param iterations: number of averaging iterations. Must be a positive Python integer.
        :param cooldown_time: resonator or qubit cooldown time in clock cycles (4ns). Must be an integer.
        :param threshold: detection threshold for time of flight estimation in V/ns.
        :return: None
        """
        calibration = "time_of_flight"
        self._user_variables_checks(calibration, scan_variables, iterations)
        self._user_variables_init(calibration, scan_variables, iterations, cooldown_time)
        self.user_specifics[calibration]["threshold"] = threshold

    def run_calibrations(self, quantum_machine, plot=None, fits=False, plot_options=None):
        """Execute the implemented calibrations.

        :param quantum_machine:
        :param plot: Can be either 'full' for plotting the data after the execution or 'live' for live plotting.
        :param fits: To be implemented
        :param plot_options: Python dictionary containing options to customize the plot (ex: options = {"fontsize": 14, "color": "b", "marker":'o', "linewidth":0, "figsize": (12, 15)})
        :return: None
        """
        self.qm = quantum_machine
        self._check_plot_options(plot_options)

        for calib in self.calibration_list:
            print(f"The calibration: {calib} is in progress...")
            if calib == "Rabi":
                self._rabi(
                    scan_dimension=len(self.scan_var[calib]) - 1,
                    plot=plot,
                    fits=fits,
                )
            elif calib == "T1":
                self._T1(
                    scan_dimension=len(self.scan_var[calib]) - 1,
                    plot=plot,
                    fits=fits,
                )
            elif calib == "Ramsey":
                self._ramsey(
                    scan_dimension=len(self.scan_var[calib]) - 1,
                    plot=plot,
                    fits=fits,
                )
            elif calib == "Resonator_spec":
                self._resonator_spec(
                    scan_dimension=len(self.scan_var[calib]) - 1,
                    plot=plot,
                    fits=fits,
                )
            elif calib == "raw_traces":
                self._raw_traces(plot=plot)
            elif calib == "time_of_flight":
                self._time_of_flight(plot=plot)

    def simulate_calibrations(self, machine, simulation_duration):
        """Simulate the implemented calibrations.

        :param machine: either a QuantumMachine or a QuantumMachinesManager instance that will be used to run the simulation.
        :param simulation_duration: duration of the simulation in clock cycle unit (4ns)
        :return: None
        """
        self.simulation = True
        for calib in self.calibration_list:
            prog = None
            if calib == "Rabi":
                prog = self._rabi(scan_dimension=len(self.scan_var[calib]) - 1)
            if calib == "T1":
                prog = self._T1(scan_dimension=len(self.scan_var[calib]) - 1)
            elif calib == "Ramsey":
                prog = self._ramsey(scan_dimension=len(self.scan_var[calib]) - 1)
            elif calib == "Resonator_spec":
                prog = self._resonator_spec(scan_dimension=len(self.scan_var[calib]) - 1)
            elif calib == "raw_traces":
                prog = self._raw_traces()
            elif calib == "time_of_flight":
                prog = self._time_of_flight()

            simulation_config = SimulationConfig(duration=int(simulation_duration))
            if isinstance(machine, QuantumMachinesManager):
                job = machine.simulate(self.config, prog, simulation_config)
            elif isinstance(machine, QuantumMachine):
                job = machine.simulate(prog, simulation_config)
            else:
                raise Exception("'machine' must be either a QuantumMachine or a QuantumMachinesManager instance.")
            plt.figure()
            job.get_simulated_samples().con1.plot()
        self.simulation = False

    def _resonator_spec(self, scan_dimension, plot=False, fits=False):
        calib = "Resonator_spec"
        if scan_dimension == 1:
            with program() as resonator_spec_1D:
                # Get the QUA variables for the 2D scan + averaging
                n, var1, var1_scan, var1_name = self._get_qua_variables(calib)
                if var1_name == "amplitude" and self.flux_line_elmt is None:
                    raise Exception(
                        "Amplitude scan of the resonator spectroscopy is only implemented for flux tunable transmons so please provide the flux line element."
                    )
                elif var1_name != "frequency" or (var1_name == "amplitude" and self.flux_line_elmt is None):
                    raise Exception("Resonator spectroscopy is only implemented for frequency scan.")

                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                n_st = declare_stream()

                with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                    with for_(*from_array(var1, var1_scan)):
                        if self.flux_line_elmt is not None:
                            if var1_name == "amplitude":
                                play(self.flux_line_op * amp(var1), self.flux_line_elmt)
                            else:
                                play(self.flux_line_op, self.flux_line_elmt)
                        # Update the resonator frequency
                        if var1_name == "frequency":
                            update_frequency(self.readout_elmt, var1)
                        # Align, measure and save data
                        self._align_measure_save(I, Q, I_st, Q_st, calib, align_flag=False)
                    save(n, n_st)

                with stream_processing():
                    I_st.buffer(len(var1_scan)).average().save("I")
                    Q_st.buffer(len(var1_scan)).average().save("Q")
                    n_st.save("iteration")

            if self.simulation:
                return resonator_spec_1D
            job = self.qm.execute(resonator_spec_1D)

            self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

        elif scan_dimension == 2:
            if self.flux_line_elmt is None:
                raise Exception(
                    "2D scan with 'amplitude' or 'duration' for the resonator spectroscopy is only implemented for flux tunable transmons so please provide the flux line element."
                )
            with program() as resonator_spec_2D:
                # Get the QUA variables for the 2D scan + averaging
                (
                    n,
                    var1,
                    var1_scan,
                    var1_name,
                    var2,
                    var2_scan,
                    var2_name,
                ) = self._get_qua_variables(calib)

                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                n_st = declare_stream()
                with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                    with for_(*from_array(var2, var2_scan)):
                        with for_(*from_array(var1, var1_scan)):
                            if var1_name == "amplitude":
                                play(self.flux_line_op * amp(var1), self.flux_line_elmt)
                            elif var2_name == "amplitude":
                                play(self.flux_line_op * amp(var2), self.flux_line_elmt)
                            else:
                                play(self.flux_line_op, self.flux_line_elmt)

                            # Update the resonator frequency
                            if var1_name == "frequency":
                                update_frequency(self.readout_elmt, var1)
                            elif var2_name == "frequency":
                                update_frequency(self.readout_elmt, var2)
                            # Align, measure and save data
                            self._align_measure_save(I, Q, I_st, Q_st, calib, align_flag=False)
                    save(n, n_st)

                with stream_processing():
                    I_st.buffer(len(var1_scan)).buffer(len(var2_scan)).average().save("I")
                    Q_st.buffer(len(var1_scan)).buffer(len(var2_scan)).average().save("Q")
                    n_st.save("iteration")

            if self.simulation:
                return resonator_spec_2D
            job = self.qm.execute(resonator_spec_2D)
            self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

    def _rabi(self, scan_dimension, plot=False, fits=False):
        calib = "Rabi"
        if scan_dimension == 1:
            with program() as prog_rabi_1D:
                # Get the QUA variables for the 2D scan + averaging
                n, var1, var1_scan, var1_name = self._get_qua_variables(calib)
                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                n_st = declare_stream()

                with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                    with for_(*from_array(var1, var1_scan)):

                        # Update the resonator frequency
                        if var1_name == "frequency":
                            update_frequency(self.qubit_elmt, var1)
                        # Adjust the pulse amplitude and/or duration
                        if var1_name == "amplitude":
                            play(self.qubit_op * amp(var1), self.qubit_elmt)
                        elif var1_name == "duration":
                            play(self.qubit_op, self.qubit_elmt, duration=var1)
                        # Align, measure and save data
                        self._align_measure_save(I, Q, I_st, Q_st, calib)
                    save(n, n_st)

                with stream_processing():
                    I_st.buffer(len(var1_scan)).average().save("I")
                    Q_st.buffer(len(var1_scan)).average().save("Q")
                    n_st.save("iteration")

            if self.simulation:
                return prog_rabi_1D
            job = self.qm.execute(prog_rabi_1D)

            self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

        elif scan_dimension == 2:
            with program() as prog_rabi_2D:
                # Get the QUA variables for the 2D scan + averaging
                (
                    n,
                    var1,
                    var1_scan,
                    var1_name,
                    var2,
                    var2_scan,
                    var2_name,
                ) = self._get_qua_variables(calib)

                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                n_st = declare_stream()
                with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                    with for_(*from_array(var2, var2_scan)):
                        with for_(*from_array(var1, var1_scan)):
                            # Update the resonator frequency
                            if var1_name == "frequency":
                                update_frequency(self.qubit_elmt, var1)
                            elif var2_name == "frequency":
                                update_frequency(self.qubit_elmt, var2)

                            # Adjust the pulse amplitude and/or duration
                            if var1_name == "amplitude":
                                if var2_name == "duration":
                                    play(
                                        self.qubit_op * amp(var1),
                                        self.qubit_elmt,
                                        duration=var2,
                                    )
                                else:
                                    play(self.qubit_op * amp(var1), self.qubit_elmt)
                            elif var2_name == "amplitude":
                                if var1_name == "duration":
                                    play(
                                        self.qubit_op * amp(var2),
                                        self.qubit_elmt,
                                        duration=var1,
                                    )
                                else:
                                    play(self.qubit_op * amp(var2), self.qubit_elmt)
                            else:
                                if var1_name == "duration":
                                    play(self.qubit_op, self.qubit_elmt, duration=var1)
                                else:
                                    play(self.qubit_op, self.qubit_elmt, duration=var2)

                            # Align, measure and save data
                            self._align_measure_save(I, Q, I_st, Q_st, calib)
                    save(n, n_st)

                with stream_processing():
                    I_st.buffer(len(var1_scan)).buffer(len(var2_scan)).average().save("I")
                    Q_st.buffer(len(var1_scan)).buffer(len(var2_scan)).average().save("Q")
                    n_st.save("iteration")

            if self.simulation:
                return prog_rabi_2D
            job = self.qm.execute(prog_rabi_2D)

            self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

    def _T1(self, scan_dimension, plot=False, fits=False):
        calib = "T1"
        with program() as prog_T1:
            # Get the QUA variables for the 2D scan + averaging
            n, var1, var1_scan, var1_name = self._get_qua_variables(calib)
            I = declare(fixed)
            Q = declare(fixed)
            I_st = declare_stream()
            Q_st = declare_stream()
            n_st = declare_stream()

            with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                with for_(*from_array(var1, var1_scan)):
                    # Play pi pulse
                    play(self.qubit_op, self.qubit_elmt)
                    align(self.qubit_elmt, self.readout_elmt)
                    # scan wait duration
                    wait(var1, self.readout_elmt)
                    # Align, measure and save data
                    self._align_measure_save(I, Q, I_st, Q_st, calib)
                save(n, n_st)

            with stream_processing():
                I_st.buffer(len(var1_scan)).average().save("I")
                Q_st.buffer(len(var1_scan)).average().save("Q")
                n_st.save("iteration")

        if self.simulation:
            return prog_T1
        job = self.qm.execute(prog_T1)

        self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

    def _ramsey(self, scan_dimension, plot=False, fits=False):
        calib = "Ramsey"
        if scan_dimension == 1:
            with program() as prog_ramsey_1D:
                # Get the QUA variables for the 2D scan + averaging
                n, var1, var1_scan, var1_name = self._get_qua_variables(calib)
                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                n_st = declare_stream()

                with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                    with for_(*from_array(var1, var1_scan)):
                        # Update the resonator frequency
                        if var1_name == "frequency":
                            update_frequency(self.qubit_elmt, var1)
                        # First pi/2 pulse
                        play(self.qubit_op, self.qubit_elmt)
                        # Adjust the idle time
                        if var1_name == "duration":
                            wait(var1, self.qubit_elmt)
                        elif self.user_specifics[calib]["idle_time"] is not None:
                            wait(self.user_specifics[calib]["idle_time"], self.qubit_elmt)
                        # Second pi/2 pulse
                        play(self.qubit_op, self.qubit_elmt)
                        # Align, measure and save data
                        self._align_measure_save(I, Q, I_st, Q_st, calib)
                    save(n, n_st)

                with stream_processing():
                    I_st.buffer(len(var1_scan)).average().save("I")
                    Q_st.buffer(len(var1_scan)).average().save("Q")
                    n_st.save("iteration")

            if self.simulation:
                return prog_ramsey_1D
            job = self.qm.execute(prog_ramsey_1D)

            self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

        elif scan_dimension == 2:
            with program() as prog_ramsey_2D:

                # Get the QUA variables for the 2D scan + averaging
                (
                    n,
                    var1,
                    var1_scan,
                    var1_name,
                    var2,
                    var2_scan,
                    var2_name,
                ) = self._get_qua_variables(calib)

                I = declare(fixed)
                Q = declare(fixed)
                I_st = declare_stream()
                Q_st = declare_stream()
                n_st = declare_stream()

                with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                    with for_(*from_array(var2, var2_scan)):
                        with for_(*from_array(var1, var1_scan)):
                            # Update the resonator frequency
                            if var1_name == "frequency":
                                update_frequency(self.qubit_elmt, var1)
                            elif var2_name == "frequency":
                                update_frequency(self.qubit_elmt, var2)
                            # First pi/2 pulse
                            play(self.qubit_op, self.qubit_elmt)
                            # Adjust the idle time
                            if var1_name == "duration":
                                wait(var1, self.qubit_elmt)
                            elif var2_name == "duration":
                                wait(var2, self.qubit_elmt)
                            elif self.user_specifics[calib]["idle_time"] is not None:
                                wait(
                                    self.user_specifics[calib]["idle_time"],
                                    self.qubit_elmt,
                                )
                            # Second pi/2 pulse
                            play(self.qubit_op, self.qubit_elmt)

                            # Align, measure and save data
                            self._align_measure_save(I, Q, I_st, Q_st, calib)
                    save(n, n_st)

                with stream_processing():
                    I_st.buffer(len(var1_scan)).buffer(len(var2_scan)).average().save("I")
                    Q_st.buffer(len(var1_scan)).buffer(len(var2_scan)).average().save("Q")
                    n_st.save("iteration")

            if self.simulation:
                return prog_ramsey_2D
            job = self.qm.execute(prog_ramsey_2D)

            self._get_IQ_data_and_plot(job, calib, plot, scan_dimension)

    def _raw_traces(self, plot=False):
        calib = "raw_traces"
        with program() as raw_trace_prog:
            n = declare(int)
            adc_st = declare_stream(adc_trace=True)

            with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                reset_phase(self.readout_elmt)
                measure(self.readout_op, self.readout_elmt, adc_st)
                if self.user_specifics[calib]["cooldown_time"] is not None:
                    wait(
                        int(self.user_specifics[calib]["cooldown_time"]),
                        self.readout_elmt,
                    )

            with stream_processing():
                # Will save average:
                adc_st.input1().average().save("adc1")
                adc_st.input2().average().save("adc2")
                # Will save only last run:
                adc_st.input1().save("adc1_single_run")
                adc_st.input2().save("adc2_single_run")

        if self.simulation:
            return raw_trace_prog
        job = self.qm.execute(raw_trace_prog)

        res_handles = job.result_handles

        if plot == "live":
            adc1_handles = res_handles.get("adc1_single_run")
            adc2_handles = res_handles.get("adc2_single_run")
            adc1_av_handles = res_handles.get("adc1")
            adc2_av_handles = res_handles.get("adc2")
            adc1_handles.wait_for_values(1)
            adc2_handles.wait_for_values(1)
            adc1_av_handles.wait_for_values(1)
            adc2_av_handles.wait_for_values(1)

            # Live plotting
            fig = plt.figure(figsize=self.plot_options["figsize"])
            interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
            while res_handles.is_processing():
                adc1 = u.raw2volts(res_handles.get("adc1").fetch_all())
                adc2 = u.raw2volts(res_handles.get("adc2").fetch_all())
                adc1_single_run = u.raw2volts(res_handles.get("adc1_single_run").fetch_all())
                adc2_single_run = u.raw2volts(res_handles.get("adc2_single_run").fetch_all())

                self.results[calib]["adc1"] = {"raw": adc1_single_run, "averaged": adc1}
                self.results[calib]["adc2"] = {"raw": adc2_single_run, "averaged": adc2}

                plt.subplot(121)
                plt.cla()
                plt.title(
                    "Single run (Check ADCs saturation)",
                    fontsize=self.plot_options["fontsize"] + 2,
                )
                plt.plot(adc1_single_run, "b")
                plt.plot(adc2_single_run, "r")
                plt.xlabel("Time [ns]", fontsize=self.plot_options["fontsize"])
                plt.ylabel("Signal amplitude [V]", fontsize=self.plot_options["fontsize"])
                plt.subplot(122)
                plt.cla()
                plt.title("Averaged run", fontsize=self.plot_options["fontsize"] + 2)
                plt.plot(adc1, "b")
                plt.plot(adc2, "r")
                plt.xlabel("Time [ns]", fontsize=self.plot_options["fontsize"])
                plt.ylabel("Signal amplitude [V]", fontsize=self.plot_options["fontsize"])
                plt.pause(0.01)
        else:
            res_handles.wait_for_all_values()
            adc1 = u.raw2volts(res_handles.get("adc1").fetch_all())
            adc2 = u.raw2volts(res_handles.get("adc2").fetch_all())
            adc1_single_run = u.raw2volts(res_handles.get("adc1_single_run").fetch_all())
            adc2_single_run = u.raw2volts(res_handles.get("adc2_single_run").fetch_all())

            self.results[calib]["adc1"] = {"raw": adc1_single_run, "averaged": adc1}
            self.results[calib]["adc2"] = {"raw": adc2_single_run, "averaged": adc2}

            if plot == "full":
                plt.figure(figsize=self.plot_options["figsize"])
                plt.subplot(121)
                plt.title(
                    "Single run (Check ADCs saturation)",
                    fontsize=self.plot_options["fontsize"] + 2,
                )
                plt.plot(adc1_single_run, "b")
                plt.plot(adc2_single_run, "r")
                plt.xlabel("Time [ns]", fontsize=self.plot_options["fontsize"])
                plt.ylabel("Signal amplitude [V]", fontsize=self.plot_options["fontsize"])
                plt.subplot(122)
                plt.title("Averaged run", fontsize=self.plot_options["fontsize"] + 2)
                plt.plot(adc1, "b")
                plt.plot(adc2, "r")
                plt.xlabel("Time [ns]", fontsize=self.plot_options["fontsize"])
                plt.ylabel("Signal amplitude [V]", fontsize=self.plot_options["fontsize"])

    def _time_of_flight(self, plot=False):
        calib = "time_of_flight"
        with program() as tof_prog:
            n = declare(int)
            adc_st = declare_stream(adc_trace=True)
            with for_(n, 0, n < self.scan_var[calib]["averaging"], n + 1):
                reset_phase(self.readout_elmt)
                measure(self.readout_op, self.readout_elmt, adc_st)
                if self.user_specifics[calib]["cooldown_time"] is not None:
                    wait(
                        int(self.user_specifics[calib]["cooldown_time"]),
                        self.readout_elmt,
                    )

            with stream_processing():
                # Will save average:
                if "out1" in self.config["elements"][self.readout_elmt]["outputs"]:
                    adc_st.input1().average().save("adc1")
                if "out2" in self.config["elements"][self.readout_elmt]["outputs"]:
                    adc_st.input2().average().save("adc2")
        if self.simulation:
            return tof_prog
        job = self.qm.execute(tof_prog)

        res_handles = job.result_handles
        if plot == "live":
            raise Exception("Live plotting is not available for time of flight calibration")
        else:
            adc1 = None
            adc2 = None
            tof1 = None
            tof2 = None
            res_handles.wait_for_all_values()
            if "out1" in self.config["elements"][self.readout_elmt]["outputs"]:
                adc1 = u.raw2volts(res_handles.get("adc1").fetch_all())
                self.results[calib]["adc1"] = adc1
                # Find the pulse edge and derive tof
                if len(np.where(np.abs(np.diff(adc1)) > self.user_specifics[calib]["threshold"])[0]) > 0:
                    tof1 = np.min(np.where(np.abs(np.diff(adc1)) > self.user_specifics[calib]["threshold"]))
                    print(f"TOF to add = {tof1} ns for out1")
                else:
                    tof1 = None
                    print("No pulse detected")
            if "out2" in self.config["elements"][self.readout_elmt]["outputs"]:
                adc2 = u.raw2volts(res_handles.get("adc2").fetch_all())
                self.results[calib]["adc2"] = adc2
                # Find the pulse edge and derive tof
                if len(np.where(np.abs(np.diff(adc2)) > self.user_specifics[calib]["threshold"])[0]) > 0:
                    tof2 = np.min(np.where(np.abs(np.diff(adc2)) > self.user_specifics[calib]["threshold"]))
                    print(f"TOF to add = {tof2} ns for out2")
                else:
                    tof2 = None
                    print("No pulse detected")

            if plot == "full":
                plt.figure(figsize=self.plot_options["figsize"])
                plt.title("Time of flight", fontsize=self.plot_options["fontsize"] + 2)
                if "out1" in self.config["elements"][self.readout_elmt]["outputs"]:
                    plt.plot(
                        adc1,
                        "b",
                        label=f"TOF to add: {tof1} ns and offset to remove: {np.mean(adc1[:tof1])*1000:.4f} mV",
                    )
                    if tof1 is not None:
                        plt.axvline(x=tof1, color="b", linestyle=":")
                    plt.axhline(y=np.mean(adc1[:tof1]), color="b", linestyle="--")
                if "out2" in self.config["elements"][self.readout_elmt]["outputs"]:
                    plt.plot(
                        adc2,
                        "r",
                        label=f"TOF to add: {tof2} ns and offset to remove: {np.mean(adc2[:tof2])*1000:.4f} mV",
                    )
                    if tof2 is not None:
                        plt.axvline(x=tof2, color="r", linestyle=":")
                    plt.axhline(y=np.mean(adc2[:tof2]), color="r", linestyle="--")
                plt.xlabel("Time [ns]", fontsize=self.plot_options["fontsize"])
                plt.ylabel("Signal amplitude [V]", fontsize=self.plot_options["fontsize"])
                plt.legend()
