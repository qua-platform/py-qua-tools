import copy
from typing import List, Dict

from qualang_tools.config.components import (
    Controller,
    MeasurePulse,
    Element,
    ConstantWaveform,
    ArbitraryWaveform,
    Mixer,
    Oscillator,
)
from qualang_tools.config.parameters import _is_callable, _is_parametric
from qualang_tools.config.primitive_components import (
    Waveform,
    Pulse,
    IntegrationWeights,
)


class QMConfiguration:
    def __init__(self, controllers: List[Controller] = None, version: int = 1):
        """A class to generate the QM configuration

        :param controllers: A controller or list of controllers used in this configuration, defaults to None
        :type controllers: List[Controller], optional
        :param version: Controller version, defaults to 1
        :type version: int, optional
        """
        self.config = dict()
        self.config["version"] = 1
        self.config["controllers"] = dict()
        for cont in controllers:
            self.config["controllers"][cont.name] = self._call_dict_parameters(cont.dict)
        self.config["elements"] = dict()
        self.config["pulses"] = dict()
        self.config["waveforms"] = dict()
        self.config["digital_waveforms"] = dict()
        self.config["integration_weights"] = dict()
        self.config["mixers"] = dict()
        self.config["oscillators"] = dict()

    def add_waveform(self, wf: Waveform):
        """Add a single waveform to this configuration

        :param wf: a Wavefrom object
        :type wf: Waveform
        """
        self.config["waveforms"][wf.name] = self._call_dict_parameters(wf.dict)

    def _call_dict_parameters(self, dic: Dict):
        if _is_callable(dic):
            if not _is_parametric(dic):
                _dic = copy.deepcopy(dic)
                for k, v in _dic.items():
                    if _is_callable(v):
                        if isinstance(v, dict):
                            _dic[k] = self._call_dict_parameters(v)
                        elif isinstance(v, list):
                            _dic[k] = [e() if _is_callable(e) else e for e in v]
                        else:
                            _dic[k] = v()
                return _dic
        return dic

    def _call_weights_dict(self, dic: Dict):
        if _is_callable(dic):
            if not _is_parametric(dic):
                _dic = copy.deepcopy(dic)
                for k, v in _dic.items():
                    if isinstance(_dic["cosine"][0], tuple):
                        val = _dic["cosine"][0][0]
                        if _is_callable(_dic["cosine"][0][0]):
                            val = _dic["cosine"][0][0]()
                        dur = _dic["cosine"][0][1]
                        if _is_callable(_dic["cosine"][0][1]):
                            dur = _dic["cosine"][0][1]()
                        _dic["cosine"][0] = (val, dur)

                    if isinstance(_dic["sine"][0], tuple):
                        val = _dic["sine"][0][0]
                        if _is_callable(_dic["sine"][0][0]):
                            val = _dic["sine"][0][0]()
                        dur = _dic["sine"][0][1]
                        if _is_callable(_dic["sine"][0][1]):
                            dur = _dic["sine"][0][1]()
                        _dic["sine"][0] = (val, dur)

                    elif _is_callable(_dic["cosine"]):
                        _dic["cosine"] = _dic["cosine"]()

                        if _is_callable(_dic["sine"]):
                            _dic["sine"] = _dic["sine"]()
                return _dic
        return dic

    def add_waveforms(self, wfs: List[Waveform]):
        """Add a list of waveforms to this configuration

        :param wfs: a list of Waveform objects
        :type wfs: List[Waveform]
        """
        for wf in wfs:
            self.add_waveform(wf)

    def add_pulse(self, pulse: Pulse):
        """Add a pulse to this configuration

        :param pulse: a Pulse object
        :type pulse: Pulse
        """
        _dict = copy.deepcopy(pulse.dict)
        self.add_waveforms(pulse.wfs)
        if pulse.digital_marker is not None:
            _dict["digital_marker"] = pulse.digital_marker.name
            self.config["digital_waveforms"][pulse.digital_marker.name] = self._call_dict_parameters(
                pulse.digital_marker.dict
            )
        if isinstance(pulse, MeasurePulse):
            _dict["integration_weights"] = dict()
            for w in pulse.integration_weights:
                _dict["integration_weights"][w.name] = w.weights.name
                self.config["integration_weights"][w.weights.name] = self._call_weights_dict(w.weights.dict)
        self.config["pulses"][pulse.name] = self._call_dict_parameters(_dict)

    def add_pulses(self, pulses: List[Pulse]):
        """Add a list of Pulses to this configuration

        :param pulses: a list of Pulse objects
        :type pulses: List[Pulse]
        """
        for pulse in pulses:
            self.add_pulse(pulse)

    def add_element(self, elm: Element):
        """Add a quantum element to this configuration

        :param elm: an object of type Element
        :type elm: Element
        """
        # check if input/output ports belong to the controller
        self.config["elements"][elm.name] = self._call_dict_parameters(elm.dict)
        if elm.type == "mixInputs":
            if elm.mixer is not None:
                self.add_mixer(elm.mixer)
            if elm.oscillator is not None:
                self.add_oscillator(elm.oscillator)
        self.add_pulses(elm.pulses)

    def update_pulse(self, elm_name: str, pulse: Pulse):
        """Change the pulse associated with an element to the pulse given

        :param elm_name: name of a quantum element in the configuration
        :type elm_name: str
        :param pulse: a Pulse object
        :type pulse: Pulse
        """
        assert elm_name in self.config["elements"].keys()
        self.config["elements"][elm_name]["operations"][pulse.name] = pulse.name
        self._add_pulse_to_config(pulse)

    def update_integration_weights(self, pulse_name: str, iw: IntegrationWeights):
        """Updates the integration_weights associated with a measurement pulse

        :param pulse_name: name of the measurement pulse
        :type pulse_name: str
        :param iw: IntegrationWeights object
        :type iw: IntegrationWeights
        """
        assert pulse_name in self.config["pulses"].keys()
        assert self.config["pulses"][pulse_name]["operation"] == "measure"
        assert len(self.config["pulses"][pulse_name]["waveforms"].keys()) == 2
        weight_name = pulse_name + "_weight"
        self.config["integration_weights"][weight_name] = self._call_dict_parameters(iw.dict)

    def update_constant_waveform(self, wf_name: str, amp: float):
        """Update the amplitude of an existing constant waveform

        :param wf_name: name of the existing waveform
        :type wf_name: str
        :param amp: amplitude to set in the range (-0.5 to 0.5)
        :type amp: float
        """
        assert wf_name in self.config["waveforms"].keys()
        assert self.config["waveforms"][wf_name]["type"] == "constant"
        self.config["waveforms"][wf_name]["sample"] = amp

    def update_arbitrary_waveform(self, wf_name: str, samples: List[float]):
        """Update the samples of an existing arbitrary waveform

        :param wf_name: name of the existing waveform
        :type wf_name: str
        :param samples: a vector of samples
        :type samples: List[float]
        """
        assert wf_name in self.config["waveforms"].keys()
        assert self.config["waveforms"][wf_name]["type"] == "arbitrary"
        self.config["waveforms"][wf_name]["samples"] = samples

    def reset(self, controllers=None):
        if controllers is None:
            controllers = []
        self.__init__(controllers)

    def update_intermediate_frequency(self, elm_name: str, freq: float, update_mixer: bool = True):
        self.config["elements"][elm_name]["intermediate_frequency"] = freq
        if update_mixer:
            m_name = self.config["elements"][elm_name]["mixer"]
            self.config["mixers"][m_name]["intermediate_frequency"] = freq

    def get_waveforms_from_op(self, elm_name, op_name):
        """Get waveforms associated with an operation

        :param elm_name: name of the element
        :type elm_name: [type]
        :param op_name: name of the operation
        :type op_name: [type]

        """
        assert elm_name in self.config["elements"].keys()
        assert op_name in self.config["elements"]["operations"].keys()
        waveforms = self.config["pulses"][op_name]["waveforms"]
        if waveforms.keys() == ["single"]:
            wf = waveforms["single"]
            _dict = self.config["waveforms"][wf]
            return [self.waveform_from_dict(wf, _dict)]
        else:
            wfI, wfQ = waveforms["I"], waveforms["Q"]
            _dictI = self.config["waveforms"][wfI]
            _dictQ = self.config["waveforms"][wfQ]
            return [
                self.waveform_from_dict(wfI, _dictI),
                self.waveform_from_dict(wfQ, _dictQ),
            ]

    def waveform_from_dict(self, wf, _dict):
        if _dict["type"] == "constant":
            return ConstantWaveform(wf, _dict["sample"])
        else:
            return ArbitraryWaveform(wf, _dict["samples"])

    def add_controller(self, cont: Controller):
        """Add a controller to this configuration

        :param cont: A Controller object
        :type cont: Controller
        """
        self.config["controllers"][cont.name] = cont.dict

    def add_integration_weights(self, weight: IntegrationWeights):
        """Add integration weights to this configuration

        :param weight: an IntegrationWeights object
        :type weight: IntegrationWeights
        """
        self.config["integration_weights"][weight.name] = self._call_dict_parameters(weight.dict)

    def add_mixer(self, mixer: Mixer):
        """Add a mixer to this configuration

        :param mixer: A Mixer object
        :type mixer: Mixer
        """
        self.config["mixers"][mixer.name] = [self._call_dict_parameters(data) for data in mixer.dict]

    def add_oscillator(self, oscillator: Oscillator):
        """Add an oscillator to this configuration

        :param oscillator: an Oscillator object
        :type oscillator: Oscillator
        """
        self.config["oscillators"][oscillator.name] = self._call_dict_parameters(oscillator.dict)
