from typing import Union, List, Tuple

from qualang_tools.config.primitive_components import *
from qualang_tools.config.exceptions import ConfigurationError


class Controller:
    def __init__(
        self,
        name: str,
        n_analog_outputs: int = 0,
        n_analog_inputs: int = 0,
        n_digital_outputs: int = 0,
        n_digital_inputs: int = 0,
        controller_type: str = "opx1",
    ):
        """A QOP controller

        :param name: Name for this controller
        :type name: str
        :param n_analog_outputs: Number of analog outputs defined at initialization, defaults to 0
        :type n_analog_outputs: int, optional
        :param n_analog_inputs: Number of analog inputs defined at initialization, defaults to 0
        :type n_analog_inputs: int, optional
        :param n_digital_outputs: Number of digital outputs defined at initialization, defaults to 0
        :type n_digital_outputs: int, optional
        :param n_digital_inputs: Number of digital inputs defined at initialization, defaults to 0
        :type n_digital_inputs: int, optional
        :param controller_type: defaults to "opx1"
        :type controller_type: str, optional
        """
        self.name = name
        self.dict = dict()
        self.dict["type"] = controller_type
        self.dict["analog_outputs"] = {
            i: {"offset": 0} for i in range(1, n_analog_outputs + 1)
        }
        self.dict["analog_inputs"] = {
            i: {"offset": 0} for i in range(1, n_analog_inputs + 1)
        }
        self.dict["digital_outputs"] = {
            i: {"offset": 0} for i in range(1, n_digital_outputs + 1)
        }
        self.dict["digital_inputs"] = {
            i: {"offset": 0} for i in range(1, n_digital_inputs + 1)
        }
        self.analog_input_ports = [
            AnalogInputPort(name, i) for i in range(1, n_analog_inputs + 1)
        ]
        self.analog_output_ports = [
            AnalogOutputPort(name, i) for i in range(1, n_analog_outputs + 1)
        ]
        self.digital_output_ports = [
            DigitalOutputPort(name, i) for i in range(1, n_digital_outputs + 1)
        ]
        self.digital_input_ports = [
            DigitalInputPort(name, i) for i in range(1, n_digital_inputs + 1)
        ]

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
        self.use_analog_output_port(port, offset)
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
        self.use_analog_input_port(port, offset)
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
        self.use_digital_output_port(port, offset)
        return self.digital_output_ports[-1]

    def digital_input(self, port: int, offset: float = 0):

        for (i, p) in enumerate(self.digital_ports):
            if port == p.info[1]:
                p.offset = offset
                return p
        self.use_digital_input_port(port, offset)
        return self.digital_input_ports[-1]

    def __contains__(self, port) -> bool:
        for p in self.input_ports + self.output_ports + self.digital_ports:
            if port == p:
                return True
        return False

    def use_analog_input_port(self, port_num: int, offset: float = 0.0):
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

    def use_analog_output_port(self, port_num: int, offset: float = 0.0):
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

    def use_digital_output_port(self, port_num: int, offset: float = 0.0):
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

    def use_digital_input_port(self, port_num: int, offset: float = 0.0):
        """Adds an instance of  DigitalInputPort to configuration if it is not used

        :param port_num: port number
        :type port_num: int
        :param offset: defaults to 0.0
        :type offset: float, optional
        """
        if port_num not in self.dict["digital_inputs"]:
            self.dict["digital_inputs"][port_num] = {"offset": offset}
            self.digital_input_ports += [
                DigitalInputPort(self.name, port_num, offset=offset)
            ]

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


class ConstantWaveform(Waveform):
    def __init__(self, name: str, sample: float):
        """A constant amplitude WF

        :param name: name of the WF
        :type name: str
        :param sample: Amplitude of the WF in the range -.5 to .5
        :type sample: float
        """
        super().__init__(name, {"type": "constant", "sample": sample})


class DigitalWaveform:
    def __init__(self, name: str, samples: List[DigitalSample]):
        """A ditial waveform played from a digital output

        :param name: The name of the digital waveform, defaults to "ON"
        :type name: str
        :param samples: The digital waveforms, specified in the format [(1/0, dur),...] where dur is in nanoseconds.  defaults to [(1, 0)]
        :type samples: List[DigitalSample]
        """
        self.name = name
        self.dict = dict()
        if isinstance(samples[0], DigitalSample):
            self._samples = samples
        else:
            self._samples = [
                DigitalSample(state, duration) for (state, duration) in samples
            ]
        self.dict["samples"] = [(ds.state, ds.duration) for ds in self._samples]

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
    def __init__(self, name: str, wfs: List[Waveform], length: int):
        """A pulse which can be used by a QUA measure() command

        :param name: name for this pulse
        :type name: str
        :param wfs: waveforms to be played during measurement
        :type wfs: List[Waveform]
        :param length: duration of the measurment pulse
        :type length: int, optional
        """
        super().__init__(name, wfs, "measure", length)
        self.integration_weights = []

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

    def _add(self, w: Union[Weights, DigitalWaveform]):
        if isinstance(w, Weights):
            if isinstance(w.weights, ConstantIntegrationWeights):
                assert w.weights.dict["cosine"][0][1] == self.dict["length"]
            else:
                assert len(w.weights.dict["sine"]) == self.dict["length"] // 4
            self.integration_weights.append(w)
        elif isinstance(w, DigitalWaveform):
            self.digital_marker = w


class ControlPulse(Pulse):
    def __init__(self, name: str, wfs: List[Waveform], length: int):
        """A pulse which can be used by a QUA play() command
        :return:
        :rtype: ControlPulse
        """
        super().__init__(name, wfs, "control", length)

    def add(self, w: DigitalWaveform):
        self.digital_marker = w
        return self


class Mixer:
    def __init__(
        self,
        name: str,
        intermediate_frequency: int,
        lo_frequency: int,
        correction: Matrix2x2,
    ):
        """A microwave mixer

        :param name: name for this mixer
        :type name: str
        :param intermediate_frequency: intermediate_frequency in MHz
        :type intermediate_frequency: int
        :param lo_frequency:  local oscillator frequency in MHz
        :type lo_frequency: int
        :param correction: correction matrix for this mixer
        :type correction: Matrix2x2
        """
        self.name = name
        self._correction = correction
        self.dict = dict()
        self.dict["intermediate_frequency"] = intermediate_frequency
        self.dict["lo_frequency"] = lo_frequency
        self.dict["correction"] = list(correction.data[0] + correction.data[1])

    @property
    def intermediate_frequency(self):
        return self.dict["intermediate_frequency"]

    @intermediate_frequency.setter
    def intermediate_frequency(self, if_freq: int):
        self.dict["intermediate_frequency"] = if_freq

    @property
    def lo_frequency(self):
        return self.dict["lo_frequency"]

    @lo_frequency.setter
    def lo_frequency(self, lo_freq: int):
        self.dict["lo_frequency"] = lo_freq

    @property
    def correction(self):
        return self._correction

    @correction.setter
    def correction(self, correction: Matrix2x2):
        self._correction = correction
        self.dict["correction"] = list(correction.data[0] + correction.data[1])


class Element:
    def __init__(
        self,
        name: str,
        analog_input_ports: List[AnalogOutputPort] = [],
        analog_output_ports: List[AnalogInputPort] = [],
        digital_input_ports: List[DigitalOutputPort] = [],
        digital_output_ports: List[DigitalInputPort] = [],
        intermediate_frequency: int = None,
        lo_frequency: int = None,
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
        self.name = name
        self.dict = dict()
        assert len(analog_input_ports) <= 2
        self.type = "singleInput" if len(analog_input_ports) == 1 else "mixInputs"
        self.pulses = []
        self.analog_input_ports = analog_input_ports
        self.analog_output_ports = analog_output_ports
        self.digital_output_ports = digital_output_ports
        self.digital_input_ports = digital_input_ports
        self.mixer = None
        if len(analog_input_ports) > 0:
            if self.type == "singleInput":
                port = analog_input_ports[0]
                self.dict["singleInput"] = dict()
                self.dict["singleInput"]["port"] = port.info
            elif self.type == "mixInputs":
                I = analog_input_ports[0]
                Q = analog_input_ports[1]
                self.dict["mixInputs"] = dict()
                self.dict["mixInputs"]["I"] = I.info
                self.dict["mixInputs"]["Q"] = Q.info
                self.dict["mixInputs"]["lo_frequency"] = lo_frequency
        if len(analog_output_ports) > 0:
            self.dict["outputs"] = dict()
            for i, port in enumerate(analog_output_ports):
                self.dict["outputs"]["out" + str(i + 1)] = port.info
        self.dict["operations"] = dict()
        self.dict["intermediate_frequency"] = intermediate_frequency
        # self.dict["outputPulseParameters"] = dict()
        if len(digital_input_ports) > 0:
            self.dict["digitalInputs"] = dict()
            for i, port in enumerate(digital_input_ports):
                self.dict["digitalInputs"]["in" + str(i + 1)] = {
                    "port": port.info,
                    "delay": 0,
                    "buffer": 0,
                }

    def set_delay(self, port_id: int, val: int):
        if "in" + str(port_id) in self.dict["digitalInputs"].keys():
            self.dict["digitalInputs"]["in" + str(port_id)]["delay"] = val
        else:
            raise ConfigurationError("digital input port must be set first")

    def set_buffer(self, port_id: int, val: int):
        if "in" + str(port_id) in self.dict["digitalInputs"].keys():
            self.dict["digitalInputs"]["in" + str(port_id)]["buffer"] = val
        else:
            raise ConfigurationError("digital input port must be set first")

    def _add_mixer(self, mix: Mixer):
        assert "mixInputs" in self.dict.keys()
        self.dict["mixInputs"]["mixer"] = mix.name
        self.mixer = mix

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

    def _add_operation(self, op: Operation):
        self.dict["operations"][op.name] = op.pulse.name
        self.pulses.append(op.pulse)

    def _add(self, obj: Union[Operation, Mixer]):
        """A method to add components to an element

        :param obj: The component to be added
        :type obj: [type]
        :raises ConfigurationError: [description]
        """
        if isinstance(obj, Operation):
            self._add_operation(obj)
        elif isinstance(obj, Mixer):
            self._add_mixer(obj)
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
        digital_input_ports: List[DigitalOutputPort] = [],
        intermediate_frequency: int = None,
        lo_frequency: int = None,
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
        super().__init__(
            name, analog_output_ports, analog_input_ports, digital_input_ports
        )
        self.dict["time_of_flight"] = 0
        self.dict["smearing"] = 0
        self.dict["intermediate_frequency"] = intermediate_frequency

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
        super().__init__(name, [(cosine, duration)], [(sine, duration)])

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
        assert len(sine) == len(cosine)
        super().__init__(name, cosine, sine)

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


class ElementCollection:
    def __init__(self, name: str, elements: List[Element] = []):
        """A named collection of Elements

        It also a useful base class for building components.
        """
        self.name = name
        self.elements = elements

    @property
    def ports(self):
        ports = []
        for elm in self.elements:
            ports += elm.ports
        return ports

    @property
    def waveform_names(self):
        names = []
        for elm in self.elements:
            names += elm.waveform_names
        return names

    @property
    def operation_names(self):
        names = []
        for elm in self.elements:
            names += elm.operation_names
        return names

    @property
    def pulse_names(self):
        names = []
        for elm in self.elements:
            names += elm.pulse_names
        return names


class ReadoutResonator(ElementCollection):
    def __init__(
        self,
        name: str,
        outputs: List[AnalogOutputPort],
        inputs: List[AnalogInputPort],
        intermediate_frequency: int,
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
        if len(outputs) != 2:
            raise ConfigurationError("Number of output ports is not equal to 2")
        if len(inputs) != 2:
            raise ConfigurationError("Number of input ports is not equal to 2")
        drive = MeasureElement(
            name, outputs, inputs, intermediate_frequency=intermediate_frequency
        )
        super().__init__(name=name, elements=[drive])

    @property
    def intermediate_frequency(self):
        return self.elements[0].intermediate_frequency

    @intermediate_frequency.setter
    def intermediate_frequency(self, if_freq: int):
        """Set an IF for the resonator

        :param if_freq: A frequency in MHz
        :type if_freq: int
        """
        self.elements[0].intermediate_frequency = if_freq

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

    def _add(self, op: Operation):
        """Add operation associated with the Readout resonator

        :param obj: The operation
        :type obj: Operation

        """
        if len(op.pulse.wfs) == 2:
            self.elements[0].add(op)
        else:
            raise ConfigurationError("adding unsupported object")

    @property
    def time_of_flight(self):
        return self.elements[0].time_of_flight

    @time_of_flight.setter
    def time_of_flight(self, tof: int):
        self.elements[0].time_of_flight = tof

    @property
    def smearing(self):
        return self.elements[0].smearing

    @smearing.setter
    def smearing(self, t: int):
        self.elements[0].smearing = t

    @property
    def lo_frequency(self):
        return self.elements[0].lo_frequency

    @lo_frequency.setter
    def lo_frequency(self, lo_frequency: int):
        self.elements[0].lo_frequency = lo_frequency

    @property
    def input_ports(self):
        return self.elements[0].analog_input_ports

    @input_ports.setter
    def input_ports(self, ports: List[AnalogInputPort]):
        assert len(ports) == 2
        self.elements[0].analog_input_ports = ports
        for i, port in enumerate(ports):
            self.elements[0].dict["outputs"]["out" + str(i)] = port.info

    @property
    def output_ports(self):
        return self.elements[0].analog_output_ports

    @output_ports.setter
    def output_ports(self, ports: List[AnalogOutputPort]):
        assert len(ports) == 2
        self.elements[0].analog_output_ports = ports
        self.elements[0].dict["mixInputs"]["I"] = ports[0].info
        self.elements[0].dict["mixInputs"]["Q"] = ports[1].info

    @property
    def mixer(self):
        return self.elements[0].mixer

    @mixer.setter
    def mixer(self, mixer: Mixer):
        self.elements[0].mixer = mixer
        self.elements[0].dict["mixInputs"]["mixer"] = mixer.name


class Transmon(ElementCollection):
    def __init__(
        self,
        name: str,
        I: AnalogOutputPort,
        Q: AnalogOutputPort,
        intermediate_frequency: int,
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
        drive = Element(name, [I, Q], intermediate_frequency=intermediate_frequency)
        super().__init__(name=name, elements=[drive])

    @property
    def I(self):
        return self.elements[0].output_ports[0]

    @I.setter
    def I(self, p: AnalogOutputPort):
        self.elements[0].output_ports[0] = p
        self.elements[0].dict["mixInputs"]["I"] = p.info

    @property
    def Q(self):
        return self.elements[0].output_ports[1]

    @Q.setter
    def Q(self, p: AnalogOutputPort):
        self.elements[0].output_ports[1] = p
        self.elements[0].dict["mixInputs"]["Q"] = p.info

    @property
    def lo_frequency(self):
        return self.elements[0].lo_frequency

    @lo_frequency.setter
    def lo_frequency(self, lo_frequency: int):
        self.elements[0].lo_frequency = lo_frequency

    @property
    def intermediate_frequency(self):
        return self.elements[0].intermediate_frequency

    @intermediate_frequency.setter
    def intermediate_frequency(self, if_freq: int):
        """Set an IF for the transmon

        :param if_freq: A frequency in MHz
        :type if_freq: int
        """
        self.elements[0].intermediate_frequency = if_freq

    def add(self, op: Union[Operation, List[Operation]]):
        """Add list of operations associated with the Transmon

        :param obj: The operations
        :type obj: list or an instance of Operation
        """
        if isinstance(op, list):
            for o in op:
                self._add(o)
        else:
            self._add(op)
        return self

    def _add(self, op: Operation):
        if len(op.pulse.wfs) == 2:
            self.elements[0].add(op)
        else:
            raise ConfigurationError("adding unsupported object")

    @property
    def mixer(self):
        return self.elements[0].mixer

    @mixer.setter
    def mixer(self, mixer: Mixer):
        self.elements[0].mixer = mixer
        self.elements[0].dict["mixInputs"]["mixer"] = mixer.name


class FluxTunableTransmon(Transmon):
    def __init__(
        self,
        name: str,
        I: AnalogOutputPort,
        Q: AnalogOutputPort,
        fl_port: AnalogOutputPort,
        intermediate_frequency: int,
    ):
        """A flux tuneable superconducting transmon qubit

        :param name: A name for this transmon
        :type name: str
        :param I: I output port
        :type I: AnalogOutputPort
        :param Q: Q output port
        :type Q: AnalogOutputPort
        :param fl_port:  Flux line output Port
        :type fl_port: AnalogOutputPort
        :param intermediate_frequency: intermediate frequency of the upconversion IQ mixer in MHz
        :type intermediate_frequency: int
        """
        super().__init__(name, I, Q, intermediate_frequency)
        self.elements.append(Element(name + "_flux_line", [fl_port]))

    def _add(self, op: Operation):
        if len(op.pulse.wfs) == 2:
            self.elements[0].add(op)
        elif len(op.pulse.wfs) == 1:
            self.elements[1].add(op)
        else:
            raise ConfigurationError(
                "Can not add a pulse with {0} waveforms".format(len(op.pulse.wfs))
            )


class Coupler(ElementCollection):
    def __init__(self, name: str, p: AnalogOutputPort):
        coupler = Element(name, analog_output_ports=[p])
        super().__init__(name=name, elements=[coupler])

    def _add(self, op: Operation):
        if len(op.pulse.wfs) == 1:
            self.elements[0].add(op)
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
    def p(self):
        return self.elements[0].analog_output_ports[0]

    @p.setter
    def p(self, p: AnalogOutputPort):
        self.elements[0].analog_output_ports[0] = p


class Oscillator:
    def __init__(
        self, name: str, intermediate_frequency: int, lo_frequency: int, mixer: str
    ):
        self.name = name
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
