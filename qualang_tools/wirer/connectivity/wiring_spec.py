from enum import Enum
from typing import Union, List


class WiringFrequency(Enum):
    DC = "DC"
    RF = "RF"

class WiringIOType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INPUT_AND_OUTPUT = "input/output"

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
        triggered: bool,
        constraints: 'ChannelSpec',
        elements: Union['Element', List['Element']],
    ):
        self.frequency = frequency
        self.io_type = io_type
        self.line_type = line_type
        self.triggered = triggered
        self.constraints = constraints
        if not isinstance(elements, list):
            elements = [elements]
        self.elements: List['Element'] = elements
