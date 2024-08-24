from enum import Enum
from typing import Union, List

from .channel_spec import ChannelSpec
from ..instruments.instrument_channel import InstrumentChannel, InstrumentChannelInput, InstrumentChannelOutput


class WiringFrequency(Enum):
    DC = "DC"
    RF = "RF"

class WiringIOType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INPUT_AND_OUTPUT = "input_output"

class WiringLineType(Enum):
    RESONATOR = "rr"
    DRIVE = "xy"
    FLUX = "z"
    COUPLER = "c"

class WiringSpec:
    """
    A technical specification for the wiring that will be required to
    manipulate the given quantum elements.
    """

    def __init__(
        self,
        frequency: WiringFrequency,
        io_type: WiringIOType,
        line_type: WiringLineType,
        channel_specs: Union[ChannelSpec, List[ChannelSpec]],
        elements: Union['Element', List['Element']],
    ):
        self.frequency = frequency
        self.io_type = io_type
        self.line_type = line_type
        if isinstance(channel_specs, ChannelSpec):
            channel_specs = [channel_specs]
        if channel_specs is None:
            channel_specs = []
        self.channel_specs = channel_specs
        if not isinstance(elements, list):
            elements = [elements]
        self.elements: List['Element'] = elements


    def get_channel_template_from_spec(self, channel_spec: ChannelSpec) -> List[InstrumentChannel]:
        if self.io_type == WiringIOType.INPUT_AND_OUTPUT or self.io_type is None:
            return channel_spec.channel_templates
        elif self.io_type == WiringIOType.INPUT:
            return list(filter(
                lambda channel: isinstance(channel, InstrumentChannelInput),
                channel_spec.channel_templates
            ))
        elif self.io_type == WiringIOType.OUTPUT:
            return list(filter(
                lambda channel: isinstance(channel, InstrumentChannelOutput),
                channel_spec.channel_templates
            ))
        else:
            raise TypeError(f"Unrecognized input or output channel type {self.io_type}")
