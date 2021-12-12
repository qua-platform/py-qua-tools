from typing import Any, Dict, List


class Port:
    def __init__(self, controller: str, port_id: int, offset: float = 0) -> None:
        self.info = (controller, port_id)
        self.offset = offset

    def __eq__(self, other) -> bool:
        return self.info == other.info and type(self) == type(other)

    def __str__(self):
        cont, port_id = self.info
        return (
            type(self).__name__
            + "("
            + str(cont)
            + " , "
            + str(port_id)
            + ", offset = "
            + str(self.offset)
            + ")"
        )


class AnalogInputPort(Port):
    def __init__(self, controller: str, port_id: int, offset: float = 0):
        self.gain_db = None
        super().__init__(controller, port_id, offset)


class AnalogOutputPort(Port):
    def __init__(self, controller: str, port_id: int, offset: float = 0):
        self.delay = None
        self.filter = None
        self.channel_weights = None
        super().__init__(controller, port_id, offset)


class DigitalInputPort(Port):
    def __init__(self, controller: str, port_id: int, offset: float = 0):
        self.polarity = None
        self.window = None
        self.threshold = None
        super().__init__(controller, port_id, offset)


class DigitalOutputPort(Port):
    def __init__(self, controller: str, port_id: int, offset: float = 0):
        super().__init__(controller, port_id, offset)


class Waveform:
    def __init__(self, name: str, dictionary: Dict[str, Any]):
        """A waveform played by the QOP

        :param name: name of the played WF
        :type name: str
        :param dictionary: parameters to initialize a WF
        :type dictionary: Dict[str, Any]
        """
        self.name = name
        self.dict = dictionary


class Pulse:
    def __init__(self, name: str, wfs: List[Waveform], operation: str, length: int):
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
        assert len(wfs) <= 2
        self.name = name
        self.wfs = wfs
        self.dict = dict()
        self.dict["operation"] = operation
        self.dict["length"] = length
        self.dict["waveforms"] = dict()
        if len(wfs) == 2:
            self.dict["waveforms"]["I"] = wfs[0].name
            self.dict["waveforms"]["Q"] = wfs[1].name
        else:
            self.dict["waveforms"]["single"] = wfs[0].name

    @property
    def waveform_names(self):
        return [wf.name for wf in self.wfs]


class Operation:
    def __init__(self, pulse: Pulse, name: str = ""):
        self.pulse = pulse
        self.name = pulse.name if name == "" else name


class IntegrationWeights:
    def __init__(self, name: str, cosine: List, sine: List):
        """A vector of integration weights used in integration and demodulation

        :param name: name for the weights vector
        :type name: str
        :param cosine: a list of weights to be used with the cosine demodulation element, specified at 1 sample per nanosecond
        :type cosine: List
        :param sine: a list of weights to be used with the sine demodulation element, specified at 1 sample per nanosecond
        :type sine: List
        """
        self.name = name
        self.dict = dict()
        self.dict["cosine"] = cosine
        self.dict["sine"] = sine


class Weights:
    def __init__(self, weights: IntegrationWeights, name: str = ""):
        self.name = weights.name if name == "" else name
        self.weights = weights


class DigitalSample:
    def __init__(self, state: int, duration: int):
        """A sample to describe digital waveform

        :param state: state of the digital output either 0 or 1
        :type state: int
        :param duration: duration of the output in nanoseconds
        :type duration: int
        """
        assert state == 0 or state == 1
        self.state = state
        self.duration = duration


class Matrix2x2:
    def __init__(self, data: List[List[float]]):
        """A correction matrix for the IQ mixer

        :param data: 2x2 matrix provided as a list containing a list of rows
        :type data: List[List[float]]
        """
        assert len(data) == 2
        assert len(data[0]) == 2
        assert len(data[1]) == 2
        self.data = data


class AnalogOutputFilter:
    def __init__(self, feedback: List[float], feedforward: List[float]):
        """A filter applied to the analog output ports

        :param feedback: feedback taps for the output filter
        :type feedback: List[float]
        :param feedforward: feedforward taps for the output filter
        :type feedforward: List[float]
        """
        self.feedback = feedback
        self.feedforward = feedforward
