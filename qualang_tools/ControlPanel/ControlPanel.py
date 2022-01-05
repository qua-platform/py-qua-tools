"""calling function libraries"""
import copy
from time import sleep
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *


class ControlPanel:
    """
    Creates a control panel to turn on and off the analog and digital channels of the OPX.
    Gets a QUA configuration file of both analog and digital elements, create two separate digital and
    analog QUA configurations running in on two different jobs, enabling the user control on the amplitude and frequency
    of a continuously running analog elements, and choose which digital elements will run at the same time, also
    continuously.
    """

    def __init__(
        self, configuration, host=None, port=None, close_previous=False, *digital_on
    ):
        """
        :param str host: Host where to find the QM orchestrator. If ``None``, local settings are used
        :param str port: Port where to find the QM orchestrator. If None, local settings are used
        :param bool close_previous: should previous instances of quantum machine be closed at the initialization.
        :param digital_on: a variable number of digital elements that will be turned on at the initialization.

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
        self._process_config(configuration)
        self.analog_qm = self.qmm.open_qm(self.analog_config, False)
        self.digital_qm = self.qmm.open_qm(self.digital_config, False)
        self._start_analog()
        self.digital_on(digital_on)

    def _QUA_update_freq_or_amp(self, input1, input2):
        """
        This function updates the amplitude or frequency of an element
        :param QUA Int input1: Indicates which element to update and whether it is amplitude or frequency using the
        following method: If there are 5 elements: ['a', 'b', 'c', 'd', 'e'], and input1 is '0', then it would change the
        amplitude of the first ('a'). If it input1 is '6', it would change the frequency of the 2nd ('b').
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
                        update_frequency(self.analog_elements[i], freq)

    def _process_config(self, config_original):
        """
        This function creates two separate configuration files, on containing only analog elements, and the other
        only contains digital elements
        :param config_original: a QUA configuration dictionary which contain all defined analog and digital elements.
        """
        config = copy.deepcopy(config_original)
        self.analog_config = {}
        self.digital_config = {}
        self.analog_config["version"] = 1
        for controller in list(config["controllers"].keys()):
            self.analog_config["controllers"] = {}
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
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        }
        if bool(config.get("mixers")):
            self.analog_config['mixers'] = config['mixers']
        elements = list(config["elements"].keys())
        self.digital_config["version"] = 1
        for controller in list(config["controllers"].keys()):
            self.digital_config["controllers"] = {
                controller: {"type": "opx1", "digital_outputs": {}}
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
        for element in elements:
            if bool(config["elements"][element].get("digitalInputs")):
                self.digital_config["elements"][element] = {
                    "operations": {
                        "ON": "digital_ON",
                    }
                }
                self.digital_config["elements"][element]["digitalInputs"] = config[
                    "elements"
                ][element]["digitalInputs"]

        for i in range(len(elements)):
            if bool(config["elements"][elements[i]].get("mixInputs")):
                self.analog_config["elements"][elements[i]] = config["elements"][
                    elements[i]
                ]
                if bool(
                    self.analog_config["elements"][elements[i]].get("digitalInputs")
                ):
                    self.analog_config["elements"][elements[i]].pop("digitalInputs")
                if bool(self.analog_config["elements"][elements[i]].get("outputs")):
                    self.analog_config["elements"][elements[i]].pop("outputs")
                    self.analog_config["elements"][elements[i]].pop("time_of_flight")
                    self.analog_config["elements"][elements[i]].pop("smearing")
                self.analog_config["elements"][elements[i]].pop("operations")
                self.analog_config["elements"][elements[i]]["operations"] = {
                    "play": "IQ_Ion"
                }

            elif bool(config["elements"][elements[i]].get("singleInput")):
                self.analog_config["elements"][elements[i]] = config["elements"][
                    elements[i]
                ]
                if bool(
                    self.analog_config["elements"][elements[i]].get("digitalInputs")
                ):
                    self.analog_config["elements"][elements[i]].pop("digitalInputs")
                self.analog_config["elements"][elements[i]].pop("operations")
                self.analog_config["elements"][elements[i]]["operations"] = {
                    "play": "single_on"
                }
        self.analog_elements = list(self.analog_config["elements"].keys())
        self.digital_elements = list(self.digital_config["elements"].keys())
        for element in self.analog_elements:
            self.analog_config['elements'][element]['hold_offset'] = {'duration': 16}
            self.analog_data[element] = {
                "amplitude": 0,
                "frequency": self.analog_config["elements"][element][
                    "intermediate_frequency"
                ],
            }
        self.digital_data = [False] * len(self.digital_elements)

    def _start_analog(self):
        """
        A QUA program that initialize the analog elements at 0 amplitude and awaits IO variables, to update the
        amplitude and frequency of each element
        """

        with program() as prog:
            io_var1 = declare(int)
            for i in range(len(self.analog_elements)):
                play("play" * amp(0), self.analog_elements[i])
            with infinite_loop_():
                pause()
                assign(io_var1, IO1)
                self._QUA_update_freq_or_amp(io_var1, IO2)

        self.analog_job = self.analog_qm.execute(prog)

    def _start_digital(self, element_to_turn_on):
        """
        A QUA program that is used to run the digital elements in an infinite loop.
        :param element_to_turn_on: A list containing the digital elements to turn on.
        """
        with program() as prog:
            for i in range(len(element_to_turn_on)):
                if element_to_turn_on[i]:
                    with infinite_loop_():
                        play("ON", self.digital_elements[i])
        pending_job = self.digital_qm.queue.add(prog)
        if self.digital_job is not None:
            self.digital_job.halt()
        self.digital_job = pending_job.wait_for_execution()

    def update_amplitude(self, element, value):
        """
        Ipdates the amplitude of an analog element.
        :param str element: the name of the analog element to be updated
        :param float value: the new amplitude of the analog element
        """
        value_tmp = value
        value = (value - self.analog_data[element]["amplitude"]) * (
            1 / self.ANALOG_WAVEFORM_AMPLITUDE
        )
        self.analog_data[element]["amplitude"] = value_tmp
        while not self.analog_job.is_paused():
            sleep(0.01)

        self.analog_qm.set_io_values(
            int(self.analog_elements.index(element)) + len(self.analog_elements),
            float(value),
        )
        self.analog_job.resume()

    def update_frequency(self, element, value):
        """
        Updates the frequency of an analog element.
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
        Switches the state of the given digital elements from on to off, and from off to on
        :param digital_element: A variable number of elements to be switched.
        """
        for element in digital_element:
            self.digital_data[
                self.digital_elements.index(element)
            ] = not self.digital_data[self.digital_elements.index(element)]
        self._start_digital(self.digital_data)

    def digital_on(self, *digital_element):
        """
        Turns on all digital elements inputted by the user and turns off all other elements.
        :param digital_element: A variable number of elements to be turned on
        """
        for element in self.digital_elements:
            if element in digital_element:
                self.digital_data[self.digital_elements.index(element)] = True
            else:
                self.digital_data[self.digital_elements.index(element)] = False
        self._start_digital(self.digital_data)

    def digital_off(self, *digital_element):
        """
        Turns off all digital elements inputted by the user and turns on all other elements.
        :param digital_element: A variable number of elements to be turned off
        """
        for element in self.digital_elements:
            if element in digital_element:
                self.digital_data[self.digital_elements.index(element)] = False
            else:
                self.digital_data[self.digital_elements.index(element)] = True
        self._start_digital(self.digital_data)

    def close(self):
        """
        Halts all jobs sent to the OPX and then closes the quantum machine
        """
        self.digital_job.halt()
        self.analog_job.halt()
        self.analog_qm.close()
        self.digital_qm.close()
        self.qmm.close()
