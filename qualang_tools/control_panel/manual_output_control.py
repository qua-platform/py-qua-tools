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
        cluster_name=None,
        close_previous=True,
        elements_to_control=None,
        isopx1=False,
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
        self.qmm = QuantumMachinesManager(host=host, port=port, cluster_name=cluster_name)
        if close_previous:
            self.qmm.close_all_qms()
            # self.qmm.close_all_quantum_machines()
        self.analog_config = None
        self.digital_configs = None
        self.analog_elements = []
        self.digital_elements = []
        self.digital_index = {}
        self.analog_data = {}
        self.digital_data = {}
        self.analog_job = None
        self.digital_jobs = None
        self.isopx1k = False
        self.isopx1 = isopx1
        self.ANALOG_WAVEFORM_AMPLITUDE = 0.5 - 2**-16
        self._process_config(configuration, elements_to_control)
        self.analog_qm = self.qmm.open_qm(self.analog_config, False)
        self._start_digital_qms()
        self._start_analog()
        print("If an element is turned on without an explicit amplitude, the amplitude defaults to 0.5 V.")

    @classmethod
    def ports(
        cls,
        isopx1k=False,
        analog_ports=None,
        digital_ports=None,
        host=None,
        port=None,
        cluster_name=None,
        close_previous=True,
        fem_types=None,
        mw_output_params=None,
    ):
        """
        Gets a list of analog and digital channels and creates different Quantum Machines. One QM continuously runs all
        the analog ports and the rest continuously runs all the digital ports. This enables controlling the amplitude
        and frequency of the analog ports and turning on and off the digital ports.
        All digital outputs start turned off, and all analog outputs start with zero amplitude and zero frequency.
        Default is using OPX/OPX+

        OPX / OPX+ mode (isopx1k=False):
        --------------------------------
        :param list analog_ports: The list of analog ports to control. A tuple creates an IQ pair.
            For example, [1, 2, (3, 4)] creates two independent channels at ports 1 & 2, and one IQ pair at ports 3 & 4.
            For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.
        :param list digital_ports: The list of digital ports to control.
            For multiple controllers, increase the port by 10. For example, controller 3 port 2 should be 32.

        OPX1000 mode (isopx1k=True):
        -----------------------------
        - analog_ports: list of 3-tuples OR IQ pairs of 3-tuples:
            ("con1", fem, port)                      -> single analog output
            (("con1", fem, I_port), ("con1", fem, Q_port)) -> IQ pair on same con/fem
        - digital_ports: list of 3-tuples:
            ("con1", fem, port) -> digital output

        FEM type & MW-FEM:
        ------------------
        - fem_types: optional dict {(con, fem): "LF" or "MW"}.
          Default is "LF" if not specified.
        - mw_output_params: optional dict {(con, fem, port): {...}} applied ONLY when fem_types[(con,fem)] == "MW".
          Example params:
              {"band": 2, "full_scale_power_dbm": -11, "sampling_rate": 1e9, "upconverter_frequency": 5e9,}
          If not given, defaults are:
              sampling_rate = 1e9, band = 2, full_scale_power_dbm = -11, upconverter_frequency =  5e9,

        :param str host: The host or IP of the QOP. Defaults to `None`: local settings are used.
        :param str port: The port used to access the QOP. Defaults to `None`, local settings are used.
        :param bool close_previous: Close currently running Quantum Machines. Note that if False, and a Quantum Machine
                                    which uses the same ports is already open, then this function would fail.
        """
        if analog_ports is None and digital_ports is None:
            raise Exception("No ports specified")
        config = {"version": 1, "controllers": {}, "elements": {}}

        if isopx1k:
            fem_types = fem_types or {}
            mw_output_params = mw_output_params or {}

            def get_fem_dict(con, fem):
                """
                Get or create the FEM dict for (con, fem),
                with the correct type ("LF" or "MW").
                """
                fem_type = fem_types.get((con, fem), "LF")
                if con not in config["controllers"]:
                    config["controllers"][con] = {
                        "type": "opx1000",
                        "fems": {},
                    }
                ctr = config["controllers"][con]
                if "fems" not in ctr:
                    ctr["fems"] = {}
                if fem not in ctr["fems"]:
                    ctr["fems"][fem] = {
                        "type": fem_type,
                        "analog_outputs": {},
                        "digital_outputs": {},
                        "analog_inputs": {},
                    }
                else:
                    # If fem already exists but fem_types is set to be a different type, return error
                    existing_type = ctr["fems"][fem].get("type", "LF")
                    if fem_type != existing_type:
                        raise Exception(f"Inconsistent FEM type for ({con}, {fem}): existing '{existing_type}', ")
                return ctr["fems"][fem], fem_type

            # Analog ports
            if analog_ports is not None:
                for ap in analog_ports:
                    # IQ pair: ((con, fem, pI), (con, fem, pQ))
                    if (
                        isinstance(ap, tuple)
                        and len(ap) == 2
                        and all(isinstance(x, tuple) and len(x) == 3 and isinstance(x[0], str) for x in ap)
                    ):
                        (con1, fem1, pI), (con2, fem2, pQ) = ap
                        if con1 != con2 or fem1 != fem2:
                            raise Exception("IQ pair ports must be on the same controller and FEM for OPX1000")
                        con, fem = con1, fem1
                        fem_dict, fem_type = get_fem_dict(con, fem)

                        if fem_type == "MW":
                            raise Exception(
                                f"MW-FEM IQ-pair syntax not supported in ManualOutputControl. "
                                f"Use single (con, fem, port) with fem_types[(con,fem)]='MW' instead."
                            )

                        # LF-FEM IQ pair (standard baseband)
                        fem_dict["analog_outputs"].setdefault(pI, {"offset": 0.0})
                        fem_dict["analog_outputs"].setdefault(pQ, {"offset": 0.0})

                        el_name = str(ap)
                        if el_name not in config["elements"]:
                            config["elements"][el_name] = {
                                "mixInputs": {
                                    "I": (con, fem, pI),
                                    "Q": (con, fem, pQ),
                                },
                                "intermediate_frequency": 0.0,
                            }
                    # Single analog: (con, fem, port)
                    elif isinstance(ap, tuple) and len(ap) == 3 and isinstance(ap[0], str):
                        con, fem, p = ap
                        fem_dict, fem_type = get_fem_dict(con, fem)

                        if fem_type == "MW":
                            base = {
                                "sampling_rate": 1e9,
                                "band": 2,
                                "full_scale_power_dbm": -11,
                                "upconverter_frequency": 5e9,
                            }
                            base.update(mw_output_params.get((con, fem, p), {}))
                            fem_dict["analog_outputs"][p] = base
                        else:
                            fem_dict["analog_outputs"].setdefault(p, {"offset": 0.0})

                        el_name = str(ap)
                        if el_name not in config["elements"]:
                            if fem_type == "MW":
                                config["elements"][el_name] = {
                                    "MWInput": {"port": (con, fem, p)},
                                    "intermediate_frequency": 0.0,
                                    "operations": {},
                                }
                            else:
                                config["elements"][el_name] = {
                                    "singleInput": {"port": (con, fem, p)},
                                    "intermediate_frequency": 0.0,
                                    "operations": {},
                                }
                    else:
                        raise Exception(
                            f"Unsupported analog port format for OPX1000: {ap}. "
                            f"Use (con, fem, port) or ((con,fem,I),(con,fem,Q))."
                        )
            # Digital ports
            if digital_ports is not None:
                for dp in digital_ports:
                    if not (isinstance(dp, tuple) and len(dp) == 3 and isinstance(dp[0], str)):
                        raise Exception(f"Unsupported digital port format for OPX1000: {dp}. Use (con, fem, port).")
                    con, fem, p = dp
                    fem_dict, _ = get_fem_dict(con, fem)
                    if p not in fem_dict["digital_outputs"]:
                        fem_dict["digital_outputs"][p] = {}
                    el_name = str(dp)
                    if el_name not in config["elements"]:
                        config["elements"][el_name] = {
                            "digitalInputs": {
                                "input": {
                                    "port": (con, fem, p),
                                    "delay": 0,
                                    "buffer": 0,
                                }
                            }
                        }
                    else:
                        config["elements"][el_name].setdefault("digitalInputs", {})
                        config["elements"][el_name]["digitalInputs"]["input"] = {
                            "port": (con, fem, p),
                            "delay": 0,
                            "buffer": 0,
                        }

        else:

            if analog_ports is not None:
                for port_int in analog_ports:
                    if isinstance(port_int, tuple):
                        if len(port_int) == 2:
                            con_number = (port_int[0] - 1) // 10 + 1
                            if con_number is not (port_int[1] - 1) // 10 + 1:
                                raise Exception(
                                    f"Ports {port_int[0]} and {port_int[1]} are not from the same controller"
                                )
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
            cluster_name=cluster_name,
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
        if self.isopx1k:
            for job in self.digital_jobs.values():
                if job is not None:
                    job.halt()
            for qm in self.digital_qms.values():
                if qm is not None:
                    qm.close()
        else:
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
        # Detect OPX1000 from presence of "fems" in any controller
        self.isopx1k = any("fems" in ctrl for ctrl in config["controllers"].values())
        # Thread counting:
        # - OPX/OPX+: key by controller name
        # - OPX1000: key by (controller name, fem id)
        pulser_count = {}
        highest_con = 0
        for con in list(config["controllers"].keys()):
            highest_con = int(con[-1]) if int(con[-1]) > highest_con else highest_con

        if self.isopx1k:
            self.digital_configs = {}
            self.digital_jobs = {}
            self.digital_qms = {}
        else:
            self.digital_configs = np.empty((highest_con, 10), dtype=dict)
            self.digital_jobs = np.empty((highest_con, 10), dtype=QmJob)
            self.digital_qms = np.empty((highest_con, 10), dtype=QuantumMachine)

        # Analog config
        self.analog_config["version"] = 1
        self.analog_config["controllers"] = {}
        for controller in list(config["controllers"].keys()):
            orig_ctrl = config["controllers"][controller]
            if self.isopx1k:
                fems = {}
                for fem_id, fem in orig_ctrl["fems"].items():
                    # keep only analog outputs
                    fems[fem_id] = {
                        "type": fem.get("type", "LF"),
                        "analog_outputs": fem.get("analog_outputs", {}),
                    }
                    pulser_count[(controller, fem_id)] = 0
                self.analog_config["controllers"][controller] = {
                    "type": orig_ctrl.get("type", "opx1000"),
                    "fems": fems,
                }
            else:
                self.analog_config["controllers"][controller] = {
                    "type": orig_ctrl.get("type", "opx1"),
                    "analog_outputs": orig_ctrl.get("analog_outputs", {}),
                }
                pulser_count[controller] = 0

        self.analog_config["elements"] = {}
        self.analog_config["waveforms"] = {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": self.ANALOG_WAVEFORM_AMPLITUDE},
        }
        self.analog_config["pulses"] = {
            "single_on": {
                "operation": "control",
                "length": 16,
                "waveforms": {"single": "const_wf"},
            },
            "IQ_Ion": {
                "operation": "control",
                "length": 16,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
            },
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
        if self.isopx1k:
            for element in elements:
                el_cfg = config["elements"][element]
                if el_cfg.get("digitalInputs") is None:
                    continue
                self.digital_index[element] = []
                self.digital_data[element] = False
                self.digital_elements.append(element)
                for din in el_cfg["digitalInputs"]:
                    port_tuple = el_cfg["digitalInputs"][din]["port"]
                    if len(port_tuple) != 3:
                        raise Exception("On OPX1000, digitalInputs ports must be (controller, fem, port) tuples")
                    con, fem, port = port_tuple
                    key = (con, fem, port)
                    self.digital_index[element].append(key)
                    if key not in self.digital_configs:
                        # count one thread on this FEM
                        pulser_count[(con, fem)] = pulser_count.get((con, fem), 0) + 1
                        dc = copy.deepcopy(digital_config)
                        orig_ctrl = config["controllers"][con]
                        fem_type = orig_ctrl["fems"][fem].get("type", "LF")
                        dc["controllers"][con] = {
                            "type": orig_ctrl.get("type", "opx1000"),
                            "fems": {
                                fem: {
                                    "type": fem_type,
                                    "digital_outputs": {port: {}},
                                }
                            },
                        }
                        dc["elements"]["digital"] = {
                            "operations": {"ON": "digital_ON"},
                            "digitalInputs": {
                                "digital": {
                                    "port": (con, fem, port),
                                    "delay": 0,
                                    "buffer": 0,
                                }
                            },
                        }
                        self.digital_configs[key] = dc
        else:
            for element in elements:
                el_cfg = config["elements"][element]
                if el_cfg.get("digitalInputs") is None:
                    continue
                self.digital_index[element] = []
                self.digital_data[element] = False
                self.digital_elements.append(element)
                for digital_input in el_cfg["digitalInputs"]:
                    con, port = el_cfg["digitalInputs"][digital_input]["port"]
                    con_int_index = int(con[-1]) - 1
                    port_index = port - 1
                    self.digital_index[element].append((con_int_index, port_index))
                    if self.digital_configs[con_int_index][port_index] is None:
                        pulser_count[con] += 1
                        self.digital_configs[con_int_index][port_index] = copy.deepcopy(digital_config)
                        ctrl_type = config["controllers"][con].get("type", "opx1")
                        self.digital_configs[con_int_index][port_index]["controllers"][con] = {
                            "type": ctrl_type,
                            "digital_outputs": {port: {}},
                        }
                        self.digital_configs[con_int_index][port_index]["elements"]["digital"] = {
                            "operations": {"ON": "digital_ON"},
                            "digitalInputs": {
                                "digital": {
                                    "port": (con, port),
                                    "delay": 0,
                                    "buffer": 0,
                                },
                            },
                        }
        # Analog
        for element in elements:
            el_cfg = config["elements"][element]
            if el_cfg.get("mixInputs") is not None:
                con = el_cfg["mixInputs"]["I"][0]
                if self.isopx1k:
                    fem = el_cfg["mixInputs"]["I"][1]
                    pulser_count[(con, fem)] = pulser_count.get((con, fem), 0) + 2
                else:
                    pulser_count[con] += 2

                self.analog_config["elements"][element] = el_cfg.copy()
                if self.analog_config["elements"][element].get("digitalInputs") is not None:
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                self.analog_config["elements"][element]["operations"] = {"play": "IQ_Ion"}
                self.analog_elements.append(element)

            elif el_cfg.get("MWInput") is not None:
                con = el_cfg["MWInput"]["port"][0]
                if self.isopx1k:
                    fem = el_cfg["MWInput"]["port"][1]
                    pulser_count[(con, fem)] = pulser_count.get((con, fem), 0) + 1
                else:
                    pulser_count[con] += 1

                self.analog_config["elements"][element] = el_cfg.copy()
                if self.analog_config["elements"][element].get("digitalInputs") is not None:
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                # MWInput elements expect a two-waveform pulse (I,Q), so reuse IQ_Ion
                self.analog_config["elements"][element]["operations"] = {"play": "IQ_Ion"}
                self.analog_elements.append(element)

            elif el_cfg.get("singleInput") is not None:
                con = el_cfg["singleInput"]["port"][0]
                if self.isopx1k:
                    fem = el_cfg["singleInput"]["port"][1]
                    pulser_count[(con, fem)] = pulser_count.get((con, fem), 0) + 1
                else:
                    pulser_count[con] += 1

                self.analog_config["elements"][element] = el_cfg.copy()
                if self.analog_config["elements"][element].get("digitalInputs") is not None:
                    self.analog_config["elements"][element].pop("digitalInputs")
                if self.analog_config["elements"][element].get("outputs") is not None:
                    self.analog_config["elements"][element].pop("outputs")
                    self.analog_config["elements"][element].pop("time_of_flight")
                    self.analog_config["elements"][element].pop("smearing")
                self.analog_config["elements"][element]["operations"] = {"play": "single_on"}
                self.analog_elements.append(element)

        for element in self.analog_elements:
            self.analog_config["elements"][element]["hold_offset"] = {"duration": 16}
            self.analog_data[element] = {
                "amplitude": 0,
                "frequency": self.analog_config["elements"][element].get("intermediate_frequency"),
            }
        if not self.isopx1k:
            # opx_plus = True if self.qmm.version_dict()["server"][0] == "2" else False
            opx_plus = False if self.isopx1 else True
        if self.isopx1k:
            for (con, fem), count in pulser_count.items():
                if count > 16:  # conservative per-FEM limit
                    raise Exception(
                        f"Given configuration requires {count} threads in {con}, FEM {fem}, but only 16 are available"
                    )
        else:
            for con, count in pulser_count.items():
                if opx_plus and count > 18:
                    raise Exception(f"Given configuration requires {count} threads in {con}, but only 18 are available")
                elif not opx_plus and count > 10:
                    raise Exception(f"Given configuration requires {count} threads in {con}, but only 10 are available")

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
        if len(self.digital_elements) == 0:
            return

        if self.isopx1k:
            # Dict keyed by (con, fem, port)
            all_keys = set()
            for key_list in self.digital_index.values():
                all_keys.update(key_list)
            for key in all_keys:
                if key not in self.digital_qms or self.digital_qms[key] is None:
                    self.digital_qms[key] = self.qmm.open_qm(self.digital_configs[key], False)
        else:
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

        # Build set of ports that should be ON
        if self.isopx1k:
            digital_on = set()
            for element in self.digital_elements:
                if self.digital_data[element]:
                    for key in self.digital_index[element]:
                        digital_on.add(key)

            all_keys = set()
            for key_list in self.digital_index.values():
                all_keys.update(key_list)

            for key in all_keys:
                job = self.digital_jobs.get(key)
                if key in digital_on:  # Needs to be on
                    if job is None or not job.result_handles.is_processing():
                        self.digital_jobs[key] = self.digital_qms[key].execute(prog)
                else:  # Needs to be off
                    if job is not None:
                        job.halt()
        # Create a list of ports that needs to be on
        else:
            digital_on = []
            for element in self.digital_elements:
                for con_idx, port_idx in self.digital_index[element]:
                    if self.digital_data[element]:
                        digital_on.append((con_idx, port_idx))

            for con_port_list in self.digital_index.values():
                for con_idx, port_idx in con_port_list:
                    if (con_idx, port_idx) in digital_on:  # Needs to be on
                        if (
                            self.digital_jobs[con_idx][port_idx] is None
                            or not self.digital_jobs[con_idx][port_idx].result_handles.is_processing()
                        ):
                            self.digital_jobs[con_idx][port_idx] = self.digital_qms[con_idx][port_idx].execute(prog)
                    else:  # Needs to be off
                        if self.digital_jobs[con_idx][port_idx] is not None:
                            self.digital_jobs[con_idx][port_idx].halt()

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
