from dataclasses import dataclass
from typing import List, Dict, Union

from .wiring_spec import WiringLineType
from ..instruments.instrument_channel import AnyInstrumentChannel


@dataclass(frozen=True)
class Reference:
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class ElementReference:
    name: str
    index: int

    def __str__(self):
        return f"{self.name}{self.index}"


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
        return f"q{self.control_index}-{self.target_index}"


ElementId = Union[Reference, ElementReference, QubitReference, QubitPairReference]


class Element:
    def __init__(self, id: Union[str, ElementReference, QubitReference, QubitPairReference]):
        if isinstance(id, str):
            id = Reference(id)
        self.id = id
        self.channels: Dict[WiringLineType, List[AnyInstrumentChannel]] = dict()

    def __str__(self):
        return str(self.channels)

    def __eq__(self, other):
        return self.id == other.id
