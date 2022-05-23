import abc
from typing import Union, List, Tuple, Optional, Dict

from qualang_tools.config.exceptions import ConfigurationError
from qualang_tools.config.primitive_components import (
    ConfigBuilderElement,
    AnalogInputPort,
    DigitalOutputPort,
    Waveform,
    DigitalSample,
    Pulse,
    Weights,
    AnalogOutputPort,
    DigitalInputPort,
    Operation,
    IntegrationWeights,
    MixerData,
)


class Controller(ConfigBuilderElement):
    def __init__(
        self,
        name: str,
        controller_type: str = "opx1",
    ):
        """A QOP controller

        :param name: Name for this controller
        :type name: str
        :param controller_type: defaults to "opx1"
        :type controller_type: str, optional
        """
        super(Controller, self).__init__(name)
        self.dict = dict()
        self.dict["type"] = controller_type
        self.controller_type = controller_type
        self.dict["analog_outputs"] = {}
        self.analog_output_ports = []
        self.dict["analog_inputs"] = {}
        self.analog_input_ports = []
        self.dict["digital_outputs"] = {}
        self.digital_output_ports = []
        self.dict["digital_inputs"] = {}
        self.digital_input_ports = []

    def analog_output(self, port: int, offset: float = 0):
        """Returns an instance of AnalogOutputPort associated  with a specific port number and offset if already in the configuration.
        otherwise, opens a new instance with the given port number.

        :param port: physical output port numebr
        :type port: int
        :param offset: sets the voltage offset of that port, defaults to 0
        :type offset: float, optional
        :return: An instance of the analog port
        :rtype: AnalogOutputPort
        """
        for (i, p) in enumerate(self.analog_output_ports):
            if port == p.info[1]:
                p.offset = offset
                return p
        self._use_analog_output_port(port, offset)
        return self.analog_output_ports[-1]

    def analog_input(self, port: int, offset: float = 0):
        """Returns an instance of AnalogInputPort with a specific port number and offset if already in the configuration.
        otherwise, opens a new instance with the given port number and offset.

        :param port: physical input port numebr
        :type port: int
        :param offset: [description], defaults to 0
        :type offset: float, optional
        :return: An instance of the input port
        :rtype: AnalogInputPort
        """
        for (i, p) in enumerate(self.analog_input_ports):
            if port == p.info[1]:
                p.offset = offset
                return p
        self._use_analog_input_port(port, offset)
        return self.analog_input_ports[-1]

    def digital_output(self, port: int, offset: float = 0):
        """Returns an instance of DigitalOutputPort with a specific port number and offset if already in the configuration.
        otherwise, opens a new instance with the given port number and offset.

        :param port: port number in the range 1-10
        :type port: int
        :param offset: defaults to 0
        :type offset: float, optional
        :return:
        :rtype: DigitalOutputPort
        """
        for (i, p) in enumerate(self.digital_output_ports):
            if port == p.info[1]:
                p.offset = offset
                return p
        self._use_digital_output_port(port, offset)
        return self.digital_output_ports[-1]

    def digital_input(self, port: int):
        """Returns an instance of DigitalInputPort with a specific port number if already in the configuration.
        otherwise, opens a new instance with the given port number.

        :param port: port number in the range 1-10
        :type port: int
        :return:
        :rtype: DigitalOutputPort
        """

        for (i, p) in enumerate(self.digital_input_ports):
            if port == p.info[1]:
                return p
        self._use_digital_input_port(port)
        return self.digital_input_ports[-1]

    def __contains__(self, port) -> bool:
        for p in self.ports:
            if port == p:
                return True
        return False

    def _use_analog_input_port(self, port_num: int, offset: float = 0.0):
        """Adds an instance of  AnalogInputPort to configuration if it is not used

        :param port_num: port number
        :type port_num: int
        :param offset: voltage offset for this port, defaults to 0.0
        :type offset: float, optional
        """
        if port_num not in self.dict["analog_inputs"]:
            self.dict["analog_inputs"][port_num] = {"offset": offset}
            self.analog_input_ports += [
                AnalogInputPort(self.name, port_num, offset=offset)
            ]

    def _use_analog_output_port(self, port_num: int, offset: float = 0.0):
        """Adds an instance of  AnalogOutputPort to configuration if it is not used

        :param port_num: port number
        :type port_num: int
        :param offset: voltage offset for this port, defaults to 0.0
        :type offset: float, optional
        """
        if port_num not in self.dict["analog_outputs"]:
            self.dict["analog_outputs"][port_num] = {"offset": offset}
            self.analog_output_ports += [
                AnalogOutputPort(self.name, port_num, offset=offset)
            ]

    def _use_digital_output_port(self, port_num: int, offset: float = 0.0):
        """Adds an instance of  DigitalOutputPort to configuration if it is not used

        :param port_num: port number
        :type port_num: int
        :param offset: defaults to 0.0
        :type offset: float, optional
        """
        if port_num not in self.dict["digital_outputs"]:
            self.dict["digital_outputs"][port_num] = {"offset": offset}
            self.digital_output_ports += [
                DigitalOutputPort(self.name, port_num, offset=offset)
            ]

    def _use_digital_input_port(self, port_num: int):
        """Adds an instance of  DigitalInputPort to configuration if it is not used

        :param port_num: port number
        :type port_num: int
        """
        if port_num not in self.dict["digital_inputs"]:
            self.dict["digital_inputs"][port_num] = {}
            self.digital_input_ports += [DigitalInputPort(self.name, port_num)]

    @property
    def ports(self):
        """Returns the set of all used ports in this configuration

        :return:
        :rtype: Set
        """
        return (
            self.digital_input_ports
            + self.digital_output_ports
            + self.analog_input_ports
            + self.analog_output_ports
        )


class ArbitraryWaveform(Waveform):
    def __init__(self, name: str, samples: List[float]):
        """An arbitrary waveform played by the QOP

        :param name: name of the played WF
        :type name: str
        :param samples: list of samples to be played (in the range -.5 to .5), specified at 1 sample per nanosecond
        :type samples: List[float]
        """
        super().__init__(name, {"type": "arbitrary", "samples": samples})

    @property
    def samples(self):
        return self.dict["samples"]

    @samples.setter
    def samples(self, samples: List[float]):
        self.dict["samples"] = samples


class ConstantWaveform(Waveform):
    def __init__(self, name: str, sample: float):
        """A constant amplitude WF

        :param name: name of the WF
        :type name: str
        :param sample: Amplitude of the WF in the range -.5 to .5
        :type sample: float
        """
        super().__init__(name, {"type": "constant", "sample": sample})

    @property
    def sample(self):
        return self.dict["sample"]

    @sample.setter
    def sample(self, samples: List[float]):
        self.dict["sample"] = samples


class DigitalWaveform(Waveform):
    def __init__(self, name: str, samples: List[DigitalSample]):
        """A digital waveform played from a digital output

        :param name: The name of the digital waveform, defaults to "ON"
        :type name: str
        :param samples: The digital waveforms, specified in the format [(1/0, dur),...] where dur is in nanoseconds.  defaults to [(1, 0)]
        :type samples: List[DigitalSample]
        """

        if isinstance(samples[0], DigitalSample):
            self._samples = samples
        else:
            self._samples = [
                DigitalSample(state, duration) for (state, duration) in samples
            ]
        dic = dict()
        dic["samples"] = [(ds.state, ds.duration) for ds in self._samples]
        super(DigitalWaveform, self).__init__(name, dic)

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def samples(self, samples: Union[List[Tuple[int, int]], List[DigitalSample]]):
        if isinstance(samples[0], DigitalSample):
            self._samples = samples
        else:
            self._samples = [
                DigitalSample(state, duration) for (state, duration) in samples
            ]
        self.dict["samples"] = [(ds.state, ds.duration) for ds in self._samples]


class MeasurePulse(Pulse):
    def __init__(self, name: str, wfs: List[Waveform], length: int, **kwargs):
        """A pulse which can be used by a QUA measure() command

        :param name: name for this pulse
        :type name: str
        :param wfs: waveforms to be played during measurement
        :type wfs: List[Waveform]
        :param length: duration of the measurment pulse
        :type length: int, optional
        """

        integration_weights: List[Weights] = kwargs.get("integration_weights", None)
        digital_marker: Optional[DigitalWaveform] = kwargs.get("digital_marker", None)
        super().__init__(name, wfs, "measure", length, digital_marker)
        if integration_weights is None:
            integration_weights = []
        self.integration_weights = integration_weights

    def add(
        self,
        objs: Union[Weights, DigitalWaveform, List[Union[Weights, DigitalWaveform]]],
    ):
        if isinstance(objs, list):
            for obj in objs:
                self._add(obj)
        else:
            self._add(objs)
        return self

    def _add(self, w: Union[Weights, IntegrationWeights, DigitalWaveform]):
        if isinstance(w, IntegrationWeights):
            w = Weights(w)

        if isinstance(w, Weights):
            if callable(self.dict):
                if isinstance(w.weights, ConstantIntegrationWeights):
                    if w.weights.dict["cosine"][0][1] == self.dict["length"]:
                        assert w.weights.dict["cosine"][0][1]() == self.dict["length"]()

                else:
                    assert len(w.weights.dict["sine"]) == self.dict["length"] // 4
            self.integration_weights.append(w)
        elif isinstance(w, DigitalWaveform):
            self.digital_marker = w


class ControlPulse(Pulse):
    def __init__(self, name: str, wfs: List[Waveform], length: int, **kwargs):
        """A pulse which can be used by a QUA play() command
        :return:
        :rtype: ControlPulse
        """
        digital_marker: Optional[DigitalWaveform] = kwargs.get("digital_marker", None)
        super().__init__(name, wfs, "control", length, digital_marker)

    def add(self, w: DigitalWaveform):
        self.digital_marker = w
        return self


class Mixer(ConfigBuilderElement):
    def __init__(self, name: str, data: Optional[List[MixerData]] = None):
        """A microwave mixer

        :param name: name for this mixer
        :type name: str
        :param data: a list of mixer data with correction matrices for every pair of IF and LO
        :type data: List[MixerData]

        """
        super(Mixer, self).__init__(name)
        if data is None:
            data = []
        self.dict = []
        for e in data:
            self.add(e)

    def add(self, data: MixerData):
        self.dict.append(
            {
                "intermediate_frequency": data.intermediate_frequency,
                "lo_frequency": data.lo_frequency,
                "correction": list(data.correction.data[0] + data.correction.data[1]),
            }
        )
        return self


class Element(ConfigBuilderElement):
    def __init__(
        self,
        name: str,
        analog_input_ports: Optional[List[AnalogOutputPort]] = None,
        analog_output_ports: Optional[List[AnalogInputPort]] = None,
        digital_input_ports: Optional[List[DigitalOutputPort]] = None,
        digital_output_ports: Optional[List[DigitalInputPort]] = None,
        intermediate_frequency: Optional[int] = None,
        lo_frequency: Optional[int] = None,
        **kwargs
    ):
        """A quantum element in a configuration

        :param name: element name
        :type name: int
        :param analog_input_ports: AnalogOutputPort(s) associated with this element, defaults to []
        :type analog_input_ports: List[AnalogOutputPort], optional
        :param analog_output_ports: AnalogInputPort(s) associated with this element, defaults to []
        :type analog_output_ports: List[AnalogInputPort], optional
        :param digital_input_ports: DigitalOutputPort(s) associated with this element, defaults to []
        :type digital_input_ports: List[DigitalOutputPort], optional
        :param intermediate_frequency: intermediate frequency associated wit this element, defaults to None
        :type intermediate_frequency: int, optional
        :param lo_frequency: LO frequency associated wit this element, defaults to None
        :type lo_frequency: int, optional
        """
        super(Element, self).__init__(name)

        mixer: Optional[Mixer] = kwargs.get("mixer", None)
        pulses: Optional[List[Pulse]] = kwargs.get("pulses", None)
        operations: Optional[Dict[str, str]] = kwargs.get("digital_marker", None)

        self.dict = dict()
        assert len(analog_input_ports) <= 2
        self.type = "singleInput" if len(analog_input_ports) == 1 else "mixInputs"
        self.pulses = []
        if pulses is not None:
            self.pulses = pulses
        self.analog_input_ports = (
            [] if analog_input_ports is None else analog_input_ports
        )
        self.analog_output_ports = (
            [] if analog_output_ports is None else analog_output_ports
        )
        self.digital_output_ports = (
            [] if digital_output_ports is None else digital_output_ports
        )
        self.digital_input_ports = (
            [] if digital_input_ports is None else digital_input_ports
        )
        self.mixer: Mixer = mixer

        if len(self.analog_input_ports) > 0:
            if self.type == "singleInput":
                port = self.analog_input_ports[0]
                self.dict["singleInput"] = dict()
                self.dict["singleInput"]["port"] = port.info
            elif self.type == "mixInputs":
                I = self.analog_input_ports[0]
                Q = self.analog_input_ports[1]
                self.dict["mixInputs"] = dict()
                self.dict["mixInputs"]["I"] = I.info
                self.dict["mixInputs"]["Q"] = Q.info
                self.dict["mixInputs"]["lo_frequency"] = lo_frequency
        if len(self.analog_output_ports) > 0:
            self.dict["outputs"] = dict()
            for i, port in enumerate(self.analog_output_ports):
                self.dict["outputs"]["out" + str(i + 1)] = port.info
        self.dict["operations"] = dict()
        if operations is not None:
            self.dict["operations"] = operations
        self.dict["intermediate_frequency"] = intermediate_frequency
        # self.dict["outputPulseParameters"] = dict()
        if len(self.digital_input_ports) > 0:
            self.dict["digitalInputs"] = dict()
            for i, port in enumerate(self.digital_input_ports):
                self.dict["digitalInputs"]["in" + str(i + 1)] = {
                    "port": port.info,
                    "delay": 0,
                    "buffer": 0,
                }

    def set_digital_input_delay(self, port_id: int, val: int):
        if "in" + str(port_id) in self.dict["digitalInputs"].keys():
            self.dict["digitalInputs"]["in" + str(port_id)]["delay"] = val
        else:
            raise ConfigurationError("digital input port must be set first")

    def set_digital_input_buffer(self, port_id: int, val: int):
        if "in" + str(port_id) in self.dict["digitalInputs"].keys():
            self.dict["digitalInputs"]["in" + str(port_id)]["buffer"] = val
        else:
            raise ConfigurationError("digital input port must be set first")

    def _set_mixer(self, mix: Mixer):
        assert "mixInputs" in self.dict.keys()
        self.dict["mixInputs"]["mixer"] = mix.name
        self.mixer = mix

    @property
    def has_lo_frequency(self):
        return "mixInputs" in self.dict.keys()

    @property
    def lo_frequency(self):
        assert "mixInputs" in self.dict.keys()
        return self.dict["mixInputs"]["lo_frequency"]

    @lo_frequency.setter
    def lo_frequency(self, lo_frequency: int):
        assert "mixInputs" in self.dict.keys()
        self.dict["mixInputs"]["lo_frequency"] = lo_frequency

    @property
    def intermediate_frequency(self):
        return self.dict["intermediate_frequency"]

    @intermediate_frequency.setter
    def intermediate_frequency(self, omega_IF: int):
        """Set the IF associated with this element

        :param omega_IF:
        :type omega_IF: int
        """
        assert self.type == "mixInputs"
        self.dict["intermediate_frequency"] = omega_IF

    @property
    def operations(self):
        return self.dict["operations"]

    def _add_operation(self, op: Operation):
        self.dict["operations"][op.name] = op.pulse.name
        self.pulses.append(op.pulse)

    def _add(self, obj: Union[Operation, Mixer, ControlPulse, MeasurePulse]):
        """A method to add components to an element

        :param obj: The component to be added
        :type obj: [type]
        :raises ConfigurationError: [description]
        """
        if isinstance(obj, Operation):
            self._add_operation(obj)
        elif isinstance(obj, Mixer):
            self._set_mixer(obj)
        elif isinstance(obj, ControlPulse) or isinstance(obj, MeasurePulse):
            self.dict["operations"][obj.name] = obj.name
            self.pulses.append(obj)
        else:
            raise ConfigurationError("Adding unsupported object")

    def add(self, objs: Union[Operation, Mixer, List[Union[Operation, Mixer]]]):
        if isinstance(objs, list):
            for obj in objs:
                self._add(obj)
        else:
            self._add(objs)
        return self

    @property
    def operation_names(self):
        return self.dict["operations"].keys()

    @property
    def pulse_names(self):
        return set([p.name for p in self.pulses])

    @property
    def waveform_names(self):
        names = []
        for pl in self.pulses:
            names += pl.waveform_names
        return set(names)

    @property
    def ports(self):
        return (
            self.analog_input_ports
            + self.analog_output_ports
            + self.digital_output_ports
            + self.digital_input_ports
        )

    @property
    def has_signal_threshold(self):
        return (
            "outputPulseParameters" in self.dict
            and "signalThreshold" in self.dict["outputPulseParameters"].keys()
        )

    @property
    def signal_threshold(self):
        if "signalThreshold" in self.dict["outputPulseParameters"].keys():
            return self.dict["outputPulseParameters"]["signalThreshold"]
        else:
            raise ConfigurationError("set the signal threshold")

    @signal_threshold.setter
    def signal_threshold(self, val: int):
        if "outputPulseParameters" not in self.dict.keys():
            self.dict["outputPulseParameters"] = dict()
        self.dict["outputPulseParameters"]["signalThreshold"] = val

    @property
    def has_signal_polarity(self):
        return (
            "outputPulseParameters" in self.dict
            and "signalPolarity" in self.dict["outputPulseParameters"].keys()
        )

    @property
    def signal_polarity(self):
        if "signalPolarity" in self.dict["outputPulseParameters"].keys():
            return self.dict["outputPulseParameters"]["signalPolarity"]
        else:
            raise ConfigurationError("set the signal polarity")

    @signal_polarity.setter
    def signal_polarity(self, val: str):
        if "outputPulseParameters" not in self.dict.keys():
            self.dict["outputPulseParameters"] = dict()
        self.dict["outputPulseParameters"]["signalPolarity"] = val

    @property
    def has_derivative_threshold(self):
        return (
            "outputPulseParameters" in self.dict
            and "derivativeThreshold" in self.dict["outputPulseParameters"].keys()
        )

    @property
    def derivative_threshold(self):
        if "derivativeThreshold" in self.dict["outputPulseParameters"].keys():
            return self.dict["outputPulseParameters"]["derivativeThreshold"]
        else:
            raise ConfigurationError("set the derivative threshold")

    @derivative_threshold.setter
    def derivative_threshold(self, val: int):
        if "outputPulseParameters" not in self.dict.keys():
            self.dict["outputPulseParameters"] = dict()
        self.dict["outputPulseParameters"]["derivativeThreshold"] = val

    @property
    def has_derivative_polarity(self):
        return (
            "outputPulseParameters" in self.dict
            and "derivativePolarity" in self.dict["outputPulseParameters"].keys()
        )

    @property
    def derivative_polarity(self):
        if "derivativePolarity" in self.dict["outputPulseParameters"].keys():
            return self.dict["outputPulseParameters"]["derivativePolarity"]
        else:
            raise ConfigurationError("set the derivative polarity")

    @derivative_polarity.setter
    def derivative_polarity(self, val: str):
        if "outputPulseParameters" not in self.dict.keys():
            self.dict["outputPulseParameters"] = dict()
        self.dict["outputPulseParameters"]["derivativePolarity"] = val


class MeasureElement(Element):
    def __init__(
        self,
        name: str,
        analog_input_ports: List[AnalogOutputPort],
        analog_output_ports: List[AnalogInputPort],
        digital_input_ports: Optional[List[DigitalOutputPort]] = None,
        intermediate_frequency: Optional[int] = None,
        lo_frequency: Optional[int] = None,
        **kwargs
    ):
        """A quantum element set for performing measurment

        :param name: [description]
        :type name: int
        :param analog_input_ports: [description]
        :type analog_input_ports: List[AnalogOutputPort]
        :param analog_output_ports: [description]
        :type analog_output_ports: List[AnalogInputPort]
        :param digital_input_ports: [description], defaults to []
        :type digital_input_ports: List[DigitalOutputPort], optional
        :param intermediate_frequency: intermediate frequency associated wit this element, defaults to None
        :type intermediate_frequency: int, optional
        :param lo_frequency: [description], defaults to None
        :type lo_frequency: int, optional
        """

        time_of_flight: Optional[int] = kwargs.get("time_of_flight", 0)
        smearing: Optional[int] = kwargs.get("smearing", 0)
        digital_output_ports: Optional[List[DigitalInputPort]] = kwargs.get(
            "digital_output_ports", None
        )
        mixer: Optional[Mixer] = kwargs.get("mixer", None)
        pulses: Optional[List[Pulse]] = kwargs.get("pulses", None)
        operations: Optional[Dict[str, str]] = kwargs.get("operations", None)
        super().__init__(
            name,
            analog_input_ports,
            analog_output_ports,
            digital_input_ports,
            digital_output_ports,
            intermediate_frequency,
            lo_frequency,
            mixer=mixer,
            pulses=pulses,
            operations=operations,
        )
        self.dict["time_of_flight"] = time_of_flight
        self.dict["smearing"] = smearing

    @property
    def time_of_flight(self):
        return self.dict["time_of_flight"]

    @time_of_flight.setter
    def time_of_flight(self, tof: int):
        self.dict["time_of_flight"] = tof

    @property
    def smearing(self):
        return self.dict["smearing"]

    @smearing.setter
    def smearing(self, smearing: int):
        self.dict["smearing"] = smearing


class ConstantIntegrationWeights(IntegrationWeights):
    def __init__(self, name: str, cosine: float, sine: float, duration: int):
        """A constant integration weight used in integration and demodulation
        :param name: name for the weights vector
        :type name: str
        :param cosine: value of the cosine vector
        :type cosine: float
        :param sine: value of the cosine vector
        :type sine: float
        :param duration: duration of the read out pulse
        :type duration: int
        """
        self._duration = duration
        self._cosine = cosine
        self._sine = sine
        super(ConstantIntegrationWeights, self).__init__(
            name, [(cosine, duration)], [(sine, duration)]
        )

    @property
    def cosine(self):
        return self.dict["cosine"]

    @cosine.setter
    def cosine(self, v: float):
        self.dict["cosine"] = [(v, self._duration)]

    @property
    def sine(self):
        return self.dict["sine"]

    @sine.setter
    def sine(self, v: float):
        self.dict["sine"] = [(v, self._duration)]


class ArbitraryIntegrationWeights(IntegrationWeights):
    def __init__(self, name: str, cosine: List[float], sine: List[float]):
        """A vector of integration weights used in integration and demodulation
        :param name: name for the weights vector
        :type name: str
        :param cosine: a list of weights to be used with the cosine demodulation element, specified at 1 sample per 4 nanoseconds
        :type cosine: List
        :param sine: a list of weights to be used with the sine demodulation element, specified at 1 sample per 4 nanoseconds
        :type sine: List
        """
        super().__init__(name, cosine, sine)
        assert len(sine) == len(cosine)

    @property
    def cosine(self):
        return self.dict["cosine"]

    @cosine.setter
    def cosine(self, w: List[float]):
        self.dict["cosine"] = w

    @property
    def sine(self):
        return self.dict["sine"]

    @sine.setter
    def sine(self, w: List[float]):
        self.dict["sine"] = w


class ElementCollection(ConfigBuilderElement):
    def __init__(self, name: str):
        """A named collection of Elements

        It also a useful base class for building components.
        """
        super(ElementCollection, self).__init__(name)

    @abc.abstractmethod
    def get_elements(self) -> List[ConfigBuilderElement]:
        pass

    @property
    def ports(self):
        ports = []
        for elm in self.get_elements():
            ports += elm.ports
        return ports

    @property
    def waveform_names(self):
        names = []
        for elm in self.get_elements():
            names += elm.waveform_names
        return names

    @property
    def operation_names(self):
        names = []
        for elm in self.get_elements():
            names += elm.operation_names
        return names

    @property
    def pulse_names(self):
        names = []
        for elm in self.get_elements():
            names += elm.pulse_names
        return names


class ReadoutResonator(ElementCollection):
    def __init__(
        self,
        name: str,
        outputs: List[AnalogOutputPort],
        inputs: List[AnalogInputPort],
        intermediate_frequency: int,
        **kwargs
    ):
        """
        A Microwave readout resonator

        :param name: A name for this resonator
        :type name: str
        :param outputs: A pair of output ports
        :type outputs: List[AnalogOutputPort]
        :param inputs: A pair of input ports
        :type inputs: List[AnalogInputPort]
        :param intermediate_frequency: The intermediate frequency
        :type intermediate_frequency: int
        """

        operations: Optional[List[Operation]] = kwargs.get("operations", None)
        time_of_flight: Optional[int] = kwargs.get("time_of_flight", 0)
        smearing: Optional[int] = kwargs.get("smearing", 0)
        mixer: Optional[Mixer] = kwargs.get("mixer", None)
        lo_frequency: Optional[int] = kwargs.get("lo_frequency", None)

        super(ReadoutResonator, self).__init__(name=name)
        if len(outputs) != 2:
            raise ConfigurationError("Number of output ports is not equal to 2")
        if len(inputs) != 2:
            raise ConfigurationError("Number of input ports is not equal to 2")
        self.drive_name = name
        self.drive_outputs = outputs
        self.drive_inputs = inputs
        self.drive_operations = []
        if operations is not None:
            self.drive_operations = operations
        self.drive_intermediate_frequency = intermediate_frequency
        self.drive_time_of_flight = time_of_flight

        self.drive_mixer = mixer
        self.drive_lo_frequency = lo_frequency
        self.drive_smearing = smearing

    def get_elements(self) -> List[ConfigBuilderElement]:
        drive = MeasureElement(
            self.drive_name,
            self.drive_outputs,
            self.drive_inputs,
            intermediate_frequency=self.drive_intermediate_frequency,
            time_of_flight=self.drive_time_of_flight,
            mixer=self.drive_mixer,
            lo_frequency=self.drive_lo_frequency,
            smearing=self.drive_smearing,
        )
        for op in self.drive_operations:
            drive.add(op)

        if self.drive_inputs:
            for (i, port) in enumerate(self.drive_inputs):
                drive.dict["outputs"]["out" + str(i + 1)] = port.info

        drive.dict["mixInputs"]["I"] = self.drive_outputs[0].info
        drive.dict["mixInputs"]["Q"] = self.drive_outputs[1].info

        if self.drive_mixer:
            drive.dict["mixInputs"]["mixer"] = self.drive_mixer.name

        return [drive]

    @property
    def intermediate_frequency(self):
        return self.drive_intermediate_frequency

    @intermediate_frequency.setter
    def intermediate_frequency(self, if_freq: int):
        """Set an IF for the resonator

        :param if_freq: A frequency in MHz
        :type if_freq: int
        """
        self.drive_intermediate_frequency = if_freq

    def add(self, obj: Union[Operation, List[Operation]]):
        """Add list of operations associated with the Transmon

        :param obj: The list of operations
        :type obj: list or an instance of Operation
        """
        if isinstance(obj, list):
            for o in obj:
                self._add(o)
        else:
            self._add(obj)
        return self

    def _add(self, op: Union[Operation, MeasurePulse]):
        """Add operation associated with the Readout resonator

        :param obj: The operation
        :type obj: Operation

        """
        if isinstance(op, Operation):
            if len(op.pulse.wfs) == 2:
                self.drive_operations.append(op)
            else:
                raise ConfigurationError("adding unsupported object")
        elif isinstance(op, MeasurePulse):
            if len(op.wfs) == 2:
                self.drive_operations.append(op)
            else:
                raise ConfigurationError("adding unsupported object")
        else:
            raise ConfigurationError("adding unsupported object")

    @property
    def time_of_flight(self):
        return self.drive_time_of_flight

    @time_of_flight.setter
    def time_of_flight(self, tof: int):
        self.drive_time_of_flight = tof

    @property
    def smearing(self):
        return self.drive_smearing

    @smearing.setter
    def smearing(self, t: int):
        self.drive_smearing = t

    @property
    def lo_frequency(self):
        return self.drive_lo_frequency

    @lo_frequency.setter
    def lo_frequency(self, lo_frequency: int):
        self.drive_lo_frequency = lo_frequency

    @property
    def input_ports(self):
        return self.drive_inputs

    @input_ports.setter
    def input_ports(self, ports: List[AnalogInputPort]):
        assert len(ports) == 2
        self.drive_inputs = ports

    @property
    def output_ports(self):
        return self.drive_outputs

    @output_ports.setter
    def output_ports(self, ports: List[AnalogOutputPort]):
        assert len(ports) == 2
        self.drive_outputs = ports

    @property
    def mixer(self):
        return self.drive_mixer

    @mixer.setter
    def mixer(self, mixer: Mixer):
        self.drive_mixer = mixer


class Transmon(ElementCollection):
    def __init__(
        self,
        name: str,
        I: AnalogOutputPort,
        Q: AnalogOutputPort,
        intermediate_frequency: int,
        **kwargs
    ):
        """A superconducting transmon qubit

        :param name: A name for this transmon
        :type name: str
        :param I: I output port
        :type I: AnalogOutputPort
        :param Q: Q output port
        :type Q: AnalogOutputPort
        :param intermediate_frequency: intermediate frequency of the upconversion IQ mixer in MHz
        :type intermediate_frequency: int
        """

        mixer: Optional[Mixer] = kwargs.get("mixer", None)
        lo_frequency: Optional[int] = kwargs.get("lo_frequency", None)
        operations: Optional[List[Operation]] = kwargs.get("operations", None)

        super(Transmon, self).__init__(name=name)
        self.drive_I = I
        self.drive_Q = Q
        self.drive_intermediate_frequency = intermediate_frequency

        self.drive_operations = []
        if operations is not None:
            self.drive_operations = operations
        self.drive_intermediate_frequency = intermediate_frequency
        self.drive_mixer = mixer
        self.drive_lo_frequency = lo_frequency

    def get_elements(self) -> List[ConfigBuilderElement]:
        drive = Element(
            self.name,
            [self.drive_I, self.drive_Q],
            intermediate_frequency=self.drive_intermediate_frequency,
            mixer=self.drive_mixer,
            lo_frequency=self.drive_lo_frequency,
        )
        drive.dict["mixInputs"]["I"] = self.drive_I.info
        drive.dict["mixInputs"]["Q"] = self.drive_Q.info

        for op in self.drive_operations:
            drive.add(op)

        if self.drive_mixer:
            drive.dict["mixInputs"]["mixer"] = self.drive_mixer.name

        return [drive]

    @property
    def I(self):
        return self.drive_I

    @I.setter
    def I(self, p: AnalogOutputPort):
        self.drive_I = p

    @property
    def Q(self):
        return self.drive_Q

    @Q.setter
    def Q(self, p: AnalogOutputPort):
        self.drive_Q = p

    @property
    def lo_frequency(self):
        return self.drive_lo_frequency

    @lo_frequency.setter
    def lo_frequency(self, lo_frequency: int):
        self.drive_lo_frequency = lo_frequency

    @property
    def intermediate_frequency(self):
        return self.drive_intermediate_frequency

    @intermediate_frequency.setter
    def intermediate_frequency(self, if_freq: int):
        """
            Set an IF for the transmon
        :param if_freq: A frequency in MHz
        :type if_freq: int
        """
        self.drive_intermediate_frequency = if_freq

    def add(self, op: Union[Operation, List[Operation]]):
        """
            Add list of operations associated with the Transmon
        :param op: The operations
        :type op: list or an instance of Operation
        """
        if isinstance(op, list):
            for o in op:
                self._add(o)
        else:
            self._add(op)
        return self

    def _add(self, op: Union[Operation, ControlPulse]):
        if isinstance(op, Operation):
            if len(op.pulse.wfs) == 2:
                self.drive_operations.append(op)
            else:
                raise ConfigurationError("adding unsupported object")
        elif isinstance(op, ControlPulse):
            if len(op.wfs) == 2:
                self.drive_operations.append(op)
            else:
                raise ConfigurationError("adding unsupported object")
        else:
            raise ConfigurationError("adding unsupported object")

    @property
    def mixer(self):
        return self.drive_mixer

    @mixer.setter
    def mixer(self, mixer: Mixer):
        self.drive_mixer = mixer


class FluxTunableTransmon(Transmon):
    def __init__(
        self,
        name: str,
        I: AnalogOutputPort,
        Q: AnalogOutputPort,
        flux_port: AnalogOutputPort,
        intermediate_frequency: int,
        **kwargs
    ):
        """A flux tuneable superconducting transmon qubit

        :param name: A name for this transmon
        :type name: str
        :param I: I output port
        :type I: AnalogOutputPort
        :param Q: Q output port
        :type Q: AnalogOutputPort
        :param flux_port:  Flux line output Port
        :type flux_port: AnalogOutputPort
        :param intermediate_frequency: intermediate frequency of the upconversion IQ mixer in MHz
        :type intermediate_frequency: int
        """

        mixer: Optional[Mixer] = kwargs.get("mixer", None)
        lo_frequency: Optional[int] = kwargs.get("lo_frequency", None)
        operations: Optional[List[Operation]] = kwargs.get("operations", None)
        flux_operations: Optional[List[Operation]] = kwargs.get("flux_operations", None)

        super(FluxTunableTransmon, self).__init__(
            name,
            I,
            Q,
            intermediate_frequency,
            mixer=mixer,
            lo_frequency=lo_frequency,
            operations=operations,
        )
        self.flux_port = flux_port
        self.flux_operations = []
        if flux_operations is not None:
            self.flux_operations = flux_operations

    def get_elements(self) -> List[ConfigBuilderElement]:
        els = super().get_elements()

        el = Element(self.name + "_flux_line", [self.flux_port])
        for op in self.flux_operations:
            el.add(op)

        els.append(el)
        return els

    def _add(self, op: Union[Operation, ControlPulse]):
        if isinstance(op, Operation):
            if len(op.pulse.wfs) == 2:
                super(FluxTunableTransmon, self)._add(op)
            elif len(op.pulse.wfs) == 1:
                self.flux_operations.append(op)
            else:
                raise ConfigurationError(
                    "Can not add a pulse with {0} waveforms".format(len(op.pulse.wfs))
                )
        elif isinstance(op, ControlPulse):
            if len(op.wfs) == 2:
                super(FluxTunableTransmon, self)._add(op)
            elif len(op.wfs) == 1:
                self.flux_operations.append(op)
            else:
                raise ConfigurationError(
                    "Can not add a pulse with {0} waveforms".format(len(op.wfs))
                )

        else:
            raise ConfigurationError(
                "adding unsupported object of type {}".format(type(op))
            )


class Coupler(ElementCollection):
    def __init__(self, name: str, port: AnalogOutputPort, **kwargs):
        operations: Optional[List[Operation]] = kwargs.get("operations", None)
        super(Coupler, self).__init__(name=name)
        self._port = port
        self.operations = []
        if operations is not None:
            self.operations = operations

    def get_elements(self) -> List[ConfigBuilderElement]:
        coupler = Element(self.name, analog_input_ports=[self._port])
        for op in self.operations:
            coupler.add(op)
        return [coupler]

    def _add(self, op: Operation):
        if len(op.pulse.wfs) == 1:
            self.operations.append(op)
        else:
            raise ConfigurationError(
                "Can not add a pulse with {0} waveforms".format(len(op.pulse.wfs))
            )

    def add(self, op: Union[List[Operation], Operation]):
        if isinstance(op, list):
            for o in op:
                self._add(o)
        else:
            self._add(op)
        return self

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, p: AnalogOutputPort):
        self._port = p


class Oscillator(ConfigBuilderElement):
    def __init__(
        self, name: str, intermediate_frequency: int, lo_frequency: int, mixer: str
    ):
        super(Oscillator, self).__init__(name)
        self.dict = dict()
        self.dict["intermediate_frequency"] = intermediate_frequency
        self.dict["lo_frequency"] = lo_frequency
        self.dict["mixer"] = mixer

    @property
    def lo_frequency(self):
        return self.dict["lo_frequency"]

    @lo_frequency.setter
    def lo_frequency(self, lo_frequency: int):
        self.dict["lo_frequency"] = lo_frequency

    @property
    def intermediate_frequency(self):
        return self.dict["intermediate_frequency"]

    @intermediate_frequency.setter
    def intermediate_frequency(self, intermediate_frequency: int):
        self.dict["intermediate_frequency"] = intermediate_frequency

    @property
    def mixer(self):
        return self.dict["mixer"]

    @mixer.setter
    def mixer(self, mixer: str):
        self.dict["mixer"] = mixer
