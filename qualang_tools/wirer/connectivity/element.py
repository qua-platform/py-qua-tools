from dataclasses import dataclass, field
from typing import List, Dict, Any, Union

from .wiring_spec import WiringLineType
from ..instruments.instrument_channel import AnyInstrumentChannel


@dataclass(frozen=True)
class QubitReference:
    index: int

    def __str__(self):
        return f"q{self.index}"

@dataclass(frozen=True)
class QubitPairReference:
    control_index: int
    target_index: int

    def __str__(self):
        return f"q{self.control_index}{self.target_index}"



ElementId = Union[QubitReference, QubitPairReference]


@dataclass
class Element:
    id: ElementId
    channels: Dict[WiringLineType, List[AnyInstrumentChannel]] = field(default_factory=dict)

    def __str__(self):
        return str(self.channels)

    def __eq__(self, other):
        return self.id == other.id