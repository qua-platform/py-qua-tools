"""calling function libraries"""

import copy
import math
from time import sleep

import numpy as np
from qm import QuantumMachine
from qm import QmJob
from qm import QuantumMachinesManager
from qm.qua import *


def _round_to_fixed_point_accuracy(x, accuracy=2**-16):
    return round(x / accuracy) * accuracy


def _floor_to_fixed_point_accuracy(x, accuracy=2**-16):
    return math.floor(x / accuracy) * accuracy


class ManualOutputControl:
    """
    Creates a control panel to turn on and off the analog and digital channels of the OPX.
    """

    def __init__(
        self,
        configuration,
        host=None,
        port=None,
        close_previous=True,
        elements_to_control=None,
    ):
        """
        Gets a QUA configuration file and creates different Quantum Machines. One QM continuously runs all the
        analog ports and the rest continuously runs all the digital ports. This enables controlling the amplitude and
        frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude, but with the frequency
        from the configuration.

        :param configuration: A configuration file containing the elements to control.
        :param str host: The host or IP of the QOP. Defaults to `None`: local settings are used.
        :param str port: The port used to access the QOP. Defaults to `None`, local settings are used.
        :param bool close_previous: Close currently running Quantum Machines. Note that if False, and a Quantum Machine
                                    which uses the same ports is already open, then this function would fail.
        :param array-like elements_to_control: A list of elements to be controlled.
                                    If empty, all elements in the config are included.
        """
        self.qmm = QuantumMachinesManager(host=host, port=port)
        if close_previous:
            self.qmm.close_all_quantum_machines()
        self.analog_config = None
        self.digital_configs = None
        self.analog_elements = []
        self.digital_elements = []
        self.digital_index = {}
        self.analog_data = {}
        self.digital_data = {}
        self.analog_job = None
        self.digital_jobs = None
        self.ANALOG_WAVEFORM_AMPLITUDE = 0.5 - 2**-16
        self._process_config(configuration, elements_to_control)
        self.analog_qm = self.qmm.open_qm(self.analog_config, False)
        self._start_digital_qms()
        self._start_analog()

    @classmethod
    def ports(
        cls,
        analog_ports=None,
        digital_ports=None,
        host=None,
        port=None,
        close_previous=True,
    ):
        """
        Gets a list of analog and digital channels and creates different Quantum Machines. One QM continuously runs all
        the analog ports and the rest continuously runs all the digital ports. This enables controlling the amplitude
        and frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude and zero frequency.

        :param list analog_ports: The list of analog ports to control. A tuple creates an IQ pair.
            For example, [1, 2, (3, 4)] creates two independent channels at ports 1 & 2, and one IQ pair at ports 3 & 4.
            For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
        :param list digital_ports: The list of digital ports to control.
            For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
        :param str host: The host or IP of the QOP. Defaults to `None`: local settings are used.
        :param str port: The port used to access the QOP. Defaults to `None`, local settings are used.
        :param bool close_previous: Close currently running Quantum Machines. Note that if False, and a Quantum Machine
                                    which uses the same ports is already open, then this function would fail.
        """
        if analog_ports is None and digital_ports is None:
            raise Exception("No ports specified")
        config = {"version": 1, "controllers": {}, "elements": {}}
        if analog_ports is not None:
            for port_int in analog_ports:
                if isinstance(port_int, tuple):
                    if len(port_int) == 2:
                        con_number = (port_int[0] - 1) // 10 + 1
                        if con_number is not (port_int[1] - 1) // 10 + 1:
                            raise Exception(f"Ports {port_int[0]} and {port_int[1]} are not from the same controller")
                    else:
                        raise Exception(f"Port {port_int} should be either an integer or a tuple of two integers")
                else:
                    con_number = (port_int - 1) // 10 + 1
                con = f"con{con_number}"
                if con not in config["controllers"]:
                    config["controllers"][con] = {
                        "type": "opx1",
                        "analog_outputs": {},
                        "digital_outputs": {},
                    }

                if isinstance(port_int, tuple):
                    port_str = str(port_int)
                    port1 = (port_int[0] - 1) % 10 + 1
                    port2 = (port_int[1] - 1) % 10 + 1
                    if port1 not in config["controllers"][con]["analog_outputs"]:
                        config["controllers"][con]["analog_outputs"][port1] = {"offset": 0.0}
                    if port2 not in config["controllers"][con]["analog_outputs"]:
                        config["controllers"][con]["analog_outputs"][port2] = {"offset": 0.0}
                    if port_str not in config["elements"]:
                        config["elements"][port_str] = {
                            "mixInputs": {
                                "I": (con, port1),
                                "Q": (con, port2),
                            },
                            "intermediate_frequency": 0e6,
                        }
                else:
                    port_str = str(port_int)
                    port_int = (port_int - 1) % 10 + 1
                    if port_int not in config["controllers"][con]["analog_outputs"]:
                        config["controllers"][con]["analog_outputs"][port_int] = {"offset": 0.0}
                    if port_str not in config["elements"]:
                        config["elements"][port_str] = {
                            "singleInput": {
                                "port": (con, port_int),
                            },
                            "intermediate_frequency": 0e6,
                        }

        if digital_ports is not None:
            for port_int in digital_ports:
                con_number = (port_int - 1) // 10 + 1
                port_str = str(port_int)
                port_int = (port_int - 1) % 10 + 1
                con = f"con{con_number}"
                if con not in config["controllers"]:
                    config["controllers"][con] = {
                        "type": "opx1",
                        "analog_outputs": {},
                        "digital_outputs": {},
                    }
                if port_int not in config["controllers"][con]["digital_outputs"]:
                    config["controllers"][con]["digital_outputs"][port_int] = {}
                if port_str not in config["elements"]:
                    config["elements"][port_str] = {
                        "digitalInputs": {
                            "input": {
                                "port": (con, port_int),
                                "delay": 0,
                                "buffer": 0,
                            }
                        }
                    }
                else:
                    config["elements"][port_str]["digitalInputs"] = {
                        "input": {
                            "port": (con, port_int),
                            "delay": 0,
                            "buffer": 0,
                        }
                    }

        return cls(
            config,
            host=host,
            port=port,
            close_previous=close_previous,
            elements_to_control=None,
        )

    def turn_on_element(self, element, amplitude=None, frequency=None):
        """
        Turns on the digital and analog output of a given element.
        If no amplitude is given, uses maximum amplitude.
        If no frequency is given, uses existing frequency.

        :param element: An element to be turned on.
        :param amplitude:The amplitude of the analog output of the element.
        :param frequency: The frequency of the analog output of the element.
        """
        if not isinstance(element, str):
            element = str(element)
        if element not in self.digital_elements and element not in self.analog_elements:
            raise Exception(f"Element {element} is not part of the elements in the configuration files")
        if amplitude is None:
            amplitude = self.ANALOG_WAVEFORM_AMPLITUDE
        if frequency is not None:
            self.set_frequency(element, frequency, ignore_missing_elements=True)
        self.set_amplitude(element, amplitude, ignore_missing_elements=True)
        self.digital_on(element, ignore_missing_elements=True)

    def turn_off_elements(self, *elements):
        """
        Turns off the digital and analog for all the given elements.
        If no elements are given, turns off all elements.

        :param elements: A variable number of elements to be turned off.
        """
        if not len(elements) == 0:
            for element in elements:
                if not isinstance(element, str):
                    element = str(element)
                if element not in self.digital_elements and element not in self.analog_elements:
                    raise Exception(f"Element {element} is not part of the elements in the configuration files")
        self.digital_off(*elements, ignore_missing_elements=True)
        if len(elements) == 0:
            elements = self.analog_elements
        for element in elements:
            self.set_amplitude(element, 0, ignore_missing_elements=True)

    def set_amplitude(self, element, value, ignore_missing_elements=False):
        """
        Sets the amplitude of an analog element.

        :param str element: The name of the analog element to be updated
        :param float value: The new amplitude of the analog element
        :param bool ignore_missing_elements: If false (default), throws an error if the element is not found.
            If false, simply returns the function.
        """
        if not isinstance(element, str):
            element = str(element)
        if element not in self.analog_elements:
            if ignore_missing_elements:
                return
            else:
                raise Exception(f"Element {element} is not part of the elements in the analog configuration file")
        if abs(value) > self.ANALOG_WAVEFORM_AMPLITUDE:
            if value == 0.5:
                value = 0.5 - 2**-16
            elif value == -0.5:
                value = -0.5 + 2**-16
            else:
                raise Exception(f"The absolute value of the amplitude must smaller than 0.5, {value} was given")

        prev_value = self.analog_data[element]["amplitude"]
        delta_value = (value - prev_value) * (1 / self.ANALOG_WAVEFORM_AMPLITUDE)
        delta_value = _round_to_fixed_point_accuracy(delta_value)
        if delta_value == 0:
            return
        self.analog_data[element]["amplitude"] = _floor_to_fixed_point_accuracy(
            prev_value + delta_value * self.ANALOG_WAVEFORM_AMPLITUDE
        )

        while not self.analog_job.is_paused():
            sleep(0.01)

        self.analog_qm.set_io_values(
            int(self.analog_elements.index(element)) + len(self.analog_elements),
            float(delta_value),
        )
        self.analog_job.resume()

    def set_frequency(self, element, value, ignore_missing_elements=False):
        """
        Sets the frequency of an analog element.

        :param str element: the name of the analog element to be updated
        :param int value: the new frequency of the analog element
        :param bool ignore_missing_elements: If false (default), throws an error if the element is not found.
            If false, simply returns the function.
        """
        if not isinstance(element, str):
            element = str(element)
        if element not in self.analog_elements:
            if ignore_missing_elements:
                return
            else:
                raise Exception(f"Element {element} is not part of the elements in the analog configuration file")
        if int(value) > int(500e6):
            raise Exception(f"The frequency should be lower than 500e6, {value} was given")
        self.analog_data[element]["frequency"] = value
        while not self.analog_job.is_paused():
            sleep(0.01)
        self.analog_qm.set_io_values(int(self.analog_elements.index(element)), int(value))
        self.analog_job.resume()

    def digital_on(self, *digital_elements, ignore_missing_elements=False):
        """
        Turns on all digital elements inputted by the user.
        If no input is given, turns on all elements.

        :param digital_elements: A variable number of elements to be turned on.
        :param bool ignore_missing_elements: If false (default), throws an error if the element is not found.
            If false, simply returns the function.
        """
        if len(digital_elements) == 0:
            digital_elements = self.digital_elements
        for element in digital_elements:
            if not isinstance(element, str):
                element = str(element)
            if element not in self.digital_elements:
                if ignore_missing_elements:
                    return
                else:
                    raise Exception(f"Element {element} is not part of the elements in the digital configuration file")
            self.digital_data[element] = True
        self._start_digital()

    def digital_off(self, *digital_elements, ignore_missing_elements=False):
        """
        Turns off all digital elements inputted by the user.
        If no input is given, turns off all elements.

        :param digital_elements: A variable number of elements to be turned off.
        :param bool ignore_missing_elements: If false (default), throws an error if the element is not found.
            If false, simply returns the function.
        """
        if len(digital_elements) == 0:
            digital_elements = self.digital_elements
        for element in digital_elements:
            if not isinstance(element, str):
                element = str(element)
            if element not in self.digital_elements:
                if ignore_missing_elements:
                    return
                else:
                    raise Exception(f"Element {element} is not part of the elements in the digital configuration file")
            self.digital_data[element] = False
        self._start_digital()

    def digital_switch(self, *digital_element):
        """
        Switches the state of the given digital elements from on to off, and from off to on.

        :param digital_element: A variable number of elements to be switched.
        """
        if len(digital_element) == 0:
            return
        for element in digital_element:
            if not isinstance(element, str):
                element = str(element)
            if element not in self.digital_elements:
                raise Exception(f"Element {element} is not part of the elements in the digital configuration file")
            self.digital_data[element] = not self.digital_data[element]
        self._start_digital()

    def analog_status(self):
        """
        Returns a dictionary of the analog elements, with their current amplitude and frequency.
        """
        return self.analog_data

    def digital_status(self):
        """
        Returns a dictionary of the digital elements, with their current status.
        """
        return self.digital_data

    def print_analog_status(self):
        """
        Prints a list of the analog elements, with their current amplitude and frequency.
        """
        for element in self.analog_elements:
            print(
                element
                + " - Amplitude: "
                + str(self.analog_data[element]["amplitude"])
                + ", Frequency: "
                + str(self.analog_data[element]["frequency"])
            )

    def print_digital_status(self):
        """
        Prints a list of the digital elements, with a True (False) to indicate the element is on (off).
        """
        for element in self.digital_elements:
            print(element + " - " + str(self.digital_data[element]))

    def close(self):
        """
        Halts all jobs sent to the OPX and then closes the quantum machine.
        """
        for con_jobs in self.digital_jobs:
            for job in con_jobs:
                if job is not None:
                    job.halt()
        for con_qms in self.digital_qms:
            for qm in con_qms:
                if qm is not None:
                    qm.close()
        self.analog_job.halt()
        self.analog_qm.close()
        self.qmm.close()

    def _process_config(self, config_original, elements_to_control=None):
        """
        This function creates multiple separate configuration files, on containing only analog elements, and the others
        only contains digital elements.

        :param config_original: a QUA configuration dictionary which contain all defined analog and digital elements.
        :param elements_to_control: A list of elements to be controlled.
                                    If empty, all elements in the config are included.
        """
        config = copy.deepcopy(config_original)
        self.analog_config = {}
        digital_config = {}
        pulser_count = {}

        highest_con = 0
        for con in list(config["controllers"].keys()):
            highest_con = int(con[-1]) if int(con[-1]) > highest_con else highest_con
        self.digital_configs = np.empty((highest_con, 10), dtype=dict)
        self.digital_jobs = np.empty((highest_con, 10), dtype=QmJob)
        self.digital_qms = np.empty((highest_con, 10), dtype=QuantumMachine)

        # Analog config
        self.analog_config["version"] = 1
        self.analog_config["controllers"] = {}
        for controller in list(config["controllers"].keys()):
            self.analog_config["controllers"][controller] = {
                "type": "opx1",
                "analog_outputs": {},
            }
            self.analog_config["controllers"][controller]["analog_outputs"] = config["controllers"][controller][
                "analog_outputs"
            ]
            pulser_count[controller] = 0
        self.analog_config["elements"] = {}
        self.analog_config["waveforms"] = {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": self.ANALOG_WAVEFORM_AMPLITUDE},
        }
        self.analog_config["pulses"] = {}
        self.analog_config["pulses"]["single_on"] = {
            "operation": "control",
            "length": 16,
            "waveforms": {"single": "const_wf"},
        }
        self.analog_config["pulses"]["IQ_Ion"] = {
            "operation": "control",
            "length": 16,
            "waveforms": {"I": "const_wf", "Q": "zero_wf"},
        }
        if config.get("mixers") is not None:
            self.analog_config["mixers"] = config["mixers"]

        # Digital config
        digital_config["version"] = 1
        digital_config["controllers"] = {}
        digital_config["elements"] = {}
        digital_config["pulses"] = {
            "digital_ON": {
                "digital_marker": "ON",
                "length": 1000,
                "operation": "control",
            }
        }
        digital_config["digital_waveforms"] = {"ON": {"samples": [(1, 0)]}}

        # Elements
        if elements_to_control is None:
            elements = list(config["elements"].keys())
        else:
            elements = elements_to_control
        # Digital
        for element in elements:
            if config["elements"][element].get("digitalInputs") is not None:
                self.digital_index[element] = []
                self.digital_data[element] = False
                self.digital_elements.append(element)
                for digital_input in config["elements"][element]["digitalInputs"]:
                    con, port = config["elements"][element]["digitalInputs"][digital_input]["port"]
                    con_int_index = int(con[-1]) - 1
                    port_index = port - 1
                    self.digital_index[element].append((con_int_index, port_index))
                    if self.digital_configs[con_int_index][port_index] is None:
                        pulser_count[con] += 1
                        self.digital_configs[con_int_index][port_index] = copy.deepcopy(digital_config)
                        self.digital_configs[con_int_index][port_index]["controllers"][con] = {
                            "type": "opx1",
                            "digital_outputs": {port: {}},
                        }
                        self.digital_configs[con_int_index][port_index]["elements"]["digital"] = {
                            "operations": {"ON": "digital_ON"}
                        }
                        self.digital_configs[con_int_index][port_index]["elements"]["digital"]["digitalInputs"] = {
                            "digital": {
                                "port": (con, port),
                                "delay": 0,
                                "buffer": 0,
                            },
                        }
        # Analog
        for element in elements:
            if config["elements"][element].get("mixInputs") is not None:
                con = config["elements"][element]["mixInputs"]["I"][0]
                pulser_count[con] += 2
                self.analog_config["elements"][element] = config["elements"][element]
                if self.analog_config["elements"][element].get("digitalInputs") is not None:
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                if self.analog_config["elements"][element].get("operations") is not None:
                    self.analog_config["elements"][element].pop("operations")
                self.analog_config["elements"][element]["operations"] = {"play": "IQ_Ion"}
                self.analog_elements.append(element)

            elif config["elements"][element].get("singleInput") is not None:
                con = config["elements"][element]["singleInput"]["port"][0]
                pulser_count[con] += 1
                self.analog_config["elements"][element] = config["elements"][element]
                if self.analog_config["elements"][element].get("digitalInputs") is not None:
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                if self.analog_config["elements"][element].get("operations") is not None:
                    self.analog_config["elements"][element].pop("operations")
                self.analog_config["elements"][element]["operations"] = {"play": "single_on"}
                self.analog_elements.append(element)
        for element in self.analog_elements:
            self.analog_config["elements"][element]["hold_offset"] = {"duration": 16}
            self.analog_data[element] = {
                "amplitude": 0,
                "frequency": self.analog_config["elements"][element].get("intermediate_frequency"),
            }

        opx_plus = True if self.qmm.version()["server"][0] == "2" else False
        for con in list(config["controllers"].keys()):
            if opx_plus and pulser_count[con] > 18:
                raise Exception(
                    f"Given configuration requires {pulser_count[con]} threads in {con}, but only {18} are available"
                )
            elif not opx_plus and pulser_count[con] > 10:
                raise Exception(
                    f"Given configuration requires {pulser_count[con]} threads in {con}, but only {10} are available"
                )

    def _start_analog(self):
        """
        Creates and starts QUA program that initialize the analog elements at 0 amplitude and awaits IO variables to
        update the amplitude and frequency of each element
        """

        with program() as prog:
            io_var1 = declare(int)
            for element in self.analog_elements:
                play("play" * amp(0), element)
            with infinite_loop_():
                pause()
                assign(io_var1, IO1)
                self._QUA_update_freq_or_amp(io_var1, IO2)

        self.analog_job = self.analog_qm.execute(prog)

    def _start_digital_qms(self):
        """
        Opens up multiple Quantum Machines to control the digital outputs
        """
        for con_port_list in self.digital_index.values():
            for con, port in con_port_list:
                if self.digital_qms[con][port] is None:
                    self.digital_qms[con][port] = self.qmm.open_qm(self.digital_configs[con][port], False)

    def _start_digital(self):
        """
        Creates and starts QUA program that is used to run the digital elements in an infinite loop.
        """
        with program() as prog:
            save(1, "a")
            with infinite_loop_():
                play("ON", "digital")
        digital_on = []

        # Create a list of ports that needs to be on
        for element in self.digital_elements:
            for con, port in self.digital_index[element]:
                if self.digital_data[element]:  # Needs to be on
                    digital_on.append((con, port))

        for con_port_list in self.digital_index.values():
            for con, port in con_port_list:
                if (con, port) in digital_on:  # Needs to be on
                    if (  # Is not on
                        self.digital_jobs[con][port] is None
                        or not self.digital_jobs[con][port].result_handles.is_processing()
                    ):
                        self.digital_jobs[con][port] = self.digital_qms[con][port].execute(prog)
                    else:  # Is already on
                        pass
                else:  # Needs to be off
                    if self.digital_jobs[con][port] is not None:
                        self.digital_jobs[con][port].halt()

    def _QUA_update_freq_or_amp(self, input1, input2):
        """
        This function updates the amplitude or frequency of an element

        :param QUA Int input1: Indicates which element to update and whether it is amplitude or frequency using the
        following method: If there are 5 elements: ['a', 'b', 'c', 'd', 'e'], and input1 is '0', then it would change
            the amplitude of the first ('a'). If it input1 is '6', it would change the frequency of the 2nd ('b').
        :param QUA IO input2: The new frequency or delta amplitude to update them element.
        """
        with if_(input1 >= len(self.analog_elements)):
            assign(input1, input1 - len(self.analog_elements))
            a = declare(fixed)
            assign(a, input2)
            with switch_(input1):
                for i in range(len(self.analog_elements)):
                    with case_(i):
                        play("play" * amp(a), self.analog_elements[i])
        with else_():
            freq = declare(int)
            assign(freq, input2)
            with switch_(input1):
                for i in range(len(self.analog_elements)):
                    with case_(i):
                        if (
                            self.analog_config["elements"][self.analog_elements[i]].get("intermediate_frequency")
                            is not None
                        ):
                            update_frequency(self.analog_elements[i], freq)
