import abc
from typing import Any, Dict, List, Optional


class ConfigBuilderClass(abc.ABC):
    def __init__(self, **kwargs) -> None:
        super().__init__()


class ConfigBuilderElement(ConfigBuilderClass):
    def __init__(self, name, **kwargs) -> None:
        super(ConfigBuilderElement, self).__init__()
        self.name = name


class Port(ConfigBuilderClass):
    def __init__(self, controller: str, port_id: int) -> None:
        super(Port, self).__init__()
        self.controller = controller
        self.port_id = port_id

    @property
    def info(self):
        return self.controller, self.port_id

    def __eq__(self, other) -> bool:
        return self.info == other.info and type(self) == type(other)

    def __str__(self):
        cont, port_id = self.info
        return type(self).__name__ + "(" + str(cont) + " , " + str(port_id) + ")"


class AnalogInputPort(Port):
    def __init__(
        self,
        controller: str,
        port_id: int,
        offset: float = 0,
        gain_db: Optional[float] = None,
    ):
        super(AnalogInputPort, self).__init__(controller, port_id)
        self.offset = offset
        self.gain_db = gain_db


class AnalogOutputFilter(ConfigBuilderClass):
    def __init__(self, feedback: List[float], feedforward: List[float]):
        """A filter applied to the analog output ports

        :param feedback: feedback taps for the output filter
        :type feedback: List[float]
        :param feedforward: feedforward taps for the output filter
        :type feedforward: List[float]
        """
        super(AnalogOutputFilter, self).__init__()
        self.feedback = feedback
        self.feedforward = feedforward


class AnalogOutputPort(Port):
    def __init__(
        self,
        controller: str,
        port_id: int,
        offset: float = 0,
        delay: Optional[float] = None,
        filter: Optional[AnalogOutputFilter] = None,
        channel_weights: Optional[float] = None,
    ):
        super(AnalogOutputPort, self).__init__(controller, port_id)
        self.offset = offset
        self.delay = delay
        self.filter = filter
        self.channel_weights = channel_weights


class DigitalInputPort(Port):
    def __init__(
        self,
        controller: str,
        port_id: int,
        polarity: Optional[float] = None,
        window: Optional[float] = None,
        threshold: Optional[float] = None,
    ):
        super(DigitalInputPort, self).__init__(controller, port_id)
        self.polarity = polarity
        self.window = window
        self.threshold = threshold


class DigitalOutputPort(Port):
    def __init__(self, controller: str, port_id: int, offset: float = 0):
        super(DigitalOutputPort, self).__init__(controller, port_id)
        self.offset = offset


class Waveform(ConfigBuilderElement):
    def __init__(self, name: str, dictionary: Dict[str, Any]):
        """A waveform played by the QOP

        :param name: name of the played WF
        :type name: str
        :param dictionary: parameters to initialize a WF
        :type dictionary: Dict[str, Any]
        """
        super(Waveform, self).__init__(name)
        self.dict = dictionary


class Pulse(ConfigBuilderElement):
    def __init__(
        self,
        name: str,
        wfs: List[Waveform],
        operation: str,
        length: int,
        digital_marker: Optional[float] = None,
    ):
        """A an analog pulse

        :param name: Name for this pulse
        :type name: str
        :param wfs: Name of the waveform
        :type wfs: List[Waveform]
        :param operation:
        :type operation: str
        :param length:
        :type length: int
        """
        super(Pulse, self).__init__(name)
        assert len(wfs) <= 2
        self.wfs = wfs
        self.operation = operation
        self.length = length
        self.digital_marker = digital_marker

        self.dict = dict()
        self.dict["operation"] = operation
        self.dict["length"] = length
        self.dict["waveforms"] = dict()
        if len(wfs) == 2:
            self.dict["waveforms"]["I"] = wfs[0].name
            self.dict["waveforms"]["Q"] = wfs[1].name
        elif len(wfs) == 1:
            self.dict["waveforms"]["single"] = wfs[0].name

    @property
    def waveform_names(self):
        return [wf.name for wf in self.wfs]


class Operation(ConfigBuilderClass):
    def __init__(self, pulse: Pulse, name: str = ""):
        super(Operation, self).__init__()
        self.pulse = pulse
        self.name = pulse.name if name == "" else name


class IntegrationWeights(ConfigBuilderElement):
    def __init__(self, name: str, cosine: List, sine: List):
        """A vector of integration weights used in integration and demodulation

        :param name: name for the weights vector
        :type name: str
        :param cosine: a list of weights to be used with the cosine demodulation element, specified at 1 sample per nanosecond
        :type cosine: List
        :param sine: a list of weights to be used with the sine demodulation element, specified at 1 sample per nanosecond
        :type sine: List
        """
        super(IntegrationWeights, self).__init__(name)
        self.dict = dict()
        self.dict["cosine"] = cosine
        self.dict["sine"] = sine

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


class Weights(ConfigBuilderClass):
    def __init__(self, weights: IntegrationWeights, name: str = ""):
        super(Weights, self).__init__()
        self.name = weights.name if name == "" else name
        self.weights = weights


class DigitalSample(ConfigBuilderClass):
    def __init__(self, state: int, duration: int):
        """A sample to describe digital waveform

        :param state: state of the digital output either 0 or 1
        :type state: int
        :param duration: duration of the output in nanoseconds
        :type duration: int
        """
        super(DigitalSample, self).__init__()
        assert state == 0 or state == 1
        self.state = state
        self.duration = duration


class Matrix2x2(ConfigBuilderClass):
    def __init__(self, data: List[List[float]]):
        """A correction matrix for the IQ mixer

        :param data: 2x2 matrix provided as a list containing a list of rows
        :type data: List[List[float]]
        """
        super(Matrix2x2, self).__init__()
        assert len(data) == 2
        assert len(data[0]) == 2
        assert len(data[1]) == 2
        self.data = data


class MixerData(ConfigBuilderClass):
    def __init__(
        self,
        intermediate_frequency: int,
        lo_frequency: int,
        correction: Matrix2x2,
    ):
        """Mixer data

        :param intermediate_frequency: intermediate frequency
        :type intermediate_frequency: int
        :param lo_frequency: frequency of the local oscillator
        :type lo_frequency: int
        :param correction: correction matrix of the mixer
        :type correction: Matrix2x2
        """
        super().__init__()
        self.intermediate_frequency = intermediate_frequency
        self.lo_frequency = lo_frequency
        self.correction = correction
