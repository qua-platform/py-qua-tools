"""calling function libraries"""
import copy
from time import sleep

import numpy as np
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *


def _round_to_fixed_point_accuracy(x, accuracy=2 ** -16):
    return np.round(x / accuracy) * accuracy


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
        Gets a QUA configuration file and creates two different QuantumMachines. One QM continuously runs all the
        analog ports and one continuously runs all the digital ports. This enables controlling the amplitude and
        frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude, but with the frequency
        from the configuration.

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
        self.digital_config = None
        self.analog_elements = []
        self.digital_elements = []
        self.analog_data = {}
        self.digital_data = []
        self.analog_job = None
        self.digital_job = None
        self.ANALOG_WAVEFORM_AMPLITUDE = 0.5 - 2 ** -16
        self._process_config(configuration, elements_to_control)
        self.analog_qm = self.qmm.open_qm(self.analog_config, False)
        self.digital_qm = self.qmm.open_qm(self.digital_config, False)
        self._start_analog()

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
                        with if_(a == 0):
                            ramp_to_zero(self.analog_elements[i], 1)
                        with else_():
                            play("play" * amp(a), self.analog_elements[i])
        with else_():
            freq = declare(int)
            assign(freq, input2)
            with switch_(input1):
                for i in range(len(self.analog_elements)):
                    with case_(i):
                        if (
                            self.analog_config["elements"][self.analog_elements[i]].get(
                                "intermediate_frequency"
                            )
                            is not None
                        ):
                            update_frequency(self.analog_elements[i], freq)

    def _process_config(self, config_original, elements_to_control=None):
        """
        This function creates two separate configuration files, on containing only analog elements, and the other
        only contains digital elements

        :param config_original: a QUA configuration dictionary which contain all defined analog and digital elements.
        :param elements_to_control: A list of elements to be controlled.
                                    If empty, all elements in the config are included.
        """
        config = copy.deepcopy(config_original)
        self.analog_config = {}
        self.digital_config = {}

        # Analog config
        self.analog_config["version"] = 1
        self.analog_config["controllers"] = {}
        for controller in list(config["controllers"].keys()):
            self.analog_config["controllers"][controller] = {
                "type": "opx1",
                "analog_outputs": {},
            }
            self.analog_config["controllers"][controller]["analog_outputs"] = config[
                "controllers"
            ][controller]["analog_outputs"]
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
        self.digital_config["version"] = 1
        self.digital_config["controllers"] = {}
        for controller in list(config["controllers"].keys()):
            self.digital_config["controllers"][controller] = {
                "type": "opx1",
                "digital_outputs": {},
            }
            self.digital_config["controllers"][controller]["digital_outputs"] = config[
                "controllers"
            ][controller]["digital_outputs"]
        self.digital_config["elements"] = {}
        self.digital_config["pulses"] = {
            "digital_ON": {
                "digital_marker": "ON",
                "length": 1000,
                "operation": "control",
            }
        }
        self.digital_config["digital_waveforms"] = {"ON": {"samples": [(1, 0)]}}

        # Elements
        if elements_to_control is None:
            elements = list(config["elements"].keys())
        else:
            elements = elements_to_control
        for element in elements:
            if config["elements"][element].get("digitalInputs") is not None:
                self.digital_config["elements"][element] = {
                    "operations": {"ON": "digital_ON"}
                }
                self.digital_config["elements"][element]["digitalInputs"] = config[
                    "elements"
                ][element]["digitalInputs"]
        for element in elements:
            if config["elements"][element].get("mixInputs") is not None:
                self.analog_config["elements"][element] = config["elements"][element]
                if (
                    self.analog_config["elements"][element].get("digitalInputs")
                    is not None
                ):
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                self.analog_config["elements"][element].pop("operations")
                self.analog_config["elements"][element]["operations"] = {
                    "play": "IQ_Ion"
                }

            elif config["elements"][element].get("singleInput") is not None:
                self.analog_config["elements"][element] = config["elements"][element]
                if (
                    self.analog_config["elements"][element].get("digitalInputs")
                    is not None
                ):
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                self.analog_config["elements"][element].pop("operations")
                self.analog_config["elements"][element]["operations"] = {
                    "play": "single_on"
                }
        self.analog_elements = list(self.analog_config["elements"].keys())
        self.digital_elements = list(self.digital_config["elements"].keys())
        for element in self.analog_elements:
            self.analog_config["elements"][element]["hold_offset"] = {"duration": 16}
            self.analog_data[element] = {
                "amplitude": 0,
                "frequency": self.analog_config["elements"][element].get(
                    "intermediate_frequency"
                ),
            }
        self.digital_data = [False] * len(self.digital_elements)

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

    def _start_digital(self):
        """
        Creates and starts QUA program that is used to run the digital elements in an infinite loop.
        """
        with program() as prog:
            for i in range(len(self.digital_data)):
                if self.digital_data[i]:
                    with infinite_loop_():
                        play("ON", self.digital_elements[i])
        pending_job = self.digital_qm.queue.add(prog)
        if self.digital_job is not None:
            self.digital_job.halt()
        self.digital_job = pending_job.wait_for_execution()

    def set_amplitude(self, element, value):
        """
        Sets the amplitude of an analog element.

        :param str element: the name of the analog element to be updated
        :param float value: the new amplitude of the analog element
        """
        if element not in self.analog_elements:
            return

        prev_value = self.analog_data[element]["amplitude"]
        self.analog_data[element]["amplitude"] = value
        if value != 0:
            value = (value - prev_value) * (1 / self.ANALOG_WAVEFORM_AMPLITUDE)
            value = _round_to_fixed_point_accuracy(value)
            if value == 0:
                return

        while not self.analog_job.is_paused():
            sleep(0.01)

        self.analog_qm.set_io_values(
            int(self.analog_elements.index(element)) + len(self.analog_elements),
            float(value),
        )
        self.analog_job.resume()

    def set_frequency(self, element, value):
        """
        Sets the frequency of an analog element.

        :param str element: the name of the analog element to be updated
        :param int value: the new frequency of the analog element
        """
        self.analog_data[element]["frequency"] = value
        while not self.analog_job.is_paused():
            sleep(0.01)
        self.analog_qm.set_io_values(
            int(self.analog_elements.index(element)), int(value)
        )
        self.analog_job.resume()

    def digital_status(self):
        """
        Prints a list of the digital elements, with a True (False) to indicate the element is on (off).
        """
        for i in range(len(self.digital_elements)):
            print(self.digital_elements[i] + " - " + str(self.digital_data[i]))

    def digital_switch(self, *digital_element):
        """
        Switches the state of the given digital elements from on to off, and from off to on.

        :param digital_element: A variable number of elements to be switched.
        """
        for element in digital_element:
            self.digital_data[
                self.digital_elements.index(element)
            ] = not self.digital_data[self.digital_elements.index(element)]
        self._start_digital()

    def digital_on(self, *digital_elements):
        """
        Turns on all digital elements inputted by the user.
        If no input is given, turns on all elements.

        :param digital_elements: A variable number of elements to be turned on.
        """
        if len(digital_elements) == 0:
            digital_elements = self.digital_elements
        for element in self.digital_elements:
            if element in digital_elements:
                self.digital_data[self.digital_elements.index(element)] = True
        self._start_digital()

    def digital_off(self, *digital_elements):
        """
        Turns off all digital elements inputted by the user.
        If no input is given, turns off all elements.

        :param digital_elements: A variable number of elements to be turned off.
        """
        if len(digital_elements) == 0:
            digital_elements = self.digital_elements
        for element in self.digital_elements:
            if element in digital_elements:
                self.digital_data[self.digital_elements.index(element)] = False
        self._start_digital()

    def turn_off_elements(self, *elements):
        """
        Turns off the digital and analog for all the given elements.
        If no elements are given, turns off all elements.

        :param elements: A variable number of elements to be turned off.
        """
        self.digital_off(*elements)
        if len(elements) == 0:
            elements = self.analog_elements
        for element in elements:
            self.set_amplitude(element, 0)

    def close(self):
        """
        Halts all jobs sent to the OPX and then closes the quantum machine
        """
        self.digital_job.halt()
        self.analog_job.halt()
        self.analog_qm.close()
        self.digital_qm.close()
        self.qmm.close()
