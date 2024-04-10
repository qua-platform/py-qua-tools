import copy
import warnings
from typing import Union, List

from qualang_tools.config.components import (
    Controller,
    ElementCollection,
    Element,
    Mixer,
    Oscillator,
    MeasureElement,
    MeasurePulse,
)
from qualang_tools.config.configuration import QMConfiguration
from qualang_tools.config.exceptions import ConfigurationError
from qualang_tools.config.parameters import _is_parametric
from qualang_tools.config.primitive_components import (
    AnalogOutputPort,
    AnalogInputPort,
    DigitalOutputPort,
    Waveform,
    Pulse,
    IntegrationWeights,
    DigitalInputPort,
    Port,
)


class ConfigBuilder:
    def __init__(self) -> None:
        """A class used to build the configuration of an experiment with QUA"""
        warnings.warn(
            "ConfigBuilder is no longer being actively developed and may not support all config functionality",
            DeprecationWarning,
            stacklevel=2,
        )
        self.objects = []
        self.configuration = QMConfiguration([])
        self.controllers = []
        self.components: List[ElementCollection] = []

    def add(self, obj):
        """Adds an entity to the configuraiton.

        :param obj: Any entity type supported by the configuration system, e.g. Element, ArbitraryWaveform or Transmon
        :type obj:
        """
        if isinstance(obj, list):
            for _obj in obj:
                if isinstance(_obj, ElementCollection):
                    self.components.append(_obj)
                else:
                    self.objects.append(_obj)
        else:
            if isinstance(obj, ElementCollection):
                self.components.append(obj)
            else:
                self.objects.append(obj)
        return self

    @property
    def ports(self):
        ports = []
        for cont in self.controllers:
            ports += cont.ports
        return ports

    def _add_controller(self, cont: Controller):
        self.controllers.append(cont)
        for port in cont.ports:
            port_info = port.info[1]
            if isinstance(port, AnalogOutputPort):
                port_dict = cont.dict["analog_outputs"][port_info]
                if port.delay is not None:
                    port_dict["delay"] = port.delay
                if port.filter is not None:
                    port_dict["filter"] = {
                        "feedback": port.filter.feedback,
                        "feedforward": port.filter.feedforward,
                    }
                if port.crosstalk is not None:
                    port_dict["crosstalk"] = port.crosstalk
                port_dict["offset"] = port.offset
                port_dict["shareable"] = port.shareable
            elif isinstance(port, AnalogInputPort):
                port_dict = cont.dict["analog_inputs"][port_info]
                if port.gain_db is not None:
                    port_dict["gain_db"] = port.gain_db
                port_dict["offset"] = port.offset
                port_dict["shareable"] = port.shareable
            elif isinstance(port, DigitalOutputPort):
                port_dict = cont.dict["digital_outputs"][port_info]
                port_dict["shareable"] = port.shareable
            elif isinstance(port, DigitalInputPort):
                port_dict = cont.dict["digital_inputs"][port_info]
                if port.polarity is not None:
                    port_dict["polarity"] = port.polarity
                if port.threshold is not None:
                    port_dict["threshold"] = port.threshold
                if port.window is not None:
                    port_dict["window"] = port.window
                port_dict["shareable"] = port.shareable
        self.configuration.config["controllers"][cont.name] = cont.dict

    def build(self, config=None):
        """Generates the QUA configuration represented by the current state of the builder object

        :param config: An initial QUA config, defaults to {}
        :type config: Dict, optional
        :return: QUA configuration
        :rtype: Dict
        """
        if config is None:
            config = {}
        if config == {}:
            self.configuration.reset()
            self.controllers = []
        else:
            self.configuration.config = copy.deepcopy(config)
        objects = self.objects
        for c in self.components:
            objects = objects + c.get_elements()

        for obj in objects:
            if _is_parametric(obj):
                raise ConfigurationError("set the parameters of {0}".format(obj.name))
            if isinstance(obj, Controller):
                self._add_controller(obj)
            # elif isinstance(obj, ElementCollection):
            #    for _obj in obj.get_elements():
            #        self._objects.append(_obj)
            elif isinstance(obj, Waveform):
                self.configuration.add_waveform(obj)
            elif isinstance(obj, Pulse):
                self.configuration.add_pulse(obj)
            elif isinstance(obj, Element):
                self.configuration.add_element(obj)
            elif isinstance(obj, IntegrationWeights):
                self.configuration.add_integration_weights(obj)
            elif isinstance(obj, Mixer):
                self.configuration.add_mixer(obj)
            elif isinstance(obj, Oscillator):
                self.configuration.add_oscillator(obj)
            else:
                raise NotImplementedError("Can not add objects of type {0}".format(type(obj)))
        return self.configuration.config

    def find_instances(self, obj_type):
        """Find instances of a certain class in the configuration

        :param obj_type: The required type
        :type obj_type: [type]
        :return: A list of instances
        :rtype: list
        """
        return [elm for elm in self.objects if isinstance(elm, obj_type)]

    def find_users_of(
        self,
        elm: Union[
            AnalogInputPort,
            AnalogOutputPort,
            Controller,
            Waveform,
            Pulse,
            Mixer,
            Oscillator,
        ],
    ):
        """Find where in the configuration a specific object is used

        :param elm: The element of interest
        :type elm: Union[AnalogInputPort, AnalogOutputPort, Controller, Waveform, Pulse]
        :return: A set of users
        :rtype: Set
        """
        if (
            isinstance(elm, AnalogInputPort)
            or isinstance(elm, AnalogOutputPort)
            or isinstance(elm, DigitalInputPort)
            or isinstance(elm, DigitalOutputPort)
        ):
            return self._find_users_of_port(elm)
        elif isinstance(elm, Controller):
            return self._find_users_of_controller(elm)
        elif isinstance(elm, Waveform):
            return self._find_users_of_waveform(elm)
        elif isinstance(elm, Pulse):
            return self._find_users_of_pulse(elm)
        elif isinstance(elm, IntegrationWeights):
            return self._find_users_of_integration_weights(elm)
        elif isinstance(elm, Mixer):
            return self._find_users_of_mixer(elm)
        else:
            raise NotImplementedError("can not find objects of type {}".format(type(elm)))

    def _find_users_of_port(self, port: Port):
        objects = []
        for obj in self.objects:
            if isinstance(obj, Element) or isinstance(obj, MeasureElement):
                if port in obj.ports:
                    objects.append(obj)
        return set(objects)

    def _find_users_of_controller(self, cont: Controller):
        objects = []
        for obj in self.objects:
            if isinstance(obj, Element) or isinstance(obj, MeasureElement):
                for port in obj.ports:
                    if port in cont.ports:
                        objects.append(obj)
                        break
        return set(objects)

    def _find_users_of_waveform(self, wf: Waveform):
        objects = []
        for obj in self.objects:
            if isinstance(obj, Element) or isinstance(obj, MeasureElement):
                for name in obj.waveform_names:
                    if name == wf.name:
                        objects.append(obj)
        return set(objects)

    def _find_users_of_pulse(self, elm: Pulse):
        objects = []
        for obj in self.objects:
            if isinstance(obj, Element) or isinstance(obj, MeasureElement):
                for name in obj.pulse_names:
                    if name == elm.name:
                        objects.append(obj)
        return set(objects)

    def _find_users_of_integration_weights(self, elm: IntegrationWeights):
        objects = []
        for obj in self.objects:
            if isinstance(obj, MeasurePulse):
                for w in obj.integration_weights:
                    if w.name == elm.name:
                        objects.append(obj)
        return set(objects)

    def _find_users_of_mixer(self, elm: Mixer):
        objects = []
        for obj in self.objects:
            if isinstance(obj, Oscillator):
                if obj.mixer == elm.name:
                    objects.append(obj)
            elif isinstance(obj, Element):
                if obj.mixer.name == elm.name:
                    objects.append(obj)
        return set(objects)

    def component(self, name: str):
        """Returns a config builder object with the given name
        :param name: name of the object
        :type name: str
        """
        for c in self.objects + self.components:
            if c.name == name:
                return c
