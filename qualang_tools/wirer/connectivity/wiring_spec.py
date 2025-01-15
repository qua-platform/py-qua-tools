from enum import Enum
from typing import Union, List

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qualang_tools.wirer.connectivity.channel_spec import ChannelSpec
    from qualang_tools.wirer.connectivity.element import Element


class WiringFrequency(Enum):
    DC = "DC"
    RF = "RF"


DC = WiringFrequency.DC
RF = WiringFrequency.RF


class WiringIOType(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INPUT_AND_OUTPUT = "input/output"


INPUT = WiringIOType.INPUT
OUTPUT = WiringIOType.OUTPUT
INPUT_AND_OUTPUT = WiringIOType.INPUT_AND_OUTPUT


class WiringLineType(Enum):
    RESONATOR = "rr"
    DRIVE = "xy"
    FLUX = "z"
    CHARGE = "q"
    COUPLER = "c"
    CROSS_RESONANCE = "cr"
    ZZ_DRIVE = "zz"


RESONATOR = WiringLineType.RESONATOR
DRIVE = WiringLineType.DRIVE
FLUX = WiringLineType.FLUX
CHARGE = WiringLineType.CHARGE
COUPLER = WiringLineType.COUPLER
CROSS_RESONANCE = WiringLineType.CROSS_RESONANCE
ZZ_DRIVE = WiringLineType.ZZ_DRIVE


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
        constraints: "ChannelSpec",
        elements: Union["Element", List["Element"]],
    ):
        self.frequency = frequency
        self.io_type = io_type
        self.line_type = line_type
        self.triggered = triggered
        self.constraints = constraints
        if not isinstance(elements, list):
            elements = [elements]
        self.elements: List["Element"] = elements
